# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import platform
import xbmcvfs
import time
from datetime import datetime, timedelta
import io
import gzip
import difflib
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote, quote_plus, unquote_plus  # Python 2.X
	from urllib2 import build_opener  # Python 2.X
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmc.translatePath, xbmc.LOGNOTICE, 'inputstreamaddon' # Stand: 05.12.20 / Python 2.X
else:
	from urllib.parse import urlencode, quote, quote_plus, unquote_plus  # Python 3.X
	from urllib.request import build_opener  # Python 3.X
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmcvfs.translatePath, xbmc.LOGINFO, 'inputstream' # Stand: 05.12.20  / Python 3.X


global debuging
HOST_AND_PATH                 = sys.argv[0]
ADDON_HANDLE                  = int(sys.argv[1])
dialog                                      = xbmcgui.Dialog()
addon                                     = xbmcaddon.Addon()
addon_id                                = addon.getAddonInfo('id')
addon_name                         = addon.getAddonInfo('name')
addon_version                      = addon.getAddonInfo('version')
addonPath                             = TRANS_PATH(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath                                = TRANS_PATH(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
channelFavsFile                    = os.path.join(dataPath, 'MYSPASS_favourChart.txt')
WORKFILE                             = os.path.join(dataPath, 'episode_data.txt')
defaultFanart                        = (os.path.join(addonPath, 'fanart.jpg') if PY2 else os.path.join(addonPath, 'resources', 'media', 'fanart.jpg'))
icon                                         = (os.path.join(addonPath, 'icon.png') if PY2 else os.path.join(addonPath, 'resources', 'media', 'icon.png'))
artpic                                      = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
alppic                                      = os.path.join(addonPath, 'resources', 'media', 'alphabet', '').encode('utf-8').decode('utf-8')
useThumbAsFanart              = addon.getSetting('useThumbAsFanart') == 'true'
split_parts = addon.getSetting('splitParts') == 'true'
enableADJUSTMENT            = addon.getSetting('show_settings') == 'true'
DEB_LEVEL                            = (LOG_MESSAGE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
BASE_LONG                           = 'https://www.myspass.de/'
BASE_URL                              = 'https://www.myspass.de'

xbmcplugin.setContent(ADDON_HANDLE, 'tvshows')

def py2_enc(s, nom='utf-8', ign='ignore'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(nom, ign) if isinstance(s, unicode) else s
	return s

def py2_uni(s, nom='utf-8', ign='ignore'):
	if PY2 and isinstance(s, str):
		s = unicode(s, nom, ign)
	return s

def py3_dec(d, nom='utf-8', ign='ignore'):
	if not PY2 and isinstance(d, bytes):
		d = d.decode(nom, ign)
	return d

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=LOG_MESSAGE): # kompatibel mit Python-2 und Python-3
	msg = py2_enc(msg)
	return xbmc.log('[{0} v.{1}]{2}'.format(addon_id, addon_version, msg), level)

def declare_Open(FILE, event='NORMAL', ign='ignore'):
	if PY2:
		DECLARED = open(FILE, 'a') if event == 'NORMAL' else open(FILE, 'a+')
	else:
		DECLARED = open(FILE, 'a', errors=ign) if event == 'NORMAL' else open(FILE, 'a+', errors=ign)
	return DECLARED

def get_Seconds(info):
	try:
		info = re.sub('[a-z]', '', info)
		first = info.split(':')[0]
		if len(info) > 5 and len(first) < 3:
			h, m, s = info.split(':')
			return int(h)*3600+int(m)*60+int(s)
		elif len(info) < 6 or len(first) > 2:
			m, s = info.split(':')
			return int(m)*60+int(s)
	except: return '0'

def build_url(query):
	return '{0}?{1}'.format(HOST_AND_PATH, urlencode(query))

def get_userAgent():
	base = 'Mozilla/5.0 {0} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
	system = platform.system()
	if system == 'Darwin':
		return base.format('(Macintosh; Intel Mac OS X 10_10_1)') # Mac OSX
	if system == 'Windows':
		return base.format('(Windows NT 10.0; WOW64)') # Windows
	if platform.machine().startswith('arm'):
		return base.format('(X11; CrOS armv7l 7647.78.0)') # ARM based Linux
	return base.format('(X11; Linux x86_64)') # x86 Linux

def getUrl(url, header=None, data=None, agent=get_userAgent()):
	opener = build_opener()
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, identity')]
	try:
		if header: opener.addheaders = header
		response = opener.open(url, data, timeout=30)
		if response.info().get('Content-Encoding') == 'gzip':
			content = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
		else:
			content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		failing("(common.getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		dialog.notification(translation(30521).format('URL'), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 15000)
		return sys.exit(0)
	return py2_enc(content)

def cleaning(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&apos;', "'"), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''),
				('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-'),
				('&quot;', '"'), ('&szlig;', 'ß'), ('&ndash;', '-'), ('&Auml;', 'Ä'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&ouml;', 'ö'), ('&uuml;', 'ü'),
				('&agrave;', 'à'), ('&aacute;', 'á'), ('&acirc;', 'â'), ('&egrave;', 'è'), ('&eacute;', 'é'), ('&ecirc;', 'ê'), ('&igrave;', 'ì'), ('&iacute;', 'í'), ('&icirc;', 'î'),
				('&ograve;', 'ò'), ('&oacute;', 'ó'), ('&ocirc;', 'ô'), ('&ugrave;', 'ù'), ('&uacute;', 'ú'), ('&ucirc;', 'û'),
				('u00c4', 'Ä'), ('u00e4', 'ä'), ('u00d6', 'Ö'), ('u00f6', 'ö'), ('u00dc', 'Ü'), ('u00fc', 'ü'), ('u00df', 'ß'), ('u00e0', 'à'), ('u00e1', 'á'), ('u00e9', 'é'), ('u00b4', '´'), ('u0060', '`'),
				('u201c', '“'), ('u201d', '”'), ('u201e', '„'), ('u201f', '‟'), ('u2013', '-'), ("u2018", "‘"), ("u2019", "’")): # last-two-Lines = php-Codes-clear
				text = text.replace(*n)
	return text.strip()

def similar(a, b, max_similarity=0.85):
	if difflib.SequenceMatcher(None, a, b).ratio() >= max_similarity:
		debug_MS("(common.similar) ##### fullURL = {0} || URL-2 = {1} || SIMILAR % = {2} #####".format(a, b, str(difflib.SequenceMatcher(None, a, b).ratio())))
		return True
	return False

def getVideodata(VideoID):
	# https://www.myspass.de/includes/apps/video/getvideometadataxml.php?id=886
	show, name, plot, stream = ("" for _ in range(4))
	seasonNR, episodeNR, duration = ('0' for _ in range(3))
	image, startDATES = (None for _ in range(2))
	url = BASE_URL+'/includes/apps/video/getvideometadataxml.php?id='+VideoID
	debug_MS("(common.getVideodata) ### URL : {0} ###".format(str(url)))
	content = getUrl(url)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(common.getVideodata) CONTENT = {0}".format(str(content)))
	debug_MS("++++++++++++++++++++++++")
	TVS = re.compile('<format><!\\[CDATA\\[(.+?)\\]\\]></format>', re.DOTALL).findall(content)
	if TVS: show = cleaning(TVS[0])
	TTL = re.compile('<title><!\\[CDATA\\[(.+?)\\]\\]></title>', re.DOTALL).findall(content)
	if TTL: name = cleaning(TTL[0])
	SEAS = re.compile('<season><!\\[CDATA\\[(.+?)\\]\\]></season>', re.DOTALL).findall(content)
	if SEAS: seasonNR = SEAS[0]
	EPIS = re.compile('<episode><!\\[CDATA\\[(.+?)\\]\\]></episode>', re.DOTALL).findall(content)
	if EPIS: episodeNR = EPIS[0]
	DESC = re.compile('<description><!\\[CDATA\\[(.+?)\\]\\]></description>', re.DOTALL).findall(content)
	if DESC: plot = cleaning(DESC[0])
	DUR = re.compile('<duration><!\\[CDATA\\[(.+?)\\]\\]></duration>', re.DOTALL).findall(content)
	if DUR: duration = get_Seconds(DUR[0])
	IMG = re.compile('<imagePreview><!\\[CDATA\\[(.+?)\\]\\]></imagePreview>', re.DOTALL).findall(content)
	if IMG: image = IMG[0]
	BCDT = re.compile('<broadcast_date><!\\[CDATA\\[(.+?)\\]\\]></broadcast_date>', re.DOTALL).findall(content)
	if BCDT:
		try:
			airedtime = datetime(*(time.strptime(BCDT[0], '%Y{0}%m{0}%d'.format('-'))[0:6])) # 2019-06-13
			startDATES = airedtime.strftime('%d{0}%m{0}%Y').format('.')
		except: pass
	VID = re.compile('<url_flv><!\\[CDATA\\[(.+?)\\]\\]></url_flv>', re.DOTALL).findall(content)
	if VID:
		stream = VID[0]
		for group in re.search(r'/myspass2009/\d+/(\d+)/(\d+)/(\d+)/', stream).groups():
			videoINT = int(VideoID)
			groupINT = int(group)
			if groupINT > videoINT:
				try: stream = stream.replace(group, unicode(groupINT // videoINT))
				except NameError: stream = stream.replace(group, str(groupINT // videoINT))
	stream = stream.replace('http://c11021-osu.p.core.cdn.streamfarm.net/', 'https://cldf-od.r53.cdn.tv1.eu/')
	return (show, name, seasonNR, episodeNR, plot, duration, image, startDATES, stream)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', 'root'))
image = unquote_plus(params.get('image', ''))
IDENTiTY = unquote_plus(params.get('IDENTiTY', ''))
direct = params.get('direct', False)
split_parts = params.get('splitParts', split_parts)
origSERIE = unquote_plus(params.get('origSERIE', ''))
extras = unquote_plus(params.get('extras', 'standard'))
