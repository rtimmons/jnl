import re
import os

class Database(object):
    def __init__(self, context):
        self.context = context

        self._entries = None
        """Use .entries instead of _entries to ensure it's initialized"""

    def path(self, *subdirs):
        out = os.path.join(self.context.settings.dbdir(), *subdirs)
        if not self.context.system.exists(out):
            self.context.system.makedirs(out)
        assert(self.context.system.isdir(out))
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

    def create_entry(self, tags=[]):
        entry = Entry(context=self.context,
                      tags=tags,
                      create=True)
        self.entries.append(entry)
        return entry

    # maybe combine all these entry_with_* stuff to have a predicate or something
    # or at least refactor internal

    def entries_with_project(self, project):
        return [e for e in self.entries if e.tag_starts_with('project', project)]

    def entry_with_guid(self, guid):
        return [e for e in self.entries if e.guid == guid][0]

    def entries_with_tag(self, name, value):
        return [e for e in self.entries if e.has_tag(name, value)]

    def daily_entry(self, yyyymmdd = None):
        if yyyymmdd is None:
            yyyymmdd = self.context.what_day_is_it.yyyymmdd()
        tag_val = 'daily/%s' % yyyymmdd
        existing = self.entries_with_tag('quick', tag_val)
        if not existing:
            existing = [self.create_entry(
                tags=[
                    Tag(name='quick', value=tag_val),
                    Tag(name='ft')
                ]
            )]
        return existing[0]

    def scan(self):
        # TODO: multi-thread all of this nonsense
        listeners = self.context.entry_listeners
        for listener in listeners:
            listener.on_pre_scan()
        for entry in self.entries:
            for listener in listeners:
                try:
                    listener.on_entry(entry)
                except Exception:
                    print "Exception on entry %s" % entry
                    raise
        for listener in listeners:
            listener.on_post_scan()


class Tag(object):

    TAG_RE = re.compile(r"""
        @
            (               # group 1: tag name
                [^(\s]+     # anything other than (
            )
        (?:                 # non-grouping
            \(              # literal paren
                (           # group 2: tag value
                    [^)]*?  # anything other than )
                )
            \)
            |
            \s*?
        )?
    """, re.VERBOSE)

    @staticmethod
    def parse(line):
        """Return list of tags"""
        out = []

        res = Tag.TAG_RE.finditer(line)
        if res is not None:
            for re_match in res:
                out.append(Tag(re_match))

        return out

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

    def __repr__(self):
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
                    # TODO: add test of this
                    print("file_name mismatch %s" % file_name)
                    raise ValueError
                guid = match.group(1).strip()
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

    def file_extension(self):
        return self.file_name.split('.')[-1]

    def _create(self):
        with open(self.file_path(), 'w+') as f:
            f.write('\n' * 4)
            f.write("My Reference: %s  \n" % self.guid)
            for tag in self.tags:
                f.write(str(tag))
                f.write('  \n')

    @property
    def tags(self):
        if self._tags is None:
            tags = []
            # TODO: use self.lines here
            with open(self.file_path()) as f:
                for line in f:
                    on_line = Tag.parse(line)
                    tags.extend(on_line)
                    if [t for t in on_line if t.name == 'noscan']:
                        break
            self._tags = [t for t in tags if t is not None]
        return self._tags

    def lines(self):
        with open(self.file_path()) as f:
            for line in f:
                yield line

    def text(self):
        out = '\n'.join([x for x in self.lines()])
        return out

    # maybe combine has_tag and tag_starts_with and pass in a predicate for the tag value?

    def has_tag(self, name, val = None):
        return any(
            t.name == name and (True if val is None else t.value == val)
            for t in self.tags
        )

    def tag_starts_with(self, name, prefix):
        return any(
            t.name == name and t.value is not None and t.value.startswith(prefix)
            for t in self.tags
        )

    def __repr__(self):
        return "%s: %s" % (self.file_name, self.tags)


