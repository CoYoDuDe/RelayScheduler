#!/usr/bin/env python3
"""RelayScheduler: Venus-Einstellungen, Wochenpläne und Schalterflanken."""
import fcntl
import json
import logging
import os
from pathlib import Path
import signal
import select
import subprocess
import sys
import tempfile
import time
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from settingsdevice import SettingsDevice
from vedbus import VeDbusService
from engine import Engine, Debounce, minute
from gpio_input import Input
from schema import SCHEMA, plans
from output import Output

PRIVATE = Path('/data/setupOptions/RelayScheduler')
RUNTIME = Path('/run/RelayScheduler')


def remember(keys):
    fd, name = tempfile.mkstemp(prefix='.seen-', dir=str(PRIVATE))
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(keys, f); f.flush(); os.fsync(f.fileno())
        os.replace(name, str(PRIVATE / 'seen.json'))
        directory = os.open(str(PRIVATE), os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(name): os.unlink(name)


class Application:
    def __init__(self, bus):
        self.bus = bus
        self.settings = SettingsDevice(bus, SCHEMA, lambda *args: None)
        self.service = VeDbusService('com.coyodude.relayscheduler', bus=bus, register=False)
        for path, value in {'/Mgmt/ProcessName': __file__, '/Mgmt/ProcessVersion': '0.1',
                            '/Mgmt/Connection': 'GX-Relais', '/DeviceInstance': 0,
                            '/ProductId': 0, '/ProductName': 'RelayScheduler', '/Connected': 1,
                            '/Status/State': 'Deaktiviert', '/Status/Actual': 0,
                            '/Status/Source': '', '/Status/RemainingSeconds': 0,
                            '/Status/Switch': -1, '/Status/Error': '', '/Status/Clock': '',
                            '/Status/Gpio': ''}.items():
            self.service.add_path(path, value)
        self.service.add_path('/Control/Command', -1, writeable=True, onchangecallback=self.command)
        self.service.register()
        self.pending = None
        self.config = None
        self.fault_config = None
        self.output = self.input = self.guard = self.pipe = self.lock = self.engine = None
        self.debounce = Debounce()

    def command(self, path, value):
        if int(value) not in (0, 1, 2) or self.output is None or not int(self.settings['Enabled']):
            return False
        self.pending = int(value)
        return True

    def heartbeat(self, armed, deadline):
        if self.guard.poll() is not None:
            raise RuntimeError('Laufzeitwache hat abgeschaltet; Aktivierung prüfen')
        os.write(self.pipe, (json.dumps({'armed': bool(armed), 'deadline': deadline}) + '\n').encode())

    def stop_output(self):
        self.pending = None
        if self.input:
            self.input.close(); self.input = None
        if self.output:
            try:
                if self.output.read(): self.output.write(0)
            except Exception:
                logging.exception('Ausschalten nicht bestätigt; Laufzeitwache bleibt zuständig')
        if self.pipe is not None:
            os.close(self.pipe); self.pipe = None
        if self.guard:
            try: self.guard.wait(timeout=6)
            except subprocess.TimeoutExpired: pass  # Sperre bleibt beim eigenen Wächter.
            self.guard = None
        if self.lock is not None:
            os.close(self.lock); self.lock = None
        self.output = self.engine = None
        self.debounce = Debounce()

    def start_output(self, cfg):
        number = cfg[0]
        output = Output(self.bus, number)
        self.lock = os.open(str(RUNTIME / ('relay%d.lock' % number)), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.output = output
        read_fd, self.pipe = os.pipe()
        ready_read, ready_write = os.pipe()
        try:
            self.guard = subprocess.Popen([sys.executable, str(Path(__file__).with_name('guard.py')),
                                           str(number), str(read_fd), str(self.lock), str(ready_write)],
                                          pass_fds=(read_fd, self.lock, ready_write))
        finally:
            os.close(read_fd)
            os.close(ready_write)
        try:
            if not select.select([ready_read], [], [], 4)[0] or os.read(ready_read, 32) != b'READY\n':
                raise RuntimeError('Laufzeitwache nicht bereit')
        finally:
            os.close(ready_read)
        seen_path = PRIVATE / 'seen.json'
        seen = json.loads(seen_path.read_text()) if seen_path.exists() else []
        if not isinstance(seen, list) or len(seen) > 128 or any(not isinstance(k, str) for k in seen):
            raise ValueError('Zeitplan-Speicher ungültig')
        self.engine = Engine(seen, remember)
        if cfg[1]:
            self.input = Input(cfg[2], cfg[3], cfg[5])
            self.service['/Status/Gpio'] = '%s / BCM %d' % (self.input.path, cfg[2])
        else:
            self.service['/Status/Gpio'] = 'Schalter deaktiviert'

    def tick(self):
        cfg = (int(self.settings['RelayNumber']), int(self.settings['SwitchEnabled']),
               int(self.settings['GpioBcm']), str(self.settings['GpioChip']),
               int(self.settings['ActiveLow']), str(self.settings['InputBias']),
               str(self.settings['SwitchMode']), int(self.settings['DebounceMs']),
               int(self.settings['Enabled']))
        try:
            if cfg != self.config:
                self.stop_output(); self.config = cfg; self.fault_config = None
            if not cfg[-1]:
                self.service['/Status/State'] = 'Deaktiviert'
                self.service['/Status/Error'] = ''
                self.service['/Status/RemainingSeconds'] = 0
                return True
            if cfg == self.fault_config:
                return True
            if self.output is None:
                self.start_output(cfg)
            now, wall = time.monotonic(), time.time()
            schedule = plans(self.settings)
            for plan in schedule:
                if plan['enabled']:
                    minute(plan['start']); minute(plan['end'])
            actual = self.output.read()
            switch = None
            if self.input:
                raw = self.input.read()
                switch = self.debounce.sample(not raw if cfg[4] else raw, now, cfg[7] / 1000.)
            command, self.pending = self.pending, None
            desired = self.engine.tick(now, wall, actual, schedule,
                                       self.settings['ManualMinutes'], self.settings['MaximumMinutes'],
                                       switch, cfg[6], command)
            # Wache VOR einem Einschaltbefehl informieren.
            armed = bool(desired) if desired is not None else bool(actual)
            self.heartbeat(armed or bool(actual), self.engine.deadline if self.engine.deadline is not None else (now + 2 if actual else None))
            if desired is not None and desired != actual:
                self.output.write(desired); actual = desired
            self.heartbeat(bool(actual), self.engine.deadline)
            self.service['/Control/Command'] = -1
            self.service['/Status/Actual'] = actual
            self.service['/Status/State'] = 'Ein' if actual else 'Bereit'
            self.service['/Status/Source'] = self.engine.source
            self.service['/Status/RemainingSeconds'] = max(0, int((self.engine.deadline or now) - now))
            self.service['/Status/Switch'] = -1 if switch is None else int(switch)
            self.service['/Status/Clock'] = time.strftime('%a %H:%M', time.localtime(wall))
            self.service['/Status/Error'] = ''
        except Exception as ex:
            logging.exception('RelayScheduler verweigert Steuerung')
            self.stop_output(); self.fault_config = cfg
            self.service['/Status/State'] = 'Fehler – erneut aktivieren'
            self.service['/Status/Error'] = str(ex)
            self.service['/Status/RemainingSeconds'] = 0
        return True


def main():
    logging.basicConfig(level=logging.INFO)
    for p in (PRIVATE, RUNTIME):
        p.mkdir(mode=0o700, parents=True, exist_ok=True)
        if p.is_symlink() or p.stat().st_uid != 0:
            raise RuntimeError('Unsicheres RelayScheduler-Verzeichnis')
        p.chmod(0o700)
    fd = os.open(str(RUNTIME / 'daemon.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    DBusGMainLoop(set_as_default=True)
    app = Application(dbus.SystemBus())
    loop = GLib.MainLoop()
    def stop(*args):
        app.stop_output(); loop.quit(); return False
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, stop)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, stop)
    GLib.timeout_add(250, app.tick)
    try: loop.run()
    finally: app.stop_output(); os.close(fd)


if __name__ == '__main__':
    main()
