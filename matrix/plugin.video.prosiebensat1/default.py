# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_encode
import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import xbmcvfs
import requests
import base64
from inputstreamhelper import Helper
from hashlib import sha1
import calendar
from datetime import datetime, timedelta
import time

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path'))
defaultFanart = os.path.join(addonPath, 'resources/fanart.png')
icon = os.path.join(addonPath, 'resources/icon.png')
baseURL = "https://www."
pluginBaseUrl = "plugin://{0}".format(addon.getAddonInfo('id'))
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
bv = xbmc.getInfoLabel('System.BuildVersion')
kodiVersion = int(bv.split('.')[0])
hasMSRepo = None
hasMySpass = None

# settings
split_parts = addon.getSetting('splitParts') == 'true'

channels = [
               {
                  'id': '1'
                , 'label': 'ProSieben'
                , 'domain': 'prosieben.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/prosieben.png')}
                , 'property_name': 'prosieben-de-24x7'
                , 'client_location': 'https://www.prosieben.de/livestream'
                , 'access_token': 'prosieben'
                , 'client_token':  '01b353c155a9006e80ae7c5ed3eb1c09c0a6995556'
                , 'epg_name': 'prosieben'
              }
            , {
                  'id': '2'
                , 'label': 'SAT.1'
                , 'domain': 'sat1.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sat1.png')}
                , 'property_name': 'sat1-de-24x7'
                , 'client_location': 'https://www.sat1.de/livestream'
                , 'access_token': 'sat1'
                , 'client_token':  '01e491d866b37341734d691a8acb48af37a77bf26f'
                , 'epg_name': 'sat1'
              }
            , {
                  'id': '3'
                , 'label': 'kabel eins'
                , 'domain': 'kabeleins.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/kabeleins.png')}
                , 'property_name': 'kabeleins-de-24x7'
                , 'client_location': 'https://www.kabeleins.de/livestream'
                , 'access_token': 'kabeleins'
                , 'client_token':  '014c87bfe2ce4aebf6219ed699602a1f152194e4cd'
                , 'epg_name': 'k1'
              }
            , {
                  'id': '4'
                , 'label': 'Sixx'
                , 'domain': 'sixx.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sixx.png')}
                , 'property_name': 'sixx-de-24x7'
                , 'client_location': 'https://www.sixx.de/livestream'
                , 'access_token': 'sixx'
                , 'client_token':  '017705703133050842d3ca11fc20a6fc205b8b4025'
                , 'epg_name': 'sixx'
              }
            , {
                  'id': '5'
                , 'label': 'ProSiebenMaxx'
                , 'domain': 'prosiebenmaxx.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/prosiebenmaxx.png')}
                , 'property_name' : 'prosiebenmaxx-de-24x7'
                , 'client_location': 'https://www.prosiebenmaxx.de/livestream'
                , 'access_token' : 'prosiebenmaxx'
                , 'client_token':  '01963623e9b364805dbe12f113dba1c4914c24d189'
                , 'epg_name': 'prosiebenmaxx'
              }
            , {
                  'id': '6'
                , 'label': 'SAT.1 Gold'
                , 'domain': 'sat1gold.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sat1gold.png')}
                , 'property_name' : 'sat1gold-de-24x7'
                , 'client_location': 'https://www.sat1gold.de/livestream'
                , 'access_token' : 'sat1gold'
                , 'client_token': '01107e433196365e4d54d0f90bdf1070cd2df5e190'
                , 'epg_name': 'sat1gold'
              }
            , {
                  'id': '7'
                , 'label': 'kabel eins Doku'
                , 'domain': 'kabeleinsdoku.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/kabeleinsdoku.png')}
                , 'property_name' : 'kabeleinsdoku-de-24x7'
                , 'client_location': 'https://www.kabeleinsdoku.de/livestream'
                , 'access_token' : 'kabeleinsdoku'
                , 'client_token': '01ea6d32ff5de5d50d0290dbdf819f9b856bcfd44a'
                , 'epg_name': 'k1doku'
              }
           ]

rootDirs = [
              {'label': 'Live', 'action': 'livechannels'}
            , {'channels': channels}
           ]


def checkMSAddon():
    global hasMySpass, hasMSRepo
    if os.path.exists(os.path.join(xbmc.translatePath('special://home/addons'), "dontpanickodi")):
        hasMSRepo = True

    if hasMySpass is None:
        hasMySpass = os.path.exists(os.path.join(xbmc.translatePath('special://home/addons'), "plugin.video.myspass_de"))


