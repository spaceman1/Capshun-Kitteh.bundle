from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
import urlparse

PLUGIN_PREFIX = "/photos/icanhascheezburger"
CACHE_TIME = CACHE_1HOUR

TEXT_PAGES = ['Crazy Things Parents Say', 'Learn From My Fail', 'It Made My Day']
DIR2_PAGES = ['The Daily What']
DIR3_PAGES = ['Lovely Listing', 'Once Upon A Win', 'Epicute', 'Failbook', 'Totally Looks Like', 'The Daily What', 'Daily Squee', 'Must Have Cute']
UNSUPPORTED = ['Bag of Misfits', u'Se\xf1or Gif']

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, L('I CAN HAS CHEEZBURGER'), 'icon-default.jpg', 'art-default.jpg')
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("Pictures", viewMode="Pictures", mediaType="photos")
  MediaContainer.title1 = L('I CAN HAS CHEEZBURGER')
  MediaContainer.art = R('art-default.jpg')
  HTTP.CacheTime = CACHE_TIME
  
####################################################################################################      
  
def MainMenu():
  dir = MediaContainer(art=R('art-default.jpg'), title1="I CAN HAS CHEEZEBURGER?", viewGroup='Details')
  i = 0
  for item in XML.ElementFromURL('http://cheezburger.com/sites/', True).xpath('//div[@class="h1Impact"]')[:-1]:
    title = item.text
    dir.Append(Function(DirectoryItem(SiteMenu, title=title, thumb=R('icon-default.jpg')), index=i))
    i += 1
  return dir
  
def getSiteData(items, dir):
  url = items[0].xpath('./a')[0].get('href')
  thumb = items[0].xpath('./a/img')[0].get('src')
  title = items[1].xpath('./span/a')[0].text
  subtitle = XML.StringFromElement(items[1]).split('<br>')[1]
  Log(repr(title))
  if title in TEXT_PAGES:
    hnd = TxtMenu
  elif title in DIR2_PAGES:
    hnd = DirMenu2
  elif title in DIR3_PAGES:
    hnd = DirMenu3
  elif title in UNSUPPORTED:
    return
  else:
    hnd = DirMenu
  dir.Append(Function(DirectoryItem(hnd, title=title, thumb=thumb, subtitle=subtitle), url=url, dirTitle=title))
  
def SiteMenu(sender, index):
  dir = MediaContainer(art=R('art-default.jpg'), title1="I CAN HAS CHEEZEBURGER", title2=sender.itemTitle, viewGroup='Details')
  page = XML.ElementFromURL('http://cheezburger.com/sites/', True)
  rows = page.xpath('//div[@class="h1Impact"]')[index].xpath('./ancestor::tr/following-sibling::tr')
  for row in rows:
    items = row.xpath('./td')
    if len(items) == 1:
      break
    getSiteData(items[0:2], dir)
    if len(items) == 4:
      getSiteData(items[2:], dir)
      
#      dir.Append(Function(DirectoryItem(hnd, title=title, subtitle=subtitle, thumb=R('icon-default.jpg')), url=url, dirTitle=title))
  return dir
    
def DirMenu(url, dirTitle, isBot=False, sender=None):
  dir = MediaContainer(art=R("art-default.jpg"), viewGroup="Pictures", title2=dirTitle)
  for item in XML.ElementFromURL(url, True).xpath('//p[starts-with(@class, "mine_asset")]'):
    try:
      thumb = item.xpath('./img')[0].get('src')
    except:
      continue
    title = item.xpath('./following-sibling::p')[0].text
    dir.Append(PhotoItem(thumb, title=title, thumb=thumb))
  nexts = XML.ElementFromURL(url, True).xpath('//div[@class="navigation"]//a[starts-with(text(), "Next")]')
  if len(nexts) != 0:
    dir.Append(Function(DirectoryItem(DirMenu, title='Moar', thumb=R('icon-next.png')), url=nexts[0].get('href'), dirTitle=dirTitle))
  return dir

def DirMenu2(url, dirTitle, isBot=False, sender=None):
  dir = MediaContainer(art=R("art-default.jpg"), viewGroup="Pictures", title2=dirTitle)
  for item in XML.ElementFromURL(url, True).xpath('//div[@class="post"]'):
    try:
      thumb = item.xpath('.//div[@class="photo"]/img')[0].get('src')
    except:
      thumb = ''
    try:
      title = item.xpath('.//div[@class="caption"]//strong')[0].text
    except:
      title = ' '
    try:
      summary = String.StripTags(XML.StringFromElement(item.xpath('./div[@class="caption"]')[0]))
    except:
      summary = ''
    if thumb != '':
      Log(thumb)
      dir.Append(Function(PhotoItem(NoMenu, title=title, thumb=thumb)))
  nexts = XML.ElementFromURL(url, True).xpath('//div[@id="footer"]//a[starts-with(text(), "Next")]')
  if len(nexts) != 0:
    nextURL = urlparse.urljoin(url, nexts[0].get('href'))
    dir.Append(Function(DirectoryItem(DirMenu2, title='Moar', thumb=R('icon-next.png')), url=nextURL, dirTitle=dirTitle))
  return dir

def DirMenu3(url, dirTitle, isBot=False, sender=None):
  dir = MediaContainer(art=R("art-default.jpg"), viewGroup="Pictures", title2=dirTitle)
  for item in XML.ElementFromURL(url, True).xpath('//div[@class="post"]'):
    thumbs = item.xpath('.//div[@class="snap_preview"]//img')
    if len(thumbs) == 0:
      continue
    title = item.xpath('./h2/a')[0].text
    if len(thumbs) > 1:
      i = 1
      for thumb in thumbs:
        parent = thumb.xpath('./parent::a')
        src = thumb.get('src')
        if len(parent) != 0 and parent[0].get('href').endswith('/Trophies') or thumb.get('class') == 'content-avatar':
          continue
        dir.Append(PhotoItem(src, title=title + ' %i' % i, thumb=src))
        i += 1
    else:
      thumb = thumbs[0].get('src')
      dir.Append(PhotoItem(thumb, title=title, thumb=thumb))
  nexts = XML.ElementFromURL(url, True).xpath('//div[@class="navigation"]//a[starts-with(text(), "Next")]')
  if len(nexts) != 0:
    dir.Append(Function(DirectoryItem(DirMenu3, title='Moar', thumb=R('icon-next.png')), url=nexts[0].get('href'), dirTitle=dirTitle))
  return dir


def TxtMenu(url, dirTitle, sender=None):
  dir = MediaContainer(art="art-default.jpg", viewGroup="Details", title2=dirTitle)
  for item in XML.ElementFromURL(url, True).xpath('//div[@class = "post"]'):
    title = item.xpath('./h2/a')[0].text
    text = unicode(String.StripTags(XML.StringFromElement(item.xpath('.//blockquote')[0])))
    cleanText = ''
    for c in text:
      if ord(c) == 226:
        cleanText += "'"
      elif ord(c) < 128:
        cleanText += c
    dir.Append(Function(DirectoryItem(NoMenu, title=title, summary=cleanText, thumb=R('icon-default.jpg'))))
  nexts = XML.ElementFromURL(url, True).xpath('//div[@class="navigation"]//a[starts-with(text(), "Next")]')
  if len(nexts) != 0:
    dir.Append(Function(DirectoryItem(TxtMenu, title='Moar', thumb=R('icon-next.png')), url=nexts[0].get('href'), dirTitle=dirTitle))
  return dir
  
def NoMenu(sender):
	pass