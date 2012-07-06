# -*- coding: utf_8 -*-
u"""
MMS-HTTP Client Classes

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

HTTP のヘッダーと、ストリーミング中に含まれるヘッダーパケットを区別するため
ヘッダーパケットの事を "情報パケット" (info_packets) と呼びます.
"""

import sys
import logging
import httplib
import socket
import threading
import time

from packet import *
from utils.event import EventHolder

__all__ = ["RequestNotSucceeded", "HTTPClient",
           "MMSHTTPClient", "MMSHTTPBufferedClient"]

#-------------------------------------------------------------------------------
# HTTPClient
#-------------------------------------------------------------------------------

class RequestNotSucceeded(Exception): pass

class HTTPClient(EventHolder):
    u"""
    HTTP プロトコルによる受信を行うクライアントを表すクラス.
    """

    # リクエストのメソッド
    request_method = "GET"

    # デフォルトのリクエストヘッダー
    default_header = {
        "Accept":     "*/*",
        "User-Agent": "HTTPClient/1.0",
    }

    # デーモンスレッドにする
    daemon_thread = False

    def __init__(self, host = 'localhost', port = 8080, path = '/',
                 addheader = {}, timeout = 30, retry = 5, retrysec = 10):
        EventHolder.__init__(self,
            "start", "terminate", "processing", "processed",
            "connecting", "connected", "request", "response",
        )

        self.host           = host
        self.port           = port
        self.path           = path
        self.peer_info      = (host, port, path)
        self.url            = "http://%s:%d%s" % self.peer_info
        self.timeout        = timeout
        self.retry          = retry
        self.retrysec       = retrysec
        self.status_line    = None
        self.header         = None
        self.body           = None
        self.request_header = self.default_header.copy()
        self.request_header.update(addheader)
        self.sock           = None
        self.terminating    = False
        self.terminated     = False
        self.client_thread  = None

        logging.debug("%s is initialized successfully." % self)

    def __str__(self):
        return "Client[%s:%d%s]" % self.peer_info

    def start(self):
        u"""別スレッドで受信を開始する."""
        if self.client_thread: return
        t = threading.Thread(target = self.client_thread_proc)
        t.setName( str(self) )
        if self.daemon_thread: t.setDaemon(1)
        self.terminating = False
        self.terminated = False
        self.client_thread = t
        t.start()

    def client_thread_proc(self):
        u"""クライアントスレッド用プロシージャ"""
        logging.debug("%s thread started." % self)
        self.notify_event("start")

        try:
            try:
                self.setup()
                self.notify_event("processing")
                self._process()
                self.notify_event("processed")
                self.finish()
            except RequestNotSucceeded, e:
                logging.error("%s failed request: %r" % (self, e))
            except socket.error, e:
                if self.terminating:
                    logging.info("%s closed for termination." % self)
                else:
                    logging.error("%s closed: %s" % (self, e))
        finally:
            self.terminated = True

        self.notify_event("terminate")
        logging.debug("%s thread finished." % self)

    def setup(self):
        u"""受信を開始する前の準備."""
        pass

    def _process(self):
        u"""受信処理を行い, 失敗したらリトライする."""
        retry = self.retry
        first = True
        while True:
            try:
                if first:
                    first = False
                    self.process()
                else:
                    self.retry_process()
                break
            except socket.error, e:
                if not self.terminating and retry > 0 and self.retrysec > 0:
                    retry -= 1
                    logging.error("%s closed: %s. Retrying %d/%d after %d sec."
                            % (self, e, self.retry - retry, self.retry,
                               self.retrysec))
                    time.sleep(self.retrysec)
                else:
                    raise

    def process(self):
        u"""実際の受信を行う処理."""
        self.send_request(self.receive_body)

    def retry_process(self):
        u"""リトライ時に行う処理."""
        self.process()

    def receive_body(self, fp):
        u"""ボディ部の受信を行う処理."""
        self.body = fp.read()

    def finish(self):
        u"""受信を終了する時の処理."""
        pass

    def join(self, timeout = None):
        u"""受信が終了するかタイムアウトするまで待機する."""
        self.client_thread.join(timeout)

    def terminate(self):
        u"""強制的に終了する."""
        self.terminating = True
        if self.sock:
            self.sock.close()

    def build_header(self, addheader = {}):
        u"""リクエストヘッダーを作成する."""
        h = self.request_header.copy()
        h["Host"] = "%s:%d" % (self.host, self.port)  # Host は自動設定
        h.update(addheader)
        return h

    def send_request(self, body_receiver, addheader = {}):
        u"""
        サーバーに接続してリクエストを送信する.
        接続に成功したら body_receiver に
        HTTPResponse オブジェクトを渡して呼び出す.
        """
        con = httplib.HTTPConnection(self.host, self.port)
        res = None
        try:
            logging.info("%s is connecting to %s." % (self, self.url))
            self.notify_event("connecting")

            con.connect()
            self.sock = con.sock
            self.sock.settimeout(self.timeout)

            self.notify_event("connected")
            logging.info("%s connected successfully." % self)

            header = self.build_header(addheader)

            logging.debug("%s is sending the request:\n%s\n%s %s %s\n%s\n%s" %
                          ( self,
                            "-" * 40,
                            self.request_method, self.path, "HTTP/1.1",
                            "\n".join(["%s: %s" % (k.capitalize(), v)
                                       for k, v in header.items()]),
                            "-" * 40,
                          ))

            self.notify_event("request", header)
            con.request(self.request_method, self.path, None, header)
            res = con.getresponse()
            self.notify_event("response", res)

            version = "HTTP/1.0"
            if   res.version < 10: version = "HTTP/0.9"
            elif res.version > 10: version = "HTTP/1.1"

            self.header      = res.msg
            self.status_line = "%s %d %s" % (version, res.status, res.reason)

            logging.debug("%s received the response from the server:\n" \
                          "%s\n%s %d %s\n%s\n%s" %
                          ( self,
                            "-" * 40,
                            version, res.status, res.reason,
                            "".join(self.header.headers).strip(),
                            "-" * 40,
                          ))

            if res.status >= 200 and res.status < 300:
                try:
                    body_receiver(res.fp)
                except EOFError, e:
                    logging.error("%s receiving failed. Reason: %s" % (self, e))
            else:
                logging.warning("%s received error from the server: %d %s" %
                                (self, res.status, res.reason))
                raise RequestNotSucceeded(res.status, res.reason)
        finally:
            if self.sock:
                self.sock = None
            if res:
                res.close()
                res = None
            if con:
                con.close()
                con = None

        logging.info("%s disconnected successfully." % self)

