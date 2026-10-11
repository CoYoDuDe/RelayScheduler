"""Zeitplan und flankenbasierter Schalter, unabhängig von GPIO und D-Bus."""
import time


def minute(text):
    if not isinstance(text, str) or len(text) != 5 or text[2] != ':':
        raise ValueError('Uhrzeit muss HH:MM sein')
    h, m = int(text[:2]), int(text[3:])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError('Ungültige Uhrzeit')
    return 60 * h + m


class Engine:
    def __init__(self, seen=None, remember=None):
        self.seen = set(seen or [])
        self.remember = remember or (lambda keys: None)
        self.previous_switch = None
        self.last_wall = None
        self.last_mono = None
        self.expected = None
        self.deadline = None
        self.started = None
        self.source = 'Bereit'
        self.blocked_bucket = None

    def tick(self, mono, wall, actual, plans, duration, maximum,
             switch=None, switch_mode='maintained', command=None, local=None):
        """None bedeutet keine Relaisoperation; manuelle Befehle haben Vorrang."""
        duration, maximum = float(duration), float(maximum)
        if not (1 <= duration <= 1440 and 1 <= maximum <= 1440):
            raise ValueError('Laufzeit muss 1–1440 Minuten sein')
        if actual not in (0, 1):
            raise ValueError('Relaiszustand unbekannt')
        desired = None
        if self.expected is None:
            self.expected = actual
            if actual:
                self.started = mono
                self.deadline = mono + maximum * 60
                self.source = 'Bereits eingeschaltet'
        elif actual != self.expected:
            self.expected = actual
            self.started = mono if actual else None
            self.deadline = mono + min(duration, maximum) * 60 if actual else None
            self.source = 'Relais direkt bedient'
        if self.deadline is not None and self.started is not None:
            self.deadline = min(self.deadline, self.started + maximum * 60)
        if self.deadline is not None and mono >= self.deadline:
            desired = 0
            self.source = 'Laufzeit beendet'

        clock_ok = wall >= 1735689600
        jumped = (self.last_wall is not None and
                  abs((wall - self.last_wall) - (mono - self.last_mono)) > 90)
        stamp = local or time.localtime(wall)
        bucket = '%04d-%03d-%02d%02d' % (stamp.tm_year, stamp.tm_yday,
                                         stamp.tm_hour, stamp.tm_min)
        if jumped:
            self.blocked_bucket = bucket
        if clock_ok and bucket != self.blocked_bucket:
            for plan in plans:
                if not plan['enabled']:
                    continue
                if plan['stop_mode'] not in ('time', 'duration'):
                    raise ValueError('Ungültiger Zeitplanmodus')
                start = minute(plan['start'])
                length = float(plan['duration'])
                if plan['stop_mode'] == 'time':
                    length = (minute(plan['end']) - start) % 1440
                if not 1 <= length <= 1440:
                    raise ValueError('Zeitplan-Laufzeit muss 1–1440 Minuten sein')
                # Gleiche Ortsminute gilt auch nach Uhrumstellung nur einmal.
                key = str(plan['id']) + ':' + bucket
                if (stamp.tm_wday in plan['days'] and
                        stamp.tm_hour * 60 + stamp.tm_min == start and
                        key not in self.seen):
                    self.seen.add(key)
                    self.seen = set(sorted(self.seen, key=lambda k: k.split(':', 1)[-1])[-128:])
                    self.remember(sorted(self.seen))  # Vor dem Einschalten dauerhaft.
                    if not actual and desired != 0:
                        desired = 1
                        self.started = mono
                        seconds = length * 60 - (stamp.tm_sec if plan['stop_mode'] == 'time' else 0)
                        self.deadline = mono + min(seconds, maximum * 60)
                        self.source = 'Zeitplan ' + str(plan['id'])
        self.last_wall, self.last_mono = wall, mono

        manual_command = command
        hardware_command = None
        if switch_mode not in ('maintained', 'toggle'):
            raise ValueError('Ungültiger Schaltermodus')
        if switch is None:
            self.previous_switch = None
        else:
            switch = bool(switch)
            previous = self.previous_switch
            self.previous_switch = switch
            if previous is not None and previous != switch:
                if switch_mode == 'maintained':
                    hardware_command = 1 if switch else 0
                elif switch_mode == 'toggle' and switch:
                    hardware_command = 0 if actual else 1

        command = manual_command if manual_command is not None else hardware_command

        if command is not None:
            if command not in (0, 1, 2):
                raise ValueError('Ungültiger Befehl')
            desired = (0 if actual else 1) if command == 2 else command
            self.source = 'Manuell' if manual_command is not None else 'Hardwareschalter'
            if desired and not actual:
                self.started = mono
                self.deadline = mono + min(duration, maximum) * 60
            elif not desired:
                self.deadline = None
        if desired == 0:
            self.deadline = None
            self.started = None
        if desired is not None:
            self.expected = desired
        return desired


class Debounce:
    def __init__(self):
        self.raw = None
        self.since = 0
        self.stable = None

    def sample(self, value, now, seconds):
        if value != self.raw:
            self.raw, self.since = value, now
        if now - self.since >= seconds:
            self.stable = value
        return self.stable
