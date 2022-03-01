import os
import re
import sys

import jnl.system

import jnl.search
from jnl.database import Database
from jnl.listeners import SetsOpenWith, Symlinker, PreScanQuickCleaner


class Main(object):
    def __init__(self, dbdir: str = None):
        self.database = Database(
            dbdir=dbdir,
            entry_listeners=[SetsOpenWith(), Symlinker(), PreScanQuickCleaner()],
        )

    def open(self, argv):
        jnl.system.open_entry(self.database.entry_with_guid(argv[2]))

    def new(self, _):
        jnl.system.open_entry(self.database.create_entry())

    def sync(self, argv):
        git_dir = self.database.path()
        jnl.system.git_pull(git_dir)
        self.scan(argv)
        jnl.system.git_stat(git_dir)
        if len(argv) > 2 and argv[2] == "push":
            jnl.system.git_autopush(git_dir)

    def rename_daily(self, argv):
        entries = [x for x in self.database.entries if x.is_a_daily_entry()]
        for entry in entries:
            daily = entry.is_a_daily_entry()
            entry.rename_file(f"{daily}.txt")

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
        return jnl.search.search(database=self.database, pattern=pattern)

    def stat(self, _):
        git_dir = self.database.path()
        jnl.system.git_stat(git_dir)

    def proj(self, argv):
        if len(argv) < 3:
            project = jnl.system.file_contents(".project").strip()
        else:
            project = argv[2]
        for e in self.database.entries_with_project(project):
            jnl.system.open_entry(e)

    def run(self, argv):
        if len(argv) == 1 or argv[1].startswith("p"):
            return self.proj(argv)
        if argv[1] == "search":
            return self.search(argv)
        if argv[1] == "new":
            return self.new(argv)
        if argv[1] == "daily" or argv[1] == "today" or argv[1] == "t":
            return self.daily(argv)
        if argv[1] == "y" or argv[1] == "yesterday" or argv[1] == "yd":
            return self.yesterday()
        if argv[1] == "stat" or argv[1] == "st":
            return self.stat(argv)
        if argv[1] == "scan":
            return self.scan(argv)
        if argv[1] == "open":
            return self.open(argv)
        if argv[1] == "sync":
            return self.sync(argv)
        if argv[1] == "rename-daily":
            return self.rename_daily(argv)
        raise ValueError("Don't know about action {}".format(argv[1]))

    def scan(self, _):
        self.database.scan()

    def yesterday(self):
        daily = self.database.yesterday_entry()
        jnl.system.open_entry(daily)
        self.database.scan()

    def daily(self, _):
        daily = self.database.daily_entry()
        jnl.system.open_entry(daily)
        self.database.scan()


def empty_fixture_path():
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "fixtures", "empty"
    )


def main(args=None):
    if args is None:
        args = sys.argv
    if "JNL_DIR" not in os.environ:
        os.environ["JNL_DIR"] = empty_fixture_path()
    mainv = Main()
    mainv.run(args)
