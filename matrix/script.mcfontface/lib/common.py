# coding=utf-8

# noinspection PyUnresolvedReferences
from kodi_six import xbmc, xbmcgui, xbmcvfs, xbmcaddon


try:
    translatePath = xbmcvfs.translatePath
except:
    translatePath = xbmc.translatePath


ADDON = xbmcaddon.Addon()


def log(message, *a, **kw):
    msg = message.format(**kw) if kw else message.format(*a) if a else message
    xbmc.log(msg, xbmc.LOGINFO)


def _(_id, default):
    return ADDON.getLocalizedString(_id) or default


def showNotification(message, time_ms=5000, icon_path=None, header=ADDON.getAddonInfo('name')):
    try:
        icon_path = icon_path or translatePath(ADDON.getAddonInfo('icon'))
        xbmc.executebuiltin('Notification({0},"{1}",{2},{3})'.format(header, message, time_ms, icon_path))
    except RuntimeError:  # Happens when disabling the addon
        log(message)


def confirmationDialog(title, message):
    return xbmcgui.Dialog().yesno(title, message)


def fontFilter(font):
    return font.endswith(".ttf") or font.endswith(".otf")


def contextMenu(*options, **kwargs):
    return xbmcgui.Dialog().contextmenu(*options, **kwargs)


def multiSelect(heading, options, autoclose=False, preselect=None, useDetails=False):
    return xbmcgui.Dialog().multiselect(heading, options, autoclose=autoclose, preselect=preselect, useDetails=useDetails)
