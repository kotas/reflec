# -*- coding: utf_8 -*-
u"""
Client Model using XML as data source

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

from Client import Client

from xml.etree.ElementTree import ElementTree

__all__ = ["XMLClient", "XMLClientFactory"]

#-------------------------------------------------------------------------------
# XMLClient
#-------------------------------------------------------------------------------

class XMLClient(Client):
    u"""
    クライアントを表すモデル.
    """

    def __init__(self, node):
        address = node.get("address")
        server  = node.get("server")
        max     = node.findtext("max")
        media   = node.find("media")

        try:
            max = int(max)
        except ValueError:
            max = None

        params = {}
        if address: params["address"] = address
        if server:  params["server"]  = server
        if max:     params["max"]     = int(max)
        if media:   params["media"]   = media.items()

        Client.__init__(self, **params)

#-------------------------------------------------------------------------------
# XMLClientFactory
#-------------------------------------------------------------------------------

class XMLClientFactory(object):
    u"""
    クライアントモデルを取得/作成するためのクラス.
    """

    def __init__(self, xmlfile):
        self.xmlfile = xmlfile

    def get_one(self, address):
        client = None
        doc = ElementTree(file = self.xmlfile)
        for node in doc.findall("client"):
            if node.get("address") == address:
                client = XMLClient(node)
        return client

    def get_all(self):
        doc = ElementTree(file = self.xmlfile)
        return [ XMLClient(node) for node in doc.findall("client") ]
