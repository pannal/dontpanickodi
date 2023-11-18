from __future__ import absolute_import
from . import kodigui
from lib import util
from kodi_six import xbmcgui


class BusyWindow(kodigui.BaseDialog):
    xmlFile = 'script-plex-busy.xml'
    path = util.ADDON.getAddonInfo('path')
    theme = 'Main'
    res = '1080i'
    width = 1920
    height = 1080


class BusyClosableWindow(BusyWindow):
    ctx = None

    def onAction(self, action):
        if action in (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK, xbmcgui.ACTION_STOP):
            self.ctx.shouldClose = True


class BusyClosableMsgWindow(BusyClosableWindow):
    xmlFile = 'script-plex-busy_msg.xml'

    def setMessage(self, msg):
        self.setProperty("message", msg)


def dialog(msg='LOADING', condition=None):
    def methodWrap(func):
        def inner(*args, **kwargs):
            w = BusyWindow.create()
            try:
                return func(*args, **kwargs)
            finally:
                w.doClose()
                del w
                util.garbageCollect()

        return condition and condition() and inner or func
    return methodWrap


def widthDialog(method, msg, *args, **kwargs):
    return dialog(msg or 'LOADING')(method)(*args, **kwargs)


class BusyMsgContext(object):
    w = None
    shouldClose = False

    def __enter__(self):
        self.w = BusyClosableMsgWindow.create()
        self.w.ctx = self
        return self

    def setMessage(self, msg):
        self.w.setMessage(msg)

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            util.ERROR()

        self.w.doClose()
        del self.w
        self.w = None
        util.garbageCollect()
        return True
