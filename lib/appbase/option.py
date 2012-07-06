# -*- coding: utf_8 -*-
u"""
Option Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import os.path
from optparse import OptionParser
from ConfigParser import RawConfigParser

__all__ = ["BaseOption"]

#-------------------------------------------------------------------------------

# バージョン
version = "Application ver x.xx"

# 使い方
usage = "Usage: %prog [options]"

# 設定のデフォルト値
config_defaults = {
    "logging": {
        "directory":  "logs",
        "filename":   "%0.log",
        "format":     "%(asctime)s %(levelname)-8s %(message)s",
        "dateformat": "%y/%m/%d %H:%M:%S",
        "level":      "info",
        "maxsize":    1048576,
        "maxbackup":  5,
    },
}

# 引数パーサー用
parser_options = {
    ("-q", "--quiet"): { "action": "store_const", "const": "warning",
        "dest": "logging-level",
        "help": "output only warnings and errors to the stdout." },
    ("-v", "--verbose"): { "action": "store_const", "const": "debug",
        "dest": "logging-level",
        "help": "output debugging information to the stdout." },
    ("-d", "--logdir"): { "metavar": "DIRNAME",
        "dest": "logging-directory",
        "help": "directory in where log files are saved." },
    ("-l", "--logfile"): { "metavar": "FILENAME",
        "dest": "logging-filename",
        "help": "name of log file." },
}

#-------------------------------------------------------------------------------
# BaseOption
#-------------------------------------------------------------------------------

class OptionContainer(object):
    u"""
    オプションを保持するためのクラス.
    """
    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

    def dict(self):
        return self.__dict__

class BaseOption(OptionContainer):
    u"""
    オプションを表すクラス.

    まず INI ファイルからデフォルト設定を読み込み, 次に実行時のパラメータとして
    渡された設定で上書きする.
    """

    version = version
    usage = usage
    defaults = config_defaults
    parser_options = parser_options

    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self, config_files):
        self.set_default()

        if type(config_files) in (tuple, list):
            for f in config_files:
                self.read_ini(f)
        elif config_files:
            self.read_ini(config_files)

        self.read_argv()

    def get(self, section, option = None, default = None):
        if section not in self.__dict__:
            return default
        else:
            if option == None:
                return self.__dict__[section]
            else:
                return self.__dict__[section].__dict__.get(option, default)

    def getint(self, section, option = None, default = None):
        try:
            return int(self.get(section, option, default))
        except:
            return default

    def getfloat(self, section, option = None, default = None):
        try:
            return float(self.get(section, option, default))
        except:
            return default

    def getboolean(self, section, option = None, default = None):
        v = self.get(section, option, default)
        if v.lower() in self._boolean_states:
            return self._boolean_states[v.lower()]
        else:
            return default

    def set(self, section, option, value):
        if section not in self.__dict__:
            self.__dict__[section] = OptionContainer()

        self.__dict__[section].__dict__[option] = value

    def set_default(self):
        for section in self.defaults:
            for option, value in self.defaults[section].items():
                self.set(section, option, value)

    def read_ini(self, filename):
        if not filename or not os.path.isfile(filename):
            return

        parser = RawConfigParser()
        parser.read(filename)
        for section in parser.sections():
            for option in parser.options(section):
                value = None
                if section in self.defaults and option in self.defaults[section]:
                    t = type(self.defaults[section][option])
                    if   t is str:   value = parser.get(section, option)
                    elif t is int:   value = parser.getint(section, option)
                    elif t is float: value = parser.getfloat(section, option)
                    elif t is bool:  value = parser.getboolean(section, option)
                else:
                    value = parser.get(section, option)
                self.set(section, option, value)

    def read_argv(self):
        parser = self.build_parser()
        (options, args) = parser.parse_args()

        for key, value in options.__dict__.items():
            if value == None: continue
            section, option = key.split("-", 1)
            self.set(section, option, value)

        self.parse_argv(args)

    def build_parser(self):
        parser = OptionParser(usage=self.usage, version=self.version)
        for args, kwargs in self.parser_options.items():
            parser.add_option(*args, **kwargs)
        return parser

    def parse_argv(self, args):
        pass
