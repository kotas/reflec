# -*- coding: utf_8 -*-
u"""
Reflec Constants

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

# アプリケーションのタイトル
APP_NAME = "Reflec2"

# アプリケーションのバージョン
APP_VERSION = "2.00"

# アプリケーションの説明
APP_DESCRIPTION = "MMS-HTTP Streaming Mirrorring Tool."

# アプリケーションのコピーライト表記
APP_COPYRIGHT = "Licensed under the MIT License.\n" \
                "Copyright (c) 2007-2012 Kota Saito"

# アプリケーションのバージョン表示 (--version で表示)
APP_VERSION_TEXT = "%s %s - %s\n\n%s" % \
                   (APP_NAME, APP_VERSION, APP_DESCRIPTION, APP_COPYRIGHT)

# アプリケーションのディレクトリ (外部から設定)
APP_DIR = ""

# 設定ファイルの名前
CONFIG_FILE = ("conf/global.ini", "conf/reflec2.ini")

# プラグインディレクトリの名前
PLUGIN_DIR = "reflec-plugins"

__all__ = ["APP_NAME", "APP_VERSION", "APP_COPYRIGHT", "APP_DESCRIPTION",
           "APP_VERSION_TEXT", "APP_DIR", "CONFIG_FILE", "PLUGIN_DIR"]
