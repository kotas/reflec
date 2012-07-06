# -*- coding: utf_8 -*-
u"""
MMS-HTTP ASF Format Reader

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import struct

__all__ = ["ASFReader"]

#-------------------------------------------------------------------------------
# ASFReader
#-------------------------------------------------------------------------------

class ASFReader(object):
    u"""
    ASF フォーマットを読み込んで, それに含まれる
    メタ情報（タイトル、製作者など）を取り出すクラス.
    """

    def __init__(self, fp = None):
        self.media_info = { }
        self.ext_info   = { }
        self.fp         = fp
        if fp: self.read()

    def read(self, fp = None):
        u"""
        渡されたファイルオブジェクトからメタ情報を読み込む.
        読み込めなかった場合は EOFError 例外を生成する.
        """
        if fp:
            self.fp = fp
        elif not self.fp:
            raise EOFException("file pointer is not set.")

        if self.fp.closed:
            raise EOFException("file pointer is closed.")

        return self._read_object()

    def close(self):
        u"""ファイルポインタを解放する."""
        self.fp = None

    def _read_object(self):
        u"""
        ASF ファイルに含まれるオブジェクトを1つ読み込む.
        """
        # オブジェクトの先頭にある 16 byte の GUID と 64bit のデータ長を読み込む
        guid, size = self._read_format("16sQ")

        # GUID に従ってオブジェクトを処理する
        if self._object_process_table.has_key(guid):
            # オブジェクトを処理するメソッドが登録されている
            func, args_format = self._object_process_table[guid]

            # フォーマットに従ってデータから引数を作成する
            args = ()
            if args_format:
                args = self._read_format(args_format)

            # オブジェクトを処理するメソッドに渡す
            return func(self, *args)
        else:
            # オブジェクトを処理できるメソッドがないので残りはスキップ
            self.fp.seek(size - struct.calcsize("16sQ"), 1)
            return False

    def _read_format(self, format):
        u"""
        フォーマットに従ってデータを読み込んで unpack したものを返す.
        読み込めなかった場合は EOFError 例外を生成する.
        """
        size = struct.calcsize(format)
        data = self.fp.read(size)
        if not data: raise EOFError("can't read a complete block.")
        return struct.unpack(format, data)

    def _read_string(self, length):
        u"""
        指定した長さの Unicode 文字列を読み込んで返す.
        読み込めなかった場合は EOFError 例外を生成する.
        """
        text = self.fp.read(length)
        if not text: raise EOFError("can't read a complete string.")
        if text[-2:] == "\x00\x00": text = text[:-2]  # ターミネータを削除
        return unicode(text, encoding = 'utf_16_le', errors = 'ignore')

    # 以下は各オブジェクト別の処理

    def _read_header_object(self, object_num, reserved1, reserved2):
        u"""
        ASF Header Object の処理.
        """
        # 含まれるオブジェクトを全て読み込む
        if object_num > 0:
            while object_num > 0:
                object_num -= 1
                self._read_object()
            return True
        else:
            return False

    def _read_content_description_object(self, *lengths):
        u"""
        ASF Content Description Object の処理.
        """
        keys = ("title", "author", "copyright", "description", "rating")
        for key, size in zip(keys, lengths):
            if size > 0:
                self.media_info[key] = self._read_string(size)

    def _read_extended_content_description_object(self, descriptors_num):
        u"""
        ASF Extended Content Description Object の処理.
        """
        while descriptors_num > 0:
            descriptors_num -= 1

            size = (self._read_format("H"))[0]
            if size <= 0: continue
            key = self._read_string(size)

            desctype, size = self._read_format("HH")
            data = None
            if desctype in self._descriptor_reader:
                data = self._descriptor_reader[desctype](self, size)
            else:
                data = self.fp.read(size)

            if not data: EOFError("can't read a descriptor block.")
            self.ext_info[key] = data

            # 「規制」は rating としても登録する
            if key == "WM/ParentalRating":
                self.media_info["rating"] = self.ext_info[key]

    # Descriptor の種類による処理分け
    _descriptor_reader = {
        0: lambda self, size: self._read_string(size),           # STRING
        1: lambda self, size: self.fp.read(size),                # BYTEARRAY
        2: lambda self, size: (self._read_format("I"))[0] != 0,  # BOOL
        3: lambda self, size: (self._read_format("I"))[0],       # DWORD
        4: lambda self, size: (self._read_format("Q"))[0],       # QWORD
        5: lambda self, size: (self._read_format("H"))[0],       # WORD
    }

    # オブジェクトの GUID から処理するメソッドを決定するためのテーブル
    _object_process_table = {

        # ASF Header Object のフォーマット
        # [#] [名前]                     [型]    [サイズ]  [struct用]
        # [0] Number of Header Objects   DWORD   4byte     I
        # [1] Reserved1                  BYTE    1byte     B
        # [2] Reserved2                  BYTE    1byte     B
        "\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C": (
            _read_header_object, "IBB"
        ),

        # ASF Content Description Object のフォーマット
        # [#] [名前]                     [型]    [サイズ]  [struct用]
        # [0] Title Length               WORD    2byte     H
        # [1] Author Length              WORD    2byte     H
        # [2] Copyright Length           WORD    2byte     H
        # [3] Description Length         WORD    2byte     H
        # [4] Rating Length              WORD    2byte     H
        #  -  (Title, Author, Copyright, Description, Rating の文字列)
        "\x33\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C": (
            _read_content_description_object, "5H"
        ),

        # ASF Extended Content Description Object のフォーマット
        # [#] [名前]                     [型]    [サイズ]  [struct用]
        # [0] Content Descriptors Count  WORD    2byte     H
        #  -  (Content Descriptors)
        "\x40\xA4\xD0\xD2\x07\xE3\xD2\x11\x97\xF0\x00\xA0\xC9\x5E\xA8\x50": (
            _read_extended_content_description_object, "H"
        ),

    }

if __name__ == "__main__":
    import zlib, base64, StringIO

    # サンプルの ASF データで試してみる
    example = """\
