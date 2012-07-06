# -*- coding: utf_8 -*-
u"""
Reflec Plug-in Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

from utils.plugin import *

__all__ = ["ReflecBasePlugin", "ReflecPluginLoader"]

#-------------------------------------------------------------------------------
# ReflecBasePlugin
#-------------------------------------------------------------------------------

class ReflecBasePlugin(BasePlugin):
    u"""
    Reflec のプラグインを表す基底クラス.
    """

    def __init__(self, app):
        self.app    = app
        self.client = app.client
        self.server = app.server
        self.option = app.option
        self.prompt = app.prompt

#-------------------------------------------------------------------------------
# ReflecPluginLoader
#-------------------------------------------------------------------------------

class ReflecPluginLoader(PluginLoader):
    u"""
    Reflec のプラグインを読み込むクラス.
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
