import random
import sys
import os
import shutil
import tempfile

bin_dir = os.path.join(os.path.dirname(__file__), "..", "bin")
sys.path.insert(0, bin_dir)

import jnl

import unittest
import mock

fixture_dir = os.path.join(bin_dir, "..", "tests", "fixtures")


class TestTag(unittest.TestCase):
    def parses(self, line, should_have=None):
        tags = jnl.Tag.parse(line)
        if should_have is None:
            should_have = [line]
        assert [str(tag) for tag in tags] == should_have

    def test_single_cases(self):
        cases = [
            "@quick",
            "@done",
            "@a-b-c",
            "@quick()",
            "@quick(foo-bar)",
            "@quick@",
            "@@",
            "@_",
            "@foo(a b)",
            "@foo(@bar)",  # odd
            # TODO: support emoji / utf-8 tags
        ]
        for case in cases:
            self.parses(case)

    def test_multi(self):
        self.parses("@ft @quick(a-b-c)", ["@ft", "@quick(a-b-c)"])

    def test_dupe(self):
        self.parses(
            # TODO: should we de-dupe or barf?
            "@ft @ft",
            ["@ft", "@ft"],
        )

    def test_triple(self):
        self.parses(
            # TODO: should we de-dupe or barf?
            "@ft @done @quick(other-foo) @abc",
            ["@ft", "@done", "@quick(other-foo)", "@abc"],
        )


# TODO: case of multiple files saying @quick(something).
# A symlink can't point to 2 things.


class TestWhatDayIsIt(unittest.TestCase):
    def test_formats_days(self):
        now = mock.MagicMock()
        now.year = 2017
        now.month = 2
        now.day = 1

        context = mock.MagicMock()
        context.system.now.return_value = now

        # test of the test
        assert context.system.now().year == 2017

        what = jnl.WhatDayIsIt(context=context)
        assert what.yyyymmdd() == "2017-02-01"


