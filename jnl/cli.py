import os
import re
import sys

from jnl.all import Context
from jnl import system


class Main(object):
    def __init__(self, environment=None):
        if environment is None:
            environment = os.environ
        self.context = Context(environment=environment)

    def open(self, argv):
        system.open(self.context.database.entry_with_guid(argv[2]))

    def new(self, _):
        system.open(self.context.database.create_entry())

    def sync(self, argv):
        git_dir = self.context.database.path()
        system.git_pull(git_dir)
        self.scan(argv)
        system.git_stat(git_dir)
        if len(argv) > 2 and argv[2] == "push":
            system.git_autopush(git_dir)

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
        git_dir = self.context.database.path()
        system.git_stat(git_dir)

    def proj(self, argv):
        if len(argv) < 3:
            project = system.file_contents(".project").strip()
        else:
            project = argv[2]
        for e in self.context.database.entries_with_project(project):
            system.open(e)

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
        raise ValueError("Don't know about action {}".format(argv[1]))

    def scan(self, _):
        self.context.database.scan()

    # TODO: finish
    def yesterday(self):
        daily = self.context.database.yesterday_entry()
        system.open(daily)
        self.context.database.scan()

    def daily(self, _):
        daily = self.context.database.daily_entry()
        system.open(daily)
        self.context.database.scan()


def empty_fixture_path():
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "fixtures", "empty"
    )


def main(args=None):
    if args is None:
        args = sys.argv
    mainv = Main(
        {
            "JNL_DIR": os.environ["JNL_DIR"]
            if "JNL_DIR" in os.environ
            else empty_fixture_path()
        }
    )
    mainv.run(args)
