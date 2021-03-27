#!/usr/bin/env python

# Postpone evaluation of annotations
from __future__ import annotations

import sys
import os
from colorama import init, Fore, Style
from contextlib import contextmanager
from typing import (
    List,
    Generator,
    AnyStr,
    Dict,
    Optional,
    Pattern,
    TextIO,
    Tuple,
)

from .entries import Entry, EntryMatch
from .listeners import SetsOpenWith, Symlinker, PreScanQuickCleaner, NopListener
from .tag import Tag

import jnl.system


class Settings:
    def __init__(self, context: Context):
        self.context = context

    def dbdir(self) -> str:
        return self.context.environment["JNL_DIR"]


class Database:
    def __init__(
        self,
        context: Context,
        settings: Settings,
        entry_listeners: List[NopListener],
    ):
        self.context = context
        self.settings = settings
        self.entry_listeners = entry_listeners

        self._entries: Optional[List[str]] = None
        """Use .entries instead of _entries to ensure it's initialized"""

    def path(self, *subdirs: str) -> str:
        out = os.path.join(self.settings.dbdir(), *subdirs)
        if not jnl.system.exists(out):
            jnl.system.makedirs(out)
        assert jnl.system.isdir(out)
        return out

    @property
    def entries(self) -> List[Entry]:
        if self._entries is None:
            my_path = self.path("worklogs")
            self._entries = [
                Entry(
                    worklogs_path=self.path("worklogs"),
                    file_name=f,
                    path=my_path,
                )
                for f in os.listdir(my_path)
                if os.path.isfile(os.path.join(my_path, f)) and Entry.valid_file_name(f)
            ]
        return self._entries

    def create_entry(self, tags: List[Tag] = None) -> Entry:
        entry = Entry(worklogs_path=self.path("worklogs"), tags=tags, create=True)
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
            yyyymmdd = jnl.system.yyyymmdd()
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


class Git:
    def __init__(self, context: Context):
        self.context = context

    def _run(self, *git_command: str):
        command = ["git"]
        command.extend(git_command)
        with self.context.in_dir():
            print(jnl.system.check_call(command))

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
        self.sets_open_with = SetsOpenWith(self)
        self.symlinker = Symlinker(self)
        self.pre_scan_quick_cleaner = PreScanQuickCleaner(self)
        self.settings = Settings(self)
        self.database = Database(
            context=self,
            settings=self.settings,
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
        jnl.system.open(entries[key_of_choice][0].entry)
