# coding=utf-8

import os
import shutil
import sys

from kodi_six import xbmc, xbmcgui, xbmcvfs, xbmcaddon

from lib.common import ADDON, translatePath, log, showNotification, confirmationDialog, fontFilter

# setup paths
addon_folder = translatePath(os.path.join(ADDON.getAddonInfo('path')))
target_folder = translatePath("special://home/media/Fonts")
extra_folder = os.path.join(translatePath("special://profile/addon_data"), "fonts")
our_folder = os.path.join(addon_folder, "resources")

# parse settings, args
cleanup = ADDON.getSetting('cleanup') == "true" or "only_cleanup" in sys.argv or "cleanup_install" in sys.argv
install = "only_cleanup" not in sys.argv or "cleanup_install" in sys.argv

permission_issue = False

# cleanup action
if cleanup and os.path.exists(target_folder):
    log("Cleanup set, clearing {}", target_folder)
    try:
        shutil.rmtree(target_folder)
    except:
        showNotification("Couldn't install fonts. Possible permission issue on data folder.")
        sys.exit(0)

# create target and custom folder
for folder in [target_folder, extra_folder]:
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except:
            permission_issue = True
            pass

if not install:
    sys.exit(0)

log("Installing fonts to: {}", target_folder)
log("Looking for fonts in: {}", [extra_folder, our_folder])

# check for existing fonts
# add userdata/addon_data/fonts/*
extra_fonts = list(filter(fontFilter, os.listdir(extra_folder)))
log("Fonts in extra folder: {}", len(extra_fonts))

# add supplied fonts
our_fonts = list(filter(fontFilter, os.listdir(our_folder)))
log("Fonts in plugin folder: {}", len(our_fonts))

all_fonts = extra_fonts + our_fonts

# get installed fonts
installed_fonts = list(filter(fontFilter, os.listdir(target_folder)))

install_fonts = set(all_fonts) - set(installed_fonts)
log("Fonts left to install: {}", len(install_fonts))

if not install_fonts:
    showNotification("No fonts left to install.")
    sys.exit(0)

if not confirmationDialog("Install fonts?", "About to install {} fonts to {}".format(len(install_fonts), target_folder)):
    sys.exit(0)


fonts_installed = False
log("Installing fonts: {}", install_fonts)
for font in install_fonts:
    base = extra_folder if os.path.exists(os.path.join(extra_folder, font)) else our_folder
    try:
        shutil.copyfile(os.path.join(base, font), os.path.join(target_folder, font))
    except:
        permission_issue = True
        break

    fonts_installed = True

if permission_issue:
    showNotification("Couldn't install fonts. Possible permission issue on data folder.")

elif fonts_installed:
    showNotification("{} fonts installed. Please restart Kodi.".format(len(install_fonts)))
