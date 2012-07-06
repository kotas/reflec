# -*- coding: utf_8 -*-
u"""
LiveAlive Monitor Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

from xml.etree.ElementTree import ElementTree

from utils.monitor import MonitorClient, PortMonitor

__all__ = ["LiveAliveClient", "LiveAliveMonitor"]

#-------------------------------------------------------------------------------
# LiveAliveClient
#-------------------------------------------------------------------------------

class LiveAliveClient(MonitorClient):
    u"""
    クライアントを表すクラス.
    アドレスが開放されているかどうかを確認できる.
    """

    def __init__(self, address, timeout = 3, server = ""):
        MonitorClient.__init__(self, address, timeout)
        self.server = server

#-------------------------------------------------------------------------------
# LiveAliveMonitor
#-------------------------------------------------------------------------------

class LiveAliveMonitor(PortMonitor):
    u"""
    クライアントのアドレスの開放状態を監視するクラス.
    開放状態が変わったらイベントを発行する.
    """

    client_class = LiveAliveClient

    def __init__(self, interval = 60, delay = 5):
        PortMonitor.__init__(self, interval, delay)

        self.load_clientsfile(clientsfile)

    def load_clientsfile(self, clientsfile):
        u"""
        clients.xml からクライアントを読み込む.
        """
        doc = ElementTree(file = clientsfile)
        for e in doc.findall("client"):
            param = dict(e.items())
            if "address" in param: self.append(**param)