#-------------------------------------------------------------------------------
# MMSHTTPClient
#-------------------------------------------------------------------------------

class MMSHTTPClient(HTTPClient):
    u"""
    MMS-HTTP プロトコルによって動画ストリーミングを受信するクラス.
    """

    # デフォルトのリクエストヘッダー
    default_header = {
        "Accept":     "*/*",
        "User-Agent": "NSPlayer/4.1.0.3928",
    }

    # 動画の情報のリクエスト(1回目)に利用する追加ヘッダー
    addheader_for_info = {
        "Pragma":     {
            "no-cache":        "",
            "rate":            "1.000000",
            "stream-time":     "0",
            "stream-offset":   "0:0",
            "request-context": "1",
            "max-duration":    "0",
        }
    }

    # 動画のストリーミングのリクエスト(2回目)に利用する追加ヘッダー
    addheader_for_streaming = {
        "Pragma":      {
            "no-cache":            "",
            "rate":                "1.000000",
            "stream-time":         "0",
            "stream-offset":       "0:0",
            "request-context":     "2",
            "max-duration":        "0",
            "xPlayStrm":           "1",
            "stream-switch-count": "2",
            "stream-switch-entry": "ffff:1:0 ffff:2:0",
        }
    }

    # パケットを表すクラス
    packet_class = MMSHTTPPacket

    # 情報パケットを表すクラス
    info_packet_class = MMSHTTPInfoPacket

    def __init__(self, *args, **kwargs):
        HTTPClient.__init__(self, *args, **kwargs)

        self.info_packet = None
        self.started     = False
        self.media_info  = { }
        self.ext_info    = { }
        self.register_event("info_packet", "start_streaming",
                            "finish_streaming")

    def process(self):
        u"""実際の受信を行う処理."""
        logging.info("%s first connect to the server for media info." % self)
        self.request_for_info()
        logging.info("%s second connect to the server for streaming." % self)
        self.request_for_streaming()

    def retry_process(self):
        u"""リトライ時に行う処理."""
        if not self.info_packet:
            self.process()
        else:
            logging.info("%s skipped first connect." % self)
            logging.info("%s second connect to the server for streaming." % self)
            self.request_for_streaming()

    def request_for_info(self):
        u"""動画の情報をリクエストする."""
        self.send_request(self.receive_info,
                          self.addheader_for_info)

    def receive_info(self, fp):
        u"""動画の情報を受信する."""
        self.info_packet = self.info_packet_class(fp)
        self.media_info.update(self.info_packet.media_info)
        self.ext_info.update(self.info_packet.ext_info)
        self.notify_event("info_packet")

        logging.info("%s received the media info successfully." % self)

        def format_info(info):
            s = ""
            enc = sys.getfilesystemencoding()
            for k, v in info.items():
                if isinstance(k, unicode): k = k.encode(enc)
                if isinstance(v, unicode): v = v.encode(enc)
                s += "%-20s : %s\n" % (k, v)
            return s.rstrip()

        if self.media_info:
            logging.info("%s Media Info:\n%s\n%s\n%s" %
                ( self, "-" * 40, format_info(self.media_info), "-" * 40 ))

        if self.info_packet.ext_info:
            logging.debug("%s Extended Info:\n%s\n%s\n%s" %
                ( self, "-" * 40, format_info(self.ext_info), "-" * 40 ))

    def request_for_streaming(self):
        u"""動画のストリーミングをリクエストする."""
        self.send_request(self.receive_streaming,
                          self.addheader_for_streaming)

    def receive_streaming(self, fp):
        u"""動画のストリーミングを受信する."""
        packet_num = 0
        try:
            for packet in self.packet_class.StreamingIterator(fp):
                if self.terminating: break

                # WME はストリーミング配信を停止した後でも接続を受け付け
                # ヘッダーパケットを送信するので, パケットを3つほど受信したら
                # ストリーミングの開始と判断する.
                packet_num += 1
                if packet_num == 3:
                    logging.info("%s has started receiving media streaming." % self)
                    self.notify_event("start_streaming")
                    self.started = True

                self.process_packet(packet)

        finally:
            if self.started:
                self.notify_event("finish_streaming")
                logging.info("%s has finished receiving media streaming." % self)

    def process_packet(self, packet):
        u"""動画のデータパケットを1つ処理する."""
        pass

    def build_header(self, addheader = {}):
        u"""リクエストヘッダーを作成する."""
        h = HTTPClient.build_header(self, addheader)

        # Pragma ヘッダーを「名前=値,名前=値,名前=値...」形式に変換
        pragmas = []
        for k, v in h["Pragma"].items():
            if v:
                pragmas.append("%s=%s" % (k, v))
            else:
                pragmas.append(k)
        h["Pragma"] = ",".join(pragmas)

        return h

