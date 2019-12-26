#!/usr/bin/env python

from __future__ import annotations

import sys
import datetime
import random
import os
import re
import subprocess
import shutil
import glob
import xattr
import binascii
import dateparser
from colorama import init, Fore, Back, Style
from contextlib import contextmanager
from typing import List, Generator, AnyStr, Dict, Optional, Match, Pattern, TextIO


class Settings(object):
    def __init__(self, context: Context):
        self.context = context

    def dbdir(self) -> str:
        return self.context.environment["JNL_DIR"]


class Database(object):
    def __init__(self, context: Context):
        self.context = context

        self._entries: Optional[List[str]] = None
        """Use .entries instead of _entries to ensure it's initialized"""

    def path(self, *subdirs: str) -> str:
        out = os.path.join(self.context.settings.dbdir(), *subdirs)
        if not self.context.system.exists(out):
            self.context.system.makedirs(out)
        assert self.context.system.isdir(out)
        return out

    @property
    def entries(self) -> List[Entry]:
        if self._entries is None:
            my_path = self.path("worklogs")
            self._entries = [
                Entry(context=self.context, file_name=f, path=my_path)
                for f in os.listdir(my_path)
                if os.path.isfile(os.path.join(my_path, f)) and Entry.valid_file_name(f)
            ]
        return self._entries

    def create_entry(self, tags: List[Tag] = None) -> Entry:
        entry = Entry(context=self.context, tags=tags, create=True)
        self.entries.append(entry)
        return entry

    # maybe combine all these entry_with_* stuff to have a predicate or something
    # or at least refactor internal

    def entries_with_project(self, project: str) -> List[Entry]:
        return [e for e in self.entries if e.tag_starts_with("project", project)]

    def entry_with_guid(self, guid: str) -> Entry:
        return [e for e in self.entries if e.guid == guid][0]

    def entries_with_tag(self, name: str, value: str = None) -> List[Entry]:
        return [e for e in self.entries if e.has_tag(name, value)]

    def daily_entry(self, yyyymmdd: str = None) -> Entry:
        if yyyymmdd is None:
            yyyymmdd = self.context.what_day_is_it.yyyymmdd()
        tag_val = "daily/%s" % yyyymmdd
        existing = self.entries_with_tag("quick", tag_val)
        if not existing:
            existing = [
                self.create_entry(
                    tags=[Tag(name="quick", value=tag_val), Tag(name="ft")]
                )
            ]
        return existing[0]

    def yesterday_entry(self) -> Entry:
        existing = [
            (e, e.is_a_daily_entry()) for e in self.entries if e.is_a_daily_entry()
        ]
        existing.sort(key=lambda tup: tup[1])
        # -1 ("last item") is today
        return existing[-2][0]

    def scan(self) -> None:
        # TODO: multi-thread all of this nonsense
        listeners = self.context.entry_listeners
        for listener in listeners:
            listener.on_pre_scan()
        for entry in self.entries:
            for listener in listeners:
                try:
                    listener.on_entry(entry)
                except Exception:
                    print("Listener %s Exception on entry %s" % (listener, entry))
                    raise
        for listener in listeners:
            listener.on_post_scan()

    def entries_matching(self, pattern: Pattern[AnyStr]) -> Dict[str, List[EntryMatch]]:
        out: Dict[str, (Entry, List[EntryMatch])] = {}
        for e in self.entries:
            matches: List[EntryMatch] = e.matches(pattern)
            if matches:
                out[e.guid] = matches
        return out


class Tag(object):
    TAG_RE = re.compile(
        r"""
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
    """,
        re.VERBOSE,
    )

    DAILY_RE = re.compile(
        r"""
        ^
        daily/(.*?)     # group 1: date
        $
        """,
        re.VERBOSE,
    )

    @staticmethod
    def parse(line: str) -> List[Tag]:
        """Return list of tags"""
        out = []

        res = Tag.TAG_RE.finditer(line)
        if res is not None:
            for re_match in res:
                out.append(Tag(re_match))

        return out

    def __init__(self, re_match: Match[AnyStr] = None, name=None, value=None):
        if re_match is not None:
            name = re_match.group(1).strip()
            value = re_match.group(2)
        self._name: str = name
        self._value: str = value

    def daily(self) -> Optional[str]:
        if self.name != "quick" or not self.value:
            return None
        match = Tag.DAILY_RE.match(self.value)
        if match:
            return match.group(1)
        return None

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "@%s%s" % (
            self.name,
            "(" + self.value + ")" if self.value is not None else "",
        )


