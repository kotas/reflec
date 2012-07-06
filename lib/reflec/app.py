# -*- coding: utf_8 -*-
u"""
Reflec Application Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import os
import os.path
import time
import logging

from appbase.app import PluginApplication
from const import *
from option import ReflecOption
from plugin import ReflecPluginLoader
from mmshttp.client import MMSHTTPBufferedClient
from mmshttp.source import MMSHTTPClientSourceFactory
from mmshttp.server import MMSHTTPServer

__all__ = ["ReflecApplication"]

#-------------------------------------------------------------------------------
# ReflecApplication
#-------------------------------------------------------------------------------

class ReflecApplication(PluginApplication):
    u"""
    Reflec2 のアプリケーションを表すクラス.
    """

    option_class = ReflecOption
    loader_class = ReflecPluginLoader
    client_class = MMSHTTPBufferedClient
    source_class = MMSHTTPClientSourceFactory
    server_class = MMSHTTPServer

    def __init__(self):
        PluginApplication.__init__(self, CONFIG_FILE, PLUGIN_DIR)
        self.client = None
        self.server = None

    def terminate(self):
        u"""アプリケーションを終了する."""
        PluginApplication.terminate(self)
        self.client.terminate()

    def setup(self):
        u"""実行するためのオブジェクトなどを全て初期化."""
        self.setup_client()
        self.setup_server()
        self.setup_plugin()
        self.setup_prompt()
        PluginApplication.setup(self)

    def setup_client(self):
        u"""クライアントを初期化."""
        self.client = self.client_class(**self.option.client.dict())

    def setup_server(self):
        u"""サーバーを初期化."""
        source = self.source_class(self.client)
        self.server = self.server_class(source, **self.option.server.dict())

    def setup_plugin(self):
        u"""プラグインを初期化."""
        logging.info("Loading plug-ins.")
        self.plugin.add_event_holder(self.client, "client")
        self.plugin.add_event_holder(self.server, "server")

    def setup_prompt(self):
        u"""コマンドプロンプトを初期化."""
        self.prompt.add_command("L", "LIST", "List up server connections.",
                                self.list_server)

    def run(self):
        u"""実行を開始する."""
        self.client.start()
        self.server.serve_forever()
        PluginApplication.run(self)

    def wait_for_termination(self):
        u"""
        アプリケーションが終了されるか,
        クライアントの受信が終了するまでブロッキングして待機.
        """
        while not self.terminated and not self.client.terminated:
            time.sleep(1)
            self.notify_event("tick")

    def finish(self):
        u"""実行の後始末を行う."""
        self.server.server_close()
        PluginApplication.finish(self)

    def replace_macro(self, text):
        u"""マクロが含まれる文字列を解決する."""
        b = self.option.server.bindings.split(':', 1)
        if len(b) == 1:
            if b[0]: b = ('', b[0])
            else:    b = ('', 8080)

        text = text.replace("%0", "reflec")
        return text.replace("%a", b[0]).replace("%p", b[1])

    def abspath(self, path):
        u"""
        ファイルパスを絶対パスにする.
        もし相対パスの場合は APP_DIR をベースにして絶対パスにする.
        """
        if not os.path.isabs(path):
            path = os.path.join(APP_DIR, path)
        return os.path.abspath(path)

    def list_server(self):
        u"""
        サーバーに接続しているクライアントをリストアップする.
        """
        s = [ ]
        s.append("="*40)
        s.append("Server Connections")
        s.append("")
        for addr in self.server.connections:
            s.append(" - %s" % addr)
        s.append("")
        s.append("="*40)
        print "\n".join(s)