#-------------------------------------------------------------------------------
# MMSHTTPBufferedClient
#-------------------------------------------------------------------------------

class MMSHTTPBufferedClient(MMSHTTPClient):
    u"""
    MMS-HTTP プロトコルによって動画ストリーミングを受信するクラス.
    受信した最近の動画データパケットをリングバッファに保存する.
    """

    def __init__(self, bufsize = 16, *args, **kwargs):
        self.buffer   = { }
        self.bufsize  = bufsize
        self.seq      = -1

        MMSHTTPClient.__init__(self, *args, **kwargs)

    def process_packet(self, packet):
        u"""
        動画のデータパケットを1つ処理する.
        受信したパケットをリングバッファに保存する.
        """
        MMSHTTPClient.process_packet(self, packet)
        newseq = self.seq + 1
        self.buffer[ newseq % self.bufsize ] = packet
        self.seq = newseq

    def get_packet(self, sequence):
        u"""
        指定したシーケンス番号に対応するパケットを返す.
        リングバッファによる実装なので一定以上古いパケットを取得しようとすると
        それよりも新しいパケットが返ってくる.
        """
        return self.buffer[sequence % self.bufsize]

    def iter_streaming(self):
        u"""
        バッファされた動画ストリーミングのパケットを順番に処理する為の
        イテレーターを返す.
        ただし動画を受信している間はブロッキングされているので
        データを逐一処理したい場合はスレッドを利用する.
        """
        return self.StreamingIterator(self)

    def __iter__(self):
        return self.iter_streaming()


    class StreamingIterator(object):
        u"""
        MMSHTTPBufferedClient でバッファされた動画のデータパケットを
        順番に処理するためのイテレーター.
        ストリーミングを全て処理するまでイテレートが中断しないので注意.
        また、クライアントでの受信に追いついた時は処理をブロッキングする.
        """

        def __init__(self, client):
            self.client = client
            self.seq    = client.seq + 1

        def __iter__(self):
            return self

        def next(self):
            u"""
            次のパケットを返す.
            """
            # 新たなパケットがバッファリングされるまで待機
            while self.seq > self.client.seq:
                if self.client.terminated: raise StopIteration()
                time.sleep(0.01)

            p = self.client.get_packet(self.seq)

            self.seq += 1
            return p

#-------------------------------------------------------------------------------

#
# テスト用
#
if __name__ == "__main__":
    logging.basicConfig(level  = logging.DEBUG,
                        format = '%(asctime)s %(levelname)s %(message)s')
    logging.debug("MMSHTTPClient test starts.")

    client = MMSHTTPBufferedClient()
    client.start()

    logging.debug("MMSHTTPClient has started.")

    time.sleep(1)

    logging.debug("Buffering Test starts.")

    for p in client.iter_streaming():
        logging.debug("%r" % p)

    logging.debug("MMSHTTPClient has been closed.")
    logging.debug("MMSHTTPClient test finished.")
