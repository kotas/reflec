# -*- coding: utf_8 -*-
u"""
MMS-HTTP Streaming Source Classes

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

from client import MMSHTTPBufferedClient

__all__ = ["MMSHTTPBaseSource", "MMSHTTPClientSource",
           "MMSHTTPSourceFactory", "MMSHTTPClientSourceFactory"]

#-------------------------------------------------------------------------------
# MMSHTTPBaseSource
#-------------------------------------------------------------------------------

class MMSHTTPBaseSource(object):
    u"""
    MMSHTTP サーバーで配信するストリーミングソースの基底クラス.
    メソッド定義だけなので, サブクラスで実装する必要がある.
    """

    def is_ready(self):
        u"""
        ソースの準備ができているかどうかを返す.
        """
        pass

    def headers(self):
        u"""
        リクエストに対するレスポンスのヘッダー文字列を返す.
        ヘッダーの終端を表す空行もついている.
        """
        pass

    def info_packet(self):
        u"""
        ストリーミングの情報パケット ($D) を MMSHTTPPacket オブジェクトで返す.
        """
        pass

    def iter_streaming(self):
        u"""
        ストリーミングのパケットオブジェクトを順番に処理するイテレータを返す.
        """
        pass

    def __iter__(self):
        return self.iter_streaming()

#-------------------------------------------------------------------------------
# MMSHTTPClientSource
#-------------------------------------------------------------------------------

class MMSHTTPClientSource(MMSHTTPBaseSource):
    u"""
    mmshttp.client.MMSHTTPBufferedClient によって受信しているストリーミングを
    そのまま中継するソース.
    """

    def __init__(self, client):
        self.client = client

    def is_ready(self):
        u"""
        ソースの準備ができているかどうかを返す.
        """
        if self.client.started and not self.client.terminated:
                return True
        else:
                return False

    def headers(self):
        u"""
        リクエストに対するレスポンスのヘッダー文字列を返す.
        ヘッダーの終端を表す空行もついている.
        """
        header =  self.client.status_line + "\r\n"
        header += "".join(self.client.header.headers)
        header += "\r\n"
        return header

    def info_packet(self):
        u"""
        ストリーミングの情報パケット ($D) を MMSHTTPPacket オブジェクトで返す.
        """
        return self.client.info_packet

    def iter_streaming(self):
        u"""
        ストリーミングのパケットオブジェクトを順番に処理するイテレータを返す.
        """
        return self.client.iter_streaming()

#-------------------------------------------------------------------------------
# MMSHTTPSourceFactory
#-------------------------------------------------------------------------------

class MMSHTTPSourceFactory(object):
    u"""
    MMS-HTTP プロトコルの配信に使われるソースをリクエストに応じて作成するクラス.
    """

    def __init__(self, source_class, *args, **kwargs):
        self.source_class  = source_class
        self.source_args   = args
        self.source_kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.create(*args, **kwargs)

    def create(self, *args, **kwargs):
        u"""
        ソースのインスタンスを作成する.
        """

        # 引数を合成
        args = self.source_args + args
        kw   = self.source_kwargs.copy()
        kw.update(kwargs)

        return self.source_class(*args, **kw)

#-------------------------------------------------------------------------------
# MMSHTTPClientSourceFactory
#-------------------------------------------------------------------------------

class MMSHTTPClientSourceFactory(MMSHTTPSourceFactory):
    u"""
    リクエストに応じて MMSHTTPClientSource を作成するクラス.
    """

    def __init__(self, client):
        MMSHTTPSourceFactory.__init__(self, MMSHTTPClientSource, client)