def listShows(entry):
    content = getContentFull(entry.get('domain'), entry.get('path'))
    if content and len(content) > 0:
        shows = getListItems(content.get('data', None), 'show').get('items')
        for show in shows:
            infoLabels = show.get('infoLabels', {})
            art = show.get('art')
            domain = entry.get('domain')
            if show.get('contentType') == 'redirect':
                match = re.search('http?:\/\/[w]{0,3}\.?([^\/]*)', show.get('url'))
                if match:
                    domain = match.group(1)
                    show.update({'url': ''})
            url = build_url({'action': 'showcontent', 'entry': {'domain': domain, 'path': '{0}{1}'.format(show.get('url'), '/video'), 'cmsId': show.get('cmsId'), 'type': 'season', 'art': art, 'infoLabels': infoLabels}})
            addDir(label=infoLabels.get('title'), url=url, art=art, infoLabels=infoLabels)

    xbmcplugin.setContent(addon_handle, 'tvshows')
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def listShowcontent(entry):
    content = getContentFull(entry.get('domain'), entry.get('path'))
    #xbmc.log('content {0}'.format(content))
    if content and len(content) > 0:
        detail = getListItems(content.get('data', None), entry.get('type'), entry.get('domain'), entry.get('path'), entry.get('cmsId'))
        items = detail.get('items')

        seasons = sorted(list(dict.fromkeys(['{0}'.format(item.get('infoLabels', {}).get('season')) for item in items if item.get('infoLabels', {}).get('season')])))
        #xbmc.log('seasons {0}'.format(seasons))
        xbmc.log('detail {0}'.format(detail))
        if detail.get('type') == 'episode' and entry.get('type') == 'season' and len(seasons) > 1:
            for season in seasons:
                url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': entry.get('path'), 'cmsId': entry.get('cmsId'), 'seasonno': season, 'type': 'episode'}})
                addDir(label='Staffel {0}'.format(season), url=url, art=entry.get('art'), infoLabels=entry.get('infoLabels'))

            noseasons = [item for item in items if not item.get('infoLabels', {}).get('season')]
            if len(noseasons) > 0:
                url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': entry.get('path'), 'cmsId': entry.get('cmsId'), 'seasonno': None, 'type': 'episode'}})
                addDir(label='Videos ohne Staffelzuordnung', url=url, art=entry.get('art'), infoLabels=entry.get('infoLabels'))

            xbmcplugin.setContent(addon_handle, 'tvshows')

        if items:
            addon_content = None
            addon_sortmethods = []
            for item in items:
                infoLabels = item.get('infoLabels', {})
                if detail.get('type') == 'season':
                    addon_content = 'tvshows'
                    addon_sortmethods.append(xbmcplugin.SORT_METHOD_LABEL)
                    entry_infoLabels = entry.get('infoLabels', {})
                    infoLabels.update({'plot': entry_infoLabels.get('plot')})
                    cmsId = detail.get('cmsId') if detail.get('cmsId') else entry.get('cmsId')

                    url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': item.get('url'), 'cmsId': cmsId, 'seasonno': infoLabels.get('season')}})
                    addDir(label='Staffel {0}'.format(infoLabels.get('season')), url=url, art=entry.get('art'), infoLabels=infoLabels)
                else:
                    if detail.get('type') != 'episode' and entry.get('seasonno') and infoLabels.get('season') != int(entry.get('seasonno')):
                        continue
                    elif detail.get('type') != 'episode' and not entry.get('seasonno') and infoLabels.get('season'):
                        continue
                    elif entry.get('type') == 'episode' and entry.get('seasonno') and infoLabels.get('season') and infoLabels.get('season') != int(entry.get('seasonno')):
                        continue
                    elif entry.get('type') == 'episode' and not entry.get('seasonno') and infoLabels.get('season'):
                        continue
                    addon_content = 'episodes'

                    if not entry.get('season') and not infoLabels.get('season'):
                        # assume missing year is this year
                        infoLabels['season'] = datetime.today().year

                    if item.get("contentType") == "article":
                        addon_content = 'tvshows'
                        addon_sortmethods.append(xbmcplugin.SORT_METHOD_LABEL)
                        entry_infoLabels = entry.get('infoLabels', {})
                        infoLabels.update({'plot': entry_infoLabels.get('plot')})
                        infoLabels["mediatype"] = None
                        cmsId = detail.get('cmsId', entry.get('cmsId'))

                        url = build_url({'action': 'showcontent',
                                         'entry': {'domain': entry.get('domain'), 'path': item.get('url'),
                                                   'cmsId': cmsId, 'seasonno': infoLabels.get('season')}})
                        addDir(label=infoLabels.get('title'), url=url, art=entry.get('art'),
                               infoLabels=infoLabels)
                        continue
                    if infoLabels.get('season') and infoLabels.get('episode'):
                        addon_sortmethods.extend([xbmcplugin.SORT_METHOD_EPISODE, xbmcplugin.SORT_METHOD_LABEL])

                    url = build_url({'action': 'play', 'entry': {'domain': entry.get('domain'), 'path': item.get('url')}})
                    addFile(infoLabels.get('title'), url, art=item.get('art', {}), infoLabels=infoLabels)

            if addon_content:
                xbmcplugin.setContent(addon_handle, addon_content)
            for sortmethod in addon_sortmethods:
                xbmcplugin.addSortMethod(addon_handle, sortMethod=sortmethod)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def getContentFull(domain, path):
    base = 'https://magellan-api.p7s1.io/content-full/{0}{1}/graphql'.format(domain, path)
    parameters = {'query': ' query FullContentQuery($domain: String!, $url: String!, $date: DateTime, $contentType: String, $debug: Boolean!, $authentication: AuthenticationInput) { site(domain: $domain, date: $date, authentication: $authentication) { domain path(url: $url) { content(type: FULL, contentType: $contentType) { ...fContent } somtag(contentType: $contentType) { ...fSomtag } tracking(contentType: $contentType) { ...fTracking } } } } fragment fContent on Content { areas { ...fContentArea } } fragment fContentArea on ContentArea { id containers { ...fContentContainer } filters { ...fFilterOptions } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentContainer on ContentContainer { id style elements { ...fContentElement } } fragment fContentElement on ContentElement { id authentication title description component config style highlight navigation { ...fNavigationItem } regwall filters { ...fFilterOptions } update styleModifiers groups { id title total cursor itemSource { type id } items { ...fContentElementItem } debug @include(if: $debug) { ...fContentDebugInfo } } groupLayout debug @include(if: $debug) { ...fContentDebugInfo } } fragment fNavigationItem on NavigationItem { selected href channel { ...fChannelInfo } contentType title items { selected href channel { ...fChannelInfo } contentType title } } fragment fChannelInfo on ChannelInfo { title shortName cssId cmsId } fragment fFilterOptions on FilterOptions { type remote categories { name title options { title id channelId } } } fragment fContentElementItem on ContentElementItem { id url info branding { ...fBrand } body config headline contentType channel { ...fChannelInfo } site picture { url } videoType orientation date duration flags genres valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fBrand on Brand { id, name } fragment fEpisode on Episode { number } fragment fSeason on Season { number } fragment fEpgInfo on EpgInfo { time endTime primetime } fragment fContentDebugInfo on ContentDebugInfo { source transformations { description } } fragment fSomtag on Somtag { configs } fragment fTracking on Tracking { context }'}
    parameters.update({'variables': '{{"authentication":null,"contentType":"frontpage","debug":false,"domain":"{0}","isMobile":false,"url":"{1}"}}'.format(domain, path)})
    url = '{0}?{1}'.format(base, urllib.urlencode(parameters).replace('+', '%20'))
    result = requests.get(url).json()
    if result and path.endswith('/video') and result.get('data', None) and result.get('data').get('site', None) and result.get('data').get('site').get('path', None) and not result.get('data').get('site').get('path').get('somtag'):
        result = getContentFull(domain, '{0}s'.format(path))
    return result


