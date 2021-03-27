import datetime
import glob
import os
import random
import shutil
import subprocess
from contextlib import contextmanager

from typing import List

import dateparser

from jnl.entries import Entry


def file_contents(path: str):
    path = os.path.join(os.environ.get("JNL_ORIG_CWD"), path)
    with open(path, "r") as f:
        return f.read()


def makedirs(*args: str):
    return os.makedirs(*args)


def check_call(args: List[str]):
    subprocess.check_call(args)


def exists(path: str):
    return os.path.exists(path)


def readlink(path: str):
    return os.readlink(path)


def symlink(source: str, destination: str):
    return os.symlink(source, destination)


def unlink(path: str):
    return os.unlink(path)


def rmtree(path: str):
    """Remove everything in a directory but don't remove the directory itself.
    This is useful if you have things referring to the file inode itself or
    things that generally get confused about treating a directory as symbolic name."""
    for f in glob.glob(os.path.join(path, "*")):
        if os.path.isfile(f) or os.path.islink(f):
            os.remove(f)
        else:
            try:
                shutil.rmtree(f)
            except Exception as e:
                print(("Cannot remove {}/{}".format(path, f)))
                raise e


@contextmanager
def in_dir(path: str) -> None:
    old_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_dir)


def _git_run(git_dir, git_command: str):
    command = ["git", git_command]
    with in_dir(git_dir):
        print(check_call(command))


def git_stat(git_dir: str):
    _git_run(git_dir, "status")


def git_pull(git_dir: str):
    _git_run(git_dir, "pull")


def git_autopush(git_dir: str):
    _git_run(git_dir, "autopush")


def isdir(path: str):
    return os.path.isdir(path)


def now() -> datetime:
    return datetime.datetime.now()


LETTERS = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "W",
    "X",
    "Y",
    "Z",
]


def guid() -> str:
    return "".join([random.choice(LETTERS) for _ in range(21)])


def open_entry(entry: Entry) -> None:
    return check_call(["open", "-a", "FoldingText", entry.file_path()])


def yyyymmdd() -> str:
    d = now()
    return "%04d-%02d-%02d" % (d.year, d.month, d.day)


def parse(somedate) -> str:
    return dateparser.parse(somedate)
