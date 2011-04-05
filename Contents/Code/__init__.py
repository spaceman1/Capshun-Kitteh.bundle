import re
import urllib2
import platform

YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YOUTUBE_FMT = [34, 18, 35, 22, 37]
USER_AGENT = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'
VIMEO_URL = 'http://www.vimeo.com/'
CHEEZBURGER_URL = 'http://cheezburger.com'
TEXT_PAGES = ['Crazy Things Parents Say', 'Learn From My Fail', 'It Made My Day']

# TODO: Fix Vimeo Video playback
# TODO: Check FavesMenu works with large number of faves (may need to add /start/count to end of url)
# Known Issue: videos don't show up in faves (blame:cheezburger api)

def Start():
	Plugin.AddPrefixHandler('/photos/capshunkitteh', PhotoMenu, L('Capshun Kitteh'), 'icon-default.png', 'art-default.jpg')
	Plugin.AddPrefixHandler('/video/capshunkitteh', VideoMenu, L('Capshun Kitteh'), 'icon-default.png', 'art-default.jpg')
	Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("_List", viewMode="List", mediaType="items")
	MediaContainer.title1 = 'Capshun Kitteh'
	MediaContainer.viewGroup = '_List'
	DirectoryItem.thumb = R('icon-default.png')
	DirectoryItem.art = R('art-default.jpg')
	PhotoItem.art = R('art-default.jpg')
	VideoItem.art = R('art-default.jpg')
	PrefsItem.art = R('art-default.jpg')
	authorise(getAuthToken())
#	HTTP.Headers['User-Agent'] = USER_AGENT

def ValidatePrefs():
	try:
		int(Prefs['itemsPerPage'])
	except:
		return False
	
#######################################################################################	

def getXMLFields(element):
	d = dict()
	for node in element.xpath('./*'):
		d[node.tag] = node.text
	return d

def unique(items, key=None):
	uniqueVals = set()
	for item in items:
		val = key(item) if (key) else item
		uniqueVals.add(val)
	return uniqueVals

#######################################################################################

def AddToFavorites(sender, key):
	#Log(key)
	Helper.Run('fave', '-a', key, Dict['token'])

def RemoveFromFavorites(sender, key):
	Helper.Run('fave', '-r', key, Dict['token'])
	

#######################################################################################

def getAuthToken():
	token = None
	try:
		token = Dict['token']
	except:
		pass
	if not token:
		token = Helper.Run('fave')
		Dict['token'] = token
	#Log(token)
	return token

def authorise(token):
	if not Prefs['userID'] or not Prefs['password']:
		return None
	# Log-in
	Log(HTTP.Request(CHEEZBURGER_URL + '/Account/SimpleLogin', values={'email':Prefs['userID'], 'password':Prefs['password']}))
	#Log('Cookies: ' + HTTP.GetCookiesForURL(CHEEZBURGER_URL+ '/'))
	
	# Simulate Browser Click
	form = HTML.ElementFromURL(CHEEZBURGER_URL + '/AuthorizeClient.aspx?token=' + token).xpath('//form[@name="aspnetForm"]')[0]
	url = CHEEZBURGER_URL + form.get('action')
	values = dict()
	for input in form.xpath('.//input'):
		values[input.get('name')] = input.get('value')
	HTTP.Request(url, values=values)

#######################################################################################
def PhotoMenu():
	return MainMenu('Image')

def VideoMenu():
	return MainMenu('Video')

def getSites(condition):
	sites = list()
	for site in XML.ElementFromURL('http://api.cheezburger.com/xml/site').xpath('//Site'):
		siteDict = getXMLFields(site) 
		if condition(siteDict) and siteDict['SiteCategory'] != 'STORE & CO.':
			sites.append(siteDict)
	return sites

def MainMenu(assetType):
	dir = MediaContainer()
	dir.Append(Function(DirectoryItem(CategoriesMenu, title='Categories', thumb=S('Book1.png')), assetType=assetType))
	dir.Append(Function(DirectoryItem(AllSitesMenu, title='All Sites', thumb=S('Book2.png')), assetType=assetType))
	dir.Append(Function(DirectoryItem(ConditionalMenu, title='New Sites', thumb=S('FlagGreen.png')), tag='IsNew', assetType=assetType))
	if len(getSites(lambda site:site['IsFeatureSite'] == 'true')):
		dir.Append(Function(DirectoryItem(ConditionalMenu, title='Featured Sites', thumb=S('FlagRed.png')), tag='IsFeatureSite', assetType=assetType))
	if assetType == 'Image' and Prefs['userID'] and Prefs['password']:
		dir.Append(Function(DirectoryItem(FavesMenu, title=L('My Favorites'), thumb=S('Favorite.png')), assetType=assetType))
	dir.Append(Function(DirectoryItem(ConditionalMenu, title='NSFW', thumb=S('Popular.png')), tag='IsNSFW', assetType=assetType))
	dir.Append(PrefsItem(title='Preferences', thumb=S('Gear.png')))
	return dir

