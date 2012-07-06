# -*- coding: utf_8 -*-
u"""
Application Base Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import os
import os.path
import time
import logging
import traceback
from logging.handlers import RotatingFileHandler

from option import BaseOption
from prompt import CommandPrompt
from utils.plugin import PluginLoader
from utils.event import EventHolder

__all__ = ["BaseApplication", "PluginApplication"]

#-------------------------------------------------------------------------------
# BaseApplication
#-------------------------------------------------------------------------------

class BaseApplication(EventHolder):
    u"""
    基本的なアプリケーションを表すクラス.
    設定の読み込みやロギング、コマンドラインでの操作などができる.
    """

    option_class = BaseOption
    prompt_class = CommandPrompt

    def __init__(self, config_file):
        EventHolder.__init__(self,
            "start", "terminate", "tick",
        )

        self.option = self.option_class(self.abspath(config_file))
        self.prompt = self.prompt_class(quit_func=self.terminate)
        self.terminated = False

        self.set_logging_options()

    def start(self):
        u"""アプリケーションを実行する."""
        logging.info("Application is starting up.")
        self.setup()
        self.notify_event("start")
        try:
            try:
                self.run()
            except:
                logging.error("Application is terminating. Error:\n%s\n%s\n%s" %
                    ("-"*40, traceback.format_exc().strip(), "-"*40))
                return
        finally:
            self.finish()
            self.notify_event("terminate")
        logging.info("Application terminated successfully.")

    def terminate(self):
        u"""アプリケーションを終了する."""
        self.terminated = True

    def setup(self):
        u"""実行するためのオブジェクトなどを全て初期化."""
        pass

    def run(self):
        u"""実行を開始する."""
        self.prompt.start()
        self.wait_for_termination()

    def wait_for_termination(self):
        u"""アプリケーションが終了されるまでブロッキングして待機."""
        while not self.terminated:
            time.sleep(1)
            self.notify_event("tick")

    def finish(self):
        u"""実行の後始末を行う."""
        self.prompt.terminate()

    def set_logging_options(self):
        u"""ログの設定を行う."""

        opt = self.option.logging
        level = logging._levelNames.get(opt.level.upper(), logging.INFO)

        # コンソールに出力するログの設定
        logging.basicConfig(
            level   = level,
            format  = opt.format,
            datefmt = opt.dateformat,
        )

        # ファイルに出力するログの設定
        if not opt.filename: return
        filename = os.path.join(opt.directory, opt.filename)
        filename = self.abspath(self.replace_macro(filename))

        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        maxsize   = opt.maxsize   or 0
        maxbackup = opt.maxbackup or 0

        filelog = RotatingFileHandler(filename, "a", maxsize, maxbackup)
        filelog.setLevel(level)
        filelog.setFormatter(logging.Formatter(opt.format, opt.dateformat))
        logging.getLogger('').addHandler(filelog)

    def replace_macro(self, text):
        u"""マクロが含まれる文字列を解決する."""
        return text.replace("%0", "app")

    def abspath(self, path):
        u"""ファイルパスを絶対パスにする."""
        return os.path.abspath(path)

#-------------------------------------------------------------------------------
# PluginApplication
#-------------------------------------------------------------------------------

class PluginApplication(BaseApplication):
    u"""
    プラグインで拡張可能なアプリケーションクラス.
    """

    loader_class = PluginLoader

    def __init__(self, config_file, plugin_dir):
        BaseApplication.__init__(self, config_file)
        self.plugin = self.loader_class(self.abspath(plugin_dir))

    def setup(self):
        self.plugin.add_event_holder(self, "app")
        self.plugin.load_all_plugins(self)
