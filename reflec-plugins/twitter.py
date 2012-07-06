# -*- coding: utf_8 -*-
u"""
Twitter Plug-in

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

開始時に Twitter で中継の開始を通知するプラグイン.
ADD されていた場合、自動的に承認する.
Twitter API を利用する.
"""

import sys
import logging

from reflec.plugin import ReflecBasePlugin
from utils.twitter import Twitter, AuthenticateError

__load__ = ["TwitterPlugin"]

#-------------------------------------------------------------------------------
# TwitterPlugin
#-------------------------------------------------------------------------------

class TwitterPlugin(ReflecBasePlugin):
    u"""
    ストリーミング開始時に Twitter で中継の開始を通知するプラグイン.
    """

    encoding = sys.getfilesystemencoding()

    def app_start(self, app):
        opt = self.app.option.get("twitter")
        if not opt:
            logging.error("Twitter: No options found.")
            return
        if not opt.username or not opt.password:
            logging.error("Twitter: No Twitter account is set.")

        self.info = {  }
        for k, v in opt.dict().items():
            if k.startswith("no_"):
                self.info[ k[3:] ] = v

        self.twitter = Twitter(opt.username, opt.password)
        self.msg = opt.msg_notify

    def client_start_streaming(self, client):
        rating = self.client.media_info.get("rating", "").lower()
        if rating.find("yes") >= 0:
            logging.info("Twitter: Twitter notification is blocked by a user.")
            return

        info = self.info.copy()
        for k, v in self.client.media_info.items():
            if isinstance(v, unicode):
                v = v.encode(self.encoding)
            info[k] = v

        info["host"] = self.server.server_address[0]
        info["port"] = self.server.server_address[1]
        info["address"] = "%s:%d" % (info["host"], info["port"])

        try:
            self.twitter.accept_followers()
        except AuthenticateError:
            logging.warning("Twitter: failed to accept followers." +
                            " Maybe authentication has failed.")

        msg = self.msg % info
        success = False
        try:
            success = self.twitter.status_update(msg)
        except:
            pass

        if not success:
            logging.error("Twitter: failed to update status.")
