# -*- coding: utf_8 -*-
u"""
Skype Bot Plug-in

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

Skype でメンバー登録・解除を自動的に行うプラグイン.
登録されたメンバーをファイルに保存しておく.
"""

import os
import logging
import threading
import traceback

from utils.com import *
from utils.skype import Skype
from utils.userlist import UserList
from livealive.plugin import LiveAliveBasePlugin

__load__ = ["SkypeBotPlugin"]

#-------------------------------------------------------------------------------
# SkypeBot
#-------------------------------------------------------------------------------

class SkypeBot(Skype):

    def __init__(self, *args, **kwargs):
        COMObject.__init__(self, *args, **kwargs)
        self.message_status = {
            "RECEIVED": self.Convert.TextToChatMessageStatus("RECEIVED"),
            "SENDING":  self.Convert.TextToChatMessageStatus("SENDING"),
            "SENT":     self.Convert.TextToChatMessageStatus("SENT"),
        }
        self.users    = None
        self.msg_add  = "[%(user)s] added."
        self.msg_dup  = "[%(user)s] is already added."
        self.msg_del  = "[%(user)s] deleted."
        self.msg_none = "[%(user)s] is not added."
        self.msg_res  = "Sorry, your command is not understandable."

    @comevent("IChatMessage")
    def OnMessageStatus(self, msg, status):
        if status != self.message_status["RECEIVED"]:
            return

        body = msg.Body.encode(self.encoding)
        user = msg.FromHandle.encode(self.encoding)
        name = msg.FromDisplayName.encode(self.encoding)

        logging.debug("Skypebot: < %s: %s" % (name, body))

        report = None
        if body.upper() == "ADD":
            if self.users.append(user):
                logging.info("Skypebot: Added [%s] to the user list." % user)
                report = self.msg_add
            else:
                logging.info("Skypebot: [%s] exists in the user list." % user)
                report = self.msg_dup
        elif body.upper() == "DEL":
            if self.users.remove(user):
                logging.info("Skypebot: Removed [%s] from the user list." % user)
                report = self.msg_del
            else:
                logging.info("Skypebot: [%s] doesn't exist in the user list." % user)
                report = self.msg_none
        else:
            report = self.msg_res

        if report:
            info = {
                "body": body,
                "user": user,
                "name": name,
            }
            report = report.replace("<br>", "\n") % info
            msg.Chat.SendMessage(report)

#-------------------------------------------------------------------------------
# SkypeBotPlugin
#-------------------------------------------------------------------------------

class SkypeBotPlugin(LiveAliveBasePlugin):
    u"""
    Skype でメンバー登録・解除を自動的に行うプラグイン.
    """

    def app_start(self, app):
        opt = self.app.option.get("skypebot")
        if not opt:
            logging.error("Skypebot: Stopped. No options found.")
            return

        listfile = self.app.abspath(opt.listfile)
        lockfile = listfile + ".lock"
        users = UserList(listfile, lockfile)
        users.load()

        params = {
            "users":    users,
            "msg_add":  opt.msg_add,
            "msg_dup":  opt.msg_dup,
            "msg_del":  opt.msg_del,
            "msg_none": opt.msg_none,
            "msg_res":  opt.msg_res,
        }

        self.skype = None
        try:
            self.skype = SkypeBot.create()
        except:
            logging.error("Skypebot: Skype4COM is not installed.")
            return

        skype = self.skype
        try:
            skype.set_options(**params)
            skype.ensure_running()
            skype.ensure_attachment()
            if self.option.getboolean("skypebot", "silentmode", True):
                self.set_silent_mode()
            logging.info("Skypebot: started successfully.")
        except:
            self.skype = None

        if self.skype:
            self.prompt.add_command(
                "S", "SILENT", "Set Skype to silent mode.",
                self.set_silent_mode)

    def app_tick(self, app):
        if self.skype:
            self.skype.process_message(0.1)

    def set_silent_mode(self):
        if self.skype:
            t = threading.Thread(target = self.set_silent_mode_thread)
            t.setDaemon(True)
            t.start()

    def set_silent_mode_thread(self):
        try:
            self.skype.SilentMode = True
        except:
            pass
