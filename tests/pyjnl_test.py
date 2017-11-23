import os
import sys
import datetime
import random
import os


class Settings(object):
    def __init__(self, context):
        self.context = context

    def dbdir(self):
        return self.context.environment['JNL_DIR']

class Database(object):
    def __init__(self, context):
        self.context = context

        self._entries = None
        """Use .entries instead of _entries to ensure it's initialized"""

    def path(self, *subdirs):
        out = os.path.join(self.context.settings.dbdir(), *subdirs)
        print "out = %s subdirs = %s" % (out, subdirs)
        if not os.path.isdir(out):
            os.path.makdedirs(path)
        return out

    @property
    def entries(self):
        if self._entries is None:
            mypath = self.path('worklogs')
            self._entries = [
                Entry(context=self.context, file_name=f)
                for f in os.listdir(mypath)
                if os.path.isfile(os.path.join(mypath, f))
            ]
        return self._entries

class Entry(object):
    def __init__(self, context, file_name):
        self.context = context
        self.file_name = file_name

class Opener(object):
    def __init__(self, context):
        self.context = context

class Symlinker(object):
    def __init__(self, context):
        self.context = context

class WhatDayIsIt(object):
    def __init__(self, context):
        self.context = context

    def yyyymmdd(self):
        now = datetime.datetime.now()
        return "%s-%s-%s" % (now.year, now.month, now.day)

class GuidGenerator(object):
    def __init__(self, context):
        self.context = context

    LETTERS = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8',
        '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
        'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T',
        'U', 'W', 'X', 'Y', 'Z',
    ]

    def guid(self):
        return "".join([
            random.choice(GuidGenerator.LETTERS) for i in range(20)
        ])
        

class Context(object):
    def __init__(self, environment):
        self.environment = environment
        self.opener = Opener(self)
        self.what_day_is_it = WhatDayIsIt(self)
        self.guid_generator = GuidGenerator(self)
        self.symlinker = Symlinker(self)
        self.settings = Settings(self)
        self.database = Database(self)

    def __str__(self):
        return "Context()"

class Main(object):
    def __init__(self, environment = None):
        if environment is None:
            environment = os.environ
        self.context = Context(environment = environment)

    def run(self, argv):
        print "Here with %s, %s" % (self.context.settings.dbdir(), argv)
        if argv[1] == 'daily':
            self.daily(argv)

    def daily(self, argv):
        print self.context.what_day_is_it.yyyymmdd()
        print self.context.guid_generator.guid()
        print self.context.database.entries


def empty_fixture_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', 'empty')

if __name__ == "__main__":
    main = Main({
        'JNL_DIR': empty_fixture_path()
    })
    main.run(sys.argv)
