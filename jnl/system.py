import datetime
import glob
import os
import random
import shutil
import subprocess


class System(object):
    def __init__(self):
        pass

    @staticmethod
    def file_contents(path: str):
        path = os.path.join(os.environ.get("JNL_ORIG_CWD"), path)
        with open(path, "r") as f:
            return f.read()

    @staticmethod
    def makedirs(*args: str):
        return os.makedirs(*args)

    @staticmethod
    def check_call(*args: str):
        subprocess.check_call(*args)

    @staticmethod
    def exists(path: str):
        return os.path.exists(path)

    @staticmethod
    def readlink(path: str):
        return os.readlink(path)

    @staticmethod
    def symlink(source: str, destination: str):
        return os.symlink(source, destination)

    @staticmethod
    def unlink(path: str):
        return os.unlink(path)

    @staticmethod
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

    @staticmethod
    def isdir(path: str):
        return os.path.isdir(path)

    @staticmethod
    def now() -> datetime:
        return datetime.datetime.now()


class GuidGenerator(object):
    def __init__(self):
        pass

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

    @staticmethod
    def guid() -> str:
        return "".join([random.choice(GuidGenerator.LETTERS) for _ in range(21)])