def getContentPreview(domain, path):
    base = 'https://magellan-api.p7s1.io/content-preview/{0}{1}/graphql'.format(domain, path)
    if path == '/livestream':
        parameters = {'query': 'query PreviewContentQuery($domain: String!, $url: String!, $date: DateTime, $contentType: String, $debug: Boolean!, $authentication: AuthenticationInput) { site(domain: $domain, date: $date, authentication: $authentication) { domain path(url: $url) { route { ...fRoute } page { ...fPage ...fLivestream24Page } content(type: PREVIEW, contentType: $contentType) { ...fContent } mainNav: navigation(type: MAIN) { items { ...fNavigationItem } } metaNav: navigation(type: META) { items { ...fNavigationItem } } channelNav: navigation(type: CHANNEL) { items { ...fNavigationItem } } showsNav: navigation(type: SHOWS) { items { ...fNavigationItem } } footerNav: navigation(type: FOOTER) { items { ...fNavigationItem } } networkNav: navigation(type: NETWORK) { items { ...fNavigationItem } } } } } fragment fRoute on Route { url exists authentication comment contentType name cmsId startDate status endDate } fragment fPage on Page { cmsId contentType pagination { ...fPagination } title shortTitle subheadline proMamsId additionalProMamsIds route source regWall { ...fRegWall } links { ...fLink } metadata { ...fMetadata } breadcrumbs { id href title text } channel { ...fChannel } seo { ...fSeo } modified published flags mainClassNames } fragment fPagination on Pagination { kind limit parent contentType } fragment fRegWall on RegWall { isActive start end } fragment fLink on Link { id classes language href relation title text outbound } fragment fMetadata on Metadata { property name content } fragment fChannel on Channel { name title shortName licenceTerms cssId cmsId proMamsId additionalProMamsIds route image hasLogo liftHeadings, logo sponsors { ...fSponsor } } fragment fSponsor on Sponsor { name url image } fragment fSeo on Seo { title keywords description canonical robots } fragment fLivestream24Page on Livestream24Page { ... on Livestream24Page { livestreamId contentResources epg { name items { ...fEpgItem tvShowTeaser { ...fTeaserItem } } } } } fragment fEpgItem on EpgItem { id title description startTime endTime episode { number } season { number } tvShow { title } images { url title copyright } links { href contentType title } } fragment fTeaserItem on TeaserItem { id url info headline contentType channel { ...fChannelInfo } branding { ...fBrand } site picture { url } videoType orientation date flags valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } } fragment fChannelInfo on ChannelInfo { title shortName cssId cmsId } fragment fBrand on Brand { id, name } fragment fEpisode on Episode { number } fragment fSeason on Season { number } fragment fEpgInfo on EpgInfo { time endTime primetime } fragment fContent on Content { areas { ...fContentArea } } fragment fContentArea on ContentArea { id containers { ...fContentContainer } filters { ...fFilterOptions } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentContainer on ContentContainer { id style elements { ...fContentElement } } fragment fContentElement on ContentElement { id authentication title description component config style highlight navigation { ...fNavigationItem } regwall filters { ...fFilterOptions } update styleModifiers groups { id title total cursor itemSource { type id } items { ...fContentElementItem } debug @include(if: $debug) { ...fContentDebugInfo } } groupLayout debug @include(if: $debug) { ...fContentDebugInfo } } fragment fNavigationItem on NavigationItem { selected href channel { ...fChannelInfo } contentType title items { selected href channel { ...fChannelInfo } contentType title } } fragment fFilterOptions on FilterOptions { type remote categories { name title options { title id channelId } } } fragment fContentElementItem on ContentElementItem { id url info branding { ...fBrand } body config headline contentType channel { ...fChannelInfo } site picture { url } videoType orientation date duration flags genres valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentDebugInfo on ContentDebugInfo { source transformations { description } } '}
        parameters.update({'variables': '{{"authentication":null,"contentType":"video","debug":false,"domain":"{0}","isMobile":false,"url":"{1}"}}'.format(domain, path)})
    else:
        parameters = {'query': ' query PreviewContentQuery($domain: String!, $url: String!, $date: DateTime, $contentType: String, $debug: Boolean!, $authentication: AuthenticationInput) { site(domain: $domain, date: $date, authentication: $authentication) { domain path(url: $url) { route { ...fRoute } page { ...fPage ...fVideoPage } content(type: PREVIEW, contentType: $contentType) { ...fContent } mainNav: navigation(type: MAIN) { items { ...fNavigationItem } } metaNav: navigation(type: META) { items { ...fNavigationItem } } channelNav: navigation(type: CHANNEL) { items { ...fNavigationItem } } showsNav: navigation(type: SHOWS) { items { ...fNavigationItem } } footerNav: navigation(type: FOOTER) { items { ...fNavigationItem } } networkNav: navigation(type: NETWORK) { items { ...fNavigationItem } } } } } fragment fRoute on Route { url exists authentication comment contentType name cmsId startDate status endDate } fragment fPage on Page { cmsId contentType pagination { ...fPagination } title shortTitle subheadline proMamsId additionalProMamsIds route source regWall { ...fRegWall } links { ...fLink } metadata { ...fMetadata } breadcrumbs { id href title text } channel { ...fChannel } seo { ...fSeo } modified published flags mainClassNames } fragment fPagination on Pagination { kind limit parent contentType } fragment fRegWall on RegWall { isActive start end } fragment fLink on Link { id classes language href relation title text outbound } fragment fMetadata on Metadata { property name content } fragment fChannel on Channel { name title shortName licenceTerms cssId cmsId proMamsId additionalProMamsIds route image hasLogo liftHeadings, logo sponsors { ...fSponsor } } fragment fSponsor on Sponsor { name url image } fragment fSeo on Seo { title keywords description canonical robots } fragment fVideoPage on VideoPage { ... on VideoPage { copyright description longDescription duration season episode airdate videoType contentResource image webUrl livestreamStartDate livestreamEndDate recommendation { results { headline subheadline duration url image videoType contentType recoVariation recoSource channel { ...fChannelInfo } } } } } fragment fChannelInfo on ChannelInfo { title shortName cssId cmsId } fragment fContent on Content { areas { ...fContentArea } } fragment fContentArea on ContentArea { id containers { ...fContentContainer } filters { ...fFilterOptions } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentContainer on ContentContainer { id style elements { ...fContentElement } } fragment fContentElement on ContentElement { id authentication title description component config style highlight navigation { ...fNavigationItem } regwall filters { ...fFilterOptions } update styleModifiers groups { id title total cursor itemSource { type id } items { ...fContentElementItem } debug @include(if: $debug) { ...fContentDebugInfo } } groupLayout debug @include(if: $debug) { ...fContentDebugInfo } } fragment fNavigationItem on NavigationItem { selected href channel { ...fChannelInfo } contentType title items { selected href channel { ...fChannelInfo } contentType title } } fragment fFilterOptions on FilterOptions { type remote categories { name title options { title id channelId } } } fragment fContentElementItem on ContentElementItem { id url info branding { ...fBrand } body config headline contentType channel { ...fChannelInfo } site picture { url } videoType orientation date duration flags genres valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fBrand on Brand { id, name } fragment fEpisode on Episode { number } fragment fSeason on Season { number } fragment fEpgInfo on EpgInfo { time endTime primetime } fragment fContentDebugInfo on ContentDebugInfo { source transformations { description } } '}
        parameters.update({'variables': '{{"authentication":null,"contentType":"livestream24","debug":false,"domain":"{0}","isMobile":false,"url":"{1}"}}'.format(domain, path)})
    url = '{0}{1}?{2}'.format(base, path, urllib.urlencode(parameters).replace('+', '%20'))
    result = requests.get(url).json()
    if result and path.endswith('/video') and result.get('data', None) and result.get('data').get('site', None) and result.get('data').get('site').get('path', None) and result.get('data').get('site').get('path').get('route').get('status').lower() == 'not_found':
        result = getContentPreview(domain, '{0}s'.format(path))
    return result


