from datetime import datetime, date, time, timedelta

class BackupItem:
    def __init__(self, day, hour, minute):
        self.day    = day
        self.hour   = hour
        self.minute = minute
        self.host   = None
        self.btype  = None
        self.bprops = None

def append_props(bprops, host):
    for service in ['mysql', 'postgresql']:
        if service in host.props['services']:
            bprops.append(service)

def build_schedule(state):
    days          = 7
    slots_number  = 12
    slot_duration = timedelta(minutes=15)
    start_time    = time(3)
    fake_date     = date(1970, 1, 1)

    backupers = filter(lambda host: 'backups' in host.props, state.hosts)
    slots = {}
    for backuper in backupers:
        slots[backuper.name] = []
        for day in range(days):
            current = datetime.combine(fake_date, start_time)
            slots[backuper.name].append([])
            for slot in range(slots_number):
                slots[backuper.name][day].append(BackupItem(
                    day, current.hour, current.minute))
                current += slot_duration

    def occupied(backuper, day, slot):
        return slots[backuper.name][day][slot].host != None
    def another_backups(host, day, slot):
        return any(map(lambda backuper:
            slots[backuper.name][day][slot].host == host, backupers))
    for backuper in backupers:
        for hostname, bprops in backuper.props['backups'][1].iteritems():
            host = state.find(hostname)
            append_props(bprops, host)
            for day in range(days):
                sn = 0
                while sn != slots_number:
                    if not (occupied(backuper, day, sn) or
                            another_backups(host, day, sn)):
                        break
                    sn += 1
                if sn == slots_number:
                    raise OverflowError
                slot = slots[backuper.name][day][sn]
                slot.host = host
                slot.btype = 'full' if day == 0 else 'diff'
                slot.bprops = bprops

    for backuper, items in slots.items():
        slots[backuper] = []
        for day in items:
            slots[backuper] += (filter(lambda item: item.host != None, day))
    return slots
