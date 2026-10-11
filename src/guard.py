"""Unabhängige Laufzeitwache; EOF, fehlender Heartbeat oder Frist schaltet aus."""
import json
import os
import select
import sys
import time
import dbus
from output import Output


def run(number, pipe_fd, lock_fd, ready_fd):
    # Geerbte Relais-Sperre bleibt bis zum bestätigten Abschluss gehalten.
    output = Output(dbus.SystemBus(private=True), number)
    os.write(ready_fd, b'READY\n')
    os.close(ready_fd)
    deadline = None
    armed = False
    last = time.monotonic()
    buffer = b''
    failure = False
    while True:
        ready, _, _ = select.select([pipe_fd], [], [], 0.25)
        if ready:
            data = os.read(pipe_fd, 8192)
            if not data:
                failure = True
                break
            buffer += data
            if len(buffer) > 65536:
                failure = True
                break
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                try:
                    d = json.loads(line)
                    new_deadline = float(d['deadline']) if d['deadline'] is not None else None
                    if d['armed'] and (new_deadline is None or not 0 < new_deadline < float('inf')):
                        raise ValueError('Aktive Wache benötigt eine gültige Frist')
                    armed = bool(d['armed'])
                    deadline = new_deadline
                except (ValueError, KeyError, TypeError):
                    failure = True
                    break
                last = time.monotonic()
            if failure:
                break
        now = time.monotonic()
        if now - last > 4 or (armed and deadline is not None and now >= deadline):
            failure = True
            break
    if armed:
        # Bei ausfallendem D-Bus nicht freigeben und unbeaufsichtigt weiterlaufen.
        while True:
            try:
                if output.read():
                    output.write(0)
                break
            except Exception as ex:
                print('RelayScheduler-Wache: Ausschalten nicht bestätigt: %s' % ex, flush=True)
                time.sleep(1)
    os.close(pipe_fd)
    os.close(lock_fd)
    return 1 if failure else 0


if __name__ == '__main__':
    raise SystemExit(run(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])))
