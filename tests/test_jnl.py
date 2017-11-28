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

    def main_with_fixture(self, fixture='typical'):
        fixture_path = os.path.join(fixture_dir, fixture)
        tmpdir = tempfile.mkdtemp()
        subdir = os.path.join(tmpdir, fixture)
        print "Copy %s -> %s" % (fixture_path, subdir)
        shutil.copytree(fixture_path, subdir)
        self.to_cleanup.append(tmpdir)
        return jnl.Main({'JNL_DIR': subdir}), tmpdir

    def setUp(self):
        self.to_cleanup = []
        pass

    def tearDown(self):
        for c in self.to_cleanup:
            print "Cleaning up %s" % c
            shutil.rmtree(c)

    def test_create_entry(self):
        main, nl = self.main_with_fixture('typical')
        print main.context.database.path()

