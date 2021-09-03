# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import io
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote, quote_plus  # Python 2.X
else: 
	from urllib.parse import urlencode, quote, quote_plus  # Python 3+

from .common import *


if not xbmcvfs.exists(dataPath):
	xbmcvfs.mkdirs(dataPath)

def mainMenu():
	addDir(translation(30601), artpic+'favourites.png', {'mode': 'listShowsFavs'})
	addDir(translation(30602), icon, {'mode': 'listEpisodes', 'url': BASE_LONG})
	addDir(translation(30603), icon, {'mode': 'listSelections', 'url': 'CHANNELS'})
	addDir(translation(30604), icon, {'mode': 'listSelections', 'url': 'TV SHOWS'})
	addDir(translation(30605), icon, {'mode': 'listSelections', 'url': 'WEB SHOWS'})
	addDir(translation(30606), icon, {'mode': 'listSelections', 'url': 'STAND UP'})
	addDir(translation(30607), icon, {'mode': 'listSelections', 'url': 'SERIEN'})
	addDir(translation(30608), icon, {'mode': 'listAlphabet'})
	addDir(translation(30609), icon, {'mode': 'listShows', 'url': 'standard'})
	if enableADJUSTMENT:
		addDir(translation(30610), artpic+'settings.png', {'mode': 'aSettings'})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listAlphabet():
	debug_MS("(navigator.listAlphabet) ------------------------------------------------ START = listAlphabet -----------------------------------------------")
	for letter in (('0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U', 'W', 'Z', '??')):
		addDir(letter, alppic+letter.replace('??', 'QM')+'.jpg', {'mode': 'listShows', 'url': letter.replace('0-9', '1').replace('??', 'QM')})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listShows(TYPE):
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	debug_MS("(navigator.listShows) -------------------------------------------------- START = listShows --------------------------------------------------")
	debug_MS("(navigator.listShows) ### URL or LETTER : {0} ###".format(TYPE))
	content = getUrl(BASE_URL+'/sendungen-a-bis-z/')
	if TYPE == 'QM':
		result = re.compile(r'<h3 class="category__headline">(.*?)</div>          </div>\s*</div>', re.DOTALL).findall(content)[-1]
	elif len(TYPE) < 4:
		result = re.findall(r'<div class="category clearfix" id="{0}">(.*?)(?:<div class="category clearfix"|<footer class=)'.format(TYPE), content, re.S)[0]
	else:
		result = re.findall('<div id="content" class="container">(.*?)<footer class=', content, re.S)[0]
	spl = result.split('<div class="category__item">')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		title = re.compile(' alt=["\']([^"]+?)["\']/>', re.DOTALL).findall(entry)[0]
		title = cleaning(title)
		link = re.compile('<a href=["\']([^"]+?)["\']', re.DOTALL).findall(entry)[0]
		link = BASE_URL+link if link[:4] != 'http' else link
		photo = re.compile(r'(?:img["\'] src=|data-src=)["\']([^"]+?)["\']', re.DOTALL).findall(entry)[0].replace('-300x169.', '.')
		photo = BASE_URL+quote(photo) if photo[:4] != 'http' else quote(photo)
		debug_MS("(navigator.listShows) ##### TITLE = {0} || LINK = {1} || IMAGE = {2} #####".format(str(title), link, photo))
		addType = 1
		if os.path.exists(channelFavsFile):
			with open(channelFavsFile, 'r') as output:
				lines = output.readlines()
				for line in lines:
					if line.startswith('###START'):
						part = line.split('###')
						if link == part[3]: addType = 2
		addDir(title, photo, {'mode': 'listSeasons', 'url': link, 'extras': photo, 'origSERIE': title}, addType=addType)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listSelections(TYPE):
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	debug_MS("(navigator.listSelections) -------------------------------------------------- START = listSelections --------------------------------------------------")
	debug_MS("(navigator.listSelections) ### TYPE : {0} ###".format(TYPE))
	content = getUrl(BASE_URL+'/ganze-folgen/')
	result = re.findall(r'<h3 class="headline has-arrow">{0}</h3>(.*?)(?:<h3 class="headline has-arrow">|<footer class=)'.format(TYPE), content, re.S)[0]
	spl = result.split('<div class="bacs-item bacs-item--hover')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		title = re.compile(r'(?:<meta itemprop=["\']name["\'] content=| alt=)["\']([^"]+?)["\'](?:/>|>)', re.DOTALL).findall(entry)[0]
		title = cleaning(title)
		link = re.compile('<a href=["\']([^"]+?)["\']', re.DOTALL).findall(entry)[0]
		link = BASE_URL+link if link[:4] != 'http' else link
		photo = re.compile(r'(?:<meta itemprop=["\']image["\'] content=|data-src=)["\']([^"]+?)["\']', re.DOTALL).findall(entry)[0].replace('-300x169.', '.')
		photo = BASE_URL+quote(photo) if photo[:4] != 'http' else quote(photo)
		debug_MS("(navigator.listSelections) ##### TITLE = {0} || LINK = {1} || IMAGE = {2} #####".format(str(title), link, photo))
		if not 'trailer' in link.lower():
			if TYPE == 'CHANNELS':
				addDir(title, photo, {'mode': 'listEpisodes', 'url': link, 'extras': 'compilation', 'origSERIE': title})
			else:
				addType = 1
				if os.path.exists(channelFavsFile):
					with open(channelFavsFile, 'r') as output:
						lines = output.readlines()
						for line in lines:
							if line.startswith('###START'):
								part = line.split('###')
								if link == part[3]: addType = 2
				addDir(title, photo, {'mode': 'listSeasons', 'url': link, 'extras': photo, 'origSERIE': title}, addType=addType)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listSeasons(url, IMG, SERIE):
	debug_MS("(navigator.listSeasons) -------------------------------------------------- START = listSeasons --------------------------------------------------")
	debug_MS("(navigator.listSeasons) ### URL : {0} ###".format(url))
	html = getUrl(url)
	index_seasons = html.find('<select title="Staffel auswählen" class=')
	if index_seasons != -1:
		seasons_block = html[index_seasons:html.find('</select>', index_seasons)]
		seasons = re.findall('<option data-remote-args="(.*?)".+?data-remote-target=.+?>(.*?)</option>', seasons_block, re.S)
		for url2, title in seasons:
			newURL = BASE_URL+'/frontend/php/ajax.php?query=bob&videosOnly=true'+url2
			title = cleaning(title)
			number = re.compile('([0-9]+)', re.DOTALL).findall(title)
			if number:
				title = translation(30620).format(str(number[0])) if 'staffel' in title.lower() else title.split(' -')[0]
				if str(number[0]) == '1': title = translation(30621)
			debug_MS("(navigator.listSeasons) ##### TITLE = {0} || newURL = {1} #####".format(str(title), newURL))
			addDir(title, IMG, {'mode': 'listEpisodes', 'url': newURL, 'origSERIE': SERIE})
	else:
		debug_MS("(navigator.listSeasons) ##### Keine SEASON-List - Kein Eintrag gefunden #####")
		return dialog.notification(translation(30523), translation(30524).format(SERIE), icon, 8000)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listEpisodes(url, SERIE):
	debug_MS("(navigator.listEpisodes) -------------------------------------------------- START = listEpisodes --------------------------------------------------")
	debug_MS("(navigator.listEpisodes) ### URL : {0} ### SERIE : {1} ###".format(url, SERIE))
	uno_LIST = []
	position = 0
	startURL = url
	content = getUrl(url).replace('\\', '')
	if startURL == BASE_LONG:
		result = re.findall(r'<div id="content" class="container">(.*?)</article>  </section>', content, re.S)[0]
		spl = result.split('<div class="homeTeaser-buttons" style=')
	elif 'channels/' in startURL:
		result = re.findall('<ul id="playlist_ul">(.*?)</ul>', content, re.S)[0]
		spl = result.split('_video_li">')
	else:
		spl = content.split('bacs-item--hover bacs-item--lg has-infos-shown bacs-item--monthly')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		debug_MS("(navigator.listEpisodes) no.01 ##### ENTRY = {0} #####".format(str(entry)))
		newSHOW, newTITLE, vidURL, Note_1, Note_2, DESC = ("" for _ in range(6))
		vidURL_2, vidURL_3, photo, bcDATE, bcDATE_2, bcDATE_3 = (None for _ in range(6))
		SEAS, EPIS, duration, duration_2, duration_3 = ('0' for _ in range(5))
		position += 1
		if startURL == BASE_LONG:
			title = re.compile('<h2 class=["\']title ellipsis["\']>([^<]+?)</h2>', re.DOTALL).findall(entry)[0]
		elif 'channels/' in startURL:
			title = re.compile('aria-hidden=["\']true["\']></i>([^<]+?)</a></li>', re.DOTALL).findall(entry)[0]
		else:
			title_1 = re.compile('class="title" title="(.*?)">', re.DOTALL).findall(entry)
			title_2 = re.compile(' alt="(.*?)"/>', re.DOTALL).findall(entry)
			title = title_1[0] if title_1 else title_2[0]
		title = cleaning(title)
		if not 'channels/' in startURL and not split_parts and ('Teil 2' in title or 'Teil 3' in title): continue
		link = re.compile('<a href=["\']([^"]+?)["\']', re.DOTALL).findall(entry)[0]
		link = BASE_URL+link if link[:4] != 'http' else link
		try: episIDD = re.compile(r'https?://(?:www\.)?myspass\.de/([^/]+/)*(?P<id>\d+)', re.DOTALL).findall(link)[0][1]
		except: continue
		newSHOW, newTITLE, SEAS, EPIS, DESC, duration, photo, bcDATE, vidURL = getVideodata(episIDD)
		if 'channels/' in startURL and 'channel erneut von vorne' in title.lower():
			position -= 1
			continue 
		if not 'channels/' in startURL and (('Teil 1' in title or 'Teil 1' in newTITLE)) and not split_parts:
			try:
				if 'www.myspass.de' in link and '-Teil-' in link: shortURL = link.split('www.myspass.de')[1].split('-Teil-')[0]
				else: shortURL = link
				plus_CONTENT = content[content.find('<table class="listView--table">')+1:]
				plus_CONTENT = plus_CONTENT[:plus_CONTENT.find('</table>')]
				match = re.findall('<tr data-month(.+?)</tr>', plus_CONTENT, re.S)
				for chtml in match:
					debug_MS("(navigator.listEpisodes) no.02 ##### more Videos CHTML = {0} #####".format(str(chtml)))
					url2 = re.compile('<a href=["\']([^"]+?)["\']', re.DOTALL).findall(chtml)[0]
					fullURL = BASE_URL+url2 if url2[:4] != 'http' else url2
					identical = similar(url2, shortURL)
					if identical is True and 'Teil-2' in fullURL:
						newIDD_2 = re.compile(r'https?://(?:www\.)?myspass\.de/([^/]+/)*(?P<id>\d+)', re.DOTALL).findall(fullURL)[0][1]
						newSHOW_2, newTITLE_2, SEAS_2, EPIS_2, DESC_2, duration_2, photo_2, bcDATE_2, vidURL_2 = getVideodata(newIDD_2)
						vidURL_2 = '@@'+vidURL_2
					if identical is True and 'Teil-3' in fullURL:
						newIDD_3 = re.compile(r'https?://(?:www\.)?myspass\.de/([^/]+/)*(?P<id>\d+)', re.DOTALL).findall(fullURL)[0][1]
						newSHOW_3, newTITLE_3, SEAS_3, EPIS_3, DESC_3, duration_3, photo_3, bcDATE_3, vidURL_3 = getVideodata(newIDD_3)
						vidURL_3 = '@@'+vidURL_3
			except: pass
		if not split_parts:
			if vidURL_2: vidURL = vidURL+vidURL_2
			if vidURL_3: vidURL = vidURL+vidURL_3
		duration = int(duration)+int(duration_2)+int(duration_3) if not split_parts else int(duration)
		image = icon
		if photo:
			if photo[:2] == '//': image = 'https:'+quote(photo)
			elif photo[:4] != 'http': image = BASE_URL+quote(photo)
			else: image = quote(photo)
		SERIE = newSHOW if startURL == BASE_LONG else SERIE
		Note_1 = translation(30622).format(SERIE)
		title = SERIE+' - '+newTITLE if startURL == BASE_LONG else \
			(title.split('- Teil')[0].split(' Teil')[0] if not split_parts else title)
		if EPIS != '0' and EPIS.isdigit():
			SEAS, EPIS = SEAS.zfill(2), EPIS.zfill(2)
			name = translation(30623).format(SEAS, EPIS, title)
			if bcDATE and not '1970' in bcDATE:
				Note_2 = translation(30624).format(newTITLE, SEAS, EPIS, str(bcDATE))
			else: Note_2 = translation(30625).format(newTITLE, SEAS, EPIS)
		else:
			name = title+'  (Special)' if 'spezial' in str(EPIS).lower() else title
			if bcDATE and not '1970' in bcDATE:
				Note_2 = translation(30626).format(newTITLE, str(bcDATE))
			else: Note_2 = '[CR]'
		if 'channels/' in startURL:
			name = translation(30627).format(str(position).zfill(2), newTITLE)
		plot = Note_1+Note_2+DESC
		EP_entry = episIDD+'###'+str(vidURL)+'###'+str(SERIE)+'###'+str(name)+'###'+str(image)+'###'+str(plot.replace('\n', '#n#').strip())+'###'+str(duration)+'###'+str(SEAS)+'###'+str(EPIS)+'###'
		if EP_entry not in uno_LIST:
			uno_LIST.append(EP_entry)
		listitem = xbmcgui.ListItem(name, path=HOST_AND_PATH+'?IDENTiTY='+episIDD+'&mode=playCODE')
		info = {}
		info['Season'] = SEAS
		info['Episode'] = EPIS
		info['Tvshowtitle'] = SERIE
		info['Title'] = name
		info['Tagline'] = None
		info['Plot'] = plot
		info['Duration'] = duration
		info['Year'] = None
		info['Genre'] = 'Unterhaltung'
		info['Studio'] = 'myspass.de'
		info['Mpaa'] = None
		info['Mediatype'] = 'episode'
		listitem.setInfo(type='Video', infoLabels=info)
		listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
		if useThumbAsFanart and image != icon and not artpic in image:
			listitem.setArt({'fanart': image})
		listitem.addStreamInfo('Video', {'Duration':duration})
		listitem.setProperty('IsPlayable', 'true')
		listitem.addContextMenuItems([(translation(30654), 'RunPlugin('+HOST_AND_PATH+'?mode=AddToQueue)')])
		xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=HOST_AND_PATH+'?IDENTiTY='+episIDD+'&mode=playCODE', listitem=listitem)
	with io.open(WORKFILE, 'w', encoding='utf-8', errors='ignore') as input:
		input.write(py2_uni('\n'.join(uno_LIST)))
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def playCODE(IDD, direct=False, _primeCacheDirect=False):
	debug_MS("(navigator.playCODE) -------------------------------------------------- START = playCODE --------------------------------------------------")
	debug_MS("(navigator.playCODE{1}) ### IDD : {0} ###".format((str(IDD)), "direct" if direct else ""))
	pos_LISTE = 0
	Special = False
	endURL = False
	PL = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	if _primeCacheDirect:
		# prime episode cache as it doesn't exist yet and we need the info;
		# super-poor-man's approach as we could possibly direct play this instead
		content = getUrl("{}/{}/".format(BASE_URL, IDD)).replace('\\', '')
		data = re.search(r"\"name\":\"(?P<name>.+?)\",.+?id: {},\s+formatId: (?P<formatId>\d+),\s+category: "
						 r"'(?P<cat>.+?)',.+?seasonId: (?P<seasonId>\d+),".format(IDD),
						 content, re.DOTALL | re.MULTILINE)
		if data:
			# /frontend/php/ajax.php?query=bob&videosOnly=true&seasonId=219&formatId=104&category=full_episode
			log(repr(data.groupdict()))
			data_gd = data.groupdict()
			data_url = "{}/frontend/php/ajax.php?query=bob&videosOnly=true&seasonId={}&formatId={}&category={}".format(
				BASE_URL, data_gd["seasonId"], data_gd["formatId"], data_gd["cat"])
			listEpisodes(data_url, data_gd["name"])
			xbmc.sleep(500)

	# shortcut for no workfile present and direct requested
	if not _primeCacheDirect and direct and not os.path.isfile(WORKFILE):
		return playCODE(IDD, direct=direct, _primeCacheDirect=True)

	with io.open(WORKFILE, 'r', encoding='utf-8', errors='ignore') as output:
		lines = output.readlines()
		for line in lines:
			field = line.split('###')
			if field[0]==IDD:
				endURL = field[1]
				seriesname = field[2]
				title = field[3]
				try: title = title.split('[/COLOR]')[1].strip()
				except:
					try: title = title.split(seriesname+" -")[1].strip()
					except: pass
				image = field[4]
				plot = field[5].replace('#n#', '\n').strip()
				duration = field[6]
				season = field[7]
				episode = field[8]
				if '@@' in endURL:
					Special = True
					videoURL = endURL.split('@@')
					complete = '/'+str(len(videoURL))
					for single in videoURL:
						log("(navigator.playCODE) PlaylistURL : {0} ".format(str(single)))
						pos_LISTE += 1
						NRS_title = translation(30628).format(title.encode("utf-8"), str(pos_LISTE)+complete)
						listitem = xbmcgui.ListItem(title)
						listitem.setInfo(type='Video', infoLabels={'Tvshowtitle': seriesname, 'Title': NRS_title, 'Season': season, 'Episode': episode, 'Plot': plot, 'Duration': duration, 'Studio': 'myspass.de', 'Genre': 'Unterhaltung', 'mediatype': 'episode'})
						listitem.setArt({'icon': icon, 'thumb': image, 'poster': image})
						xbmc.sleep(50)
						PL.add(url=single, listitem=listitem, index=pos_LISTE)
				else:
					log("(navigator.playCODE) StreamURL : {0} ".format(str(endURL)))
					listitem = xbmcgui.ListItem(path=endURL)
					listitem.setInfo(type='Video', infoLabels={'Tvshowtitle': seriesname, 'Title': title, 'Season': season, 'Episode': episode, 'Plot': plot, 'Duration': duration, 'Studio': 'myspass.de', 'Genre': 'Unterhaltung', 'mediatype': 'episode'})
					listitem.setArt({'icon': icon, 'thumb': image, 'poster': image})
	if endURL and Special:
		return PL
	elif endURL and not Special:
		xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem)
	else:
		if direct and not _primeCacheDirect:
			log("(navigator.playCODE:direct) Trying to prime cache")
			return playCODE(IDD, direct=True, _primeCacheDirect=True)
		failing("(navigator.playCODE) AbspielLink-00 : *MYSPASS* Der angeforderte -VideoLink- wurde NICHT gefunden !!!")
		return dialog.notification(translation(30521).format('Video'), translation(30525), icon, 8000)

