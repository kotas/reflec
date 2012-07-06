# -*- coding: utf_8 -*-
u"""
MMS-HTTP Server Classes

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import logging
import threading
import socket
import time

from utils.event import EventHolder

__all__ = ["MMSHTTPBaseHandler", "MMSHTTPStreamingHandler",
           "MMSHTTPClientMaxHandler", "MMSHTTPServer"]

#-------------------------------------------------------------------------------
# MMSHTTPBaseHandler
#-------------------------------------------------------------------------------

class MMSHTTPBaseHandler(BaseHTTPRequestHandler):
    u"""
    MMS-HTTP プロトコルによる接続を処理するハンドラの基底クラス.
    """

    loginfo_setup  = "%s connected successfully."
    loginfo_finish = "%s disconnected successfully."

    error_message_format = u"""\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>%(code)d %(message)s</title>
</head>
<body>
<h1>%(code)d %(message)s</h1>
<p>Sorry, the server could not handle your request.</p>
<p>%(explain)s</p>
</body>
</html>
"""

    def __str__(self):
        return "Handler[%s:%d]" % (self.host, self.client_address[1])

    def setup(self):
        u"""処理の前準備を行う."""
        self.server.inc_client_num()

        BaseHTTPRequestHandler.setup(self)

        self.pragmas = {}
        self.host    = self.address_string()

        logging.info(self.loginfo_setup % self)

    def parse_request(self):
        u"""リクエストの解析を行う."""

        # リクエストされているパスが
        #     GET HTTP/1.0
        # のように空白の場合は
        #     GET / HTTP/1.0
        # になるように修正する
        words = self.raw_requestline.rstrip().split()
        if len(words) == 2 and words[1].startswith("HTTP/"):
            self.raw_requestline = "%s / %s\n" % tuple(words)

        r = BaseHTTPRequestHandler.parse_request(self)
        if not r:
            logging.warning("%s can't parse the request." % self)
            return

        self.parse_pragma()

        # リクエストヘッダーをログ出力
        logging.debug("%s received the request:\n%s\n%s %s %s\n%s\n%s" %
                      (self,
                       "-" * 40,
                       self.command, self.path, self.request_version,
                       "".join(self.headers.headers).strip(),
                       "-" * 40))
        return r

    def handle_one_request(self):
        u"""1つのリクエストを処理する."""
        try:
            BaseHTTPRequestHandler.handle_one_request(self)
        except socket.error, e:
            logging.debug("%s stopped handling the request."\
                          " Reason: %s" % (self, str(e)))

    def finish(self):
        u"""処理の後始末を行う."""
        BaseHTTPRequestHandler.finish(self)
        logging.info(self.loginfo_finish % self)

        self.server.dec_client_num()

    def parse_pragma(self):
        u"""
        Pragma ヘッダーを解析して ',' で区切られた 名前=値 リストを
        辞書に変換する.
        """
        self.pragmas = {}

        pragmas = self.headers.getheaders("Pragma")
        if not pragmas: return

        for lines in pragmas:
            for line in lines.split("\n"):
                lst = [v.split("=", 1) for v in line.split(",")]
                for p in lst:
                    k = p[0].strip().lower()
                    if len(p) >= 2:
                        v = p[1].strip()
                    else:
                        v = ""
                    self.pragmas[k] = v

    def log_error(self, format, *args):
        u"""エラーメッセージを記録する."""
        logging.error("%s %s" % (self, format % args))

    def log_message(self, format, *args):
        u"""ログメッセージを記録する."""
        logging.info("%s %s" % (self, format % args))

    def version_string(self):
        u"""サーバーのバージョン文字列を返す."""
        return "%s/%s" % self.server.version

#-------------------------------------------------------------------------------
# MMSHTTPStreamingHandler
#-------------------------------------------------------------------------------

class MMSHTTPStreamingHandler(MMSHTTPBaseHandler):
    u"""
    MMS-HTTP プロトコルによってメディアストリーミングを配信するハンドラ.
    """

    # ストリーミングのリクエストヘッダーに含まれる Pragma
    pragmas_for_streaming = (
        "xplaystrm",
        "stream-switch-count",
        "stream-switch-entry",
    )

    # 情報パケットのリクエストヘッダーに含まれる Pragma
    pragmas_for_header = pragmas_for_streaming + (
        "rate",
        "stream-time",
        "stream-offset",
        "request-context",
        "max-duration",
        "xclientguid",
    )

    # ASX プレイリストのフォーマット
    playlist_format = """\
