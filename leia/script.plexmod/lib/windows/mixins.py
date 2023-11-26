# coding=utf-8

from . import kodigui


class SeasonsMixin():
    SEASONS_CONTROL_ATTR = "subItemListControl"

    THUMB_DIMS = {
        'show': {
            'main.thumb': (347, 518),
            'item.thumb': (174, 260)
        },
        'episode': {
            'main.thumb': (347, 518),
            'item.thumb': (198, 295)
        },
        'artist': {
            'main.thumb': (519, 519),
            'item.thumb': (215, 215)
        }
    }

    def _createListItem(self, mediaItem, obj):
        mli = kodigui.ManagedListItem(
            obj.title or '',
            thumbnailImage=obj.defaultThumb.asTranscodedImageURL(*self.THUMB_DIMS[mediaItem.type]['item.thumb']),
            data_source=obj
        )
        return mli

    def fillSeasons(self, mediaItem, update=False, seasonsFilter=None):
        seasons = mediaItem.seasons()
        if not seasons or (seasonsFilter and not seasonsFilter(seasons)):
            return False

        items = []
        idx = 0
        for season in seasons:
            mli = self._createListItem(mediaItem, season)
            if mli:
                mli.setProperty('index', str(idx))
                mli.setProperty('thumb.fallback', 'script.plex/thumb_fallbacks/show.png')
                mli.setProperty('unwatched.count', not season.isWatched and str(season.unViewedLeafCount) or '')
                items.append(mli)
                idx += 1

        subItemListControl = getattr(self, self.SEASONS_CONTROL_ATTR)
        if update:
            subItemListControl.replaceItems(items)
        else:
            subItemListControl.reset()
            subItemListControl.addItems(items)

        return True

