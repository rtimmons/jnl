#!/usr/bin/env python

from __future__ import annotations

import sys
import os
import re
from colorama import init, Fore, Style
from contextlib import contextmanager
from typing import (
    List,
    Generator,
    AnyStr,
    Dict,
    Optional,
    Match,
    Pattern,
    TextIO,
    Tuple,
)

from .system import System, GuidGenerator, Opener, WhatDayIsIt
from .listeners import SetsOpenWith, Symlinker, PreScanQuickCleaner, NopListener
from .tag import Tag


class Settings(object):
    def __init__(self, context: Context):
        self.context = context

    def dbdir(self) -> str:
        return self.context.environment["JNL_DIR"]


class Database(object):
    def __init__(
        self,
        system: System,
        settings: Settings,
        guid_generator: GuidGenerator,
        what_day_is_it: WhatDayIsIt,
        entry_listeners: List[NopListener],
    ):
        self.system = system
        self.settings = settings
        self.guid_generator = guid_generator
        self.what_day_is_it = what_day_is_it
        self.entry_listeners = entry_listeners

        self._entries: Optional[List[str]] = None
        """Use .entries instead of _entries to ensure it's initialized"""

    def path(self, *subdirs: str) -> str:
        out = os.path.join(self.settings.dbdir(), *subdirs)
        if not self.system.exists(out):
            self.system.makedirs(out)
        assert self.system.isdir(out)
        return out

    @property
    def entries(self) -> List[Entry]:
        if self._entries is None:
            my_path = self.path("worklogs")
            self._entries = [
                Entry(
                    guid_generator=self.guid_generator,
                    database=self,
                    file_name=f,
                    path=my_path,
                )
                for f in os.listdir(my_path)
                if os.path.isfile(os.path.join(my_path, f)) and Entry.valid_file_name(f)
            ]
        return self._entries

    def create_entry(self, tags: List[Tag] = None) -> Entry:
        entry = Entry(
            guid_generator=self.guid_generator, database=self, tags=tags, create=True
        )
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
            yyyymmdd = self.what_day_is_it.yyyymmdd()
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
        existing: List[Tuple[Entry, Optional[str]]] = [
            (e, e.is_a_daily_entry()) for e in self.entries if e.is_a_daily_entry()
        ]
        existing.sort(key=lambda tup: tup[1])
        # -1 ("last item") is today
        return existing[-2][0]

    def scan(self) -> None:
        # TODO: multi-thread all of this nonsense
        listeners = self.entry_listeners
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
        guid_generator: GuidGenerator,
        database: Database,
        path: str = None,
        file_name: str = None,
        guid: str = None,
        tags: List[Tag] = None,
        create: bool = False,
    ):
        self.guid_generator = guid_generator
        self.database = database

        if guid is None:
            if file_name is None:
                guid = self.guid_generator.guid()
            else:
                match = Entry.FILENAME_RE.match(file_name)
                if match is None:
                    # TODO: add test of this
                    print(("file_name mismatch %s" % file_name))
                    raise ValueError
                guid = match.group(1).strip()
        self.guid: str = guid

        if path is None:
            path = self.database.path("worklogs")
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
        self.system = System()
        self.opener = Opener(self.system)
        self.sets_open_with = SetsOpenWith(self)
        self.what_day_is_it = WhatDayIsIt(self.system)
        self.guid_generator = GuidGenerator()
        self.symlinker = Symlinker(self)
        self.pre_scan_quick_cleaner = PreScanQuickCleaner(self)
        self.settings = Settings(self)
        self.database = Database(
            system=self.system,
            settings=self.settings,
            guid_generator=self.guid_generator,
            what_day_is_it=self.what_day_is_it,
            entry_listeners=[
                self.sets_open_with,
                self.symlinker,
                self.pre_scan_quick_cleaner,
            ],
        )
        self.git = Git(self)
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