def ConditionalMenu(sender, tag, assetType):
	dir = MediaContainer(title1=sender.itemTitle)
	for site in getSites(lambda site:site[tag] == 'true'):
			dir.Append(Function(DirectoryItem(SiteMenu, title=site['Name'], summary=site['Description'], thumb=site['SquareLogoUrl']), assetType=assetType, baseURL=site['SiteId']))
	return dir
	
def FavesMenu(sender, assetType):
	cm = ContextMenu(includeStandardItems=False)
	cm.Append(Function(DirectoryItem(RemoveFromFavorites, title=L('Remove from favorites'))))
	dir = MediaContainer(title2=sender.itemTitle, noCache=True)
	if platform.version().startswith('Darwin Kernel Version 10.6.'):
		dir.contextMenu = cm
	
	try:
		userID = Prefs['userID']
	except:
		return MessageContainer('Not logged in', 'You need to specify a username in your preferences')
	for lol in XML.ElementFromURL('http://api.cheezburger.com/xml/user/%s/favorite/lol' % userID).xpath('//Lol'):
		itemDict = getXMLFields(lol)
		dir.Append(PhotoItem(itemDict['LolImageUrl'], title=itemDict['Title'], thumb=itemDict['ThumbnailImageUrl'], summary=itemDict.get('FullText', ''), contextKey=itemDict['LolId'], contextArgs={}))
	return dir

def AllSitesMenu(sender, assetType):
	sites = getSites(lambda x: True)
	dir = MediaContainer(title2='All Sites')
	for site in sorted(sites, key=lambda site: site['Name']):
		dir.Append(Function(DirectoryItem(SiteMenu, title=site['Name'], thumb=site['SquareLogoUrl'], summary=['Description']), assetType=assetType, baseURL=site['SiteId']))
	return dir
	
#######################################################################################

def CategoriesMenu(sender, assetType):
	sites = getSites(lambda x: True)
	categories = unique(sites, lambda s: s['SiteCategory'])
	dir = MediaContainer()
	
	for category in categories:
		matchingSites = [site for site in sites if (site['SiteCategory'] == category)]
		dir.Append(Function(DirectoryItem(CategoryMenu, title=category, thumb=matchingSites[0]['SquareLogoUrl']), assetType=assetType, sites=matchingSites))
	return dir

def CategoryMenu(sender, assetType, sites):
	dir = MediaContainer(title2=sender.itemTitle)
	for site in sites:
		dir.Append(Function(DirectoryItem(SiteMenu, title=site['Name'], summary=site['Description'], thumb=site['SquareLogoUrl']), assetType=assetType, baseURL=site['SiteId']))
	return dir