class Entry(object):
    FILENAME_RE = re.compile(
        r"""
        ^
        ([A-Z0-9]+)     # group 1: file name without extension
        \.
        (.*?)           # group 2: extension
        $
    """,
        re.X,
    )

    @staticmethod
    def valid_file_name(file_name) -> Optional[Match[AnyStr]]:
        return Entry.FILENAME_RE.match(file_name)

    def __init__(
        self,
        context: Context,
        path: str = None,
        file_name: str = None,
        guid: str = None,
        tags: List[Tag] = None,
        create: bool = False,
    ):
        self.context = context

        if guid is None:
            if file_name is None:
                guid = self.context.guid_generator.guid()
            else:
                match = Entry.FILENAME_RE.match(file_name)
                if match is None:
                    # TODO: add test of this
                    print(("file_name mismatch %s" % file_name))
                    raise ValueError
                guid = match.group(1).strip()
        self.guid: str = guid

        if path is None:
            path = self.context.database.path("worklogs")
        self.path: str = path
        """dirname of full file_name path"""

        if file_name is None:
            file_name = "%s.txt" % self.guid
        self.file_name: str = file_name

        self._tags: List[Tag] = tags

        if create:
            self._create()

    def is_a_daily_entry(self) -> Optional[str]:
        """
        :return: if this entry has @quick(daily/X) returns X else None
        """
        tags = [t for t in self.tags if t.daily()]
        if not tags:
            return None
        return tags[0].daily()

    def file_path(self) -> str:
        return os.path.join(self.path, self.file_name)

    def file_extension(self) -> str:
        return self.file_name.split(".")[-1]

    def _create(self) -> None:
        with open(self.file_path(), "w+") as f:
            f.write("\n")
            f.write("My Reference: %s  \n" % self.guid)
            for tag in self.tags:
                f.write(str(tag))
                f.write("  \n")

    @property
    def tags(self) -> List[Tag]:
        if self._tags is None:
            tags = []
            # TODO: use self.lines here
            with open(self.file_path()) as f:
                for line in f:
                    on_line = Tag.parse(line)
                    tags.extend(on_line)
                    if [t for t in on_line if t.name == "noscan"]:
                        break
            self._tags = [t for t in tags if t is not None]
        return self._tags

    def lines(
        self, min_index: int = 0, max_index: Optional[int] = None
    ) -> Generator[(str, int)]:
        if min_index < 0 or (max_index is not None and min_index > max_index):
            raise ValueError("Invalid min={} and max={}".format(min_index, max_index))
        line_index = -1
        with open(self.file_path()) as f:
            for line in f:
                line_index = line_index + 1
                if max_index is not None and line_index > max_index:
                    break
                elif line_index < min_index:
                    continue
                yield (line.strip(), line_index)

    def text(self) -> str:
        out = "\n".join([x for x in self.lines()])
        return out

    # maybe combine has_tag and tag_starts_with and pass in a predicate for the tag value?

    def has_tag(self, name: str, val: str = None) -> bool:
        return any(
            t.name == name and (True if val is None else t.value == val)
            for t in self.tags
        )

    def tag_starts_with(self, name: str, prefix: str) -> bool:
        return any(
            t.name == name and t.value is not None and t.value.startswith(prefix)
            for t in self.tags
        )

    def __repr__(self) -> str:
        return "%s: %s" % (self.file_name, self.tags)

    def matches(self, pattern: Pattern[AnyStr]) -> List[EntryMatch]:
        # can probably be turned into a nicer comprehension
        out = []
        for (line, line_index) in self.lines():
            match: Optional[Match[AnyStr]] = pattern.search(line)
            if match:
                entry_match = EntryMatch(self, match, line_index)
                out.append(entry_match)
        return out


class EntryMatch(object):
    def __init__(self, entry: Entry, match: Match[AnyStr], matched_line_index: int):
        self.entry = entry
        self.match = match
        self.matched_line_index = matched_line_index

    def print(
        self,
        scr: TextIO,
        before_context: int = 0,
        after_context: int = 0,
        prefix: str = "  ",
    ):
        min_line = max(0, self.matched_line_index - before_context)
        max_line = self.matched_line_index + after_context
        for (line, line_index) in self.entry.lines(min_line, max_line):
            scr.write(prefix)
            if line_index == self.matched_line_index:
                begin, end = self.match.span()
                scr.write(line[0:begin])
                scr.write(Fore.YELLOW + line[begin:end])
                scr.write(line[end:])
            else:
                scr.write(line)
            scr.write("\n")


class Opener(object):
    def __init__(self, context: Context):
        self.context = context

    def open(self, entry: Entry) -> None:
        return self.context.system.check_call(
            ["open", "-a", "FoldingText", entry.file_path()]
        )


class NopListener(object):
    def __init__(self, context: Context):
        self.context = context
        self.state = {}

    def on_entry(self, entry: Entry) -> None:
        pass

    def on_pre_scan(self) -> None:
        pass

    def on_post_scan(self) -> None:
        pass


