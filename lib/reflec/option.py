# -*- coding: utf_8 -*-
u"""
Reflec Option Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import re
import sys

from const import *
from appbase.option import BaseOption

__all__ = ["ReflecOption"]

#-------------------------------------------------------------------------------

# バージョン
version = APP_VERSION_TEXT

# 使い方
usage = "Usage: %prog [options] ( host port [path] | host:port | url )"

# 設定のデフォルト値
config_defaults = {
    "logging": {
        "filename":   "%0_%a%p.log",
    },
    "server": {
        "bindings":   ":8080",
        "client_max": 100,
        "timeout":    180,
        "countdown":  10,
    },
    "client": {
        "host":       "localhost",
        "port":       8888,
        "path":       "/",
        "bufsize":    16,
        "timeout":    30,
        "retry":      5,
        "retrysec":   10,
    }
}

# 引数パーサー用
parser_options = {
    ("-p", "--bindings"): { "metavar": "ADDR:PORT",
        "dest": "server-bindings",
        "help": "to which address and port the server binds. "
                "if only a number given, treated as a port number." },
    ("-m", "--client-max"): { "metavar": "MAX",
        "dest": "server-client_max", "type": "int",
        "help": "how many clients can connect to the server "
                "at the same time." },
    ("-b", "--buffer-size"): { "metavar": "SIZE",
        "dest": "client-bufsize", "type": "int",
        "help": "the size of buffer for streaming. "
                "big number gets more stable but uses more memory." },
    ("-t", "--timeout"): { "metavar": "SECS",
        "dest": "client-timeout", "type": "int",
        "help": "timeout seconds of the client's receiving." },
    ("-r", "--retry"): { "metavar": "NUM",
        "dest": "client-retry", "type": "int",
        "help": "the number of retries when the client failed." },
}

#-------------------------------------------------------------------------------
# ReflecOption
#-------------------------------------------------------------------------------

class ReflecOption(BaseOption):
    u"""
    Reflec のオプションを表すクラス.

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

    def parse_argv(self, args):
        try:
            if len(args) >= 1:
                r = re.match(r"^(?:[^:]+://)?([^/:]+)(?::(\d+))?(.*)", args[0])
                if r:
                    self.set('client', 'host', r.group(1))
                    if r.group(2): self.set('client', 'port', int(r.group(2)))
                    if r.group(3): self.set('client', 'path', r.group(3))
            if len(args) >= 2:
                self.set('client', 'port', int(args[1]))
            if len(args) >= 3:
                self.set('client', 'path', args[2])
        except ValueError, e:
            sys.exit("Given client port is not a number.")