def SiteMenu(sender, baseURL, assetType, pageNum=1, title2=None, query=None):
	itemsPerPage = int(Prefs['itemsPerPage'])
	
	dirTitle2 = title2 if (title2) else sender.itemTitle
	
	dir = MediaContainer(title2=dirTitle2)
	
	if Prefs['userID'] != 'None' and Prefs['password'] != 'None' and platform.version().startswith('Darwin Kernel Version 10.6.'):
		cm = ContextMenu(includeStandardItems=False)
		cm.Append(Function(DirectoryItem(AddToFavorites, title=L('Add to favorites'))))
		dir.contextMenu = cm
	
	if dirTitle2 in TEXT_PAGES:
		dir.viewGroup = 'Details'
	
	if assetType == 'Video':
		youTubeCookies = HTTP.GetCookiesForURL('http://www.youtube.com/')
		#vimeoCookies = HTTP.GetCookiesForURL(VIMEO_URL)
		#if not youTubeCookies: youTubeCookies = ''
		#if not vimeoCookies: vimeoCookies = ''
		dir.httpCookies = youTubeCookies #+ ';' + vimeoCookies
		#Log(dir.httpCookies)
	
	items = XML.ElementFromURL(baseURL + '/featured/%i/%i' % (pageNum, itemsPerPage)).xpath('//Asset')
	for item in items:
		itemDict = getXMLFields(item)
		itemAssetType = itemDict['AssetType']
		if itemAssetType != assetType and itemAssetType != 'Text': continue
		
		title = itemDict.get('Title', 'Untitled')
		thumb = itemDict.get('ImageUrl', sender.thumb)
		key = itemDict.get('ContentUrl', sender.thumb)
		summary = itemDict.get('Description', '')
		contextKey = itemDict['AssetId']
		contextArgs = {}
		
		if itemAssetType == 'Image':
			dir.Append(PhotoItem(key, title=title, thumb=thumb, summary=summary, contextKey=contextKey, contextArgs=contextArgs))
		elif itemAssetType == 'Video' and itemDict['VideoType'] == 'YouTube':
			dir.Append(Function(VideoItem(PlayYouTubeVideo, title=title, thumb=thumb, summary=summary, contextKey=contextKey, contextArgs=contextArgs), url=itemDict['ContentUrl']))
		#elif itemAssetType == 'Video' and itemDict['VideoType'] == 'Vimeo':
			#id = key.split('?')[0].split('/')[-1]
			#dir.Append(Function(VideoItem(PlayVimeoVideo, title=title, thumb=thumb, summary=summary, contextKey=contextKey, contextArgs=contextArgs), url=itemDict['ContentUrl']))
		elif itemAssetType == 'Text':
			dir.Append(PhotoItem(sender.thumb, title=title, thumb=thumb, summary=itemDict['FullText']))
		else:
			Log('Unknown type: '+ itemDict['AssetType'])
	
	#if len(dir) == 0:
	#	return SiteMenu(sender, baseURL, assetType, pageNum=pageNum + itemsPerPage, title2=dirTitle2)
	if len(items) == itemsPerPage:
		dir.Append(Function(DirectoryItem(SiteMenu, title='Moar', thumb=sender.thumb), baseURL=baseURL, assetType=assetType, pageNum=pageNum + itemsPerPage, title2=dirTitle2))
	return dir

#######################################################################################
import urllib2, httplib
class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301( 
            self, req, fp, code, msg, headers)              
        result.status = code                                 
        return result                                       

    def http_error_302(self, req, fp, code, msg, headers):   
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)              
        result.status = code                                
        return result

def PlayVimeoVideo(sender, url):
	# Intertube records
	id = url.split('?')[0].split('/')[-1]
	Log(id)
	Log(url)
	headers = {'User-agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-us) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5', 'Cookie' : HTTP.GetCookiesForURL(VIMEO_URL) }
	video = HTTP.Request(url, cacheTime=0, headers=headers).content

	m1 = re.search('"hd":([0-9])', video)
	m2 = re.search('"signature":"([0-9a-f]+)","timestamp":([0-9]+)', video)
	
	if m1 and m2:
		hd = int(m1.groups()[0])
		if Prefs['hd'] == True and hd == True:
			format = 'hd'
		else:
			format = 'sd'
		Log(m2.groups())
		(sig, time) = m2.groups()
		headers['Referer'] = 'http://vimeo.com/%s' % id
		#redirect = 'http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s&codecs=H264,VP8,VP6&type=moogaloop_local&embed_location=' % (id, sig, time, format)
		quality = 'hd' if Prefs['hd'] else 'sd'
		redirect = 'http://player.vimeo.com/play_redirect?quality=%s&codecs=h264&clip_id=%s&time=%s&sig=%s&type=html5_desktop_local' % (quality, id, time, sig)
		Log(redirect)
		return Redirect(redirect)

# Based on YouTube Plug-in
def PlayYouTubeVideo(sender, url):
	yt_page = HTTP.Request(url, cacheTime=1).content
	#yt_page = HTTP.Request(YOUTUBE_VIDEO_PAGE % (video_id), cacheTime=1).content

	fmt_url_map = re.findall('"fmt_url_map".+?"([^"]+)', yt_page)[0]
	fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

	fmts = []
	fmts_info = {}

	for f in fmt_url_map:
		(fmt, url) = f.split('|')
		fmts.append(fmt)
		fmts_info[str(fmt)] = url

	index = YOUTUBE_VIDEO_FORMATS.index(Prefs['youtube_fmt'])
	if YOUTUBE_FMT[index] in fmts:
		fmt = YOUTUBE_FMT[index]
	else:
		for i in reversed( range(0, index+1) ):
			if str(YOUTUBE_FMT[i]) in fmts:
				fmt = YOUTUBE_FMT[i]
				break
			else:
				fmt = 5

	url = fmts_info[str(fmt)].replace('\\u0026', '&')
	return Redirect(url)
