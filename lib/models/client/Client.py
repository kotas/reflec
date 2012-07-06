# -*- coding: utf_8 -*-
u"""
Client Model

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

__all__ = ["Client", "ClientFactory"]

#-------------------------------------------------------------------------------
# Client
#-------------------------------------------------------------------------------

class Client(object):
    u"""
    クライアントを表すモデル.
    """

    default_max = 100

    def __init__(self, **options):
        self.address = options.get("address")
        self.server = options.get("server")
        self.max = options.get("max", self.default_max)
        self.media = options.get("media", {})

#-------------------------------------------------------------------------------
# ClientFactory
#-------------------------------------------------------------------------------

class ClientFactory(object):
    u"""
    クライアントモデルを取得/作成するためのクラス.
    """

    def __init__(self, storage, *args, **kwargs):
        self.model = None

        if storage == "xml":
            import XMLClient
            self.model = XMLClient.XMLClientFactory(*args, **kwargs)
        elif storage == "mysql":
            import MySQLClient
            self.model = MySQLClient.MySQLClientFactory(*args, **kwargs)

    def get_one(self, address):
        return self.model.get_one(address)

    def get_all(self):
        return self.model.get_all()