<asx version="3.0">
	<entry>
		<ref href="%s" />
	</entry>
</asx>
"""

    def setup(self):
        u"""処理の前準備を行う."""
        MMSHTTPBaseHandler.setup(self)

        # 配信に利用するソース（MMSHTTPBaseSource）をサーバーから取得する
        self.source = self.server.new_source()

    def do_POST(self):
        u"""
        POST リクエストに対する処理を行う.
        クライアントからのログ情報の送信を受け付ける.
        レスポンスとして 204 No Content を返す.
        """
        if "log-line" in self.pragmas:
            logging.info("%s has log-line: %s" %
                         (self, self.pragmas["log-line"]))

        self.send_response(204)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Pragma", "no-cache")
        self.end_headers()

    def do_GET(self):
        u"""
        GET リクエストに対する処理を行う.
        リクエストにはヘッダ情報だけを取得するリクエストと
        本体のストリーミングを取得するリクエストの2種類がある.
        """

        if not self.source:
            logging.debug("%s doesn't have source." % self)
            self.send_error(501)

        elif not self.source.is_ready():
            logging.debug("%s source is not ready." % self)
            self.send_error(503, "Service is not ready.")

        elif self.is_request_for_streaming():
            logging.debug("%s requests for streaming." % self)
            self.send_headers()
            self.send_streaming()

        elif self.is_request_for_header():
            logging.debug("%s requests for headers only." % self)
            self.send_headers()

        else:
            logging.debug("%s requests for play list." % self)
            self.send_default_page()

    def send_headers(self):
        u"""
        動画の情報パケットのリクエストに対するレスポンスヘッダーと
        ストリーミングの情報パケットを送信する.
        """
        logging.debug("%s is sending a response header." % self)

        self.wfile.write( self.source.headers() )

        logging.debug("%s has sent the response to the client:\n%s\n%s\n%s" %
            ( self,
              "-" * 40,
              self.source.headers().strip(),
              "-" * 40
            ))

        self.wfile.write( str(self.source.info_packet()) )

        logging.debug("%s has sent the media info %r." %
                      (self, self.source.info_packet()))

    def send_streaming(self):
        u"""
        ストリーミングが終了するまでパケットを順番に送信する.
        送信はブロッキングするので注意.
        """
        logging.debug("%s starts sending streaming." % self)

        for packet in self.source.iter_streaming():
            self.wfile.write( str(packet) )

    def send_default_page(self):
        u"""
        通常のウェブページのリクエストに対するレスポンスを返す.
        リクエストが MMS-HTTP のものでない場合に呼び出される.

        恐らくブラウザなどからただの HTTP としてアクセスされているので,
        プレイリストを送信して動画の URL に誘導する.
        """

        # Shoutcast ではない
        if self.headers.has_key("Icy-MetaData"):
            self.send_error(400, "Shoutcast Not Supported. Try mms Protocol.")
            return

        self.send_playlist()

    def send_playlist(self):
        u"""
        mms:// から始まる動画 URL が書かれた ASX プレイリストを送信する.
        ただし, 処理の都合上, リクエストヘッダに Host が含まれている
        必要がある.

        Host が含まれていない場合は 400 Bad Request を返す.
        """
        host = self.headers.get("Host", "")
        if host:
            if host.find(":") < 0:
                host += ":%d" % self.server.server_address[1]

            url = "mms://%s%s" % (host, self.path)
            playlist = self.playlist_format % url

            self.send_response(200)
            self.send_header("Content-Type",   "video/x-ms-asf")
            self.send_header("Content-Length", len(playlist))
            self.send_header("Connection",     "close")
            self.end_headers()
            self.wfile.write(playlist)
        else:
            self.send_error(400, "Unknown Headers. Try mms Protocol.")

    def is_request_for_streaming(self):
        u"""リクエストがストリーミングを要求しているかどうか."""

        # ストリーミング要求時の Pragma があるかどうか調べる
        for p in self.pragmas_for_streaming:
            if p in self.pragmas:
                return True

        # request-context が 1 でない場合はストリーミングの要求
        if self.pragmas.get("request-context", "1") != "1":
            return True

        return False

    def is_request_for_header(self):
        u"""リクエストがヘッダーと情報パケットを要求しているかどうか."""

        # ヘッダー要求時の Pragma があるかどうか調べる
        for p in self.pragmas_for_header:
            if p in self.pragmas:
                return True

        return False

#-------------------------------------------------------------------------------
# MMSHTTPClientMaxHandler
#-------------------------------------------------------------------------------

class MMSHTTPClientMaxHandler(MMSHTTPBaseHandler):
    u"""
    MMS-HTTP プロトコルで接続数が最大数に達した事を伝えるハンドラ.
    """

    loginfo_setup  = "%s connected, but disconnecting due to ClientMax."

    def do_GET(self):
        u"""
        GET リクエストに対する処理を行う.
        最大人数に達しているので 503 Service Unavailable を返す.
        """
        self.send_error(503, "Too Many Clients")

    def do_POST(self):
        u"""POST リクエストも GET リクエストと同様."""
        self.do_GET()

    def do_HEAD(self):
        u"""HEAD リクエストも GET リクエストと同様."""
        self.do_GET()

#-------------------------------------------------------------------------------
# MMSHTTPServer
#-------------------------------------------------------------------------------

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer): pass

class MMSHTTPServer(ThreadingHTTPServer, EventHolder):
    u"""
    MMS-HTTP プロトコルによる接続を受け付ける為のクラス.
    実際のクライアントに対する処理はハンドラに委譲する.
    """

    # サーバーのバージョン
    version = ("MMSHTTPServer", "1.0")

    # スレッドをデーモンスレッドにする
    daemon_threads = True

    def __init__( self,
                  source_class,
                  bindings       = ('', 8080),
                  req_handler    = MMSHTTPStreamingHandler,
                  max_handler    = MMSHTTPClientMaxHandler,
                  client_max     = 100,
                  timeout        = 180,
                  countdown      = 10 ):

        EventHolder.__init__(self,
            "start", "terminating", "terminate", "request",
            "processing", "processed", "client_num",
        )

        try:
            if isinstance(bindings, basestring):
                if bindings.find(':') >= 0:
                    bindings    = bindings.split(':', 1)
                    bindings    = (bindings[0], int(bindings[1]))
                else:
                    bindings    = ('', int(bindings))
            elif isinstance(bindings, int):
                bindings = ('', bindings)
        except ValueError, e:
            logging.error("Given binding port is not a number.")
            bindings = ('', 8080)

        ThreadingHTTPServer.__init__(self, bindings, req_handler)
        self.socket.settimeout(None)

        self.serving_thread = None
        self.connections    = []
        self.terminated     = False
        self.source_class   = source_class
        self.req_handler    = req_handler
        self.max_handler    = max_handler
        self.client_max     = client_max
        self.client_num     = 0
        self.timeout        = timeout
        self.countdown      = countdown
        self.lockobj        = threading.Lock()

        logging.info("%s is initialized successfully." % self)

    def __str__(self):
        return "Server[%s:%d]" % self.server_address

    def serve_forever(self):
        u"""別スレッドでリクエストを処理し続ける."""
        if self.serving_thread: return

        t = threading.Thread(target = self.server_thread_proc)
        t.setName( str(self) )
        t.start()
        self.serving_thread = t

    def server_thread_proc(self):
        u"""サーバースレッド用プロシージャ"""
        self.notify_event("start")
        while not self.terminated:
            self.handle_request()

    def server_close(self):
        u"""サーバーを終了する."""
        logging.info("%s terminating..." % self)
        self.notify_event("terminating")

        self.terminated = True
        ThreadingHTTPServer.server_close(self)

        logging.debug("%s waiting for threads terminate..." % self)

        # スレッドが全て終了するまで待機
        start_time   = time.time()
        elapsed_time = 0
        remains = self.client_num
        lastdiv = 0
        while elapsed_time < self.timeout:
            self.lockobj.acquire()
            try:
                remains = self.client_num
            finally:
                self.lockobj.release()

            if remains == 0: break

            div = int( elapsed_time / self.countdown )
            if div > lastdiv:
                lastdiv = div
                leftsec = self.timeout - elapsed_time
                logging.info("%s has %d sec left (%d clients remain)" %
                             (self, leftsec, remains))

            time.sleep(1)
            elapsed_time = time.time() - start_time

        if remains == 0:
            logging.info("%s terminated successfully." % self)
        else:
            logging.warning("%s terminated, but %d clients remained." %
                            (self, remains))

        self.notify_event("terminate")

    def process_request_thread(self, request, client_address):
        u"""リクエストをスレッドとして処理する."""

        connection = "%s:%d" % (
            socket.getfqdn(client_address[0]),
            client_address[1])

        # スレッドをリストに加えておく
        self.lockobj.acquire()
        try:
            self.connections.append(connection)
        finally:
            self.lockobj.release()

        self.notify_event("processing")

        ThreadingHTTPServer.process_request_thread(self, request, client_address)

        self.notify_event("processed")

        # スレッドをリストから取り除く
        self.lockobj.acquire()
        try:
            self.connections.remove(connection)
        finally:
            self.lockobj.release()

    def process_request(self, request, client_address):
        u"""
        リクエストを処理する.
        接続クライアント数が既に上限に達している場合は max_handler を
        それ以外なら req_handler をハンドラとして利用する.
        """
        logging.info("%s is processing request from %r." %
                     (self, client_address))

        self.lockobj.acquire()
        try:
            if self.client_num < self.client_max:
                self.RequestHandlerClass = self.req_handler
            else:
                self.RequestHandlerClass = self.max_handler
        finally:
            self.lockobj.release()

        self.notify_event("request", client_address)
        logging.debug("%s has selected %s for request handling." %
                      (self, repr(self.RequestHandlerClass)))

        ThreadingHTTPServer.process_request(self, request, client_address)

    def new_source(self, *args, **kwargs):
        u"""クライアントに配信するソースを返す"""
        if self.source_class and callable(self.source_class):
            return self.source_class(*args, **kwargs)
        else:
            logging.warn("%s can't create a new source." % self)

    def log_connections(self):
        u"""クライアント接続数をログに記録する."""
        logging.info("%s Connections: %d/%d" %
                     (self, self.client_num, self.client_max))

    def inc_client_num(self):
        u"""クライアント接続数を増やす."""
        self.lockobj.acquire()
        try:
            self.client_num += 1
        finally:
            self.lockobj.release()

        self.notify_event("client_num")
        self.log_connections()

    def dec_client_num(self):
        u"""クライアント接続数を減らす."""
        self.lockobj.acquire()
        try:
            self.client_num -= 1
        finally:
            self.lockobj.release()

        self.notify_event("client_num")
        self.log_connections()

#-------------------------------------------------------------------------------

#
# テスト用
#
if __name__ == "__main__":
    logging.basicConfig(level  = logging.DEBUG,
                        format = '%(asctime)s %(levelname)s %(message)s')
    logging.debug("MMSHTTPServer test starts.")
    server = MMSHTTPServer()
    server.timeout_on_termination = 60
    server.serve_forever()

    logging.debug("MMSHTTPServer started serving.")

    import time
    time.sleep(180)

    logging.debug("MMSHTTPServer is beging closed...")

    server.server_close()

    logging.debug("MMSHTTPServer has been closed.")
    logging.debug("MMSHTTPServer test finished.")
