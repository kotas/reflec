# -*- coding: utf_8 -*-
u"""
Win32COM Utility Classes

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

COM オブジェクトをラッピングして利用する為のクラスを提供する.

COMObject を継承したクラスを定義する事で, COM オブジェクトクラスを作成できる.
そのクラスに @comevent() デコレーターをつけたメソッドを定義する事で
イベントハンドラを記述する事ができる. また, イベントメッセージを処理する
process_message() と, メッセージループを行う message_loop() メソッドを提供する.

また、comevent デコレータに引数の型を指定する事ができる. 型を指定した場合,
イベントハンドラに渡されたパラメータが自動的にその型にキャストされる.

制限として, COM オブジェクトクラスをインスタンス化する際に, クラスを直に呼び出す
のではなく, クラスメソッドである create() を利用する必要がある.
"""

import win32com.client
import win32event
import pythoncom
import time

__all__ = ["comevent", "COMObject"]

def comevent(*types):
    u"""
    COM オブジェクトのイベントハンドラを表すデコレーター.
    型名を指定しておくと, 自動的に渡されたパラメータをキャストする.
    """
    def decorator(f):
        def wrapper(self, *args):
            new_args = []
            for i, v in enumerate(args):
                if len(types) > i:
                    new_args.append(win32com.client.CastTo(v, types[i]))
                else:
                    new_args.append(v)
            ret = f(self, *new_args)
            win32event.SetEvent(self.event)
            return ret
        return wrapper
    return decorator


class COMObject(object):
    u"""
    win32com を利用して COM オブジェクトをラッピングするクラス.
    このクラスを継承してイベントハンドラを記述する事ができる.

    インスタンス化する際には COMObject() を直接呼ばずに, クラスメソッドである
    COMObject.create() を呼び出すこと.
    """

    clsid = None

    @classmethod
    def create(klass, clsid = None):
        if not clsid and klass.clsid: clsid = klass.clsid
        return win32com.client.DispatchWithEvents(clsid, klass)

    def __init__(self):
        self.event = win32event.CreateEvent(None, 0, 0, None)

    def process_message(self, timeout = 0):
        start = time.clock()
        while True:
            rc = win32event.MsgWaitForMultipleObjects( (self.event, ),
                    0, 250, win32event.QS_ALLEVENTS)
            if rc == win32event.WAIT_OBJECT_0:
                return True
            if timeout > 0 and (time.clock() - start) > timeout:
                return False
            pythoncom.PumpWaitingMessages()

    def message_loop(self):
        while True:
            self.process_message()

