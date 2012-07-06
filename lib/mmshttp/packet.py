# -*- coding: utf_8 -*-
u"""
MMS-HTTP Packet Classes

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

from StringIO import StringIO

import asf

__all__ = ["MMSHTTPPacket", "MMSHTTPInfoPacket"]

#-------------------------------------------------------------------------------
# MMSHTTPPacket
#-------------------------------------------------------------------------------

class MMSHTTPPacket(object):
    u"""
    MMS-HTTP プロトコルで配信されるパケット1つを表すクラス.
    """

    MARKER_MEDIA_INFO     = "$H"
    MARKER_MEDIA_DATA     = "$D"
    MARKER_MEDIA_DATA2    = "?D"
    MARKER_END_OF_STREAM  = "$E"
    MARKER_CHANGING_MEDIA = "$C"
    MARKER_META_DATA      = "$M"
    MARKER_PAIR_DATA      = "$P"

    def __init__(self, fp = None):
        self.raw_packet = ""
        self.marker     = ""
        self.data_size  = 0
        self.data       = ""

        if fp: self.receive(fp)

    def __repr__(self):
        return "<Packet %s Length: %d>" % (self.marker, self.data_size)

    def __str__(self):
        return self.raw_packet

    def receive(self, fp):
        u"""
        渡されたファイルポインタからパケットを読み込む.
        読み込みに失敗した場合は EOFError 例外を発生させる.
        """
        if not fp or fp.closed: return False

        # マーカー（パケットの種類を表す文字列）を受信
        marker = fp.read(2)
        if not marker: raise EOFError("can't receive a marker.")
        self.raw_packet += marker
        self.marker      = marker

        # パケットの残りデータサイズを受信
        sizebin = fp.read(2)
        if not sizebin: raise EOFError("can't receive a packet size.")
        self.raw_packet += sizebin
        self.data_size   = ord(sizebin[1]) << 8 | ord(sizebin[0])

        # パケットのデータを全て読み込む
        data = fp.read(self.data_size)
        if not data: raise EOFError("can't receive a data.")
        self.raw_packet += data
        self.data        = data

        return True

    def is_info(self):
        u"""パケットが情報パケットである場合は真を返す."""
        return self.marker == self.MARKER_MEDIA_INFO

    def is_last(self):
        u"""パケットが最後のパケットである場合は真を返す."""
        return self.marker == self.MARKER_END_OF_STREAM


    class StreamingIterator(object):
        u"""
        MMSHTTPPacket のストリーミングを受信する為のイテレーター.
        """

        def __init__(self, fp):
            self.fp = fp

        def __iter__(self):
            return self

        def next(self):
            if not self.fp:
                raise StopIteration()

            p = MMSHTTPPacket(self.fp)
            if p.is_last(): self.fp = None
            return p

#-------------------------------------------------------------------------------
# MMSHTTPInfoPacket
#-------------------------------------------------------------------------------

class MMSHTTPInfoPacket(MMSHTTPPacket):
    u"""
    MMS-HTTP プロトコルで配信されるパケットのうち
    ストリーミングのメタ情報などが含まれる情報パケット($H)を表すクラス.
    """

    def __init__(self, fp = None):
        self.media_info = { }
        self.ext_info = { }
        MMSHTTPPacket.__init__(self, fp)

    def receive(self, fp):
        u"""
        渡されたファイルポインタからパケットを読み込む.
        読み込みに失敗した場合は EOFError 例外を発生させる.
        """
        r = MMSHTTPPacket.receive(self, fp)
        if not r: return r

        # パケットの先頭についている MMS Pre-Header (8バイト) をとばす
        data = StringIO( self.data[8:] )
        try:
            reader = asf.ASFReader(data)
            self.media_info = reader.media_info
            self.ext_info   = reader.ext_info
            reader.close()
        except EOFError:
            pass

        return r
