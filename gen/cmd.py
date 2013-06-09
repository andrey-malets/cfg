class Cmd:
    @staticmethod
    def execute(state, argv):
        if not len(argv):
            raise Exception('please provide a command, available: %s' %
                ' '.join(Cmd.cmds.iterkeys()))
        cmd = argv.pop(0)

        if not cmd in Cmd.cmds:
            raise Exception('no such command, available: %s' %
                ' '.join(Cmd.cmds.iterkeys()))

        fn = Cmd.cmds[cmd]
        return fn(state, argv)

    cmds = {}

def add_cmd(name, has_template, arity):
    def gen(fn):
        def check(args):
            if len(args) != arity:
                raise Exception('"%s" has %d args, %d given' % (name, arity, len(args)))

        def no_templ(state, args):
            check(args)
            return fn(state, *args)

        def templ(state, args):
            if not len(args):
                raise Exception('"%s" requires template name as 1st arg' % name)
            tname = args.pop(0)
            with open(tname, 'r') as tfile:
                template = tfile.read()
            check(args)
            return fn(state, template, *args)

        if name in Cmd.cmds: raise Exception('duplicate cmd "%s"' % name)
        Cmd.cmds[name] = no_templ if not has_template else templ
    return gen