eNrtWGlIVFEU/t7Ma8wQ9bXvjf2QFrPr0iKBODljihqipdWUNulU0zLGmEULJFkhuEQUbUSLTYtaBE
MhtJAQLaOUZv3IiLKFaKMMIiSL6bxlxtG0P/2L9z3Oveeee893zr3v/Dos3FVctbJZONuGWqx4sK5j
KCQMJOE0Mb12j8mbmIkgBGMKaS72k7UzPdbBhk2wIgx65Hr0yIYB6chACjJhIlsqaWn0mWgNZLEkZm
GlbD+jSJ54j1sb7xnjCfQAa1i+smNnL9kF5mbvmTZ3sXWOtbQgjTUU5jAjG+8ZSycfFHduq0x6KFTu
xPJD7mpXuJKbBhyeuMW58RaPU8/qKubVNAtVb9AQpM+yrlZOfb0X+G1EnN1U/b1rfuq5kpCJw2R7R9
eVz69W3+U8BPSBsiHyHEjiHCBLdeUAXNHezIsU47yW44wS5HNC66O6q6L9rWzX4WMoUJOUuL39y89U
1+S4+OeGpbvDFHYOujWwkNJ05u1Qx53oxNIjNbZMnXnJIvSNw9e6U/LXzbyXsCd689r74W3fz/u4/H
X4HhloGTzEl3bGgRt3duwJSCk9fXdLWH3MRY1kX1b+NXyX6dO8E3nB1gl8pnu015v70NR5+5J5c/Ku
VbUVxh9pjU+VHV5iCyJ+kSEFRVRIc6WSkePE0qgjMVKpbaKSy6c5EYWwYyWNDqyn17NL1gUk67GBCt
OCjaSDii9ayb0/fs0/8WdRuQMbH+tGvmgMNDmvHq1rOlj7LjQEKlSoUKFChQoVKlSoUKFCxX+PfQHP
6uv9GiAOxZ5w3NaZbm4Wzv9CSd5S49SM+7du7rU0C+Uu1OLyK73Xf6y3GQWxAWXhNDBeAIpGiD2OUA
wCyoAJaJtIJ8y8mef+jLhbYWr4Muq6f0TkdOkX+q8VzOrucVDEBGLsEFcRiBDTVpYcRiInPTumryvz
hhIuwdnSGvC6VTjUgZPu3PMZTmVPSxfKQTqSkAUjUpENKxwogk1qMsgXjgJDJEn3GEvjDKk5MbqH93
zytqJAEhHDFZ9In6/4AUE9Wh0ayN2hhMyHe8ZFtQinnZSjNvn7NyVHQy+7RvKh+1KWdopUiM3Epqc8
xLg2WEg3oFjSC0mPo9hR5DOF9FjMpnEtVmAD+URIlljJkoyt0rpIap84SETfScQ0nTKdTHoUppGXhU
6I0RJ92Vs4jm76t2yyaS5QGOOUNhgv/a+ZvTqa0f30A73/kuN+A6b7VsY="""

    example = zlib.decompress( base64.b64decode(example) )

    reader = ASFReader( StringIO.StringIO(example) )
    reader.close()

    print "*** Media Info ***"
    for k, v in reader.media_info.items():
        print "%-20s : %s" % (k, v)

    print "*** Extended Info ***"
    for k, v in reader.ext_info.items():
        print "%-20s : %s" % (k, v)

