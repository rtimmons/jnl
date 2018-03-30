#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import jnl
import os
import sys


class LiteMain(jnl.Main):
    def __init__(self, *args, **kwargs):
        super(LiteMain, self).__init__(*args, **kwargs)
        self.context.slite = SLite(self.context)

    def run(self, argv):
        self.context.slite.sql_import()

SCHEMA = '''
drop table if exists commits;
%%
CREATE TABLE commits(
    sha text primary key,
    date text,
    message text
);
%%
drop table if exists entries;
%%
CREATE TABLE entries(
    guid text primary key,
    contents text
);
%%
drop table if exists tags;
%%
CREATE TABLE tags(
    id integer primary key asc,
    name text
);
%%
drop table if exists tag_values;
%%
create table tag_values (
    id integer primary key asc,
    tag_id integer,
    val text,
    foreign key(tag_id) references tags(id)
);
'''

class SLite:
    def __init__(self, context):
        self.context = context

    def connection(self):
        parent_dir = self.context.database.path()
        conn = sqlite3.connect(os.path.join(parent_dir, 'entries.sqlite'))
        conn.text_factory = str
        return conn

    def migrate_schema(self, conn):
        for it in SCHEMA.split('%%'):
            try:
                conn.execute(it)
            except Exception as e:
                print it
                raise e

    def _insert_entry(self, conn, entry):
        conn.execute('insert into entries (guid, contents) values (?,?)', (entry.guid, entry.text()))

    def insert_entries(self, conn):
        for entry in self.context.database.entries:
            try:
                self._insert_entry(conn, entry)
            except Exception as e:
                print entry
                raise e

    def sql_import(self):
        with self.connection() as conn:
            self.migrate_schema(conn)
            self.insert_entries(conn)
            conn.commit()

if __name__ == "__main__":
    main = LiteMain({
        'JNL_DIR': os.environ['JNL_DIR'] if 'JNL_DIR' in os.environ else jnl.empty_fixture_path()
    })
    main.run(sys.argv)