def getListItems(data, type, domain=None, path=None, cmsId=None, content=None):
    if not content:
        content = {'items': []}

    if type == 'season':
        subcontent = getContentPreview(domain, path)
        content = getShownav(subcontent.get('data', None), content, domain, cmsId)

    checkMSAddon()

    if (len(content.get('items')) == 0 or content.get('type') == 'episode') and data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('content', None) and data.get('site').get('path').get('content').get('areas', None):
        areas = data.get('site').get('path').get('content').get('areas')
        if len(areas) > 0:
            containers = areas[0].get('containers')
            for container in containers:
                elements = container.get('elements', None)
                if elements and len(elements) > 0:
                    element = elements[0]
                    groups = element.get('groups', None)
                    if groups and len(groups) > 0:
                        groupitems = groups[0].get('items', None)
                        if groupitems:
                            for groupitem in groupitems:
                                if not groupitem or groupitem.get("contentType", None) == "frontpage":
                                    continue

                                citems = content.get('items')
                                if type == 'show':
                                    item = getContentInfos(groupitem, 'show')
                                    if checkItemUrlExists(citems, item) == False:
                                        citems.append(item)
                                        content.update({'items': citems})
                                elif cmsId and groupitem.get('channel', {}).get('cmsId') == cmsId:
                                    if not groupitem.get('videoType') and ((groupitem.get('headline') and (groupitem.get('headline').lower().startswith('staffel') or groupitem.get('headline').lower().startswith('season'))
                                            or "shows" in groupitem.get('headline').lower())):
                                        content.update({'type': 'season'})
                                        item = getContentInfos(groupitem, 'season')
                                        if checkItemUrlExists(citems, item) == False:
                                            citems.append(item)
                                            content.update({'items': citems})
                                    elif (groupitem.get('videoType') and groupitem.get('videoType').lower() == 'full') \
                                         or (not groupitem.get('videoType') and groupitem.get('url') and groupitem.get('url').startswith(path) and groupitem.get('url').find('playlist') == -1 and groupitem.get('url').find('clip') == -1):
                                        content.update({'type': 'episode'})
                                        item = getContentInfos(groupitem, 'episode')
                                        if checkItemUrlExists(citems, item) == False:
                                            citems.append(item)
                                            content.update({'items': citems})
                                    elif groupitem.get('contentType') == "redirect" \
                                            and '//www.myspass.de/' in groupitem.get("url"):
                                        headline = groupitem.get('headline')

                                        if not split_parts:
                                            if "ganze folge" in headline.lower():
                                                gf_base, gf_rest = headline.lower().split("ganze folge")
                                                if "teil" in gf_rest:
                                                    gf_part = gf_rest.split("teil")[1]
                                                    try:
                                                        gf_num = int(gf_part.strip())
                                                        if gf_num > 1:
                                                            continue
                                                        groupitem["headline"] = groupitem["headline"][:len(gf_base) +
                                                                                                       len("ganze folge")]
                                                    except ValueError:
                                                        pass
                                        item = getContentInfos(groupitem, 'episode')
                                        myspass_id = groupitem.get("url").split('//www.myspass.de/')[1]
                                        if myspass_id.endswith("/"):
                                            myspass_id = myspass_id[:-1]
                                        try:
                                            myspass_id = int(myspass_id)
                                        except ValueError:
                                            continue
                                        item['path'] = item['url'] = \
                                            'plugin://plugin.video.myspass_de/?IDENTiTY={}&mode=playCODE&direct=True{}'\
                                                .format(myspass_id, "&splitParts=True" if split_parts else "")
                                        item['infoLabels']['title'] = "{}: {}".format("MySpass" if hasMySpass else "MySpass required", item['infoLabels']['title'])
                                        if checkItemUrlExists(citems, item) == False:
                                            citems.append(item)
                                            content.update({'items': citems})

    if not content.get('type'):
        content.update({'type': type})

    return content


