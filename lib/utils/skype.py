# -*- coding: utf_8 -*-
u"""
Skype Class

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito
"""

import sys
import logging

from com import *

__all__ = ["Skype"]

#-------------------------------------------------------------------------------
# Skype
#-------------------------------------------------------------------------------

class Skype(COMObject):
    u"""
    Skype4COM の COM オブジェクトをラッピングするクラス.
    """

    clsid = "Skype4COM.Skype"

    encoding = sys.getfilesystemencoding()

    def set_options(self, **kwargs):
        u"""設定を上書きする."""
        self.__dict__.update(kwargs)

    def ensure_running(self):
        u"""起動しているか確認する."""
        if not self.Client.IsRunning:
            self.Client.Start()
            logging.info("Running Skype...")
        else:
            logging.debug("Skype is running.")

    def ensure_attachment(self):
        u"""Skype API への接続を行う."""
        try:
            self.Attach()
            logging.debug("Connected to Skype API.")
        except:
            logging.error("Can't connect to Skype API.")
            raise

    @comevent()
    def OnAttachmentStatus(self, status):
        logging.debug("Skype AttachmentStatus = %s" %
            self.Convert.AttachmentStatusToText(status).encode(self.encoding))
