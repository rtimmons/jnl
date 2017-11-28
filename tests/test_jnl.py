import random
import sys
import os
import shutil
import tempfile

bin_dir = os.path.join(os.path.dirname(__file__), '..', 'bin')
sys.path.insert(0, bin_dir)

import jnl

import unittest
import mock

fixture_dir = os.path.join(bin_dir, '..', 'tests', 'fixtures')

class TestDatabase(unittest.TestCase):

    def main_with_fixture(self, fixture_name='typical'):
        source_fixture = os.path.join(fixture_dir, fixture_name)

        tmp_dir = tempfile.mkdtemp()
        jnl_dir = os.path.join(tmp_dir, fixture_name)
        shutil.copytree(source_fixture, jnl_dir)

        self.to_cleanup.append(tmp_dir)
        return jnl.Main({'JNL_DIR': jnl_dir}), jnl_dir

    def setUp(self):
        random.seed(100)
        self.to_cleanup = []

    def tearDown(self):
        for c in self.to_cleanup:
            print "Cleaning up %s" % c
            # shutil.rmtree(c)

    def test_path(self):
        main, jnl_dir = self.main_with_fixture('typical')
        assert main.context.database.path() == jnl_dir

        assert os.path.exists(main.context.database.path('quick'))
        assert os.path.exists(main.context.database.path('quick', 'something_we_create_now'))

    def test_list_entries(self):
        main, jnl_dir = self.main_with_fixture('typical')
        entries = main.context.database.entries
        assert len(entries) == 2
        guids = [e.guid for e in entries]
        assert guids == ['HMKYKM4NNG4KREW61D55', 'W5BNE202WYF031H7J3RY']

    def test_entries_with_tags(self):
        main, jnl_dir = self.main_with_fixture('typical')

        with_tag = main.context.database.entries_with_tag('quick', 'tickets/PERF-1188')
        assert len(with_tag) == 1
        assert with_tag[0].guid == 'HMKYKM4NNG4KREW61D55'
        self.has_tags(with_tag[0], 
            '@ft',
            '@quick(tickets/PERF-1188)',
            '@quick(entry-one-one)',
            '@quick(entry-one-two)'
        )

    def has_tags(self, entry, *tags):
        assert set([str(t) for t in entry.tags]) == set(tags)

    def mock_what_day_is_it(self, main):
        what_day_is_it = mock.MagicMock()
        what_day_is_it.yyyymmdd.return_value = '2009-11-28'
        main.context.what_day_is_it = what_day_is_it
        return what_day_is_it

    def test_creates_daily_entry(self):
        main, jnl_dir = self.main_with_fixture('typical')
        self.mock_what_day_is_it(main)

        daily = main.context.database.daily_entry()
        entries = main.context.database.entries
        assert len(entries) == 3

        with_tag = main.context.database.entries_with_tag('quick', 'daily/2009-11-28')
        assert len(with_tag) == 1
        assert with_tag[0].guid == '4ERPQDSH2E1XYA9R656B' # guaranteed cuz we set random.seed
        self.has_tags(with_tag[0],
            '@ft',
            '@quick(daily/2009-11-28)'
        )

    def test_uses_existing_daily_entry(self):
        main, jnl_dir = self.main_with_fixture('typical')
        self.mock_what_day_is_it(main)

        daily = main.context.database.daily_entry()
        entries = main.context.database.entries
        assert len(entries) == 3

        another = jnl.Main({'JNL_DIR': jnl_dir})
        self.mock_what_day_is_it(another)

        assert len(another.context.database.entries) == 3
        another_daily = another.context.database.daily_entry()
        assert another_daily.guid == daily.guid

        assert another_daily is not daily

    