def getShownav(data, content, domain, cmsId):
    if data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('channelNav', None) and data.get('site').get('path').get('channelNav').get('items', None):
        channelitems = data.get('site').get('path').get('channelNav').get('items')
        for channelitem in channelitems:
            if channelitem.get('title').lower() == 'video' or channelitem.get('title').lower() == 'videos':
                for channelsubitem in channelitem.get('items'):
                    if channelsubitem.get('title').lower().find('staffel') > -1 or channelsubitem.get('title').lower().find('season') > -1:
                        content.update({'type': 'season', 'cmsId': channelitem.get('channel').get('cmsId')})
                        citems = content.get('items')
                        citems.append(getContentInfos(channelsubitem, 'season'))
                        content.update({'items': citems})
                    elif channelsubitem.get('title').lower().find('episode') > -1 or channelsubitem.get('title').lower().find('folge') > -1:
                        subcontent = getContentFull(domain, channelsubitem.get('href'))
                        content = getListItems(subcontent.get('data'), 'episode', domain, channelsubitem.get('href'), cmsId, content)
                        content.update({'type': 'episode'})

    return content


def getContentInfos(data, type):
    infos = {}
    if type == 'live':
        now_item = None
        next_item = None
        for index, item in enumerate(data.get('items')):
            now = datetime.utcnow()

            start_time = datetime.fromtimestamp(time.mktime(time.strptime(item.get('startTime'), '%Y-%m-%dT%H:%M:%S.%fZ')))
            end_time = datetime.fromtimestamp(time.mktime(time.strptime(item.get('endTime'), '%Y-%m-%dT%H:%M:%S.%fZ')))

            infos.update({'stime': start_time})
            infos.update({'etime': end_time})
            if (now >= start_time) and (now <= end_time):
                now_item = item
                next_item = data.get('items')[index + 1]
                break

        if now_item:
            infoLabels = {'title': now_item.get('title')}
            if now_item.get('tvShow'):
                if not infoLabels.get('title'):
                    infoLabels.update({'title': now_item.get('tvShow').get('title')})
                infoLabels.update({'tvShowTitle': now_item.get('tvShow').get('title')})
                infoLabels.update({'mediatype': 'episode'})

            infoLabels.update({'season': now_item.get('season').get('number')})
            infoLabels.update({'episode': now_item.get('episode').get('number')})

            local_start_time = utc_to_local(infos.get('stime'))
            local_end_time = utc_to_local(infos.get('etime'))
            plot = '{0} - {1}'.format(local_start_time.strftime('%H:%M'), local_end_time.strftime('%H:%M'))
            if next_item:
                next_title = next_item.get('title') if next_item.get('title') else None
                next_show = next_item.get('tvShow').get('title') if next_item.get('tvShow') else ''

                plot = '{0}{1}'.format(plot, '\nDanach: [COLOR blue]{0}[/COLOR] {1}'.format(next_show, next_title) if next_title and next_show != '' and next_title != next_show else '\nDanach: {0}'.format(next_title if next_title else next_show))

            plot = '{0}\n\n'.format(plot)
            plot = '{0}{1}'.format(plot, now_item.get('description') if now_item.get('description') else '')
            infoLabels.update({'plot': plot})

            if now_item.get('images') and len(now_item.get('images')) > 0:
                art = {'thumb': '{0}{1}'.format(now_item.get('images')[0].get('url'), '/profile:mag-648x366')}
                infos.update({'art' : art})

            infos.update({'infoLabels' : infoLabels})
    else:
        infos.update({'url': data.get('url') if data.get('url') else data.get('href'), 'type': type, 'contentType': data.get('contentType')})

        if type == 'episode':
            title = data.get('headline')
            if title.find('Originalversion') > -1:
                title = title.replace('Originalversion', 'OV')
            if (title.lower().find('episode') > -1 or title.lower().find('folge') > -1) and title.find(':') > -1:
                splits = title.split(':', 1)
                for split in splits:
                    if split.lower().find('episode') == -1 and split.lower().find('folge') == -1:
                        title = split.strip()
                        break
            infoLabels = {'title': title}
            infoLabels.update({'tvShowTitle': data.get('channel').get('title')})
            season_match = re.search('(staffel|season)[\S](\d+)', infos.get('url'))
            if season_match:
                infoLabels.update({'season': int(season_match.group(2))})
            episode_match = re.search('(episode|folge)\S(\d+)', infos.get('url'))
            if episode_match:
                infoLabels.update({'episode': int(episode_match.group(2))})
            if not infoLabels.get('season'):
                season = data.get('epg').get('season').get('number')
                if season and season.startswith('s'):
                    season = season.split('s', 1)[1]
                if season:
                    infoLabels.update({'season': int(season)})
            if not infoLabels.get('episode'):
                episode = data.get('epg').get('episode').get('number')
                if episode and episode.startswith('e'):
                    episode = episode.split('e', 1)[1]
                if episode:
                    infoLabels.update({'episode': int(episode)})
            infoLabels.update({'duration': data.get('epg').get('duration')})
            infoLabels.update({'mediatype': 'episode'})
        elif type == 'season':
            title = data.get('headline') if data.get('headline') else data.get('title')
            if title.find(':') > -1:
                splits = title.split(':')
                for split in splits:
                    if split.lower().find('staffel') > -1 or split.lower().find('season') > -1:
                        title = split.strip()
                        break
            infoLabels = {'title': title}
            season_match = re.search('staffel[\S\s]+(\d+)|season[\S\s]+(\d+)', title.lower())
            if not season_match:
                season_match = re.search('(\d+)[\S\s]+staffel|(\d+)[\S\s]+season', title.lower())
            if season_match:
                infoLabels.update({'season': int(season_match.group(1))})

        elif type == 'show':
            infoLabels = {'title': data.get('channel').get('shortName') if data.get('channel').get('shortName') else data.get('headline')}
            infos.update({'cmsId': data.get('id')})

        infoLabels.update({'plot': data.get('info') if data.get('info') else None})
        infos.update({'infoLabels' : infoLabels})

        if data.get('picture'):
            art = {'thumb': '{0}{1}'.format(data.get('picture').get('url'), '/profile:mag-648x366')}
            infos.update({'art' : art})

    return infos


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def getVideoId(data):
    videoid = None
    if data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('page', None):
        page = data.get('site').get('path').get('page')
        videoid = page.get('contentResource')[0].get('id')

    return videoid


