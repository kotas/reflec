# -*- coding: utf_8 -*-
u"""
Skype User List Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import os
import time
import logging

__all__ = ["UserList"]

#-------------------------------------------------------------------------------
# UserList
#-------------------------------------------------------------------------------

class UserList(dict):

    # ロックを試す回数
    lock_try = 3

    def __init__(self, listfile, lockfile):
        self.listfile = listfile
        self.lockfile = lockfile

    def append(self, user):
        u"""
        ユーザーを登録する.
        登録にした場合は True を, 既に登録されている場合は False を返す.
        """
        if user in self:
            return False
        else:
            self[user] = True
            self.save()
            return True

    def remove(self, user):
        u"""
        ユーザーの登録を解除する.
        解除した場合は True を, 登録されていない場合は False を返す.
        """
        if user in self:
            del self[user]
            self.save()
            return True
        else:
            return False

    def load(self):
        u"""
        ユーザーリストファイルを読み込む.
        """
        if not os.path.isfile(self.listfile):
            return

        if not self._lock(): return
        try:
            f = open(self.listfile)
            for user in f:
                self[user.strip()] = True
            f.close()
        finally:
            self._unlock()

    def save(self):
        u"""
        ユーザーリストファイルを保存する.
        """
        if not self._lock(): return
        try:
            f = open(self.listfile, "w")
            f.write("\n".join(self.keys()))
            f.close()
        finally:
            self._unlock()

    def _lock(self):
        u"""
        ファイルを書き込む為に排他ロックする.
        """
        f = None
        count = self.lock_try
        while count > 0:
            count -= 1
            try:
                f = os.open(self.lockfile, os.O_RDWR | os.O_CREAT | os.O_EXCL)
                f = os.fdopen(f, "w")
                break
            except:
                time.sleep(0.3)
        if f:
            f.write("locked!")
            f.close()
            return True
        else:
            logging.error("UserList: Locking failed.")
            return False

    def _unlock(self):
        u"""
        ファイルのロックを解除する.
        """
        try:
            os.remove(self.lockfile)
        except:
            logging.error("UserList: Unlocking failed.")
