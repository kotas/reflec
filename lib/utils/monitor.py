# -*- coding: utf_8 -*-
u"""
TCP Port Monitor Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import re
import socket
import threading
import logging
import time

from event import EventHolder

__all__ = ["MonitorClient", "PortMonitor"]

#-------------------------------------------------------------------------------
# MonitorClient
#-------------------------------------------------------------------------------

class MonitorClient(object):
    u"""
    監視されるクライアントを表すクラス.
    アドレスが開放されているかどうかを確認できる.
    """

    def __init__(self, address, timeout = 3):
        self.address = address
        self.timeout = timeout
        self.alive = False
        self.terminating = False

        r = re.match(r"^(?:[^:]+://)?([^/:]+)(?::(\d+))?.*", address)
        if r:
            self.host = r.group(1)
            self.port = int(r.group(2))
        else:
            logging.error("%s is not valid address." % address)

    def __str__(self):
        return "Client[%s:%d]" % (self.host, self.port)

    def terminate(self):
        self.terminating = True

    def status(self):
        return "ALIVE" if self.alive else "DEAD"

    def check_alive(self):
        u"""
        開放されているか確かめる.
        """
        if not self.host: return False
        alive = True
        sock = socket.socket()
        sock.settimeout(self.timeout)
        try:
            try:
                sock.connect((self.host, self.port))
            except socket.error:
                alive = False
        finally:
            sock.close()

        self.alive = alive
        return alive

#-------------------------------------------------------------------------------
# PortMonitor
#-------------------------------------------------------------------------------

class PortMonitor(EventHolder):
    u"""
    指定したホストのTCPポートの開放状態を監視するクラス.
    開放状態が変わったらイベントを発行する.
    """

    client_class = MonitorClient

    def __init__(self, interval = 60, delay = 5):
        EventHolder.__init__(self,
            "start", "alive", "dead", "change",
            "checking", "checked")
        self.clients     = {}
        self.interval    = interval
        self.delay       = delay
        self.terminating = False

    def append(self, address, *args, **kwargs):
        u"""監視対象のアドレスを追加する."""
        self.clients[address] = self.client_class(address, *args, **kwargs)

    def remove(self, address):
        u"""監視対象のアドレスを削除する."""
        c = self.clients.pop(address, None)
        if c: c.terminate()

    def clear(self):
        "全てのクライアントを削除する."
        for address in self.clients.keys():
            self.remove(address)

    def start(self):
        u"""クライアントの監視を開始する."""
        self.terminating = False
        t = threading.Thread(target = self.starting_thread_proc)
        t.start()

    def starting_thread_proc(self):
        u"""
        監視を開始するスレッド関数.
        遅延付きで順番に開始していくと, ブロッキング時間が長いので
        別スレッドで実行する.
        """
        for client in self.clients.values():
            t = threading.Thread(target = self.client_thread_proc,
                                 kwargs = { "client": client })
            t.setName(str(client))
            t.setDaemon(1)
            t.start()
            time.sleep(self.delay)

    def client_thread_proc(self, client):
        u"""クライアント監視スレッド関数."""
        try:
            self.notify_event("start", client)
            while not self.terminating and not client.termnating:
                self.notify_event("checking", client)

                last_alive = client.alive
                if last_alive != client.check_alive():
                    logging.info("Monitor: %s has become %s."
                        % (client, client.status()))

                    self.notify_event("change", client)
                    if client.alive:
                        self.notify_event("alive", client)
                    else:
                        self.notify_event("dead", client)
                else:
                    logging.debug("Monitor: %s stays %s."
                        % (client, client.status()))

                self.notify_event("checked", client)

                time_until = time.time() + self.interval
                while time.time() < time_until:
                    if self.terminating or client.terminating:
                        break
                    time.sleep(1)
        finally:
            self.remove(client.address)

    def terminate(self):
        u"""強制的に終了する."""
        self.terminating = True

#-------------------------------------------------------------------------------

#
# テスト用
#
if __name__ == "__main__":
    import time

    def change(monitor, client):
        print "Changed: %s" % ("ALIVE" if client.alive else "DEAD")

    monitor = PortMonitor(20)
    monitor.append("localhost:8888")
    monitor.add_event_handler("change", change)
    monitor.start()
    while True:
        time.sleep(60)