def playVideo(entry):
    video_id = None
    if "myspass" in entry.get("path"):
        checkMSAddon()
        if not hasMSRepo:
            xbmcgui.Dialog().ok("Install repository", "To see MySpass content you need to add this repository: "
                                                      "https://pannal.github.io/dontpanickodi/repo")
            return

        play_item = xbmcgui.ListItem(path=entry.get("path"))
        play_item.setProperty("IsPlayable", "true")
        xbmcplugin.setResolvedUrl(addon_handle, True, play_item)
        return

    content = getContentPreview(entry.get('domain'), entry.get('path'))
    if content:
        video_id = getVideoId(content.get('data'))

    # Inputstream and DRM
    helper = Helper(protocol='mpd', drm='widevine')
    isInputstream = helper.check_inputstream()

    if not isInputstream:
        access_token = 'h''b''b''t''v'
        salt = '0''1''r''e''e''6''e''L''e''i''w''i''u''m''i''e''7''i''e''V''8''p''a''h''g''e''i''T''u''i''3''B'
        client_name = 'h''b''b''t''v'
    else:
        access_token = 'seventv-web'
        salt = '01!8d8F_)r9]4s[qeuXfP%'
        client_name = ''

    source_id = 0
    json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/{0}?{1}'.format(video_id, urllib.urlencode({
            'access_token': access_token,
            'client_location': entry.get('path'),
            'client_name': client_name
        }))
    json_data = requests.get(json_url).json()

    if isInputstream:
        for stream in json_data['sources']:
            if stream['mimetype'] == 'application/dash+xml':
                if int(source_id) < int(stream['id']):
                    source_id = stream['id']
    else:
        if json_data["is_protected"] == True:
            xbmc.executebuiltin('Notification("Inputstream", "DRM geschützte Folgen gehen nur mit Inputstream")')
            return
        else:
            for stream in json_data['sources']:
                if stream['mimetype'] == 'video/mp4':
                    if int(source_id) < int(stream['id']):
                        source_id = stream['id']

    client_id_1 = '{0}{1}'.format(salt[:2], sha1('{0}{1}{2}{3}{4}{5}'.format(video_id, salt, access_token, entry.get('path'), salt, client_name).encode('utf-8')).hexdigest())

    json_url = 'https://vas.sim-technik.de/vas/live/v2/videos/{0}/sources?{1}'.format(video_id, urllib.urlencode({
        'access_token':  access_token,
        'client_location':  entry.get('path'),
        'client_name':  client_name,
        'client_id': client_id_1
    }))
    json_data = requests.get(json_url).json()
    server_id = json_data['server_id']

    # client_name = 'kolibri-1.2.5'
    client_id = '{0}{1}'.format(salt[:2], sha1('{0}{1}{2}{3}{4}{5}{6}{7}'.format(salt, video_id, access_token, server_id, entry.get('path'), source_id, salt, client_name).encode('utf-8')).hexdigest())
    url_api_url = 'http://vas.sim-technik.de/vas/live/v2/videos/{0}/sources/url?{1}'.format(video_id, urllib.urlencode({
        'access_token': access_token,
        'client_id': client_id,
        'client_location': entry.get('path'),
        'client_name': client_name,
        'server_id': server_id,
        'source_ids': str(source_id),
    }))

    json_data = requests.get(url_api_url).json()
    max_id = 0
    for stream in json_data["sources"]:
        ul = stream["url"]
        try:
            sid = re.compile('-tp([0-9]+).mp4', re.DOTALL).findall(ul)[0]
            id = int(sid)
            if max_id < id:
                max_id = id
                data = ul
        except:
          data = ul

    li = xbmcgui.ListItem(path='{0}|{1}'.format(data, userAgent))
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstreamaddon' if kodiVersion <= 18 else 'inputstream', 'inputstream.adaptive')

    try:
        lic = json_data['drm']['licenseAcquisitionUrl']
        token = json_data['drm']['token']
        li.setProperty('inputstream.adaptive.license_key', '{0}?token={1}|{2}|{3}|'.format(lic, token, userAgent, 'R{SSM}'))
    except:
        pass

    if entry.get('infoLabels') and len(entry.get('infoLabels')) > 0:
        li.setInfo('video', entry.get('infoLabels'))

    xbmcplugin.setResolvedUrl(addon_handle, True, li)


