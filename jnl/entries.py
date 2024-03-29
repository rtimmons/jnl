import os
import re
from typing import (
    Callable,
    Optional,
    Match,
    AnyStr,
    List,
    Generator,
    Pattern,
    TextIO,
    Tuple,
)

from colorama import Fore

import jnl.system


class Tag:
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

    ONE_ON_ONE_RE = re.compile(
        r"""
        ^
        [O|o]ne
        /(.*?)          # group 1: person
        /(.*?)          # group 2: date
        $
        """,
        re.VERBOSE,
    )

    @staticmethod
    def parse(line: str) -> List["Tag"]:
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

    def one_on_one(self) -> Optional[Tuple[str, str]]:
        """
        :returns [name, date] if the tag represents a @quick(One/name/date) value.
        """
        if self.name != "quick" or not self.value:
            return None
        match = Tag.ONE_ON_ONE_RE.match(self.value)
        if match:
            return match.group(1), match.group(2)
        return None

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


class EntryMatch:
    def __init__(self, entry: "Entry", match: Match[AnyStr], matched_line_index: int):
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


class Entry:
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

    EXTRACT_GUID_RE = re.compile(
        r"^(?:My Reference):\s+([A-Z0-9]+)\s*$",
    )

    @staticmethod
    def valid_file_name(file_name: str) -> bool:
        return file_name.endswith(".txt")

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

        found_guid = guid
        if found_guid is None:
            if file_name is None:
                found_guid = jnl.system.guid()
            else:
                match = Entry.FILENAME_RE.match(file_name)
                if match is not None:
                    found_guid = match.group(1).strip()
        if found_guid is None:
            with open(os.path.join(self.worklogs_path, file_name), "r") as handle:
                for line in handle.readlines():
                    match = Entry.EXTRACT_GUID_RE.match(line)
                    if match:
                        found_guid = match.group(0)
        if found_guid is None:
            raise ValueError(f"Couldn't find guid on {file_name}")
        self.guid: str = found_guid

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

        self._tags: List[Tag] = []

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

    def rename_file(self, new_name: str):
        jnl.system.git_mv(self.worklogs_path, self.file_name, new_name)

    def _create(self) -> None:
        with open(self.file_path(), "w+") as f:
            f.write("\n")
            f.write("My Reference: %s  \n" % self.guid)
            for tag in self.tags:
                f.write(str(tag))
                f.write("  \n")

    @property
    def tags(self) -> List[Tag]:
        if not self._tags:
            tags = []
            for line, line_no in self.lines():
                on_line = Tag.parse(line)
                tags.extend(on_line)
                if [t for t in on_line if t.name == "noscan"]:
                    break
            self._tags = [t for t in tags if t is not None]
        return self._tags

    def single_quick_entry(self) -> Optional[str]:
        quick = [t for t in self.tags if t.name == "quick"]
        if len(quick) != 1 or self.is_a_daily_entry():
            return None
        val = quick[0].value
        if "/" in val:
            # TODO: handle subdirs separately
            return None
        return val

    def lines(
        self, min_index: int = 0, max_index: Optional[int] = None, strip=False
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
                yield line.strip() if strip else line, line_index

    def text(self) -> str:
        out = "\n".join([line for (line, line_no) in self.lines()])
        return out

    def rewrite(self, replacements: List[Callable[[str], str]]):
        lines = [*self.lines(strip=False)]
        replaced = []
        for line, line_no in lines:
            for replacement in replacements:
                line = replacement(line)
            replaced.append(line)
        if lines == replaced:
            return
        with open(self.file_path(), "w") as handle:
            handle.writelines(replaced)

    def convert_ft_tags_to_obsidian(self):
        """
        Convert lines like
            @quick(One/Foo/yyyy-mm-dd)
        to
            #one/Foo yyyy-mm-dd
        """

        def _conv_tag(line: str) -> str:
            tags = Tag.parse(line)
            if not tags:
                return line
            one = [t for t in tags if t.one_on_one()]
            if not one or not one[0]:
                return line
            person, when = one[0].one_on_one()
            person = person.replace(" ", "_")
            return line.replace(str(one[0]), f"#one/{person} {when}")

        self.rewrite([_conv_tag])

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
            the_match: Optional[Match[AnyStr]] = pattern.search(line)
            if the_match:
                entry_match = EntryMatch(self, the_match, line_index)
                out.append(entry_match)
        return out
