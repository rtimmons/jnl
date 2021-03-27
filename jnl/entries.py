import os
import re
from typing import Optional, Match, AnyStr, List, Generator, Pattern, TextIO, Tuple

from colorama import Fore

import jnl.system
from jnl.tag import Tag


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
        worklogs_path: str,
        path: str = None,
        file_name: str = None,
        guid: str = None,
        tags: List[Tag] = None,
        create: bool = False,
    ):
        self.worklogs_path = worklogs_path

        if guid is None:
            if file_name is None:
                guid = jnl.system.guid()
            else:
                match = Entry.FILENAME_RE.match(file_name)
                if match is None:
                    # TODO: add test of this
                    print(("file_name mismatch %s" % file_name))
                    raise ValueError
                guid = match.group(1).strip()
        self.guid: str = guid

        if path is None:
            path = self.worklogs_path
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
    ) -> Generator[Tuple[str, int], None, None]:
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

    def matches(self, pattern: Pattern[AnyStr]) -> List["EntryMatch"]:
        # can probably be turned into a nicer comprehension
        out = []
        for (line, line_index) in self.lines():
            match: Optional[Match[AnyStr]] = pattern.search(line)
            if match:
                entry_match = EntryMatch(self, match, line_index)
                out.append(entry_match)
        return out


class EntryMatch:
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
