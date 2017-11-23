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
                and Entry.valid_file_name(f)
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

    def scan(self):
        listeners = self.context.entry_listeners
        for entry in self.entries:
            for listener in listeners:
                listener.on_entry(entry)

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

    @staticmethod
    def valid_file_name(file_name):
        return Entry.FILENAME_RE.match(file_name)

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
                if match is None:
                    print "file_name mismatch %s" % file_name
                    raise ValueError
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
        subprocess.check_call([
            'open', '-a', 'FoldingText',
            entry.file_path(),
        ])

class SetsOpenWith(object):
    def __init__(self, context):
        self.context = context

    """The xattr controlling the "Open With" functionality is unfortunately binary.
    To use a different application, use `xattr -l`

        $ xattr -l $FILE
        com.apple.LaunchServices.OpenWith:
        00000000  62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57  |bplist00.......W|
        00000010  76 65 72 73 69 6F 6E 54 70 61 74 68 5F 10 10 62  |versionTpath_..b|
        00000020  75 6E 64 6C 65 69 64 65 6E 74 69 66 69 65 72 10  |undleidentifier.|
        00000030  00 5F 10 1D 2F 41 70 70 6C 69 63 61 74 69 6F 6E  |._../Application|
        00000040  73 2F 46 6F 6C 64 69 6E 67 54 65 78 74 2E 61 70  |s/FoldingText.ap|
        00000050  70 5F 10 1B 63 6F 6D 2E 66 6F 6C 64 69 6E 67 74  |p_..com.foldingt|
        00000060  65 78 74 2E 46 6F 6C 64 69 6E 67 54 65 78 74 08  |ext.FoldingText.|
        00000070  0F 17 1C 2F 31 51 00 00 00 00 00 00 01 01 00 00  |.../1Q..........|
        00000080  00 00 00 00 00 07 00 00 00 00 00 00 00 00 00 00  |................|
        00000090  00 00 00 00 00 6F                                |.....o|
        00000096

    or with `-px`:

        $ xattr -px com.apple.LaunchServices.OpenWith $FILE
        62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57
        76 65 72 73 69 6F 6E 54 70 61 74 68 5F 10 10 62
        75 6E 64 6C 65 69 64 65 6E 74 69 66 69 65 72 10
        00 5F 10 1D 2F 41 70 70 6C 69 63 61 74 69 6F 6E
        73 2F 46 6F 6C 64 69 6E 67 54 65 78 74 2E 61 70
        70 5F 10 1B 63 6F 6D 2E 66 6F 6C 64 69 6E 67 74
        65 78 74 2E 46 6F 6C 64 69 6E 67 54 65 78 74 08
        0F 17 1C 2F 31 51 00 00 00 00 00 00 01 01 00 00
        00 00 00 00 00 07 00 00 00 00 00 00 00 00 00 00
        00 00 00 00 00 6F

    TODO: better support for an arbitrary application that doesn't require the user to modify the source :)
    """

    OPEN_WITH_ATTR = '''
        62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57
        76 65 72 73 69 6F 6E 54 70 61 74 68 5F 10 10 62
        75 6E 64 6C 65 69 64 65 6E 74 69 66 69 65 72 10
        00 5F 10 1D 2F 41 70 70 6C 69 63 61 74 69 6F 6E
        73 2F 46 6F 6C 64 69 6E 67 54 65 78 74 2E 61 70
        70 5F 10 1B 63 6F 6D 2E 66 6F 6C 64 69 6E 67 74
        65 78 74 2E 46 6F 6C 64 69 6E 67 54 65 78 74 08
        0F 17 1C 2F 31 51 00 00 00 00 00 00 01 01 00 00
        00 00 00 00 00 07 00 00 00 00 00 00 00 00 00 00
        00 00 00 00 00 6F
    '''

    def on_entry(self, entry):
        if not entry.has_tag('ft', None):
            return

        subprocess.check_call([
            'xattr', '-wx', 'com.apple.LaunchServices.OpenWith',
            SetsOpenWith.OPEN_WITH_ATTR,
            entry.file_path()
        ])

class Symlinker(object):
    def __init__(self, context):
        self.context = context

    def on_entry(self, entry):
        pass

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
        self.sets_open_with = SetsOpenWith(self)
        self.what_day_is_it = WhatDayIsIt(self)
        self.guid_generator = GuidGenerator(self)
        self.symlinker = Symlinker(self)
        self.settings = Settings(self)
        self.database = Database(self)
        self.entry_listeners = [
            self.sets_open_with,
            self.symlinker,
        ]

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
        if argv[1] == 'scan':
            self.scan(argv)

    def scan(self, argv):
        self.context.database.scan()

    def daily(self, argv):
        pass
        # print self.context.what_day_is_it.yyyymmdd()
        # print self.context.guid_generator.guid()
        # print "Daily: %s" % self.context.database.daily_entry()
        # print [str(f) for f in self.context.database.entries]

        daily = self.context.database.daily_entry()
        self.context.opener.open(daily)


def empty_fixture_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', 'empty')

if __name__ == "__main__":
    main = Main({
        'JNL_DIR': os.environ['JNL_DIR'] if 'JNL_DIR' in os.environ else empty_fixture_path()
    })
    main.run(sys.argv)