class SetsOpenWith(NopListener):
    def __init__(self, context: Context):
        super().__init__(context)

    """The xattr controlling the "Open With" functionality is unfortunately binary.
    To use a different application, use `xattr -px`

    or with `-px`:

        $ xattr -px com.apple.LaunchServices.OpenWith $FILE
        62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57
        [...]
        00 00 00 00 00 6F
    """

    OPEN_WITH_ATTR_HEX = re.sub(
        r"\s*",
        "",
        """
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
    """,
        flags=re.M,
    )

    OPEN_WITH_ATTR = binascii.unhexlify(OPEN_WITH_ATTR_HEX)

    def on_entry(self, entry: Entry) -> None:
        if not entry.has_tag("ft", None):
            return

        return xattr.setxattr(
            entry.file_path(),
            "com.apple.LaunchServices.OpenWith",
            SetsOpenWith.OPEN_WITH_ATTR,
        )


class System(object):
    def __init__(self, context: Context):
        self.context = context

    @staticmethod
    def file_contents(path: str):
        path = os.path.join(os.environ.get("JNL_ORIG_CWD"), path)
        with open(path, "r") as f:
            return f.read()

    @staticmethod
    def makedirs(*args: str):
        return os.makedirs(*args)

    @staticmethod
    def check_call(*args: str):
        subprocess.check_call(*args)

    @staticmethod
    def exists(path: str):
        return os.path.exists(path)

    @staticmethod
    def readlink(path: str):
        return os.readlink(path)

    @staticmethod
    def symlink(source: str, destination: str):
        return os.symlink(source, destination)

    @staticmethod
    def unlink(path: str):
        return os.unlink(path)

    @staticmethod
    def rmtree(path: str):
        """Remove everything in a directory but don't remove the directory itself.
        This is useful if you have things referring to the file inode itself or
        things that generally get confused about treating a directory as symbolic name."""
        for f in glob.glob(os.path.join(path, "*")):
            if os.path.isfile(f) or os.path.islink(f):
                os.remove(f)
            else:
                try:
                    shutil.rmtree(f)
                except Exception as e:
                    print(("Cannot remove {}/{}".format(path, f)))
                    raise e

    @staticmethod
    def isdir(path: str):
        return os.path.isdir(path)

    @staticmethod
    def now() -> datetime:
        return datetime.datetime.now()


class Symlinker(NopListener):
    def on_entry(self, entry: Entry) -> None:
        if self.state.get("yyyymmdd") is None:
            self.state["yyyymmdd"] = self.context.what_day_is_it.yyyymmdd()
        tags = [t for t in entry.tags if t.name == "quick" and t.value is not None]
        for tag in tags:
            val = tag.value
            parts = val.split("/")
            dir_parts = parts[:-1]
            past = parts[-1]
            filename_part = "%s.%s" % (past, entry.file_extension())
            into_dir = self.context.database.path("quick", *dir_parts)
            symlink = os.path.join(into_dir, filename_part)
            if self.context.system.exists(symlink):
                existing = self.context.system.readlink(symlink)
                if existing == entry.file_path():
                    # job already done
                    continue
                else:
                    raise ValueError(
                        "@quick(%s) owned by %s, so %s can't take it"
                        % (val, existing, entry.file_path())
                    )
            self.context.system.symlink(entry.file_path(), symlink)


class PreScanQuickCleaner(NopListener):
    def on_pre_scan(self) -> None:
        path = self.context.database.path("quick")
        print(("Scanning %s" % path))
        if self.context.system.exists(path):
            self.context.system.rmtree(path)


class WhatDayIsIt(object):
    def __init__(self, context: Context):
        self.context = context

    def yyyymmdd(self) -> str:
        now = self.context.system.now()
        return "%04d-%02d-%02d" % (now.year, now.month, now.day)

    def parse(self, somedate) -> str:
        return dateparser.parse(somedate)

class GuidGenerator(object):
    def __init__(self, context: Context):
        self.context = context

    LETTERS = [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "J",
        "K",
        "M",
        "N",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "W",
        "X",
        "Y",
        "Z",
    ]

    @staticmethod
    def guid() -> str:
        return "".join([random.choice(GuidGenerator.LETTERS) for _ in range(21)])


class Git(object):
    def __init__(self, context: Context):
        self.context = context

    def _run(self, *git_command: str):
        command = ["git"]
        command.extend(git_command)
        with self.context.in_dir():
            print(self.context.system.check_call(command))

    def stat(self):
        self._run("status")

    def pull(self):
        self._run("pull")

    def status(self):
        self._run("status")

    def autopush(self):
        self._run("autopush")


