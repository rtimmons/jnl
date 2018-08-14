#!/usr/bin/env python

import db
import system

import re

from contextlib import contextmanager


class Settings(object):
    def __init__(self, context):
        self.context = context

    def dbdir(self):
        return self.context.environment['JNL_DIR']

class Opener(object):
    def __init__(self, context):
        self.context = context

    def open(self, entry):
        return self.context.system.check_call([
            'open', '-a', 'FoldingText',
            entry.file_path(),
        ])


class NopListener(object):
    def __init__(self, context):
        self.context = context

    def on_entry(self, entry):
        pass

    def on_pre_scan(self):
        pass

    def on_post_scan(self):
        pass


class SetsOpenWith(NopListener):
    import binascii
    import xattr

    def __init__(self, context):
        self.context = context

    """The xattr controlling the "Open With" functionality is unfortunately binary.
    To use a different application, use `xattr -px`

    or with `-px`:

        $ xattr -px com.apple.LaunchServices.OpenWith $FILE
        62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57
        [...]
        00 00 00 00 00 6F
    """

    OPEN_WITH_ATTR_HEX = re.sub(r'\s*', '', '''
        62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57
        76 65 72 73 69 6F 6E 54 70 61 74 68 5F 10 10 62
        75 6E 64 6C 65 69 64 65 6E 74 69 66 69 65 72 10
        00 5F 10 1D 2F 41 70 70 6C 69 63 61 74 69 6F 6E
        73 2F 46 6F 6C 64 69 6E 67 54 65 78 74 2E 61 70
        70 5F 10 1B 63 6F 6D 2E 66 6F 6C 64 69 6E 67 74
        65 78 74 2E 46 6F 6C 64 69 6E 67 54 65 78 74 08
        0F 17 1C 2F 31 51 00 00 00 00 00 00 01 01 00 00
        00 00 00 00 00 07 00 00 00 00 00 00 00 00 00 00
        00 00 00 00 00 6F
    ''', flags=re.M)
    OPEN_WITH_ATTR = binascii.unhexlify(OPEN_WITH_ATTR_HEX)

    def on_entry(self, entry):
        if not entry.has_tag('ft', None):
            return

        return xattr.setxattr(
            entry.file_path(),
            'com.apple.LaunchServices.OpenWith',
            SetsOpenWith.OPEN_WITH_ATTR
        )


class Symlinker(NopListener):
    def on_entry(self, entry):
        import os
        tags = [t for t in entry.tags if t.name in ('quick', 'daily') and t.value is not None]
        for tag in tags:
            val = tag.value
            name = tag.name
            # TODO: temporary; WIP support for @daily(yyyy-mm-dd) for creating "Last Week" etc dirs
            if name == 'daily':
                name = 'quick'
                val = "daily/%s" % val
            parts = val.split('/')
            dir_parts = parts[:-1]
            fname_part = "%s.%s" % (parts[-1], entry.file_extension())
            into_dir = self.context.database.path('quick', *dir_parts)
            symlink = os.path.join(into_dir, fname_part)
            if self.context.system.exists(symlink):
                existing = self.context.system.readlink(symlink)
                if existing == entry.file_path():
                    # job already done
                    continue
                else:
                    raise ValueError("@quick(%s) owned by %s, so %s can't take it" % (val, existing, entry.file_path()))
            self.context.system.symlink(entry.file_path(), symlink)


class PreScanQuickCleaner(NopListener):
    def on_pre_scan(self):
        path = self.context.database.path('quick')
        print("Scanning %s" % path)
        if self.context.system.exists(path):
            self.context.system.rmtree(path)


class GuidGenerator(object):
    import random

    def __init__(self, context):
        self.context = context

    LETTERS = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8',
        '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
        'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T',
        'U', 'W', 'X', 'Y', 'Z',
    ]

    def guid(self):
        return "".join([
            random.choice(GuidGenerator.LETTERS) for i in range(21)
        ])

class Context(object):
    def __init__(self, environment):
        self.environment = environment
        self.system = system.System(self)
        self.opener = Opener(self)
        self.sets_open_with = SetsOpenWith(self)
        self.what_day_is_it = system.WhatDayIsIt(self)
        self.guid_generator = GuidGenerator(self)
        self.symlinker = Symlinker(self)
        self.pre_scan_quick_cleaner = PreScanQuickCleaner(self)
        self.settings = Settings(self)
        self.database = db.Database(self)
        self.git = system.Git(self)
        self.entry_listeners = [
            self.sets_open_with,
            self.symlinker,
            self.pre_scan_quick_cleaner
        ]

    def __str__(self):
        return "Context()"

    @contextmanager
    def in_dir(self, *path):
        old_dir = os.getcwd()
        try:
            os.chdir(self.database.path(*path))
            yield
        finally:
            os.chdir(old_dir)


class Main(object):
    def __init__(self, environment = None):
        if environment is None:
            environment = os.environ
        self.context = Context(environment = environment)

    def open(self, argv):
        self.context.opener.open(
            self.context.database.entry_with_guid(argv[2])
        )

    def new(self, argv):
        self.context.opener.open(
            self.context.database.create_entry()
        )

    def sync(self, argv):
        self.context.git.pull()
        self.scan(argv)
        self.context.git.status()
        if len(argv) > 2 and argv[2] == 'push':
            self.context.git.autopush()

    def proj(self, argv):
        if len(argv) < 3:
            project = self.context.system.file_contents(".project").strip()
        else:
            project = argv[2]
        for e in self.context.database.entries_with_project(project):
            self.context.opener.open(e)

    def run(self, argv):
        if len(argv) == 1 or argv[1].startswith("p"):
            return self.proj(argv)
        if argv[1] == "new":
            return self.new(argv)
        if argv[1] == 'daily' or argv[1] == 'today':
            return self.daily(argv)
        if argv[1] == 'scan':
            return self.scan(argv)
        if argv[1] == 'open':
            return self.open(argv)
        if argv[1] == 'sync':
            return self.sync(argv)
        raise ValueError("Don't know about action {}".format(argv[1]))

    def scan(self, argv):
        self.context.database.scan()

    def daily(self, argv):
        daily = self.context.database.daily_entry()
        self.context.opener.open(daily)
        self.context.database.scan()


def empty_fixture_path():
    import os
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', 'empty')


def main():
    import sys
    import os
    main = Main({
        'JNL_DIR': os.environ['JNL_DIR'] if 'JNL_DIR' in os.environ else empty_fixture_path()
    })
    main.run(sys.argv)