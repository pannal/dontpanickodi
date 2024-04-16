# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import media
from . import plexobjects
from . import plexmedia


class Photo(media.MediaItem):
    TYPE = 'photo'

    def _setData(self, data):
        self.art = plexobjects.PlexValue('')
        media.MediaItem._setData(self, data)

        # fallback; we might not be a full object but we _can_ have Media
        if self.isFullObject() or data.find("Media") is not None:
            self.media = plexobjects.PlexMediaItemList(data, plexmedia.PlexMedia, media.Media.TYPE,
                                                       initpath=self.initpath, server=self.server, media=self)

    def analyze(self):
        """ The primary purpose of media analysis is to gather information about that media
            item. All of the media you add to a Library has properties that are useful to
            know–whether it's a video file, a music track, or one of your photos.
        """
        self.server.query('/%s/analyze' % self.key)

    def markWatched(self):
        path = '/:/scrobble?key=%s&identifier=com.plexapp.plugins.library' % self.ratingKey
        self.server.query(path)
        self.reload()

    def markUnwatched(self):
        path = '/:/unscrobble?key=%s&identifier=com.plexapp.plugins.library' % self.ratingKey
        self.server.query(path)
        self.reload()

    def play(self, client):
        client.playMedia(self)

    def refresh(self):
        self.server.query('%s/refresh' % self.key, method=self.server.session.put)

    def isPhotoOrDirectoryItem(self):
        return True

    def asTranscodedImageURL(self, w, h, **extras):
        try:
            return self.server.getImageTranscodeURL(self.media[0].parts[0].key, w, h, **extras)
        except:
            pass


class PhotoDirectory(media.MediaItem):
    TYPE = 'photodirectory'

    def all(self, *args, **kwargs):
        path = self.key
        return plexobjects.listItems(self.server, path)

    def isPhotoOrDirectoryItem(self):
        return True


@plexobjects.registerLibFactory('photo')
@plexobjects.registerLibFactory('image')
def PhotoFactory(data, initpath=None, server=None, container=None):
    if data.tag == 'Photo':
        return Photo(data, initpath=initpath, server=server, container=container)
    else:
        return PhotoDirectory(data, initpath=initpath, server=server, container=container)
