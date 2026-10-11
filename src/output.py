"""Bedient nur manuell konfigurierte GX-Relais über Venus D-Bus."""
import dbus

SYSTEM = 'com.victronenergy.system'
SETTINGS = 'com.victronenergy.settings'


def get(bus, service, path):
    return dbus.Interface(bus.get_object(service, path), 'com.victronenergy.BusItem').GetValue(timeout=2)


class Output:
    def __init__(self, bus, number):
        self.bus = bus
        self.index = int(number) - 1
        if not 0 <= self.index < 18:
            raise ValueError('Zuerst ein GX-Relais auswählen')
        root = '/SwitchableOutput/%d' % self.index
        try:
            get(bus, SYSTEM, root + '/State')
        except dbus.DBusException:
            root = '/Relay/%d' % self.index
            get(bus, SYSTEM, root + '/State')
        self.path = root + '/State'
        self.function = (root + '/Settings/Function' if root.startswith('/SwitchableOutput/')
                         else '/Settings/Relay/Function')
        self.function_service = SYSTEM if root.startswith('/SwitchableOutput/') else SETTINGS
        self.validate()

    def validate(self):
        if int(get(self.bus, self.function_service, self.function)) != 2:
            raise RuntimeError('Relais muss im Venus-Menü auf Manuell stehen')
        try:
            enabled = int(get(self.bus, SETTINGS, '/Settings/Devices/DPlusSimulator/Enabled'))
        except dbus.DBusException:
            enabled = 0
        if enabled:
            prefix = '/Settings/Devices/DPlusSimulator/'
            target = str(get(self.bus, SETTINGS, prefix + 'RelayTarget'))
            mode = str(get(self.bus, SETTINGS, prefix + 'OutputMode'))
            channel = str(get(self.bus, SETTINGS, prefix + 'RelayChannel'))
            if target == 'system' and mode == 'relay' and channel in (str(self.index), str(self.index + 1)):
                raise RuntimeError('Relais wird bereits durch DPlusSimulator verwendet')

    def read(self):
        self.validate()
        value = int(get(self.bus, SYSTEM, self.path))
        if value not in (0, 1):
            raise RuntimeError('Relaiszustand unbekannt')
        return value

    def write(self, value):
        self.validate()
        result = dbus.Interface(self.bus.get_object(SYSTEM, self.path),
                                'com.victronenergy.BusItem').SetValue(dbus.Int32(value), timeout=2)
        if int(result) != 0 or self.read() != value:
            raise RuntimeError('Relais hat Schaltbefehl nicht bestätigt')
