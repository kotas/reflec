# -*- coding: utf_8 -*-
u"""
LiveAlive Application Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import os.path
import logging

from appbase.app import PluginApplication
from const import *
from option import LiveAliveOption
from plugin import LiveAlivePluginLoader
from monitor import LiveAliveMonitor

__all__ = ["LiveAliveApplication"]

#-------------------------------------------------------------------------------
# LiveAliveApplication
#-------------------------------------------------------------------------------

class LiveAliveApplication(PluginApplication):
    u"""
    LiveAlive2 のアプリケーションを表すクラス.
    """

    option_class = LiveAliveOption
    loader_class = LiveAlivePluginLoader
    monitor_class = LiveAliveMonitor

    def __init__(self):
        PluginApplication.__init__(self, CONFIG_FILE, PLUGIN_DIR)
        self.monitor = None

    def setup(self):
        u"""前準備."""
        self.setup_monitor()
        self.setup_plugin()
        self.setup_prompt()
        PluginApplication.setup(self)

    def setup_monitor(self):
        u"""監視スレッドを初期化."""
        self.option.monitor.clients_xml = \
            self.abspath(self.option.monitor.clients_xml)
        self.monitor = self.monitor_class(**self.option.monitor.dict())

    def setup_plugin(self):
        u"""プラグインを初期化."""
        logging.info("Loading plug-ins.")
        self.plugin.add_event_holder(self.monitor, "monitor")

    def setup_prompt(self):
        u"""コマンドプロンプトを初期化."""
        self.prompt.add_command("L", "LIST", "List up monitored clients.",
                                self.list_monitored_clients)

    def run(self):
        u"""実行を開始する."""
        self.monitor.start()
        PluginApplication.run(self)

    def finish(self):
        u"""実行の後始末を行う."""
        self.monitor.terminate()
        PluginApplication.finish(self)

    def replace_macro(self, text):
        u"""マクロが含まれる文字列を解決する."""
        return text.replace("%0", "livealive")

    def abspath(self, path):
        u"""
        ファイルパスを絶対パスにする.
        もし相対パスの場合は APP_DIR をベースにして絶対パスにする.
        """
        if not os.path.isabs(path):
            path = os.path.join(APP_DIR, path)
        return os.path.abspath(path)

    def list_monitored_clients(self):
        u"""
        監視しているクライアントをリストアップする.
        """
        s = [ ]
        s.append("="*40)
        s.append("Monitored Clients")
        s.append("")
        for client in self.monitor.clients.values():
            s.append("  - %-5s %s" % (client.status(), client))
        s.append("")
        s.append("="*40)
        print "\n".join(s)