def listShowsFavs():
	debug_MS("(navigator.listShowsFavs) ------------------------------------------------ START = listShowsFavs -----------------------------------------------")
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	if os.path.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as textobj:
			lines = textobj.readlines()
			for line in lines:
				if line.startswith('###START'):
					part = line.split('###')
					debug_MS("(navigator.listShowsFavs) ### NAME : {0} || URL : {1} || IMAGE : {2} ###".format(str(part[2]), part[3], part[4]))
					addDir(name=part[2], image=part[4], params={'mode': 'listSeasons', 'url': part[3], 'extras': part[4], 'origSERIE': part[2]}, FAVdel=True)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def favs(elem):
	modus = elem[elem.find('MODE=')+5:+8]
	TVSe = elem[elem.find('###START'):]
	TVSe = TVSe[:TVSe.find('END###')]
	name = TVSe.split('###')[2]
	url = TVSe.split('###')[3]
	if modus == 'ADD':
		NORMAL = declare_Open(channelFavsFile, 'NORMAL')
		PLUS = declare_Open(channelFavsFile, 'PLUS')
		if os.path.exists(channelFavsFile):
			with PLUS as textobj:
				content = textobj.read()
				if content.find(TVSe) == -1:
					textobj.seek(0,2) # change is here (for Windows-Error = "IOError: [Errno 0] Error") - because Windows don't like switching between reading and writing at same time !!!
					textobj.write(TVSe+'END###\n')
		else:
			with NORMAL as textobj:
				textobj.write(TVSe+'END###\n')
		xbmc.sleep(500)
		dialog.notification(translation(30526), translation(30527).format(name), icon, 8000)
	elif modus == 'DEL':
		with open(channelFavsFile, 'r') as output:
			lines = output.readlines()
		with open(channelFavsFile, 'w') as input:
			for line in lines:
				if url not in line:
					input.write(line)
		xbmc.executebuiltin('Container.Refresh')
		xbmc.sleep(1000)
		dialog.notification(translation(30526), translation(30528).format(name), icon, 8000)

def AddToQueue():
	return xbmc.executebuiltin('Action(Queue)')

def addDir(name, image, params={}, plot=None, addType=0, FAVdel=False):
	u = '{0}?{1}'.format(HOST_AND_PATH, urlencode(params))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image and params.get('extras') != 'compilation':
		liz.setArt({'fanart': image})
	entries = []
	if addType == 1 and FAVdel is False:
		FAVInfos_1 = 'MODE=ADD###START###{0}###{1}###{2}###END###'.format(params.get('origSERIE'), params.get('url'), image)
		entries.append([translation(30651), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'url': str(FAVInfos_1)}))])
	if FAVdel is True:
		FAVInfos_2 = 'MODE=DEL###START###{0}###{1}###{2}###END###'.format(name, params.get('url'), image)
		entries.append([translation(30652), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'url': str(FAVInfos_2)}))])
	liz.addContextMenuItems(entries, replaceItems=False)
	return xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz, isFolder=True)
