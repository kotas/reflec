# -*- coding: utf_8 -*-
u"""
Make Index Plug-in

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

Reflec の中継状態を表す XML ファイルを作成します.
Reflec を複数起動している場合, 複数の中継状態が
1つの XML ファイルに書かれる事になります.
"""

import os
import os.path
import time
import logging
import threading
from xml.etree.ElementTree import ElementTree, Element, SubElement

from reflec.plugin import ReflecBasePlugin

__all__ = ["MakeIndexPlugin"]

__load__ = ["MakeIndexPlugin"]

#-------------------------------------------------------------------------------
# MakeIndexPlugin
#-------------------------------------------------------------------------------

class MakeIndexPlugin(ReflecBasePlugin):
    u"""
    Reflec でのミラー状況のインデックスファイルを作成するプラグイン.
    """

    # XML ファイルのエンコーディング
    encoding = "utf-8"

    # ロックを試す回数
    lock_try = 3

    def app_start(self, app):
        self.lock = threading.Lock()
        self.filename = self.app.abspath(
            self.option.get("makeindex", "filename", "index.dat") )
        self.server_address = "%s:%d" % self.server.server_address
        self.start_time = time.strftime("%Y/%m/%d %H:%M:%S")
        self.on_list = False

    def client_start_streaming(self, client):
        if not self.on_list:
            self.on_list = True
            self.emit()

    def server_client_num(self, server):
        if self.on_list:
            self.emit()

    def client_finish_streaming(self, app):
        if self.on_list:
            self.on_list = False
            self.emit()

    def emit(self, removal = False):
        u"""
        インデックスファイルを更新する.
        """
        self.lock.acquire()
        try:
            doc = None
            if os.path.isfile(self.filename):
                doc = ElementTree(file = self.filename)
            else:
                root = Element("index")
                doc = ElementTree(root)

            index = -1
            for i, e in enumerate(doc.findall("live")):
                if e.get("server", "") == self.server_address:
                        index = i
                        doc.getroot().remove(e)

            if self.on_list:
                doc.getroot().insert(index, self.live_element())

            f = open(self.filename, "w")
            f.write('<?xml version="1.0" encoding="%s"?>\n' % self.encoding)
            doc.write(f, self.encoding)
            f.close()
        finally:
            self.lock.release()

    def live_element(self):
        u"""
        現在の状態を表す Element オブジェクトを作成して返す.
        """
        el = Element("live", server = self.server_address)
        SubElement(el, "start").text = self.start_time
        SubElement(el, "num").text = str(self.server.client_num)
        SubElement(el, "max").text = str(self.server.client_max)
        info = SubElement(el, "media")
        for k, v in self.client.media_info.items():
            SubElement(info, k).text = v
        return el
