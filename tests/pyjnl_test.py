import os
import sys
import datetime
import random
import os
import re
import subprocess


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
        # print "out = %s subdirs = %s" % (out, subdirs)
        if not os.path.exists(out):
            os.path.makdedirs(path)
        return out

    @property
    def entries(self):
        if self._entries is None:
            mypath = self.path('worklogs')
            self._entries = [
                Entry(context=self.context, file_name=f, path=mypath)
                for f in os.listdir(mypath)
                if os.path.isfile(os.path.join(mypath, f))
            ]
        return self._entries

    def create_entry(self, tags):
        """See Entry.create() for semantics of tags"""
        entry = Entry(context=self.context,
                      tags=tags,
                      create=True)
        self._entries.append(entry)
        return entry

    def entries_with_tag(self, name, value):
        return [e for e in self.entries if e.has_tag(name, value)]

    def daily_entry(self, yyyymmdd = None):
        if yyyymmdd is None:
            yyyymmdd = self.context.what_day_is_it.yyyymmdd()
        existing = self.entries_with_tag('daily', yyyymmdd)
        if existing == []:
            existing = [self.create_entry(
                tags=[Tag(name='daily', value=yyyymmdd)]
            )]
        return existing[0]

class Tag(object):

    TAG_RE = re.compile(r"""
    .*
        @
            (               # group 1: tag name
                [^(]+       # anything other than (
            )
        (?:                 # non-grouping
            \(              # literal paren
                (           # group 2: tag value
                    [^)]*   # anything other than )
                )
            \)
        )?
    .*
    """, re.X)

    @staticmethod
    def parse(line):
        re_match = Tag.TAG_RE.match(line)
        if re_match:
            tag = Tag(re_match)
            return tag
        else:
            return None

    def __init__(self, re_match = None, name = None, value = None):
        if re_match is not None:
            name = re_match.group(1).strip()
            value = re_match.group(2)
        self._name = name
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    def __str__(self):
        return "@%s%s" % (
            self.name,
            "(" + self.value + ")" if self.value is not None else ''
        )


class Entry(object):

    FILENAME_RE = re.compile(r"""
        ^
        ([A-Z0-9]+)     # group 1: file name without extension
        \.
        (.*?)           # group 2: extension
        $
    """, re.X)

    def __init__(self,
                 context,
                 path = None,
                 file_name = None,
                 guid = None,
                 tags = None,
                 create = False):
        self.context = context

        if guid is None:
            if file_name is None:
                guid = self.context.guid_generator.guid()
            else:
                match = Entry.FILENAME_RE.match(file_name)
                guid = match.group(1).strip()
                if match is None:
                    raise ValueError
        self.guid = guid

        if path is None:
            path = self.context.database.path('worklogs')
        self.path = path
        """dirname of full file_name path"""

        if file_name is None:
            file_name = "%s.txt" % self.guid
        self.file_name = file_name

        self._tags = tags

        if create:
            self._create()

    def file_path(self):
        return os.path.join(self.path, self.file_name)

    def _create(self):
        with open(self.file_path(), 'w+') as f:
            f.write('\n' * 4)
            f.write("My Reference: %s  \n" % self.guid)
            for tag in self.tags:
                f.write(str(tag))
                f.write('  \n')
            print("Created %s" % self.file_path())

    @property
    def tags(self):
        if self._tags is None:
            tags = []
            with open(self.file_path()) as f:
                for line in f:
                    t = Tag.parse(line)
                    tags.append(t)
                    if t is not None and t.name == 'noscan':
                        break
            self._tags = [t for t in tags if t is not None]
        return self._tags

    def has_tag(self, name, val):
        print "Has_tag %s=%s in %s" % (name,val,self.tags)
        return any(
            t.name == name and t.value == val 
            for t in self.tags
        )

    def __str__(self):
        return "%s: %s" % (self.file_name, [str(t) for t in self.tags])


class Opener(object):
    def __init__(self, context):
        self.context = context

    def open(self, entry):
        subprocess.call(
            'open', '-a', 'FoldingText',
            entry.file_path()
        )

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
        # print "Here with %s, %s" % (self.context.settings.dbdir(), argv)
        if argv[1] == 'daily':
            self.daily(argv)

    def daily(self, argv):
        pass
        # print self.context.what_day_is_it.yyyymmdd()
        # print self.context.guid_generator.guid()
        # print "Daily: %s" % self.context.database.daily_entry()
        # print [str(f) for f in self.context.database.entries]

        # self.context.opener.open(
        #     self.context.database.daily_entry()
        # )


def empty_fixture_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', 'empty')

if __name__ == "__main__":
    main = Main({
        'JNL_DIR': os.environ['JNL_DIR'] if 'JNL_DIR' in os.environ else empty_fixture_path()
    })
    main.run(sys.argv)
