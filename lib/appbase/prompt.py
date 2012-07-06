# -*- coding: utf_8 -*-
u"""
Command Prompt Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import os
import sys
import threading
import logging
import string

__all__ = ["CommandPrompt"]

#-------------------------------------------------------------------------------
# OS 別に関数を定義
#-------------------------------------------------------------------------------

if os.name == "nt":
    import msvcrt
    def read_console():
        return msvcrt.getch()

elif os.name == 'posix':
    import sys
    def read_console():
        return sys.stdin.readline()

#-------------------------------------------------------------------------------
# CommandPrompt
#-------------------------------------------------------------------------------

class CommandPrompt(object):
    u"""
    コマンド入力を受け付けるクラス.
    """

    def __init__(self, quit_func = sys.exit):
        self.thread     = None
        self.terminated = False
        self.quit_func  = quit_func
        self.commands   = { }

        self.add_command("H", "HELP", "Show this help message.", self.help)
        self.add_command("Q", "QUIT", "Quit the application.", self.quit)

    def start(self):
        u"""入力を受け付けるスレッドを開始する."""
        if self.thread: return
        t = threading.Thread(target = self.prompt_thread_proc)
        t.setName("CommandPrompt")
        t.setDaemon(True)
        t.start()
        self.terminated = False
        self.thread = t

    def terminate(self):
        u"""入力の受け付けを終了する."""
        self.terminated = True
        self.thread = None

    def prompt_thread_proc(self):
        u"""入力を受け付けて処理するスレッド関数."""
        while not self.terminated:
            command = read_console().rstrip().upper()
            if not command: break

            key = command[0]
            if key in self.commands and \
               (len(command) == 1 or command == self.commands[key][0]):
                    self.commands[key][2]()
            else:
                    self.write("No command for %r. Type 'H' for help." % key)
                    continue

        self.thread = None

    def add_command(self, key, name, description, func):
        u"""コマンドを追加する."""
        self.commands[key.upper()] = (name.upper(), description, func)

    def write(self, msg, *args):
        u"""情報を表示する."""
        print(">>> %s" % (msg % args))

    def ask_user(self, msg, keys, default = None):
        u"""ユーザーに質問する."""
        keylist = [("[%s]"%k) if k == default else k for k in keys]
        self.write("%s (%s)" % (msg, "/".join(keylist)))

        key = read_console()
        if not key: return default

        key = key[0].lower()
        if key in keys:
            return key
        else:
            return default

    def help(self):
        u"""コマンドのヘルプを表示する."""
        print("=" * 40)
        print("Command Help")
        print("")
        for k, v in sorted(self.commands.items()):
            print("    %s %-10s %s" % (k, "(%s)" % v[0], v[1]))
        print("")
        print("=" * 40)

    def quit(self):
        u"""アプリケーションを終了する."""
        if self.ask_user("Are you sure to quite the application?",
                         ["y", "n"], "n") == "y":
            self.write("Quiting the application...")
            self.quit_func()
        else:
            self.write("Quit command has been cancelled.")
