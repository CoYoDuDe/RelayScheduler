PREFIX = '/Settings/RelayScheduler'
SCHEMA = {
    'Enabled': [PREFIX + '/Enabled', 0, 0, 1],
    'RelayNumber': [PREFIX + '/RelayNumber', 0, 0, 18],
    'Label': [PREFIX + '/Label', 'RelayScheduler', 0, 0],
    'ManualMinutes': [PREFIX + '/ManualMinutes', 30, 1, 1440],
    'MaximumMinutes': [PREFIX + '/MaximumMinutes', 60, 1, 1440],
    'SwitchEnabled': [PREFIX + '/SwitchEnabled', 0, 0, 1],
    'GpioBcm': [PREFIX + '/GpioBcm', 12, -1, 27],
    'GpioChip': [PREFIX + '/GpioChip', 'auto', 0, 0],
    'ActiveLow': [PREFIX + '/ActiveLow', 1, 0, 1],
    'InputBias': [PREFIX + '/InputBias', 'pull_up', 0, 0],
    'SwitchMode': [PREFIX + '/SwitchMode', 'maintained', 0, 0],
    'DebounceMs': [PREFIX + '/DebounceMs', 100, 20, 1000],
}
for i in range(1, 5):
    path = PREFIX + '/Plan' + str(i)
    fields = {'Enabled': (0, 0, 1), 'Start': ('06:30', 0, 0),
              'StopMode': ('duration', 0, 0), 'End': ('07:00', 0, 0),
              'Minutes': (30, 1, 1440)}
    fields.update({day: (1 if n < 5 else 0, 0, 1) for n, day in
                   enumerate(('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'))})
    for key, (default, low, high) in fields.items():
        SCHEMA['Plan' + str(i) + key] = [path + '/' + key, default, low, high]


def plans(settings):
    out = []
    for i in range(1, 5):
        p = 'Plan' + str(i)
        out.append({'id': i, 'enabled': bool(settings[p + 'Enabled']),
                    'start': str(settings[p + 'Start']), 'end': str(settings[p + 'End']),
                    'duration': int(settings[p + 'Minutes']), 'stop_mode': str(settings[p + 'StopMode']),
                    'days': [n for n, day in enumerate(('Monday', 'Tuesday', 'Wednesday', 'Thursday',
                                                     'Friday', 'Saturday', 'Sunday')) if settings[p + day]]})
    return out
