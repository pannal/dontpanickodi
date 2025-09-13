# coding=utf-8

import os
import shutil
import sys

from lib.common import (ADDON, translatePath, log, _, showNotification, confirmationDialog, fontFilter, contextMenu,
                        multiSelect)

# setup paths
addon_folder = translatePath(os.path.join(ADDON.getAddonInfo('path')))
target_folder = translatePath("special://home/media/Fonts")
extra_folder = os.path.join(translatePath("special://profile/addon_data"), "fonts")
our_folder = os.path.join(addon_folder, "resources")

permission_issue = False

action = contextMenu([_(32006, "Font management"),
                      _(32005, "Install all"),
                      _(32004, "Cleanup and install all"),
                      _(32003, "Cleanup installed fonts")])

if action == -1:
    sys.exit(0)

# poor man's action management
cleanup = action in (2, 3)
install = action in (0, 1, 2)
selective = action == 0

# cleanup action
if cleanup and os.path.exists(target_folder):
    log("Cleanup set, clearing {}", target_folder)
    try:
        shutil.rmtree(target_folder)
        showNotification(_(32015, "Fonts cleaned."))
    except:
        permission_issue = True

# create target and custom folder
for folder in [target_folder, extra_folder]:
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except:
            permission_issue = True
            break

if permission_issue:
    showNotification(_(32009, "Couldn't install/remove fonts. Possible permission issue on data folder."))
    sys.exit(0)

if not (install or selective):
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
install_fonts = []
remove_fonts = []

# font management
if selective:
    combined_fonts = sorted(list(set(all_fonts + installed_fonts)))
    preselect = [i for i, font in enumerate(combined_fonts) if font in installed_fonts]
    selection = multiSelect(_(32007, "Install/uninstall fonts"), combined_fonts, preselect=preselect)
    if not selection:
        sys.exit(0)

    install_fonts = list(set([combined_fonts[index] for index in selection]) - set(installed_fonts))
    remove_fonts = [combined_fonts[i] for i in set(preselect) - set(selection)]
else:
    install_fonts = list(set(all_fonts) - set(installed_fonts))

log("Fonts left to install: {}", len(install_fonts))

if not (install_fonts or remove_fonts):
    showNotification(_(32013, "Nothing to do."))
    sys.exit(0)

confirm_body = []
if install_fonts:
    confirm_body.append(_(32011, "Install: {}").format(", ".join(install_fonts)))
if remove_fonts:
    confirm_body.append(_(32012, "Remove: {}").format(", ".join(remove_fonts)))
confirm_body.append(_(32014, "Target: {}").format(target_folder))

if not confirmationDialog(_(32008, "Apply changes?"), "\n".join(confirm_body)):
    sys.exit(0)


fonts_installed = False
if install_fonts:
    log("Installing fonts: {}", install_fonts)
    for font in install_fonts:
        base = extra_folder if os.path.exists(os.path.join(extra_folder, font)) else our_folder
        try:
            shutil.copyfile(os.path.join(base, font), os.path.join(target_folder, font))
        except:
            permission_issue = True
            break

    fonts_installed = True

fonts_removed = False
if remove_fonts:
    log("Removing fonts: {}", remove_fonts)
    for font in remove_fonts:
        try:
            os.remove(os.path.join(target_folder, font))
        except:
            permission_issue = True
            break

    fonts_removed = True

if permission_issue:
    showNotification(_(32009, "Couldn't install/remove fonts. Possible permission issue on data folder."))

elif fonts_installed or fonts_removed:
    showNotification(_(32010, "{} fonts installed, {} removed. Please restart Kodi.").format(len(install_fonts), len(remove_fonts)))