def playLive(entry):
    # Inputstream and DRM
    helper = Helper(protocol='mpd', drm='widevine')
    if helper.check_inputstream() == False:
        return

    url = 'https://vas-live-mdp.glomex.com/live/1.0/getprotocols?{0}'.format(urllib.urlencode({
        'access_token': entry.get('access_token'),
        'client_location':  entry.get('client_location'),
        'property_name':  entry.get('property_name'),
        'client_token':  entry.get('client_token'),
        'secure_delivery': 'true'
    }))

    data = requests.get(url).json()

    server_token = data.get('server_token')
    salt = '01!8d8F_)r9]4s[qeuXfP%'
    client_token = '{0}{1}'.format(salt[:2], sha1('{0}{1}{2}{3}{4}{5}'.format(entry.get('property_name'), salt, entry.get('access_token'), server_token, entry.get('client_location'), 'dash:widevine').encode('utf-8')).hexdigest())

    url = 'https://vas-live-mdp.glomex.com/live/1.0/geturls?{0}'.format(urllib.urlencode({
        'access_token':  entry.get('access_token'),
        'client_location':  entry.get('client_location'),
        'property_name':  entry.get('property_name'),
        'protocols': 'dash:widevine',
        'server_token': server_token,
        'client_token': client_token,
        'secure_delivery': 'true'
    }))

    data = requests.get(url).json()['urls']['dash']['widevine']

    li = xbmcgui.ListItem(path='{0}|{1}'.format(data['url'], userAgent))
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
    li.setProperty('inputstreamaddon' if kodiVersion <= 18 else 'inputstream', 'inputstream.adaptive')

    try:
        lic = data['drm']['licenseAcquisitionUrl']
        token = data['drm']['token']
        li.setProperty('inputstream.adaptive.license_key', '{0}?token={1}|{2}|{3}|'.format(lic, token, userAgent, 'R{SSM}'))
    except:
        pass

    xbmcplugin.setResolvedUrl(addon_handle, True, li)


