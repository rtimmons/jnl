import re

from typing import List, Match, AnyStr, Optional


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
