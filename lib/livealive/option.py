# -*- coding: utf_8 -*-
u"""
LiveAlive Option Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import sys

from const import *
from appbase.option import BaseOption

__all__ = ["LiveAliveOption"]

#-------------------------------------------------------------------------------

# バージョン
version = APP_VERSION_TEXT

# 使い方
usage = "Usage: %prog [options]"

# 設定のデフォルト値
config_defaults = {
    "monitor": {
        "clientsfile": "clients.xml",
        "interval":    60,
        "delay":       5,
    }
}

# 引数パーサー用
parser_options = {
    ("-i", "--interval"): { "metavar": "SECS",
        "dest": "monitor-interval", "type": "int",
        "help": "interval seconds of monitors check." },
    ("-e", "--delay"): { "metavar": "SECS",
        "dest": "monitor-delay", "type": "int",
        "help": "delay seconds for each monitor launching." },
}

#-------------------------------------------------------------------------------
# LiveAliveOption
#-------------------------------------------------------------------------------

class LiveAliveOption(BaseOption):
    u"""
    LiveAlive のオプションを表すクラス.

    まず INI ファイルからデフォルト設定を読み込み, 次に実行時のパラメータとして
    渡された設定で上書きする.
    """

    version = version
    usage = usage

    def __init__(self, config_file = None):
        self.update_defaults()
        BaseOption.__init__(self, config_file)

    def update_defaults(self):
        for section, value in config_defaults.items():
            if section not in self.defaults:
                self.defaults[section] = value
            else:
                self.defaults[section].update(value)
        for key, value in parser_options.items():
            if key not in self.parser_options:
                self.parser_options[key] = value
            else:
                self.parser_options[key].update(value)
