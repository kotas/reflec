# -*- coding: utf_8 -*-
u"""
Plug-in Utility Classes

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import os.path
import logging
import traceback

__all__ = ["BasePlugin", "PluginLoader"]

#-------------------------------------------------------------------------------
# BasePlugin
#-------------------------------------------------------------------------------

class BasePlugin(object):
    u"""
    プラグインを表す基底クラス.
    """
    pass

#-------------------------------------------------------------------------------
# PluginLoader
#-------------------------------------------------------------------------------

class PluginLoader(object):
    u"""
    プラグインを読み込む為のクラス.

    プラグインディレクトリの中のスクリプトファイルを自動的に読み込む.

    スクリプトファイルには BasePlugin を継承したプラグインクラスを定義して
    トップレベルに定義した __load__ というリストにそのクラスの名前(文字列)を
    並べておくと, 自動的にインスタンス化される.

    EventHolder を登録してからプラグインを読み込むことで
    プラグインクラスに定義されている 'EventHolder名_イベント名' という
    メソッドが自動的に add_event_handler によって登録され, イベント時に
    呼び出されるようになる.
    """

    loadlist_name = "__load__"

    def __init__(self, dir):
        self.dir           = os.path.abspath(dir)
        self.event_holders = { }
        self.plugins       = { }

    def add_event_holder(self, holder, name = None):
        u"""
        EventHolder オブジェクトを登録する.

        name を指定した場合 EventHolder 名として, プラグインクラスの
        イベントメソッド登録の際のメソッドサーチに利用される.
        """
        self.event_holders[name] = holder

    def remove_event_holder(self, holder):
        u"""
        登録した EventHolder オブジェクトの登録を解除する.
        """
        for k, v in self.event_holders.items():
            if v == holder:
                del self.event_holders[k]

    def load_all_plugins(self, *args, **kwargs):
        u"""
        ディレクトリの中にあるプラグインを全て読み込む.
        """
        def exec_all_in_dir(arg, dirname, files):
            for f in files:
                if not f.endswith('.py') and not f.endswith('.pyw'): continue
                f = os.path.abspath(os.path.join(dirname, f))
                self.load_plugin(f, *args, **kwargs)
        os.path.walk(self.dir, exec_all_in_dir, None)

    def load_plugin(self, filename, *args, **kwargs):
        u"""
        指定したスクリプトファイルをプラグインとして読み込む.
        """
        modulename = os.path.splitext(filename)[0]
        modulename = modulename[len(self.dir)+1:]
        modulename = modulename.replace('\\', '.').replace('/', '.')
        try:
            namespace = { }
            execfile(filename, namespace, namespace)
            if self.loadlist_name in namespace:
                for cls in namespace[self.loadlist_name]:
                    name = "%s.%s" % (modulename, cls)
                    plugin = namespace[cls](*args, **kwargs)
                    self.register_event_methods(plugin)
                    self.plugins[name] = plugin
                    logging.debug("Plug-in %s loaded successfully." % name)
        except:
            logging.warning("Plug-in module %s loading failed:\n%s\n%s\n%s" %
                (modulename, "-"*40, traceback.format_exc().strip(), "-"*40))

    def register_event_methods(self, plugin):
        u"""
        プラグインオブジェクトのイベントメソッドを
        登録されている EventHolder に登録する.
        """
        for name in dir(plugin):
            names = name.split("_", 1)
            if len(names) < 2 or not names[1]: continue

            value = getattr(plugin, name)
            holder, event = names
            if callable(value) and holder in self.event_holders:
                self.event_holders[holder].add_event_handler(event, value)
