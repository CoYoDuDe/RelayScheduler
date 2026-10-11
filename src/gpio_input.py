"""Exklusiver Eingang über libgpiod 2, ohne zusätzliche Python-Pakete."""
import ctypes as c
import glob
from pathlib import Path


class Input:
    def __init__(self, bcm, chip='auto', bias='pull_up'):
        bcm = int(bcm)
        if bcm not in (4, 12, 18, 20, 25):
            raise ValueError('Reservierter GPIO; mögliche Eingänge: BCM 4, 12, 18, 20, 25')
        if bias not in ('pull_up', 'pull_down'):
            raise ValueError('Ungültiger Eingangswiderstand')
        if Path('/sys/class/gpio/gpio%d' % bcm).exists():
            raise RuntimeError('GPIO bereits über sysfs belegt')
        self.lib = c.CDLL('libgpiod.so.3', use_errno=True)
        self.device = self.request = None
        signatures = {
            'gpiod_chip_open': (c.c_void_p, [c.c_char_p]),
            'gpiod_chip_close': (None, [c.c_void_p]),
            'gpiod_chip_get_line_offset_from_name': (c.c_int, [c.c_void_p, c.c_char_p]),
            'gpiod_line_settings_new': (c.c_void_p, []),
            'gpiod_line_settings_free': (None, [c.c_void_p]),
            'gpiod_line_settings_set_direction': (c.c_int, [c.c_void_p, c.c_int]),
            'gpiod_line_settings_set_bias': (c.c_int, [c.c_void_p, c.c_int]),
            'gpiod_line_config_new': (c.c_void_p, []),
            'gpiod_line_config_free': (None, [c.c_void_p]),
            'gpiod_line_config_add_line_settings': (c.c_int, [c.c_void_p, c.POINTER(c.c_uint), c.c_size_t, c.c_void_p]),
            'gpiod_request_config_new': (c.c_void_p, []),
            'gpiod_request_config_free': (None, [c.c_void_p]),
            'gpiod_request_config_set_consumer': (None, [c.c_void_p, c.c_char_p]),
            'gpiod_chip_request_lines': (c.c_void_p, [c.c_void_p, c.c_void_p, c.c_void_p]),
            'gpiod_line_request_get_value': (c.c_int, [c.c_void_p, c.c_uint]),
            'gpiod_line_request_release': (None, [c.c_void_p]),
        }
        for name, (result, args) in signatures.items():
            f = getattr(self.lib, name); f.restype = result; f.argtypes = args
        if chip != 'auto' and (not chip.startswith('gpiochip') or not chip[8:].isdigit()):
            raise ValueError('Ungültiger GPIO-Chip')
        found = []
        paths = sorted(glob.glob('/dev/gpiochip*')) if chip == 'auto' else ['/dev/' + chip]
        for path in paths:
            device = self.lib.gpiod_chip_open(path.encode())
            if not device:
                continue
            offset = self.lib.gpiod_chip_get_line_offset_from_name(device, ('GPIO%d' % bcm).encode())
            self.lib.gpiod_chip_close(device)
            if offset >= 0:
                found.append((path, offset))
        if len(found) != 1:
            raise RuntimeError('BCM-Leitung nicht eindeutig gefunden')
        self.path, self.offset = found[0]
        self.device = self.lib.gpiod_chip_open(self.path.encode())
        settings = self.lib.gpiod_line_settings_new()
        config = self.lib.gpiod_line_config_new()
        request_config = self.lib.gpiod_request_config_new()
        try:
            if not all((self.device, settings, config, request_config)):
                raise MemoryError('GPIO-Konfiguration fehlt')
            # libgpiod 2: INPUT=2, PULL_UP=4, PULL_DOWN=5.
            for result in (self.lib.gpiod_line_settings_set_direction(settings, 2),
                           self.lib.gpiod_line_settings_set_bias(settings, 4 if bias == 'pull_up' else 5),
                           self.lib.gpiod_line_config_add_line_settings(config, c.pointer(c.c_uint(self.offset)), 1, settings)):
                if result < 0:
                    raise OSError(c.get_errno(), 'GPIO-Einstellungen verweigert')
            self.lib.gpiod_request_config_set_consumer(request_config, b'RelayScheduler')
            self.request = self.lib.gpiod_chip_request_lines(self.device, request_config, config)
            if not self.request:
                raise OSError(c.get_errno(), 'GPIO belegt oder Eingang nicht verfügbar')
        except BaseException:
            self.close(); raise
        finally:
            if settings: self.lib.gpiod_line_settings_free(settings)
            if config: self.lib.gpiod_line_config_free(config)
            if request_config: self.lib.gpiod_request_config_free(request_config)

    def read(self):
        value = self.lib.gpiod_line_request_get_value(self.request, self.offset)
        if value < 0:
            raise OSError(c.get_errno(), 'GPIO konnte nicht gelesen werden')
        return bool(value)

    def close(self):
        if self.request:
            self.lib.gpiod_line_request_release(self.request); self.request = None
        if self.device:
            self.lib.gpiod_chip_close(self.device); self.device = None
