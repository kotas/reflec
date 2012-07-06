# -*- coding: utf_8 -*-
u"""
Twitter API Simple Wrapper

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

Twitter API のシンプルなラッパー.
"""

import re
import sys
import urllib
import urllib2
import cookielib
try:
    from xml.etree import ElementTree
except:
    from elementtree import ElementTree

#-------------------------------------------------------------------------------
# Twitter
#-------------------------------------------------------------------------------

class Twitter(object):
    u"""
    Twitter API のシンプルなラッパークライアント.
    """

    uri = "http://twitter.com/"
    user_agent = "ReflectTwitterPlugin/1.0"

    def __init__(self, username, password):
        self.username = username
        self.password = password

        handler = urllib2.HTTPBasicAuthHandler()
        if self.username and self.password:
            handler.add_password("Twitter API", self.uri, username, password)
        self.opener = urllib2.build_opener(handler)
        self.opener.addheaders = [('User-Agent', self.user_agent)]

    def call(self, path, **params):
        uri = self.uri + path + ".xml"

        for k, v in params.items():
            if v == None:
                del params[k]

        response = None
        if params:
            data = urllib.urlencode(params)
            response = self.opener.open(uri, data)
        else:
            response = self.opener.open(uri)

        if response:
            xml = response.read()
            print xml
            return ElementTree.fromstring(xml)
        else:
            return False

    def status_update(self, status):
        r = self.call("statuses/update", status = status)
        return Status(r) if r else False

    def status_friends(self, id = None):
        p = "statuses/friends"
        if id: p += "/%s" % id
        r = self.call("statuses/friends")
        return [User(e) for e in r.findall("user")]

    def status_followers(self, id = None):
        r = self.call("statuses/followers", id = id)
        return [User(e) for e in r.findall("user")]

    def status_featured(self):
        r = self.call("statuses/featured")
        return [User(e) for e in r.findall("user")]

    def friendships_create(self, id):
        r = self.call("friendships/create/%s" % id)

    def friendships_destroy(self, id):
        r = self.call("friendships/destroy/%s" % id)

    def logined_opener(self):
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        uri = self.uri + "sessions"
        params = urllib.urlencode({
            "username_or_email": self.username,
            "password": self.password,
            "commit": "Sign In!"
        })
        res = opener.open(uri, params)
        if res.geturl().endswith("sessions"):
            raise AuthenticateError()

        return opener

    def accept_followers(self):
        opener = self.logined_opener()
        uri = self.uri + "friend_requests"
        res = opener.open(uri)
        if res.geturl().endswith("login"):
            raise AuthenticateError()

        user_ids = []
        for m in re.finditer(r'"/(friend_requests/accept/([0-9]+))"', res.read()):
            uri = self.uri + m.group(1)
            res = opener.open(uri)
            user_ids.append(m.group(2))
        return user_ids

class Status(object):

    def __init__(self, elem, child_user = True):
        for s in ["created_at", "id", "text", "source"]:
            text = elem.findtext(s)
            if text:
                if isinstance(text, unicode):
                    text = text.encode(sys.getfilesystemencoding())
                if s == "id":
                    text = int(text)
            setattr(self, s, text)

        self.user = User(elem.find("user"), False) if child_user else None

    def __str__(self):
        if self.user:
            return "%s: %s" % (self.user, self.text)
        else:
            return self.text

    def __repr__(self):
        if self.user:
            return "<Status: %d, %s, %s, User: %s>" % (
                self.id, self.text, self.created_at, self.user)
        else:
            return "<Status: %d, %s, %s>" % (
                self.id, self.text, self.created_at)

    def __cmp__(self, other):
        return self.id - other.id

    def __hash__(self):
        return self.id

class User(object):
    
    def __init__(self, elem, child_status = True):
        for s in ["id", "name", "screen", "location", "description",
                  "profile_image_url", "url", "protected"]:
            text = elem.findtext(s)
            if text:
                if isinstance(text, unicode):
                    text = text.encode(sys.getfilesystemencoding())
                if s == "id":
                    text = int(text)
                if s == "protected":
                    text = text != "false"
            setattr(self, s, text)

        self.status = Status(elem.find("status"), False) if child_status else None

    def __str__(self):
        if self.status:
            return "%s: %s" % (self.name, self.status)
        else:
            return self.name

    def __repr__(self):
        if self.status:
            return "<User: %d, %s, %s, %s, Status: %s>" % (
                self.id, self.name, self.screen, self.description, self.status)
        else:
            return "<User: %d, %s, %s, %s>" % (
                self.id, self.name, self.screen, self.description)

    def __cmp__(self, other):
        return self.id - other.id

    def __hash__(self):
        return self.id

class AuthenticateError(Exception):
    pass

#-------------------------------------------------------------------------------

#
# テスト用
#
if __name__ == "__main__":
    tw = Twitter("example", "")

    #tw.accept_followers()

    """
    print tw.status_featured()

    followers = tw.status_followers()
    friends = tw.status_friends()

    notadded = []
    for user in followers:
        if user not in friends:
            notadded.append(user)
            print user

    for user in notadded:
        tw.friendships_create(user.id)
    """

    #print tw.status_update("更新のテストー")