def rootDir():
    for dir in rootDirs:
        if not dir.get('channels'):
            url = build_url({'action': dir.get('action')})
            addDir(label=dir.get('label'), url=url)
        else:
            channels = dir.get('channels')
            for channel in channels:
                parameter = {'action': 'shows', 'entry': channel}
                addDir(label=channel.get('label'), url=build_url(parameter), art=channel.get('art'))

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def listLiveChannels():
    content = getContentPreview(channels[0].get('domain'), '/livestream')
    epg_data = None
    if content.get('data') and content.get('data').get('site') and content.get('data').get('site').get('path') and content.get('data').get('site').get('path').get('page') and content.get('data').get('site').get('path').get('page').get('epg'):
        epg_data = content.get('data').get('site').get('path').get('page').get('epg')

    contextmenuitems = [(('Aktualisieren', 'RunPlugin({0})'.format(build_url({'action': 'refresh'}))))]
    for channel in channels:
        thumbnailImage = None
        if channel.get('property_name', None) and epg_data:
            infoLabels = None
            art = None
            for epg in epg_data:
                if epg.get('name').lower() == channel.get('epg_name').lower():
                    infos = getContentInfos(epg, 'live')
                    infoLabels = infos.get('infoLabels')
                    art = infos.get('art')

            channel.update({'infoLabels': infoLabels, 'art': art})
            url = build_url({'action': 'playlive', 'entry': channel})
            title = infoLabels.get('title') if infoLabels.get('tvShowTitle', None) is None or infoLabels.get('tvShowTitle') == infoLabels.get('title') else '[COLOR blue]{0}[/COLOR] {1}'.format(infoLabels.get('tvShowTitle'), infoLabels.get('title'))
            title = '[COLOR orange]{0}[/COLOR] {1}'.format(channel.get('label'), title)
            addFile(title, url, art=art, infoLabels=infoLabels, contextMenuItems=contextmenuitems)

    xbmcplugin.setContent(addon_handle, 'files')
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)


def addDir(label, url, art={}, infoLabels={}):
    addFile(label=label, url=url, art=art, infoLabels=infoLabels, isFolder=True)


def addFile(label, url, art={}, infoLabels={}, contextMenuItems=[], isFolder=False):
    li = xbmcgui.ListItem(label)
    li.setInfo('video', infoLabels)
    li.setArt(art)
    li.setProperty('IsPlayable', str(isFolder))
    if len(contextMenuItems) > 0:
        li.addContextMenuItems(contextMenuItems)

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=isFolder)


def build_url(query):
    return '{0}?{1}'.format(pluginBaseUrl, base64.urlsafe_b64encode(json.dumps(query).encode('utf-8')).decode('utf-8'))


def checkItemUrlExists(items, compItem):
    for item in items:
        if item.get('url') == compItem.get('url'):
            return True

    return False


params = urllib.unquote(sys.argv[2][1:])
if len(params) > 0:
    if len(params) % 4 != 0:
        params = '{0}{1}'.format(params, '=' * (4 - len(params) % 4))

    params = dict(json.loads(base64.urlsafe_b64decode(py2_encode(params))))
xbmc.log('params = {0}'.format(params))
if 'action' in params:
    action = params.get('action')
    if action == 'livechannels':
        listLiveChannels()
    elif action == 'shows':
        listShows(params.get('entry'))
    elif action == 'showcontent':
        listShowcontent(params.get('entry'))
    elif action == 'play':
        playVideo(params.get('entry'))
    elif action == 'playlive':
        playLive(params.get('entry'))
    elif action == 'refresh':
        xbmc.executebuiltin("Container.Refresh")
else:
    rootDir()