class TestDatabase(unittest.TestCase):
    def main_with_fixture(self, fixture_name: str = "typical") -> (jnl.Main, str):
        source_fixture = os.path.join(fixture_dir, fixture_name)

        tmp_dir = tempfile.mkdtemp()
        jnl_dir = os.path.join(tmp_dir, fixture_name)
        shutil.copytree(source_fixture, jnl_dir)

        self.to_cleanup.append(tmp_dir)
        return jnl.Main({"JNL_DIR": jnl_dir}), jnl_dir

    def setUp(self):
        random.seed(100)
        self.to_cleanup = []

    def tearDown(self):
        for c in self.to_cleanup:
            # print "Cleaning up %s" % c
            shutil.rmtree(c)

    def test_path(self):
        main, jnl_dir = self.main_with_fixture("typical")
        assert main.context.database.path() == jnl_dir

        assert os.path.exists(main.context.database.path("quick"))
        assert os.path.exists(
            main.context.database.path("quick", "something_we_create_now")
        )

    def test_list_entries(self):
        main, jnl_dir = self.main_with_fixture("typical")
        entries = main.context.database.entries
        assert len(entries) == 2
        guids = [e.guid for e in entries]
        assert guids == ["HMKYKM4NNG4KREW61D55", "W5BNE202WYF031H7J3RY"]

    def test_entries_with_tags(self):
        main, jnl_dir = self.main_with_fixture("typical")

        with_tag = main.context.database.entries_with_tag("quick", "tickets/PERF-1188")
        assert len(with_tag) == 1
        assert with_tag[0].guid == "HMKYKM4NNG4KREW61D55"
        self.has_tags(
            with_tag[0],
            "@ft",
            "@quick(tickets/PERF-1188)",
            "@quick(daily/2018-05-30)",
            "@quick(entry-one-one)",
            "@quick(entry-one-two)",
        )

    def has_tags(self, entry, *tags):
        assert set([str(t) for t in entry.tags]) == set(tags)

    def mock_what_day_is_it(self, main):
        what_day_is_it = mock.MagicMock()
        what_day_is_it.yyyymmdd.return_value = "2009-11-28"
        main.context.what_day_is_it = what_day_is_it
        return what_day_is_it

    def test_creates_daily_entry(self):
        main, jnl_dir = self.main_with_fixture("typical")
        self.mock_what_day_is_it(main)

        daily = main.context.database.daily_entry()
        entries = main.context.database.entries
        assert len(entries) == 3

        with_tag = main.context.database.entries_with_tag("quick", "daily/2009-11-28")
        assert len(with_tag) == 1
        assert (
            with_tag[0].guid == "9XXBSPU775XG3DNEKDB9C"
        )  # guaranteed cuz we set random.seed
        self.has_tags(with_tag[0], "@ft", "@quick(daily/2009-11-28)")

    def test_uses_existing_daily_entry(self):
        main, jnl_dir = self.main_with_fixture("typical")
        self.mock_what_day_is_it(main)

        daily = main.context.database.daily_entry()
        entries = main.context.database.entries
        assert len(entries) == 3

        another = jnl.Main({"JNL_DIR": jnl_dir})
        self.mock_what_day_is_it(another)

        assert another is not main

        assert len(another.context.database.entries) == 3
        another_daily = another.context.database.daily_entry()
        assert another_daily.guid == daily.guid

        assert another_daily is not daily

    class MockSystem(object):
        def __init__(self, root, files={}):
            self.files = files
            self.calls = []
            self.root = root

        def _rmroot(self, path):
            return path.replace(self.root, "root")

        def exists(self, path):
            return self._rmroot(path) in self.files

        def now(self):
            class YMD:
                def __init__(self):
                    self.year = 2009
                    self.month = 11
                    self.day = 28

            return YMD()

        def isdir(self, path):
            path = self._rmroot(path)
            return (
                path in self.files and self.files[path] == "dir"
            )  # change if using tuple

        def makedirs(self, *path):
            # TODO: use path as second item in tuple to be consistent
            self.files[self._rmroot(os.path.join(*path))] = "dir"

        def symlink(self, source, link_name):
            self.files[self._rmroot(link_name)] = ("symlink", self._rmroot(source))

        def readlink(self, link):
            typ, path = self.files[self._rmroot(link)]
            assert typ == "symlink"
            return path.replace("root", self.root, 1)

        def unlink(self, path):
            path = self._rmroot(path)
            self.files = {k: v for k, v in self.files.items() if k == path}

        def check_call(self, cmd):
            self.calls.append(cmd)
            # could return a canned value if want to test
            # behavior around failures or if we care about
            # what the shell call actually returns
            return None

        def rmtree(self, to_remove):
            to_remove = self._rmroot(to_remove)
            self.files = {
                k: v for k, v in self.files.items() if not k.startswith(to_remove)
            }

    def test_creates_symlinks(self):
        (main, jnl_dir) = self.main_with_fixture("typical")
        msys = TestDatabase.MockSystem(jnl_dir)
        main.context.system = msys

        main.context.database.scan()

        assert msys.files == {
            "root/quick": "dir",
            "root/quick/entry-one-one.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/quick/entry-one-two.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/quick/example-tag.txt": (
                "symlink",
                "root/worklogs/W5BNE202WYF031H7J3RY.txt",
            ),
            "root/quick/tickets": "dir",
            "root/quick/tickets/PERF-1188.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/quick/daily": "dir",
            "root/quick/daily/2018-05-30.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/worklogs": "dir",
        }

    def test_creates_symlinks_removes_others(self):
        main, jnl_dir = self.main_with_fixture("typical")
        msys = TestDatabase.MockSystem(jnl_dir)
        main.context.system = msys

        msys.files = {
            "root/quick": "dir",
            "root/quick/some-other-thing-that-we-should-remove.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
        }

        main.context.database.scan()

        assert msys.files == {
            "root/quick": "dir",
            "root/quick/entry-one-one.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/quick/entry-one-two.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/quick/example-tag.txt": (
                "symlink",
                "root/worklogs/W5BNE202WYF031H7J3RY.txt",
            ),
            "root/quick/tickets": "dir",
            "root/quick/tickets/PERF-1188.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/quick/daily": "dir",
            "root/quick/daily/2018-05-30.txt": (
                "symlink",
                "root/worklogs/HMKYKM4NNG4KREW61D55.txt",
            ),
            "root/worklogs": "dir",
        }

    def test_cant_create_dupe_symlinks(self):
        main, jnl_dir = self.main_with_fixture("empty")
        one = main.context.database.create_entry([jnl.Tag(name="quick", value="foo")])
        two = main.context.database.create_entry(
            [jnl.Tag(name="quick", value="foo")]  # same `quick` tag as `one`
        )

        assert one is not two
        assert one != two

        with self.assertRaises(Exception) as _:
            main.context.database.scan()


if __name__ == "__main__":
    unittest.main()
