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

from jnl.database import Database
from jnl.entries import EntryMatch

import jnl.system


@contextmanager
def _colored_screen() -> Generator[TextIO, None, None]:
    try:
        init(autoreset=True)
        yield sys.stdout
    finally:
        pass


def search(database: Database, pattern: Pattern[AnyStr]) -> None:
    with _colored_screen() as scr:
        return _search(database=database, pattern=pattern, scr=scr)


def _search(database: Database, pattern: Pattern[AnyStr], scr: TextIO) -> None:
    entries: Dict[str, List[EntryMatch]] = database.entries_matching(pattern)
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
    jnl.system.open_entry(entries[key_of_choice][0].entry)
