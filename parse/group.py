import re
from util import ValueFromGroup, ValidationError, primitive

class Group:
    def __init__(self, data):
        self.name    = data.pop(0)
        self.childs  = set(data.pop(0) if type(data[0]) == list else [])
        self.pattern = (re.compile(data.pop(0))
            if len(data) and type(data[0]) == str else None)
        self.props   = data.pop(0) if len(data) else {}

    def __str__(self):
        return '{}: childs: {}, pattern: {}'.format(
            self.name, self.childs, self.pattern)

    def remove_childs(self, bad_childs):
        self.childs = self.childs - set(bad_childs)

    def get_matching(self, hosts):
        return filter(lambda host: any(map(lambda name:
            self.pattern.match(name), host.snames)), hosts) if self.pattern else []

class MergeError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message
    def __repr__(self):
        return self.__str__()

def merge(src, dst):
    errors = []
    def check(name, prop, dst):
        valid = name not in dst
        if not valid:
            stype, dtype = type(prop), type(dst[name])
            if stype == None: valid = True
            elif stype in [str, ValueFromGroup]: valid = dtype in [str, ValueFromGroup]
            elif stype in [dict, list]: valid = (stype == dtype)
        if not valid:
            errors.append(MergeError('property "%s" type mismatch: %s and %s' %
                (name, type(prop), type(dst[name]))))
        return valid

    def step(sprops, dprops):
        for name, prop in sprops.iteritems():
            if not check(name, prop, dprops):
                return
            if primitive(prop):
                if name not in dprops: dprops[name] = ValueFromGroup(prop, src)
            elif type(prop) == ValueFromGroup:
                if name not in dprops:
                    dprops[name] = ValueFromGroup(prop.value, src)
                else:
                    errors.append(MergeError(
                        ('string value "%s" for "%s" has no value in "%s" but ' +
                         'came from two diffrent groups: "%s" and "%s", can\'t merge') %
                        (prop, name, dst.name, src.name, dprops[name].source.name)))
            elif type(prop) == list:
                dprops[name] = (list(set(dprops[name] + prop))
                    if name in dprops else prop)
            elif type(prop) == dict:
                dprops[name] = (step(prop, dprops[name])
                    if name in dprops else prop)
            else:
                errors.append(MergeError("unknown type of prop %s (%s), can't merge" %
                    (name, type(prop))))
        return dprops

    step(src.props, dst.props)
    return errors

def expand_groups(groups, hosts):
    def fold_names(groups):
        rv = {}
        for group in groups:
            name = group.name
            if name in rv:
                errors.append(ValidationError('duplicate group name "%s"' % name))
            else:
                rv[name] = group
        return rv

    def check_cycles(group_names):
        def step(group, stack):
            bad_childs = []
            for child_name in group.childs:
                if child_name not in group_names:
                    errors.append(ValidationError('no such group "%s" in childs of "%s"' %
                        (child_name, group.name)))
                    bad_childs.append(child_name)
                else:
                    child = group_names[child_name]
                    if child in stack:
                        errors.append(ValidationError('group dependency cycle: %s' % (stack)))
                    else:
                        step(child, stack + [child])
            group.remove_childs(bad_childs)
        for group in groups:
            step(group, [])

    errors = []
    group_names = fold_names(groups)
    check_cycles(group_names)

    def empty_parents(group): return not len(group.parents)

    for group in groups: group.parents = set()
    for group in groups:
        for child_name in group.childs:
            group_names[child_name].parents.add(group)

    empty = filter(empty_parents, groups)
    while len(empty):
        group = empty.pop()
        for host in group.get_matching(hosts):
            errors.extend(merge(group, host))
        for child_name in group.childs:
            child = group_names[child_name]
            child.parents.remove(group)
            if empty_parents(child):
                empty.append(child)
            errors.extend(merge(group, child))
    return errors
