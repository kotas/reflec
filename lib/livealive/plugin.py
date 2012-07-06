# -*- coding: utf_8 -*-
u"""
LiveAlive Plug-in Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

from utils.plugin import *

__all__ = ["LiveAliveBasePlugin", "LiveAlivePluginLoader"]

#-------------------------------------------------------------------------------
# LiveAliveBasePlugin
#-------------------------------------------------------------------------------

class LiveAliveBasePlugin(BasePlugin):
    u"""
    LiveAlive のプラグインを表す基底クラス.
    """

    def __init__(self, app):
        self.app     = app
        self.monitor = app.monitor
        self.option  = app.option
        self.prompt  = app.prompt

#-------------------------------------------------------------------------------
# LiveAlivePluginLoader
#-------------------------------------------------------------------------------

class LiveAlivePluginLoader(PluginLoader):
    u"""
    LiveAlive のプラグインを読み込むクラス.
    """

    def load_all_plugins(self, app, *args, **kwargs):
        u"""
        ディレクトリの中にあるプラグインを全て読み込む.
        """
        PluginLoader.load_all_plugins(self, app, *args, **kwargs)

    def load_plugin(self, filename, app, *args, **kwargs):
        u"""
        指定したスクリプトファイルをプラグインとして読み込む.
        """
        PluginLoader.load_plugin(self, filename, app, *args, **kwargs)
