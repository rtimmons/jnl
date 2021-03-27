import os
from typing import List, Optional, Tuple, Pattern, AnyStr, Dict

import jnl.system
from jnl.entries import Entry, Tag, EntryMatch


def dbdir() -> str:
    return os.getenv("JNL_DIR")


class NopListener(object):
    def on_entry(self, database: "Database", entry: "Entry") -> None:
        pass

    def on_pre_scan(self, database: "Database") -> None:
        pass

    def on_post_scan(self, database: "Database") -> None:
        pass


class Database:
    def __init__(
        self,
        entry_listeners: List[NopListener],
    ):
        self.entry_listeners = entry_listeners

        self._entries: Optional[List[str]] = None
        """Use .entries instead of _entries to ensure it's initialized"""

    def path(self, *subdirs: str) -> str:
        out = os.path.join(dbdir(), *subdirs)
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
            listener.on_pre_scan(database=self)
        for entry in self.entries:
            for listener in listeners:
                try:
                    listener.on_entry(database=self, entry=entry)
                except Exception:
                    print("Listener %s Exception on entry %s" % (listener, entry))
                    raise
        for listener in listeners:
            listener.on_post_scan(database=self)

    def entries_matching(self, pattern: Pattern[AnyStr]) -> Dict[str, List[EntryMatch]]:
        out: Dict[str, (Entry, List[EntryMatch])] = {}
        for e in self.entries:
            matches: List[EntryMatch] = e.matches(pattern)
            if matches:
                out[e.guid] = matches
        return out
