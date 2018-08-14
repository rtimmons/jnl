import os
import sys
import datetime
import subprocess

import shutil
import glob


class WhatDayIsIt(object):
    def __init__(self, context):
        self.context = context

    def yyyymmdd(self):
        now = self.context.system.now()
        return "%04d-%02d-%02d" % (now.year, now.month, now.day)

class Git(object):
    def __init__(self, context):
        self.context = context

    def _run(self, *git_command):
        command = ['git']
        command.extend(git_command)
        with self.context.in_dir():
            print self.context.system.check_call(command)

    def pull(self):
        self._run('pull')

    def status(self):
        self._run('status')

    def autopush(self):
        self._run('autopush')



class System(object):
    def __init__(self, context):
        self.context = context

    def file_contents(self, path):
        path = os.path.join(os.getcwd(), path)
        with open(path, "r") as f:
            return f.read()

    def makedirs(self,*args):
        return os.makedirs(*args)

    def check_call(self, *args):
        subprocess.check_call(*args)

    def exists(self, path):
        return os.path.exists(path)

    def readlink(self, path):
        return os.readlink(path)
    
    def symlink(self, src, dest):
        return os.symlink(src, dest)

    def unlink(self, path):
        return os.unlink(path)

    def rmtree(self,path):
        """Remove everything in a directory but don't remove the directory itself.
        This is useful if you have things referring to the file inode itself or
        things that generally get confused about treating a directory as symbolic name."""
        for f in glob.glob(os.path.join(path, '*')):
            if os.path.isfile(f) or os.path.islink(f):
                os.remove(f)
            else:
                try:
                    shutil.rmtree(f)
                except Exception as e:
                    print("Cannot remove {}/{}".format(path, f))
                    raise e

    def isdir(self, path):
        return os.path.isdir(path)

    def now(self):
        return datetime.datetime.now()
