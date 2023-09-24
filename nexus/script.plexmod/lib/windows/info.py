from __future__ import absolute_import
from . import kodigui
from . import windowutils
from lib import util
from plexnet.video import Episode, Movie, Clip

import os


def split2len(s, n):
    def _f(s, n):
        while s:
            yield s[:n]
            s = s[n:]
    return list(_f(s, n))


class InfoWindow(kodigui.ControlledWindow, windowutils.UtilMixin):
    xmlFile = 'script-plex-info.xml'
    path = util.ADDON.getAddonInfo('path')
    theme = 'Main'
    res = '1080i'
    width = 1920
    height = 1080

    PLAYER_STATUS_BUTTON_ID = 204

    THUMB_DIM_POSTER = (519, 469)
    THUMB_DIM_SQUARE = (519, 519)

    def __init__(self, *args, **kwargs):
        kodigui.ControlledWindow.__init__(self, *args, **kwargs)
        self.title = kwargs.get('title')
        self.subTitle = kwargs.get('sub_title')
        self.thumb = kwargs.get('thumb')
        self.thumbFallback = kwargs.get('thumb_fallback')
        self.info = kwargs.get('info')
        self.background = kwargs.get('background')
        self.isSquare = kwargs.get('is_square')
        self.is16x9 = kwargs.get('is_16x9')
        self.isPoster = not (self.isSquare or self.is16x9)
        self.thumbDim = self.isSquare and self.THUMB_DIM_SQUARE or self.THUMB_DIM_POSTER
        self.video = kwargs.get('video')

    def getVideoInfo(self):
        """
        Append media/part/stream info to summary
        """
        if not isinstance(self.video, (Episode, Movie, Clip)):
            return self.info

        summary = [self.info]

        addMedia = ["\n\n\n\nMedia\n"]
        for media_ in self.video.media():
            for part in media_.parts:
                addMedia.append("File: ")
                splitFnAt = 74
                fnLen = len(os.path.basename(part.file))
                appended = False
                for s in split2len(os.path.basename(part.file), splitFnAt):
                    if fnLen > splitFnAt and not appended:
                        addMedia.append("{} ...\n".format(s))
                        appended = True
                        continue
                    addMedia.append("{}\n".format(s))

                subs = []
                for stream in part.streams:
                    streamtype = stream.streamType.asInt()
                    # video
                    if streamtype == 1:
                        addMedia.append("Video: {}x{}, {}/{}bit/{}/{}@{} kBit, {} fps\n".format(
                            stream.width, stream.height, stream.codec.upper(),
                            stream.bitDepth, stream.chromaSubsampling, stream.colorPrimaries, stream.bitrate,
                            stream.frameRate))
                    # audio
                    elif streamtype == 2:
                        addMedia.append("Audio: {}{}, {}/{}ch@{} kBit, {} Hz\n".format(
                            stream.language,
                            " (default)" if stream.default else "",
                            stream.codec.upper(),
                            stream.channels, stream.bitrate,
                            stream.samplingRate))
                    # subtitle
                    elif streamtype == 3:
                        subs.append("{} ({})".format(stream.language, stream.codec.upper()))

                if subs:
                    addMedia.append("Subtitles: {}\n\n".format(", ".join(subs)))
            addMedia.append("\n\n")

        return "".join(summary + addMedia)

    def onFirstInit(self):
        self.setProperty('is.poster', self.isPoster and '1' or '')
        self.setProperty('is.square', self.isSquare and '1' or '')
        self.setProperty('is.16x9', self.is16x9 and '1' or '')
        self.setProperty('title.main', self.title)
        self.setProperty('title.sub', self.subTitle)
        self.setProperty('thumb.fallback', self.thumbFallback)
        self.setProperty('thumb', self.thumb.asTranscodedImageURL(*self.thumbDim))
        self.setProperty('info', self.getVideoInfo())
        self.setProperty('background', self.background)

    def onClick(self, controlID):
        if controlID == self.PLAYER_STATUS_BUTTON_ID:
            self.showAudioPlayer()
