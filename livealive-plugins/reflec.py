# -*- coding: utf_8 -*-
u"""
Reflec Plug-in

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

ALIVE になったクライアントを自動的に Reflec でミラーするプラグイン.
Windows でのみ利用可能.
"""

import logging
from win32com.shell.shell import ShellExecuteEx
from win32process import GetExitCodeProcess

from livealive.plugin import LiveAliveBasePlugin

__load__ = ["ReflecPlugin"]

#-------------------------------------------------------------------------------
# Process
#-------------------------------------------------------------------------------

class Process(object):
    u"""
    Windows でのプロセスを表すクラス.
    簡易版なので, パラメータはほとんど固定.
    """

    def __init__(self, command, params):
        d = ShellExecuteEx(fMask = 0x40,
                           lpFile = command,
                           lpParameters = params,
                           nShow = 1)
        self.handle = d["hProcess"]

    def is_active(self):
        # 259 = STILL_ACTIVE
        return GetExitCodeProcess(self.handle) == 259

    def is_terminated(self):
        return not self.is_active()

    def exit_code(self):
        return GetExitCodeProcess(self.handle)

#-------------------------------------------------------------------------------
# ReflecPlugin
#-------------------------------------------------------------------------------

class ReflecPlugin(LiveAliveBasePlugin):
    u"""
    ALIVE になったクライアントを自動的に Reflec でミラーするプラグイン.
    """

    default_params = '-p %(server)s %(client)s'

    def app_start(self, app):
        self.reflec = self.option.get("reflec", "reflec", "reflec2.py")
        self.reflec = self.app.abspath(self.reflec)
        self.params = self.option.get("reflec", "params", self.default_params)

    def monitor_start(self, monitor, client):
        client.reflec = None

    def monitor_alive(self, monitor, client):
        if self.should_start_reflec_for(client):
            logging.info("Reflec: starting Reflec for %s." % client)
            self.start_reflec(client)

    def monitor_checked(self, monitor, client):
        if self.should_start_reflec_for(client):
            logging.info("Reflec: %s is ALIVE, but Reflec is terminated. " \
                         "Starting Reflec again." % client)
            self.start_reflec(client)

    def should_start_reflec_for(self, client):
        if client.reflec:
            logging.debug("Reflec: %s Reflec process is %s (%d)" %
                ( client,
                  "ACTIVE" if client.reflec.is_active() else "DEACTIVE",
                  client.reflec.exit_code() ))

        return client.alive and \
               (not client.reflec or client.reflec.is_terminated())

    def start_reflec(self, client):
        u"""
        Reflec を開始する.
        """
        params = self.params % {
            "server": client.server,
            "client": client.address,
        }

        try:
            client.reflec = Process(self.reflec, params)
        except:
            logging.error("Reflec: can't start Reflec.")
            raise
