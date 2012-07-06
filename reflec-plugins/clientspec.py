# -*- coding: utf_8 -*-
u"""
Client Specific Plug-in

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

XML で書かれた専用の設定ファイルを読み込んで, クライアント別の設定を行う.
"""

import logging
from xml.etree.ElementTree import ElementTree

from reflec.plugin import ReflecBasePlugin

__all__ = ["ClientSpecificPlugin"]

__load__ = ["ClientSpecificPlugin"]

#-------------------------------------------------------------------------------
# ClientSpecificPlugin
#-------------------------------------------------------------------------------

class ClientSpecificPlugin(ReflecBasePlugin):
    u"""
    クライアントの接続先に応じて設定を変更するプラグイン.
    """

    encoding = "utf8"

    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def app_start(self, app):
        xmlfile = self.option.get("clientspec", "xmlfile", "clients.xml")
        xmlfile = self.app.abspath(xmlfile)

        address = [ "%s:%d%s" % self.client.peer_info ]
        if self.client.path == "/":
            address.append(address[0][:-1])

        doc = ElementTree(file = xmlfile)
        for e in doc.findall("client"):
            if e.get("address", "") in address:
                self.load_client_option(e)
                break

    def load_client_option(self, elem):
        u"""
        <client> 要素から設定を読み込む.
        """
        client_max = elem.find("max")
        if client_max != None:
            self.server.client_max = int(client_max.text)

        media_info = elem.find("media")
        if media_info != None:
            for it in media_info.getchildren():
                self.client.media_info[it.tag] = it.text
