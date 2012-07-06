# -*- coding: utf_8 -*-
u"""
Event Utility Classes

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

__all__ = ["EventHolder"]

#-------------------------------------------------------------------------------
# EventHolder
#-------------------------------------------------------------------------------

GLOBAL_EVENT = "__global__"

class EventHolder(object):
    u"""
    イベントを処理・登録する事ができるクラス.

    1つのイベントを処理するイベントハンドラに対して
    全てのイベントを処理するグローバルイベントハンドラも登録できる.

    例えば、イベント 'click' が発生した場合、まず add_event_handler で
    'click' イベントに対して登録されているイベントハンドラが順番に実行される.
    その後、add_global_event_handler にて登録されたグローバルイベントハンドラが
    順番に実行される.（ここでいう順番とは, 登録された順番のことである）

    イベントハンドラが 'on_イベント名'（on_click など）という名前の
    メソッドを持っている場合, そのメソッドが呼び出される.
    メソッドが見つからず, イベントハンドラが呼び出し可能（callable）な場合は
    イベントハンドラが直接実行される.
    """

    def __init__(self, *event_names):
        self._event_handlers = { GLOBAL_EVENT: [] }

        if event_names:
            self.register_event(*event_names)

    def register_event(self, *event_names):
        u"""イベントを登録する."""
        for name in event_names:
            if name not in self._event_handlers:
                self._event_handlers[name] = []

    def add_global_event_handler(self, *handlers):
        u"""グローバルなイベントハンドラを登録する."""
        self.add_event_handler(GLOBAL_EVENT, *handlers)

    def remove_global_event_handler(self, *handlers):
        u"""グローバルなイベントハンドラの登録を解除する."""
        self.remove_event_handler(GLOBAL_EVENT, *handlers)

    def add_event_handler(self, event_name, *handlers):
        u"""指定したイベントのみを処理するイベントハンドラを登録する."""
        self._event_handlers[event_name].extend(handlers)

    def remove_event_handler(self, event_name, *handlers):
        u"""指定したイベントを処理するイベントハンドラの登録を解除する."""
        m = self._event_handlers[event_name]
        for handler in handlers:
            m.remove(handler)

    def map_event_handlers(self, mappings):
        u"""イベントとイベントハンドラ関数の対応を複数登録する."""
        if hasattr(mappings, "items") and callable(mappings.items):
            mappings = mappings.items()
        for name, handler in mappings:
            self.add_event_handler(name, handler)

    def notify_event(self, event_name, *args, **kwargs):
        u"""イベントを登録されているイベントハンドラに通知する."""
        handlers  = self._event_handlers[event_name]    \
                  + self._event_handlers[GLOBAL_EVENT]
        event_name = "on_%s" % event_name
        try:
            for handler in handlers:
                try:
                    if hasattr(handler, event_name):
                        getattr(handler, event_name)(self, *args, **kwargs)
                    elif callable(handler):
                        handler(self, *args, **kwargs)
                    else:
                        logging.warning("Notifying %s to %s failed." %
                                        (event_name, repr(handler)))
                except:
                    logging.warning(
                        "Notifying %s to %s failed:\n%s\n%s\n%s" %
                        (event_name, repr(handler),
                         "-"*40, traceback.format_exc().strip(), "-"*40))
        except StopIteration:
            pass
        return

#-------------------------------------------------------------------------------

#
# テスト用
#
if __name__ == "__main__":
    holder = EventHolder("test", "hige", "huge")
    holder.register_event("ahya", "uhyo")

    def global_handler(sender, value):
        print "Global Handler Called: ", value

    def hige_handler(sender, value):
        print "Hige Handler Called: ", value

    def ahya_handler(sender, value):
        print "Ahya Handler Called: ", value

    holder.add_global_event_handler(global_handler)
    holder.add_event_handler("hige", hige_handler)
    holder.add_event_handler("ahya", ahya_handler)

    holder.notify_event("hige", "Hige Testing!")
    holder.notify_event("ahya", "Ahya Testing!")
    holder.notify_event("test", "Test Testing!")

    holder.remove_event_handler("hige", hige_handler)
    holder.notify_event("hige", "Hige Testing 2!")

    class TestHandler1:
        def on_test(self, sender, value):
            print "TestHandler1.on_test Called: ", value
        def on_hige(self, sender, value):
            print "TestHandler1.on_hige Called: ", value

    class TestHandler2:
        def on_test(self, sender, value):
            print "TestHandler2.on_test Called: ", value
        def __call__(self, sender, value):
            print "TestHandler2.__call__ Called: ", value

    handler1, handler2 = TestHandler1(), TestHandler2()
    holder.add_global_event_handler(handler1)
    holder.add_global_event_handler(handler2)

    holder.notify_event("test", "Another Test Testing!")
    holder.notify_event("hige", "Another Hige Testing!")
    holder.notify_event("ahya", "Another Ahya Testing!")

    holder.remove_global_event_handler(handler2)
    holder.add_event_handler("test", handler2)

    holder.notify_event("test", "Yet another Test Testing!")
    holder.notify_event("hige", "Yet another Hige Testing!")
    holder.notify_event("ahya", "Yet another Ahya Testing!")