class Context(object):
    def __init__(self, environment: Dict[str, str]):
        self.environment = environment
        self.system = System(self)
        self.opener = Opener(self)
        self.sets_open_with = SetsOpenWith(self)
        self.what_day_is_it = WhatDayIsIt(self)
        self.guid_generator = GuidGenerator(self)
        self.symlinker = Symlinker(self)
        self.pre_scan_quick_cleaner = PreScanQuickCleaner(self)
        self.settings = Settings(self)
        self.database = Database(self)
        self.git = Git(self)
        self.entry_listeners = [
            self.sets_open_with,
            self.symlinker,
            self.pre_scan_quick_cleaner,
        ]
        self.searcher = Searcher(self)

    def __str__(self):
        return "Context()"

    @contextmanager
    def in_dir(self, *path: str) -> None:
        old_dir = os.getcwd()
        try:
            os.chdir(self.database.path(*path))
            yield
        finally:
            os.chdir(old_dir)


# TODO: is this really necessary?
class ColoredUI(object):
    @contextmanager
    def colored_screen(self) -> Generator[TextIO]:
        try:
            init(autoreset=True)
            yield sys.stdout
        finally:
            pass


class Searcher(object):
    def __init__(self, context: Context):
        self.context = context

    def search(self, pattern: Pattern[AnyStr]) -> None:
        ui = ColoredUI()
        with ui.colored_screen() as scr:
            return self._search(pattern, scr)

    def _search(self, pattern: Pattern[AnyStr], scr: TextIO) -> None:
        entries: Dict[str, List[EntryMatch]] = self.context.database.entries_matching(
            pattern
        )
        index: int = 0
        options: Dict[int, str] = {}
        # TODO: this impl is messy and split up between EntryMatch and here
        # TODO: better sorting
        scr.write(Fore.LIGHTGREEN_EX + "Found " + str(len(entries)) + ":\n")
        written = 0
        for k, v in entries.items():
            if written > 10:
                break
            else:
                written = written + 1
            scr.write(Fore.RED + Style.BRIGHT + str(index))
            scr.write("  ")
            scr.write(Fore.LIGHTYELLOW_EX + v[0].entry.file_name)
            scr.write("\n")
            [m.print(scr) for m in v[0:2]]
            options[index] = k
            index = index + 1
        choice = int(input("? "))
        key_of_choice = options[choice]
        self.context.opener.open(entries[key_of_choice][0].entry)


class Main(object):
    def __init__(self, environment=None):
        if environment is None:
            environment = os.environ
        self.context = Context(environment=environment)

    def open(self, argv):
        self.context.opener.open(self.context.database.entry_with_guid(argv[2]))

    def new(self, _):
        self.context.opener.open(self.context.database.create_entry())

    def sync(self, argv):
        self.context.git.pull()
        self.scan(argv)
        self.context.git.status()
        if len(argv) > 2 and argv[2] == "push":
            self.context.git.autopush()

    def search(self, argv):
        pat_source: str = argv[2]

        if not pat_source.startswith("/"):
            pattern = re.compile(pat_source, re.I)
        else:
            if not pat_source.endswith("/"):
                raise ValueError(
                    "Pattern '{}' must begin and end with /".format(pat_source)
                )
            pat_source = pat_source[1:-1]
            pattern = re.compile(pat_source)
        return self.context.searcher.search(pattern)

    def stat(self, _):
        self.context.git.status()

    def proj(self, argv):
        if len(argv) < 3:
            project = self.context.system.file_contents(".project").strip()
        else:
            project = argv[2]
        for e in self.context.database.entries_with_project(project):
            self.context.opener.open(e)

    def run(self, argv):
        if len(argv) == 1 or argv[1].startswith("p"):
            return self.proj(argv)
        if argv[1] == "search":
            return self.search(argv)
        if argv[1] == "new":
            return self.new(argv)
        if argv[1] == "daily" or argv[1] == "today" or argv[1] == "y":
            return self.daily(argv)
        if argv[1] == "yesterday":
            return self.yesterday()
        if argv[1] == "stat" or argv[1] == "st":
            return self.stat(argv)
        if argv[1] == "scan":
            return self.scan(argv)
        if argv[1] == "open":
            return self.open(argv)
        if argv[1] == "sync":
            return self.sync(argv)
        raise ValueError("Don't know about action {}".format(argv[1]))

    def scan(self, _):
        self.context.database.scan()

    # TODO: finish
    def yesterday(self):
        daily = self.context.database.yesterday_entry()
        self.context.opener.open(daily)
        self.context.database.scan()

    def daily(self, _):
        daily = self.context.database.daily_entry()
        self.context.opener.open(daily)
        self.context.database.scan()


def empty_fixture_path():
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "fixtures", "empty"
    )


if __name__ == "__main__":
    main = Main(
        {
            "JNL_DIR": os.environ["JNL_DIR"]
            if "JNL_DIR" in os.environ
            else empty_fixture_path()
        }
    )
    main.run(sys.argv)
