#!/usr/bin/env python

# Postpone evaluation of annotations
from __future__ import annotations

import sys
from colorama import init, Fore, Style
from contextlib import contextmanager
from typing import (
    List,
    Generator,
    AnyStr,
    Dict,
    Pattern,
    TextIO,
)

from .database import Database
from .entries import EntryMatch

import jnl.system


class Searcher(object):
    def __init__(self, database: Database):
        self.database = database

    @contextmanager
    def colored_screen(self) -> Generator[TextIO]:
        try:
            init(autoreset=True)
            yield sys.stdout
        finally:
            pass

    def search(self, pattern: Pattern[AnyStr]) -> None:
        with self.colored_screen() as scr:
            return self._search(pattern, scr)

    def _search(self, pattern: Pattern[AnyStr], scr: TextIO) -> None:
        entries: Dict[str, List[EntryMatch]] = self.database.entries_matching(pattern)
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
