# -*- coding: utf_8 -*-
u"""
Skype Notify Plug-in

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

開始時に Skype で中継の開始を通知するプラグイン.
あらかじめ登録されているメンバーに通知する.
"""

import sys
import time
import logging
import threading

from utils.skype import Skype
from utils.userlist import UserList
from reflec.plugin import ReflecBasePlugin

__load__ = ["SkypeNotifyPlugin"]

#-------------------------------------------------------------------------------
# SkypeNotifier
#-------------------------------------------------------------------------------

class SkypeNotifier(Skype):

    interval = 0.1

    def notify(self, users, msg):
        for user in users:
            try:
                self.SendMessage(user, msg)
                time.sleep(self.interval)
            except:
                logging.error("SkypeNotify: couldn't notify [%s]" % user)

#-------------------------------------------------------------------------------
# SkypeNotifyPlugin
#-------------------------------------------------------------------------------

class SkypeNotifyPlugin(ReflecBasePlugin):
    u"""
    ストリーミング開始時に Skype で中継の開始を通知するプラグイン.
    """

    encoding = sys.getfilesystemencoding()

    def app_start(self, app):
        opt = self.app.option.get("skypenotify")
        if not opt:
            logging.error("SkypeNotify: No options found.")
            return

        listfile = self.app.abspath(opt.listfile)
        lockfile = listfile + ".lock"
        self.users = UserList(listfile, lockfile)

        self.info = {  }
        for k, v in opt.dict().items():
            if k.startswith("no_"):
                self.info[ k[3:] ] = v

        self.msg = opt.msg_notify
        self.notify = None

        self.skype = None
        try:
            self.skype = SkypeNotifier.create()
        except:
            logging.error("SkypeNotify: Skype4COM is not installed.")
            return
        try:
            self.skype.ensure_running()
            self.skype.ensure_attachment()
        except:
            self.skype = None

    def app_tick(self, app):
        if self.skype:
            self.skype.process_message(0.1)

        if self.notify:
            self.users.load()

            logging.info("SkypeNotify: notifying all %d users." % len(self.users))
            self.skype.notify(self.users, self.notify)
            logging.info("SkypeNotify: notification is sent to all users.")

            self.skype = None
            self.notify = None

    def client_start_streaming(self, client):
        if not self.skype:
            return

        rating = self.client.media_info.get("rating", "").lower()
        if rating.find("yes") >= 0:
            logging.info("SkypeNotify: Skype notification is blocked by a user.")
            return

        info = self.info.copy()
        for k, v in self.client.media_info.items():
            if isinstance(v, unicode):
                v = v.encode(self.encoding)
            info[k] = v

        info["host"] = self.server.server_address[0]
        info["port"] = self.server.server_address[1]
        info["address"] = "%s:%d" % (info["host"], info["port"])

        msg = self.msg % info
        msg = msg.replace("<br>", "\n")
        self.notify = msg

        # Skype COM の操作はメインスレッドで行う必要があるが
        # client イベントは client スレッド内で発生するので
        # いったん変数に格納しておき, app_tick イベントで通知する
