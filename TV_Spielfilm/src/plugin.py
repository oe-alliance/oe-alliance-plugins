#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from base64 import b64encode, b64decode
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, configfile, ConfigDirectory, ConfigInteger, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Input import Input
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest, MultiContentEntryProgress
from Components.Pixmap import Pixmap, MovingPixmap
from Components.ScrollLabel import ScrollLabel
from Components.Slider import Slider
from Components.Sources.List import List
from enigma import eConsoleAppContainer, eListboxPythonMultiContent, eListbox, eEPGCache, eServiceCenter, eServiceReference, eTimer, getDesktop, gFont, loadPic, loadPNG, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
from Plugins.Plugin import PluginDescriptor
from re import findall, match, search, split, sub
from RecordTimer import RecordTimerEntry
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.Standby import TryQuitMainloop
from Screens.TimerEdit import TimerEditList, TimerSanityConflict
from Screens.TimerEntry import TimerEntry
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from ServiceReference import ServiceReference
from time import mktime
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from twisted.web import client, error
from twisted.web.client import getPage, downloadPage
from six.moves.http_client import HTTPException
from six.moves.urllib.parse import unquote_plus, urlencode, parse_qs
from six.moves.urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler, HTTPHandler, HTTPCookieProcessor
from six.moves.urllib.error import URLError, HTTPError
import datetime, os, re, socket, sys, time, six
from os import path
from .util import applySkinVars, MEDIAROOT, PICPATH, ICONPATH, TVSPNG, serviceDB, BlinkingLabel, ItemList, makeWeekDay, scaleskin
from .parser import transCHANNEL, shortenChannel, transHTML, cleanHTML, parsedetail, fiximgLink, parseInfoTable, parseInfoTable2, parsePrimeTimeTable
from .skindef import SKHEADTOP, SKHEADBOTTOM, SKMENU, SKHEADPIC, SKHEADPLAY, SKTIME

try:
    from cookielib import MozillaCookieJar
except Exception:
    from http.cookiejar import MozillaCookieJar

NOTIMER = '\nTimer nicht m\xc3\xb6glich:\nKeine Service Reference vorhanden, der ausgew\xc3\xa4hlte Sender wurde nicht importiert.'
OKZV = 'OK = Vollbild\n< > = Zur\xfcck / Vorw\xc3\xa4rts'
NOEPG = 'Keine EPG Informationen verf\xfcgbar'
if six.PY3:
    NOTIMER = '\nTimer nicht möglich:\nKeine Service Reference vorhanden, der ausgewählte Sender wurde nicht importiert.'
    OKZV = 'OK = Vollbild\n< > = Zurück / Vorwärts'
    NOEPG = 'Keine EPG Informationen verfügbar'
    
def getEPGText():
    try:
        if six.PY2:
            NOEPGTIME = 'Noch keine EPG Informationen verf\xfcgbar\n\nEPG Vorschauzeit: %s Tage\nEPG Vorhaltezeit: %s Stunden' % (str(config.misc.epgcache_timespan.value), str(config.misc.epgcache_outdated_timespan.value))
        else:
            NOEPGTIME = 'Noch keine EPG Informationen verfügbar\n\nEPG Vorschauzeit: %s Tage\nEPG Vorhaltezeit: %s Stunden' % (str(config.misc.epgcache_timespan.value), str(config.misc.epgcache_outdated_timespan.value))
        return NOEPGTIME
    except (KeyError, NameError):
        return NOEPG


config.plugins.tvspielfilm = ConfigSubsection()
#deskWidth = getDesktop(0).size().width()
#if deskWidth >= 1280:
#    config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='full', choices=[('full', '1280x720'), ('normal', '1024x576')])
#    config.plugins.tvspielfilm.position = ConfigInteger(60, (0, 80))
#else:
#    config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='normal', choices=[('full', '1280x720'), ('normal', '1024x576')])
#    config.plugins.tvspielfilm.position = ConfigInteger(40, (0, 160))
config.plugins.tvspielfilm.font_size = ConfigSelection(default='large', choices=[('verylarge', 'Sehr gross'), ('large', 'Gross'), ('normal', 'Normal')])
#config.plugins.tvspielfilm.font = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
#if config.plugins.tvspielfilm.font.value == 'yes':
#    from enigma import addFont
#    try:
#        addFont('/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/font/Sans.ttf', 'Sans', 100, False)
#    except Exception as ex:
#        addFont('/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/font/Sans.ttf', 'Sans', 100, False, 0)

config.plugins.tvspielfilm.meintvs = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.login = ConfigText(default='', fixed_size=False)
config.plugins.tvspielfilm.password = ConfigPassword(default='', fixed_size=False)
config.plugins.tvspielfilm.encrypt = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.picon = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.piconfolder = ConfigDirectory(default='/media/usb/picon/')
config.plugins.tvspielfilm.color = ConfigSelection(default='0x00000000', choices=[('0x00000000', 'Skin Default'),
 ('0x00F0A30A', 'Amber'),
 ('0x007895BC', 'Blue'),
 ('0x00825A2C', 'Brown'),
 ('0x000050EF', 'Cobalt'),
 ('0x00911D10', 'Crimson'),
 ('0x001BA1E2', 'Cyan'),
 ('0x00008A00', 'Emerald'),
 ('0x0070AD11', 'Green'),
 ('0x006A00FF', 'Indigo'),
 ('0x00BB0048', 'Magenta'),
 ('0x0076608A', 'Mauve'),
 ('0x006D8764', 'Olive'),
 ('0x00C3461B', 'Orange'),
 ('0x00F472D0', 'Pink'),
 ('0x00E51400', 'Red'),
 ('0x007A3B3F', 'Sienna'),
 ('0x00647687', 'Steel'),
 ('0x00149BAF', 'Teal'),
 ('0x004176B6', 'Tufts'),
 ('0x006C0AAB', 'Violet'),
 ('0x00BF9217', 'Yellow')])
config.plugins.tvspielfilm.tipps = ConfigSelection(default='yes', choices=[('no', 'Gruene Taste im Startmenue'), ('yes', 'Beim Start des Plugins'), ('false', 'Deaktiviert')])
config.plugins.tvspielfilm.primetime = ConfigSelection(default='primetime', choices=[('primetime', 'Primetime'), ('now', 'Aktuelle Zeit')])
config.plugins.tvspielfilm.eventview = ConfigSelection(default='list', choices=[('list', 'Programmliste'), ('info', 'Sendungsinfo')])
config.plugins.tvspielfilm.genreinfo = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
config.plugins.tvspielfilm.zapexit = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.maxsearch = ConfigInteger(50, (10, 999))
config.plugins.tvspielfilm.maxgenre = ConfigInteger(250, (10, 999))
config.plugins.tvspielfilm.autotimer = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])


skinFactor = 1

# Check if is Full HD / UHD
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()
if DESKTOP_WIDTH > 1920:
	skinFactor = 3.0
elif DESKTOP_WIDTH > 1280:
	skinFactor = 1.5
else:
	skinFactor = 1

class tvAllScreen(Screen):
    def __init__(self, session, skin=None, dic=None, scale=False):
        self.session = session
        w = DESKTOP_WIDTH - (40 * skinFactor)
        mw = w - (20 * skinFactor)
        h = DESKTOP_HEIGHT - (60 * skinFactor) - 40
        mh = h - 60
        self.menuwidth = mw
        if dic == None:
            dic = {}

        if config.plugins.tvspielfilm.font_size.value == 'verylarge':
            fontsize = 28
            fontsize2 = 26
        elif config.plugins.tvspielfilm.font_size.value == 'large':
            fontsize = 20
            fontsize2 = 18
        else:
            fontsize = 18
            fontsize2 = 16

        if skinFactor == 1:
            dic["slider"] = '315'
        elif skinFactor == 1.5:
            dic["slider"] = '450'
        dic["fontsize"] = str(fontsize)
        dic["fontsize2"] = str(fontsize2)
        dic["fullsize"] = "%s,%s" % (DESKTOP_WIDTH,DESKTOP_HEIGHT)
        dic["screenpos"] = "center,%s" % (60 * skinFactor)
        dic["screensize"] = "%s,%s" % (w,h)
        dic["headw"] = str(w)
        dic["picpath"] = PICPATH
        dic["menusize"] = "%s,%s" % (mw,mh)
        if skin != None:
            self.skin = applySkinVars(skin, dic)
            if scale == True:
                self.skin = scaleskin(self.skin, skinFactor)
        Screen.__init__(self, session)
        self.fontlarge = True
        if config.plugins.tvspielfilm.font_size.value == 'normal':
            self.fontlarge = False
        self.baseurl = 'https://www.tvspielfilm.de'
        self.servicefile = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/service.references'

    def hideScreen(self):
        if self.hideflag == True:
            self.hideflag = False
            count = 40
            while count > 0:
                count -= 1
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * count / 40))
                f.close()

        else:
            self.hideflag = True
            count = 0
            while count < 40:
                count += 1
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * count / 40))
                f.close()

    def zapUp(self):
        if InfoBar and InfoBar.instance:
            InfoBar.zapUp(InfoBar.instance)

    def zapDown(self):
        if InfoBar and InfoBar.instance:
            InfoBar.zapDown(InfoBar.instance)

    def picReturn(self):
        pass

    def makeTimerDB(self):
        timerxml = open('/etc/enigma2/timers.xml').read()
        timer = re.findall('<timer begin="(.*?)" end=".*?" serviceref="(.*?)"', timerxml)
        timerfile = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/timer.db'
        f = open(timerfile, 'w')
        data = ''
        idx = 0
        for x in timer:
            idx += 1

        for i in range(idx):
            try:
                timerstart = timer[i - 1][0]
                timerstart = int(timerstart) + int(config.recording.margin_before.value) * 60
                timerday = time.strftime('%Y-%m-%d', time.localtime(timerstart))
                timerhour = time.strftime('%H:%M', time.localtime(timerstart))
                timersref = timer[i - 1][1]
                data = data + timerday + ':::' + timerhour + ':::' + timersref + '\n'
            except IndexError:
                pass

        f.write(data)
        f.close()
        self.timer = data
    
    def getFill(self, text):
        return '______________________________________\n%s' % text

class tvAllScreenFull(tvAllScreen):
    skin = '\n\t\t\t\t<screen position="0,0" size="{size}" >\n\t\t\t\t</screen>'
    def __init__(self, session):
        size = "%s,%s" % (DESKTOP_WIDTH,DESKTOP_HEIGHT)
        dict = {'size' : size}
        tvAllScreen.__init__(self, session, tvAllScreenFull.skin, dict)


class tvBaseScreen(tvAllScreen):
    def __init__(self, session, skin=None, dic=None, scale=True):
        tvAllScreen.__init__(self, session, skin, dic, scale)
        self.picfile = '/tmp/tvspielfilm.jpg'
        self.pic1 = '/tmp/tvspielfilm1.jpg'
        self.pic2 = '/tmp/tvspielfilm2.jpg'
        self.pic3 = '/tmp/tvspielfilm3.jpg'
        self.pic4 = '/tmp/tvspielfilm4.jpg'
        self.pic5 = '/tmp/tvspielfilm5.jpg'
        self.pic6 = '/tmp/tvspielfilm6.jpg'
        self.localhtml = '/tmp/tvspielfilm.html'
        self.localhtml2 = '/tmp/tvspielfilm2.html'
        self.tagestipp = False
        if config.plugins.tvspielfilm.picon.value == 'yes':
            self.picon = True
            self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
        else:
            self.picon = False
        return

    def finishedAutoTimer(self, answer):
        if answer:
            from Plugins.Extensions.AutoTimer.AutoTimerEditor import AutoTimerEditor
            answer, session = answer
            session.openWithCallback(self.finishedAutoTimerEdit, AutoTimerEditor, answer)

    def finishedAutoTimerEdit(self, answer):
        if answer:
            from Plugins.Extensions.AutoTimer.plugin import autotimer
            if autotimer is None:
                from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                autotimer = AutoTimer()
            autotimer.add(answer)
            autotimer.writeXml()
        return

    def _getPic(self, pic, output):
        f = open(pic, 'wb')
        f.write(output)
        f.close()
        return loadPic(pic, 135, 90, 3, 0, 0, 0)

    def getPic1(self, output):
        currPic = self._getPic(self.pic1, output)
        if currPic != None:
            self['pic1'].instance.setPixmap(currPic)
        return

    def getPic2(self, output):
        currPic = self._getPic(self.pic2, output)
        if currPic != None:
            self['pic2'].instance.setPixmap(currPic)
        return

    def getPic3(self, output):
        currPic = self._getPic(self.pic3, output)
        if currPic != None:
            self['pic3'].instance.setPixmap(currPic)
        return

    def getPic4(self, output):
        currPic = self._getPic(self.pic4, output)
        if currPic != None:
            self['pic4'].instance.setPixmap(currPic)
        return

    def getPic5(self, output):
        currPic = self._getPic(self.pic5, output)
        if currPic != None:
            self['pic5'].instance.setPixmap(currPic)
        return

    def getPic6(self, output):
        currPic = self._getPic(self.pic6, output)
        if currPic != None:
            self['pic6'].instance.setPixmap(currPic)
        return

    def GetPics(self, picurllist, offset, show=True, playshow=False):
        try:
            picurl1 = picurllist[offset]
            self.picdownload(picurl1, self.getPic1)
            if show:
                self['pic1'].show()
            if playshow:
                self['play1'].show()
        except IndexError:
            if playshow:
                self['play1'].hide()
            if show:
                self['pic1'].hide()
            else:
                return

        try:
            picurl2 = picurllist[offset + 1]
            self.picdownload(picurl2, self.getPic2)
            if show:
                self['pic1'].show()
            if playshow:
                self['play2'].show()
        except IndexError:
            if playshow:
                self['play2'].hide()
            if show:
                self['pic2'].hide()
            else:
                return

        try:
            picurl3 = picurllist[offset + 2]
            self.picdownload(picurl3, self.getPic3)
            if show:
                self['pic3'].show()
            if playshow:
                self['play3'].show()
        except IndexError:
            if playshow:
                self['play3'].hide()
            if show:
                self['pic3'].hide()
            else:
                return

        try:
            picurl4 = picurllist[offset + 3]
            self.picdownload(picurl4, self.getPic4)
            if show:
                self['pic4'].show()
            if playshow:
                self['play4'].show()
        except IndexError:
            if playshow:
                self['play4'].hide()
            if show:
                self['pic4'].hide()
            else:
                return

        try:
            picurl5 = picurllist[offset + 4]
            self.picdownload(picurl5, self.getPic5)
            if playshow:
                self['play5'].show()
            if show:
                self['pic5'].show()
        except IndexError:
            if playshow:
                self['play5'].hide()
            if show:
                self['pic5'].hide()
            else:
                return

        try:
            picurl6 = picurllist[offset + 5]
            self.picdownload(picurl6, self.getPic6)
            if playshow:
                self['play6'].show()
            if show:
                self['pic6'].show()
        except IndexError:
            if playshow:
                self['play6'].hide()
            if show:
                self['pic6'].hide()

    def picdownload(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.picdownloadError)

    def picdownloadError(self, output):
        pass

    def getRecPNG(self):
        return self.getPNG("icon-rec", self.menuwidth - 140)

    def getPNG(self, x, Pos):
        if self.picon == True:
            png = '%s%sHD.png' % (ICONPATH, x)
            if fileExists(png):
                return MultiContentEntryPixmapAlphaTest(pos=(Pos, 20), size=(60, 20), png=loadPNG(png))
        else:
            png = '%s%sHD.png' % (ICONPATH, x)
            if fileExists(png):
                return MultiContentEntryPixmapAlphaTest(pos=(Pos, 10), size=(60, 20), png=loadPNG(png))
        return None

    def makePostTimer(self, output):
        output = six.ensure_str(output)
        startpos = output.find('<div class="content-area">')
        endpos = output.find('>Weitere Bildergalerien<')
        if endpos == -1:
            endpos = output.find('<h2 class="broadcast-info">')
            if endpos == -1:
                endpos = output.find('<div class="OUTBRAIN"')
                if endpos == -1:
                    endpos = output.find('</footer>')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        infotext = re.findall('<span class="text-row">(.*?)<', bereich)
        try:
            parts = infotext[0].split(', ')
            x = parts[0]
            if x == 'Heute':
                d = sub('....-', '', str(self.date))
                d2 = sub('-..', '', d)
                d3 = sub('..-', '', d)
                x = 'he ' + d3 + '.' + d2 + '.'
            day = sub('.. ', '', x)
            self.day = sub('[.]..[.]', '', day)
            month = sub('.. ..[.]', '', x)
            month = sub('[.]', '', month)
            date = str(self.date) + 'FIN'
            year = sub('......FIN', '', date)
            self.postdate = year + '-' + month + '-' + self.day
            today = datetime.date(int(year), int(month), int(self.day))
            one_day = datetime.timedelta(days=1)
            self.nextdate = today + one_day
        except:
            pass

        try:
            parts = infotext[0].split(', ')
            x = parts[1]
            start = sub(' - ..:..', '', x)
            start = start + ':00'
            end = sub('..:.. - ', '', x)
            end = end + ':00'
            self.start = start
            self.end = end
        except IndexError:
            pass

        shortdesc = search('<section class="serial-info">\\n\\s+(.*?)</section>', bereich)
        if shortdesc is not None:
            self.shortdesc = sub('<span class="info">', '', shortdesc.group(1))
            self.shortdesc = sub('</span>\\s+', ', ', self.shortdesc)
            self.shortdesc = sub('  ', '', self.shortdesc)
        else:
            self.shortdesc = ''
        name = re.findall('<h1 class="headline headline--article">(.*?)</h1>', bereich)
        try:
            self.name = name[0]
        except IndexError:
            name = re.findall('<span itemprop="name"><strong>(.*?)</strong></span>', bereich)
            try:
                self.name = name[0]
            except IndexError:
                self.name = ''

        self.current = 'postview'
        self.postviewready = True
        self.red()
        return

    def makeTimer(self):
        if config.plugins.tvspielfilm.autotimer.value == 'yes' and fileExists('/usr/lib/enigma2/python/Plugins/Extensions/AutoTimer/plugin.pyo'):
            self.autotimer = True
            self.session.openWithCallback(self.choiceTimer, ChoiceBox, title='Timer Auswahl', list=[('Timer', 'timer'), ('AutoTimer', 'autotimer')])
        else:
            self.autotimer = False
            self.red()

    def choiceTimer(self, choice):
        choice = choice and choice[1]
        if choice == 'autotimer':
            self.autotimer = True
            self.red()
        else:
            self.autotimer = False
            self.red()

    def finishSanityCorrection(self, answer):
        self.finishedTimer(answer)

    def _makePostviewPage(self, string):
        output = open(self.localhtml2, 'r').read()
        output = six.ensure_str(output)
        self['label2'].setText('= Timer')
        self['label3'].setText('= YouTube')
        self['label4'].setText('= Wikipedia')
        self['searchmenu'].hide()
        self['searchlogo'].hide()
        self['searchtimer'].hide()
        self['searchtext'].hide()
        output = sub('</dl>.\n\\s+</div>.\n\\s+</section>', '</cast>', output)
        startpos = output.find('<div class="content-area">')
        endpos = output.find('>Weitere Bildergalerien<')
        if endpos == -1:
            endpos = output.find('</cast>')
            if endpos == -1:
                endpos = output.find('<h2 class="broadcast-info">')
                if endpos == -1:
                    endpos = output.find('<div class="OUTBRAIN"')
                    if endpos == -1:
                        endpos = output.find('</footer>')
        bereich = output[startpos:endpos]
        bereich = cleanHTML(bereich)
        if search('rl: .https://video.tvspielfilm.de/.*?mp4', output) is not None:
            trailerurl = search('rl: .https://video.tvspielfilm.de/(.*?).mp4', output)
            self.trailerurl = 'https://video.tvspielfilm.de/' + trailerurl.group(1) + '.mp4'
            self.trailer = True
        else:
            self.trailer = False
        bereich = sub('" alt=".*?" width="', '" width="', bereich)
        picurl = search('<img src="(.*?)" width="', bereich)
        if picurl is not None:
            self.download(picurl.group(1), self.getPicPost)
            self['picpost'].show()
        else:
            picurl = search('<meta property="og:image" content="(.*?)"', output)
            if picurl is not None:
                self.download(picurl.group(1), self.getPicPost)
                self['picpost'].show()
            else:
                picurl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
                self.download(picurl, self.getPicPost)
                self['picpost'].show()
        if self.search == False:
            title = search('<title>(.*?)</title>', output)
            self.title = transHTML(title.group(1))
            self.setTitle(self.title)
        if search('<ul class="rating-dots">', bereich) is not None:
            self.movie = True
        else:
            self.movie = False
        if search('<div class="film-gallery">', output) is not None:
            self.mehrbilder = True
            if self.trailer == True:
                self['label'].setText('OK = Zum Video, Text = Fotostrecke, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
            else:
                self['label'].setText('OK = Fotostrecke, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
        else:
            self.mehrbilder = False
            if self.trailer == True:
                self['label'].setText('OK = Zum Video, Text = Vollbild, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
            else:
                self['label'].setText('OK = Vollbild, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
        infotext = re.findall('<span class="text-row">(.*?)<', bereich)
        try:
            parts = infotext[0].split(', ')
            x = parts[0]
            if x == 'Heute':
                d = sub('....-', '', str(self.date))
                d2 = sub('-..', '', d)
                d3 = sub('..-', '', d)
                x = 'he ' + d3 + '.' + d2 + '.'
            day = sub('.. ', '', x)
            self.day = sub('[.]..[.]', '', day)
            month = sub('.. ..[.]', '', x)
            month = sub('[.]', '', month)
            date = str(self.date) + 'FIN'
            year = sub('......FIN', '', date)
            self.postdate = year + '-' + month + '-' + self.day
            today = datetime.date(int(year), int(month), int(self.day))
            one_day = datetime.timedelta(days=1)
            self.nextdate = today + one_day
        except:
            pass

        try:
            parts = infotext[0].split(', ')
            x = parts[1]
            start = sub(' - ..:..', '', x)
            start = start + ':00'
            end = sub('..:.. - ', '', x)
            end = end + ':00'
            self.start = start
            self.end = end
        except IndexError:
            pass

        try:
            parts = infotext[0].split(', ')
            self['infotext'].setText(parts[0])
            self['infotext'].show()
        except IndexError:
            self['infotext'].setText('')

        try:
            parts = infotext[0].split(', ')
            self['infotext2'].setText(parts[1])
            self['infotext2'].show()
        except IndexError:
            self['infotext2'].setText('')

        try:
            parts = infotext[0].split(', ')
            self['infotext3'].setText(parts[2])
            self['infotext3'].show()
        except IndexError:
            self['infotext3'].setText('')

        try:
            parts = infotext[1].split(', ')
            self['infotext4'].setText(parts[0])
            self['infotext4'].show()
        except IndexError:
            self['infotext4'].setText('')

        try:
            parts = infotext[1].split(', ')
            self['infotext5'].setText(parts[1])
            self['infotext5'].show()
        except IndexError:
            self['infotext5'].setText('')

        try:
            parts = infotext[1].split(', ')
            self['infotext6'].setText(parts[2])
            self['infotext6'].show()
        except IndexError:
            self['infotext6'].setText('')

        try:
            parts = infotext[2].split(', ')
            self['infotext7'].setText(parts[0] + ', ' + parts[1])
            self['infotext7'].show()
        except IndexError:
            self['infotext7'].setText('')

        try:
            self['infotext8'].setText(infotext[3])
            self['infotext8'].show()
        except IndexError:
            self['infotext8'].setText('')

        tvinfo = re.findall('<span class="add-info (.*?)">', bereich)
        for pos in list(range(4)):
            try:
                tvi = ICONPATH + tvinfo[pos] + 'HD.png'
                tvis = 'tvinfo' + str(pos+1)
                self.showPicTVinfoX(tvi, tvis)
                self[tvis].show()
            except IndexError:
                pass

        self['piclabel'].setText(self.start[0:5])
        try:
            parts = infotext[0].split(', ')
            text = shortenChannel(parts[2])
            self['piclabel2'].setText(text[0:10])
        except IndexError:
            self['piclabel2'].setText('')

        shortdesc = search('<section class="serial-info">\\n\\s+(.*?)</section>', bereich)
        if shortdesc is not None:
            self.shortdesc = sub('<span class="info">', '', shortdesc.group(1))
            self.shortdesc = sub('</span>\\s+', ', ', self.shortdesc)
            self.shortdesc = sub('  ', '', self.shortdesc)
        else:
            self.shortdesc = ''
        name = re.findall('<h1 class="headline headline--article">(.*?)</h1>', bereich)
        try:
            self.name = name[0]
        except IndexError:
            name = re.findall('<span itemprop="name"><strong>(.*?)</strong></span>', bereich)
            try:
                self.name = name[0]
            except IndexError:
                self.name = ''

        if self.tagestipp == True:
            channel = re.findall("var adsc_sender = '(.*?)'", output)
            try:
                self.sref = self.service_db.lookup(channel[0])
                if self.sref != 'nope':
                    self.zap = True
            except IndexError:
                pass

        text = parsedetail(bereich)

        fill = self.getFill('TV Spielfilm Online\n\n*Info/EPG = EPG einblenden')
        self.POSTtext = text + fill
        self['textpage'].setText(self.POSTtext)
        self['textpage'].show()
        self['slider_textpage'].show()
        self.showEPG = False
        self.postviewready = True
        return

    def showsearch(self):
        self.postviewready = False
        self['infotext'].hide()
        self['infotext2'].hide()
        self['infotext3'].hide()
        self['infotext4'].hide()
        self['infotext5'].hide()
        self['infotext6'].hide()
        self['infotext7'].hide()
        self['infotext8'].hide()
        self['cinlogo'].hide()
        self['playlogo'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['piclabel'].hide()
        self['piclabel2'].hide()
        self['tvinfo1'].hide()
        self['tvinfo2'].hide()
        self['tvinfo3'].hide()
        self['tvinfo4'].hide()
        self['tvinfo5'].hide()
        self['label'].setText('')
        self['label2'].setText('')
        self['label3'].setText('')
        self['label4'].setText('')
        self['searchmenu'].show()
        self['searchlogo'].show()
        self['searchtimer'].show()
        self['searchtext'].show()

    def IMDb(self):
        if self.current == 'postview':
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo'):
                from Plugins.Extensions.IMDb.plugin import IMDB
                self.session.open(IMDB, self.name)
            else:
                self.session.openWithCallback(self.IMDbInstall, MessageBox, '\nDas IMDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)
                return

    def TMDb(self):
        if self.current == 'postview':
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo'):
                from Plugins.Extensions.TMDb.plugin import TMDbMain
                self.session.open(TMDbMain, self.name)
            else:
                self.session.openWithCallback(self.TMDbInstall, MessageBox, '\nDas TMDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)
                return

    def TVDb(self):
        if self.current == 'postview':
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TheTVDB/plugin.pyo'):
                from Plugins.Extensions.TheTVDB.plugin import TheTVDBMain
                self.name = sub('Die ', '', self.name)
                self.session.open(TheTVDBMain, self.name)
            else:
                self.session.openWithCallback(self.TVDbInstall, MessageBox, '\nDas TheTVDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)
                return

    def IMDbInstall(self, answer):
        if answer is True:
            self.container = eConsoleAppContainer()
            self.container.appClosed.append(self.finishedIMDbInstall)
            self.container.execute('opkg update && opkg install enigma2-plugin-extensions-imdb')

    def finishedIMDbInstall(self, retval):
        del self.container.appClosed[:]
        del self.container
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo'):
            self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas IMDb Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, '\nDas IMDb Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das IMDb Plugin manuell.', MessageBox.TYPE_ERROR)

    def TMDbInstall(self, answer):
        if answer is True:
            self.container = eConsoleAppContainer()
            self.container.appClosed.append(self.finishedTMDbInstall)
            self.container.execute('opkg update && opkg install enigma2-plugin-extensions-tmdbinfo')

    def finishedTMDbInstall(self, retval):
        del self.container.appClosed[:]
        del self.container
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo'):
            self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas TMDb Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, '\nDas TMDb Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das TMDb Plugin manuell.', MessageBox.TYPE_ERROR)

    def TVDbInstall(self, answer):
        if answer is True:
            self.container = eConsoleAppContainer()
            self.container.appClosed.append(self.finishedTVDbInstall)
            self.container.execute('opkg update && opkg install enigma2-plugin-extensions-thetvdb')

    def finishedTVDbInstall(self, retval):
        del self.container.appClosed[:]
        del self.container
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TheTVDB/plugin.pyo'):
            self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas TheTVDb Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, '\nDas TheTVDb Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das TheTVDb Plugin manuell.', MessageBox.TYPE_ERROR)

    def restartGUI(self, answer):
        if answer is True:
            try:
                self.session.open(TryQuitMainloop, 3)
            except RuntimeError:
                self.close()

    def playTrailer(self):
        if self.current == 'postview' and self.postviewready == True and self.trailer == True:
            sref = eServiceReference(4097, 0, self.trailerurl)
            sref.setName(self.name)
            self.session.open(MoviePlayer, sref)

    def _pressText(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.mehrbilder == True:
                self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
            else:
                self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)


class TVTippsView(tvBaseScreen):
    def __init__(self, session, link, sparte):
        skin = """
        <screen name="TVTippsView" position="{screenpos}" size="{screensize}" title=" ">
            %s%s%s%s
        </screen>""" % ( SKHEADTOP, SKMENU, SKHEADPIC, SKHEADBOTTOM )
        tvBaseScreen.__init__(self, session, skin)
        if sparte == 'neu':
            self.titel = 'TV Neuerscheinungen - TV Spielfilm'
        else:
            self.titel = 'TV-Tipps - TV Spielfilm'
        self.current = 'menu'
        self.oldcurrent = 'menu'
        self.sparte = sparte
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.picurllist = []
        self.searchlink = []
        self.searchref = []
        self.searchentries = []
        self.start = ''
        self.end = ''
        self.day = ''
        self.name = ''
        self.shortdesc = ''
        self.sref = []
        self.postlink = link
        self.link = link
        self.trailerurl = ''
        self.POSTtext = ''
        self.EPGtext = ''
        self.hideflag = True
        self.new = False
        self.newfilter = False
        self.search = False
        self.rec = False
        self.ready = False
        self.postviewready = False
        self.mehrbilder = False
        self.trailer = False
        self.movie = False
        self.datum = False
        self.filter = True
        self.len = 0
        self.oldindex = 0
        self.oldsearchindex = 1
        self['pic1'] = Pixmap()
        self['pic2'] = Pixmap()
        self['pic3'] = Pixmap()
        self['pic4'] = Pixmap()
        self['pic5'] = Pixmap()
        self['pic6'] = Pixmap()
        self['picpost'] = Pixmap()
        self['tvinfo1'] = Pixmap()
        self['tvinfo2'] = Pixmap()
        self['tvinfo3'] = Pixmap()
        self['tvinfo4'] = Pixmap()
        self['tvinfo5'] = Pixmap()
        self['cinlogo'] = Pixmap()
        self['cinlogo'].hide()
        self['playlogo'] = Pixmap()
        self['playlogo'].hide()
        self['searchlogo'] = Pixmap()
        self['searchlogo'].hide()
        self['searchtimer'] = Pixmap()
        self['searchtimer'].hide()
        self['searchtext'] = Label('')
        self['searchtext'].hide()
        self['textpage'] = ScrollLabel('')
        self['infotext'] = Label('')
        self['infotext'].hide()
        self['infotext2'] = Label('')
        self['infotext2'].hide()
        self['infotext3'] = Label('')
        self['infotext3'].hide()
        self['infotext4'] = Label('')
        self['infotext4'].hide()
        self['infotext5'] = Label('')
        self['infotext5'].hide()
        self['infotext6'] = Label('')
        self['infotext6'].hide()
        self['infotext7'] = Label('')
        self['infotext7'].hide()
        self['infotext8'] = Label('')
        self['infotext8'].hide()
        self['piclabel'] = Label('')
        self['piclabel'].hide()
        self['piclabel2'] = Label('')
        self['piclabel2'].hide()
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['searchmenu'] = ItemList([])
        self['searchmenu'].hide()
        self['menu'] = ItemList([])
        self['label'] = BlinkingLabel('Bitte warten...')
        self['label'].startBlinking()
        self['label2'] = Label('= Timer')
        self['label3'] = Label('= Suche')
        self['label4'] = Label('= Zappen')
        self['actions'] = ActionMap(['OkCancelActions',
         'ChannelSelectBaseActions',
         'DirectionActions',
         'EPGSelectActions',
         'NumberActions',
         'InfobarTeletextActions',
         'MoviePlayerActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.nextDay,
         'prevBouquet': self.prevDay,
         'nextMarker': self.nextWeek,
         'prevMarker': self.prevWeek,
         '0': self.gotoEnd,
         '1': self.zapUp,
         '2': self.zapDown,
         '7': self.IMDb,
         '8': self.TMDb,
         '9': self.TVDb,
         'info': self.getEPG,
         'epg': self.getEPG,
         'leavePlayer': self.youTube,
         'startTeletext': self.pressText}, -1)
        self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
         'yellow': self.yellow,
         'red': self.makeTimer,
         'blue': self.hideScreen}, -1)
        self.service_db = serviceDB(self.servicefile)
        self.timer = open('/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/timer.db').read()
        self.date = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        self.nextdate = self.date + one_day
        self.weekday = makeWeekDay(self.date.weekday())
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        if config.plugins.tvspielfilm.genreinfo.value == 'no':
            self.showgenre = False
        else:
            self.showgenre = True
        self.makeTVTimer = eTimer()
        self.makeTVTimer.callback.append(self.downloadFullPage(link, self.makeTVTipps))
        self.makeTVTimer.start(500, True)

    def makeTVTipps(self, string):
        output = open(self.localhtml, 'r').read()
        output = six.ensure_str(output)
        self.sref = []
        self['pic1'].hide()
        self['pic2'].hide()
        self['pic3'].hide()
        self['pic4'].hide()
        self['pic5'].hide()
        self['pic6'].hide()
        if self.sparte == 'neu':
            startpos = output.find('id="c-sp-opener"><span>Spielfilm</span></a>')
            endpos = output.find('id="c-spo-opener"><span>Sport</span></a>')
        elif self.sparte == 'Spielfilm':
            startpos = output.find('id="c-sp-opener"><span>Spielfilm</span></a>')
            endpos = output.find('id="c-se-opener"><span>Serie</span></a>')
        elif self.sparte == 'Serie':
            startpos = output.find('id="c-se-opener"><span>Serie</span></a>')
            endpos = output.find('id="c-re-opener"><span>Report</span></a>')
        elif self.sparte == 'Report':
            startpos = output.find('id="c-re-opener"><span>Report</span></a>')
            endpos = output.find('id="c-u-opener"><span>Unterhaltung</span></a>')
        elif self.sparte == 'Unterhaltung':
            startpos = output.find('id="c-u-opener"><span>Unterhaltung</span></a>')
            endpos = output.find('id="c-kin-opener"><span>Kinder</span></a>')
        elif self.sparte == 'Kinder':
            startpos = output.find('id="c-kin-opener"><span>Kinder</span></a>')
            endpos = output.find('id="c-spo-opener"><span>Sport</span></a>')
        elif self.sparte == 'Sport':
            startpos = output.find('id="c-spo-opener"><span>Sport</span></a>')
            endpos = output.find('<p class="h3 headline headline--section">')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        date = str(self.date.strftime('%d.%m.%Y'))
        self.titel = 'TV-Tipps - ' + str(self.sparte) + ' - ' + str(self.weekday) + ', ' + date
        if self.sparte == 'neu':
            self.titel = 'TV Neuerscheinungen - ' + str(self.weekday) + ', ' + date
        self.setTitle(self.titel)
        bereich = sub('<div class="full-image image-wrapper.*?">\n\\s+<a href="', '<td>LINK', bereich)
        bereich = sub('" target="_self" onclick="', '</td>', bereich)
        bereich = sub('class="aholder" title=".*?<strong>', '<td>NAME', bereich)
        bereich = sub('class="aholder" title="', '<td>TITEL', bereich)
        bereich = sub('<span class="add-info ', '<td>INFO', bereich)
        bereich = sub('">TIPP</span>', '</td>', bereich)
        bereich = sub('">LIVE</span>', '</td>', bereich)
        bereich = sub('">HDTV</span>', '</td>', bereich)
        bereich = sub('">NEU</span>', '</td>', bereich)
        bereich = sub('">OMU</span>', '</td>', bereich)
        bereich = sub('"></span>', '</td>', bereich)
        bereich = sub('" data-src="', '</td><td>PIC', bereich)
        bereich = sub('" alt="', '</td>', bereich)
        bereich = sub('<span class="time">', '<td>TIME', bereich)
        bereich = sub('</span>', '</td>', bereich)
        bereich = sub('</strong>', '</td>', bereich)
        bereich = sub('opener"><span>', '', bereich)
        bereich = sub('<span>Play</td>', '', bereich)
        bereich = sub('<span>', '<td>GENRE', bereich)
        bereich = sub('<span class="logotype chl_bg_. c-', '<td>LOGO', bereich)
        bereich = sub('">\n.*?<a href="', '</td>', bereich)
        bereich = sub('<wbr/>', '', bereich)
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.picurllist = []
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        pictopoffset = 0
        picleftoffset = 0
        if self.picon == True:
            pictopoffset = 11
            picleftoffset = 41
        sref = None
        for x in a:
            if search('LINK', x) is not None:
                icount = 0
                if sref != None and self.new == True:
                    self.sref.append(sref)
                    self.picurllist.append(picfilter)
                    self.tvlink.append(linkfilter)
                    self.tvtitel.append(titelfilter)
                    self.tventries.append(res)
                res = [x]
                self.new = False
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, 90), font=-1, backcolor_sel=self.back_color, text=''))
                x = sub('LINK', '', x)
                linkfilter = x
            if search('PIC', x) is not None:
                x = sub('PIC', '', x)
                picfilter = x
            if search('TIME', x) is not None:
                x = sub('TIME', '', x)
                start = x
                res.append(MultiContentEntryText(pos=(74 + picleftoffset, 18), size=(75, 25), font=-1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
            if search('INFO', x) is not None:
                icount = icount + 1
                x = sub('INFO', '', x)
                if search('neu|new', x) is not None:
                    self.new = True
                png = '%s%sHD.png' % (ICONPATH, x)
                if fileExists(png):
                    if icount == 1:
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 90, 20), size=(60, 20), png=loadPNG(png)))
                    else:
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 90, 50), size=(60, 20), png=loadPNG(png)))
            if search('NAME', x) is not None:
                x = sub('NAME', '', x)
                titelfilter = x
                res.append(MultiContentEntryText(pos=(162 + picleftoffset, 17), size=(self.menuwidth - 330 - picleftoffset, 30), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
            if search('GENRE', x) is not None:
                x = sub('GENRE', '', x)
                res.append(MultiContentEntryText(pos=(162 + picleftoffset, 48), size=(self.menuwidth - 330 - picleftoffset, 30), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                if self.sparte == 'Spielfilm':
                    png = ICONPATH + 'rating small1HD.png'
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 160, 25), size=(40, 40), png=loadPNG(png)))
            if search('LOGO', x) is not None:
                x = sub('LOGO', '', x)
                service = x
                sref = self.service_db.lookup(service)
                if self.picon == True:
                    picon = self.findPicon(sref)
                    if picon is not None:
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(100, 60), png=LoadPixmap(picon)))
                    else:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                else:
                    png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 12), size=(59, 36), png=loadPNG(png)))
                if sref == 'nope':
                    sref = None
                elif self.new == True:
                    hour = sub(':..', '', start)
                    if int(hour) < 5:
                        one_day = datetime.timedelta(days=1)
                        date = self.date + one_day
                    else:
                        date = self.date
                    timer = str(date) + ':::' + start + ':::' + str(sref)
                    if timer in self.timer:
                        png = ICONPATH + 'icon-recHD.png'
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(89 + picleftoffset, 52), size=(60, 20), png=loadPNG(png)))

        if sref != None and self.new == True:
            self.sref.append(sref)
            self.picurllist.append(picfilter)
            self.tvlink.append(linkfilter)
            self.tvtitel.append(titelfilter)
            self.tventries.append(res)

        self['menu'].l.setItemHeight(90)
        self['menu'].l.setList(self.tventries)
        self['menu'].moveToIndex(self.oldindex)
        if self.oldindex > 5:
            self.leftUp()
            self.rightDown()
        self.len = len(self.tventries)
        self['label'].setText('Info = Filter: NEU, Bouquet = +- Tag, <> = +- Woche')
        if self.sparte == 'neu':
            self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
        self['label'].stopBlinking()
        self['label'].show()
        self.ready = True
        
        self.GetPics(self.picurllist, 0)
        
        return

    def makePostviewPage(self, string):
        print("DEBUG makePostviewPage TVTippsView")
        self['menu'].hide()
        self['pic1'].hide()
        self['pic2'].hide()
        self['pic3'].hide()
        self['pic4'].hide()
        self['pic5'].hide()
        self['pic6'].hide()
        self._makePostviewPage(string)

    def makeSearchView(self, url):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        searchrequest = Request(url, None, header)
        try:
            output = urlopen(searchrequest).read()
            output = six.ensure_str(output)
        except (HTTPError,
         URLError,
         HTTPException,
         socket.error,
         AttributeError):
            output = ' '

        title = search('<title>(.*?)</title>', output)
        if title is not None:
            self['searchtext'].setText(title.group(1))
            self['searchtext'].show()
            self.setTitle('')
            self.setTitle(title.group(1))
        bereich = parsePrimeTimeTable(output, self.showgenre)
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 10
        mh = 40
        pictopoffset = 0
        picleftoffset = 0
        if self.picon == True:
            mh = 60
            pictopoffset = 10
            picleftoffset = 40
        for x in a:
            if y == 0:
                res = [x]
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))

                if search('DATUM', x) is not None:
                    if self.datum == True:
                        try:
                            del self.searchref[-1]
                            del self.searchlink[-1]
                            del self.searchentries[-1]
                        except IndexError:
                            pass

                    else:
                        self.datum = True
                    x = sub('DATUM', '', x)
                    self.datum_string = x
                    res_datum = [x]
                    if self.backcolor == True:
                        res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                    res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
                    self.searchref.append('na')
                    self.searchlink.append('na')
                    self.searchentries.append(res_datum)
                    self.filter = True
                    y = 9
                else:
                    y = 1
            if y == 1:
                x = sub('TIME', '', x)
                start = x
                res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
            if y == 2:
                if search('LOGO', x) is not None:
                    logo = search('LOGO(.*?)">', x)
                    if logo is not None:
                        x = logo.group(1)
                    service = x
                    sref = self.service_db.lookup(service)
                    if sref == 'nope':
                        self.filter = True
                    else:
                        self.filter = False
                        self.searchref.append(sref)
                        if self.picon == True:
                            picon = self.findPicon(sref)
                            if picon is not None:
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(100, 60), png=LoadPixmap(picon)))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                        else:
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
                        start = sub(' - ..:..', '', start)
                        daynow = sub('....-..-', '', str(self.date))
                        day = search(', ([0-9]+). ', self.datum_string)
                        if day is not None:
                            day = day.group(1)
                        else:
                            day = daynow
                        if int(day) >= int(daynow) - 1:
                            date = str(self.date) + 'FIN'
                        else:
                            four_weeks = datetime.timedelta(weeks=4)
                            date = str(self.date + four_weeks) + 'FIN'
                        date = sub('[0-9][0-9]FIN', day, date)
                        timer = date + ':::' + start + ':::' + str(sref)
                        if timer in self.timer:
                            self.rec = True
                            rp = self.getRecPNG()
                            if rp != None:
                                res.append(rp)
            if y == 3:
                if self.filter == False:
                    x = sub('LINK', '', x)
                    self.searchlink.append(x)
            if y == 4:
                if self.filter == False:
                    x = sub('TITEL', '', x)
                    titelfilter = x
            if y == 5:
                if self.filter == False:
                    if search('GENRE', x) is None:
                        res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                        y = 6
            if y == 6:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        if self.rec == True:
                            self.rec = False
                        else:
                            x = sub('INFO', '', x)
                            rp = self.getPNG(x, self.menuwidth - 140)
                            if rp != None:
                                res.append(rp)
                else:
                    y = 9
            if y == 7:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 210)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 8:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 280)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 9:
                if search('INFO', x) is not None:
                    y = 7
                elif self.filter == False:
                    self.datum = False
                    if search('RATING', x) is not None:
                        x = sub('RATING', '', x)
                        if x != 'rating small':
                            png = '%s%sHD.png' % (ICONPATH, x)
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(1175, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                    self.searchentries.append(res)
            y += 1
            if y == offset:
                y = 0

        self['searchmenu'].l.setItemHeight(mh)
        self['searchmenu'].l.setList(self.searchentries)
        self['searchmenu'].show()
        self.searchcount += 1
        if self.searchcount <= self.maxsearchcount and search('<a class="next" href=".*?"', bereich) is not None:
            nextpage = search('<a class="next" href="(.*?)"', bereich)
            if nextpage is not None:
                self.makeSearchView(nextpage.group(1))
            else:
                self.ready = True
        else:
            try:
                if self.searchref[-1] == 'na':
                    del self.searchref[-1]
                    del self.searchlink[-1]
                    del self.searchentries[-1]
                    self['searchmenu'].l.setList(self.searchentries)
            except IndexError:
                pass

            self['searchmenu'].moveToIndex(self.oldsearchindex)
            self.current = 'searchmenu'
            self.ready = True
        return

    def ok(self):
        if self.hideflag == False:
            return
        if self.current == 'menu' or self.current == 'searchmenu':
            self.selectPage('ok')
        elif self.current == 'postview' and self.postviewready == True:
            if self.trailer == True:
                sref = eServiceReference(4097, 0, self.trailerurl)
                sref.setName(self.name)
                self.session.open(MoviePlayer, sref)
            elif self.mehrbilder == True:
                self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
            else:
                self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)

    def selectPage(self, action):
        if self.current == 'menu' and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                self.postlink = self.tvlink[c]
            except IndexError:
                pass

        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

        if action == 'ok' and self.ready == True:
            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.current = 'postview'
                self.downloadPostPage(self.postlink, self.makePostviewPage)
        return

    def getEPG(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.showEPG == False:
                self.showEPG = True
                if self.search == False:
                    try:
                        c = self['menu'].getSelectedIndex()
                        sref = self.sref[c]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                else:
                    try:
                        c = self['searchmenu'].getSelectedIndex()
                        sref = self.searchref[c]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                if sref is not None:
                    try:
                        start = self.start
                        s1 = sub(':..', '', start)
                        date = str(self.postdate) + 'FIN'
                        date = sub('..FIN', '', date)
                        date = date + self.day
                        parts = start.split(':')
                        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                        start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                        s2 = sub(':..:..', '', start)
                        if int(s2) > int(s1):
                            start = str(self.date) + ' ' + start
                        else:
                            start = date + ' ' + start
                        start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                        start = int(mktime(start.timetuple()))
                        epgcache = eEPGCache.getInstance()
                        event = epgcache.startTimeQuery(eServiceReference(sref), start)
                        if event == -1:
                            self.EPGText = getEPGText()

                        else:
                            event = epgcache.getNextTimeEntry()
                            self.EPGtext = event.getEventName()
                            short = event.getShortDescription()
                            ext = event.getExtendedDescription()
                            dur = '%d Minuten' % (event.getDuration() / 60)
                            if short and short != self.EPGtext:
                                self.EPGtext += '\n\n' + short
                            if ext:
                                self.EPGtext += '\n\n' + ext
                            if dur:
                                self.EPGtext += '\n\n' + dur
                    except:
                        self.EPGText = getEPGText()

                else:
                    self.EPGtext = NOEPG
                fill = self.getFill(channel)
                self.EPGtext += '\n\n' + fill
                self['textpage'].setText(self.EPGtext)
                self['textpage'].show()
            else:
                self.showEPG = False
                self['textpage'].setText(self.POSTtext)
                self['textpage'].show()
        elif self.sparte != 'neu' and self.current == 'menu' and self.ready == True and self.search == False:
            if self.newfilter == False:
                self.newfilter = True
            else:
                self.newfilter = False
            self.refresh()
        return

    def red(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.search == False:
                try:
                    c = self['menu'].getSelectedIndex()
                    self.oldindex = c
                    sref = self.sref[c]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.search == True:
                try:
                    c = self['searchmenu'].getSelectedIndex()
                    self.oldsearchindex = c
                    sref = self.searchref[c]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            else:
                self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
        elif self.current == 'menu' and self.ready == True:
            c = self['menu'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink[c]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.download(self.postlink, self.makePostTimer)
        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            self.oldsearchindex = c
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.download(self.postlink, self.makePostTimer)
        return

    def finishedTimer(self, answer):
        if answer[0]:
            entry = answer[1]
            simulTimerList = self.session.nav.RecordTimer.record(entry)
            if simulTimerList is not None:
                for x in simulTimerList:
                    if x.setAutoincreaseEnd(entry):
                        self.session.nav.RecordTimer.timeChanged(x)

                simulTimerList = self.session.nav.RecordTimer.record(entry)
                if simulTimerList is not None:
                    self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
            self.makeTimerDB()
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
                self.refresh()
            else:
                self.showsearch()
        else:
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
            else:
                self.showsearch()
        return

    def green(self):
        if self.current == 'menu' and self.search == False:
            c = self['menu'].getSelectedIndex()
            try:
                sref = self.sref[c]
                if sref != '':
                    self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

    def yellow(self):
        if self.current == 'postview':
            self.youTube()
        elif self.current == 'menu' and self.search == False and self.ready == True:
            try:
                c = self['menu'].getSelectedIndex()
                self.oldindex = c
                titel = self.tvtitel[c]
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
            except IndexError:
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

    def searchReturn(self, search):
        if search and search != '':
            self.searchstring = search
            self['menu'].hide()
            self['pic1'].hide()
            self['pic2'].hide()
            self['pic3'].hide()
            self['pic4'].hide()
            self['pic5'].hide()
            self['pic6'].hide()
            self['label'].setText('')
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            self['searchlogo'].show()
            self['searchtimer'].show()
            self.searchlink = []
            self.searchref = []
            self.searchentries = []
            self.search = True
            self.datum = False
            self.filter = True
            search = search.replace(' ', '+')
            searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
            self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
            self.searchcount = 0
            self.makeSearchView(searchlink)

    def pressText(self):
        self._pressText()

    def youTube(self):
        if self.current == 'postview' and self.postviewready == True:
            self.session.open(searchYouTube, self.name, self.movie)
        elif self.current == 'menu' and self.search == False and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                titel = self.tvtitel[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

    def nextDay(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_day = datetime.timedelta(days=1)
                tomorrow = today + one_day
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextday = sub('date=(.*?FIN)', 'date=', self.link)
                nextday = nextday + str(tomorrow)
                self.date = tomorrow
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            else:
                today = datetime.date.today()
                one_day = datetime.timedelta(days=1)
                tomorrow = today + one_day
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextday = self.link + '?date=' + str(tomorrow)
                self.date = tomorrow
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            self.link = nextday
            self.oldindex = 0
            self.refresh()
        elif self.current == 'postview' or self.search == True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)
        return

    def prevDay(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_day = datetime.timedelta(days=1)
                yesterday = today - one_day
                self.weekday = makeWeekDay(yesterday.weekday())
                prevday = sub('date=(.*?FIN)', 'date=', self.link)
                prevday = prevday + str(yesterday)
                self.date = yesterday
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            else:
                today = datetime.date.today()
                one_day = datetime.timedelta(days=1)
                yesterday = today - one_day
                self.weekday = makeWeekDay(yesterday.weekday())
                prevday = self.link + '?date=' + str(yesterday)
                self.date = yesterday
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            self.link = prevday
            self.oldindex = 0
            self.refresh()
        elif self.current == 'postview' or self.search == True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)
        return

    def nextWeek(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_week = datetime.timedelta(days=7)
                tomorrow = today + one_week
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextweek = sub('date=(.*?FIN)', 'date=', self.link)
                nextweek = nextweek + str(tomorrow)
                self.date = tomorrow
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            else:
                today = datetime.date.today()
                one_week = datetime.timedelta(days=7)
                tomorrow = today + one_week
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextweek = self.link + '?date=' + str(tomorrow)
                self.date = tomorrow
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            self.link = nextweek
            self.oldindex = 0
            self.refresh()
        return

    def prevWeek(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_week = datetime.timedelta(days=7)
                yesterday = today - one_week
                self.weekday = makeWeekDay(yesterday.weekday())
                prevweek = sub('date=(.*?FIN)', 'date=', self.link)
                prevweek = prevweek + str(yesterday)
                self.date = yesterday
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            else:
                today = datetime.date.today()
                one_week = datetime.timedelta(days=7)
                yesterday = today - one_week
                self.weekday = makeWeekDay(yesterday.weekday())
                prevweek = self.link + '?date=' + str(yesterday)
                self.date = yesterday
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            self.link = prevweek
            self.oldindex = 0
            self.refresh()
        return

    def gotoEnd(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            end = self.len - 1
            self['menu'].moveToIndex(end)
            if end > 5:
                self.leftUp()
                self.rightDown()
        elif self.current != 'postview' and self.ready == True and self.search == True:
            end = len(self.searchentries) - 1
            self['searchmenu'].moveToIndex(end)

    def findPicon(self, sref):
        sref = sref + 'FIN'
        sref = sref.replace(':', '_')
        sref = sref.replace('_FIN', '')
        sref = sref.replace('FIN', '')
        pngname = self.piconfolder + sref + '.png'
        if fileExists(pngname):
            return pngname

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        currPic = loadPic(picpost, 490, 245, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
            self['piclabel'].show()
            self['piclabel2'].show()
            if self.trailer == True:
                self['cinlogo'].show()
                self['playlogo'].show()
        return

    def showPicTVinfoX(self, picinfo, X):
        currPic = loadPic(picinfo, 60, 20, 3, 0, 0, 0)
        if currPic != None:
            self[X].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadPostPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

    def downloadPageError(self, output):
        print(output)
        self['label'].setText('Info = Filter: NEU, Bouquet = +- Tag, <> = +- Woche')
        if self.sparte == 'neu':
            self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
        self['label'].stopBlinking()
        self['label'].show()
        self.ready = True

    def refresh(self):
        self.postviewready = False
        self.ready = False
        self.current = 'menu'
        self['label'].setText('Bitte warten...')
        self['label'].startBlinking()
        self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVTipps))

    def showProgrammPage(self):
        self['label'].setText('Info = Filter: NEU, Bouquet = +- Tag, <> = +- Woche')
        if self.sparte == 'neu':
            self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
        self['label2'].setText('= Timer')
        self['label3'].setText('= Suche')
        self['label4'].setText('= Zappen')
        self['infotext'].hide()
        self['infotext2'].hide()
        self['infotext3'].hide()
        self['infotext4'].hide()
        self['infotext5'].hide()
        self['infotext6'].hide()
        self['infotext7'].hide()
        self['infotext8'].hide()
        self['cinlogo'].hide()
        self['playlogo'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['piclabel'].hide()
        self['piclabel2'].hide()
        self['tvinfo1'].hide()
        self['tvinfo2'].hide()
        self['tvinfo3'].hide()
        self['tvinfo4'].hide()
        self['tvinfo5'].hide()
        self['searchmenu'].hide()
        self['searchlogo'].hide()
        self['searchtimer'].hide()
        self['searchtext'].hide()
        self.current = 'menu'
        self['menu'].show()
        try:
            c = self['menu'].getSelectedIndex()
            d = self.len - c
            x = self.len % 6
            if d > 6:
                x = 0
            elif d > x:
                x = 0
        except IndexError:
            x = 0

        if x == 0:
            self['pic1'].show()
            self['pic2'].show()
            self['pic3'].show()
            self['pic4'].show()
            self['pic5'].show()
            self['pic6'].show()
        elif x == 1:
            self['pic1'].show()
        elif x == 2:
            self['pic1'].show()
            self['pic2'].show()
        elif x == 3:
            self['pic1'].show()
            self['pic2'].show()
            self['pic3'].show()
        elif x == 4:
            self['pic1'].show()
            self['pic2'].show()
            self['pic3'].show()
            self['pic4'].show()
        elif x == 5:
            self['pic1'].show()
            self['pic2'].show()
            self['pic3'].show()
            self['pic4'].show()
            self['pic5'].show()

    def down(self):
        if self.current == 'menu':
            try:
                c = self['menu'].getSelectedIndex()
            except IndexError:
                return

            self['menu'].down()
            if c + 1 == self.len:
                self.GetPics(self.picurllist, 0)
            elif c % 6 == 5:
                self.GetPics(self.picurllist, c + 1)

        elif self.current == 'searchmenu':
            self['searchmenu'].down()
        else:
            self['textpage'].pageDown()

    def up(self):
        if self.current == 'menu':
            try:
                c = self['menu'].getSelectedIndex()
            except IndexError:
                return

            self['menu'].up()
            if c == 0:
                l = self.len
                d = l % 6
                if d == 0:
                    d = 6

                self.GetPics(self.picurllist, l - d)

            elif c % 6 == 0:
                self.GetPics(self.picurllist, c - 6)

        elif self.current == 'searchmenu':
            self['searchmenu'].up()
        else:
            self['textpage'].pageUp()

    def rightDown(self):
        if self.current == 'menu':
            try:
                c = self['menu'].getSelectedIndex()
            except IndexError:
                return

            self['menu'].pageDown()
            l = self.len
            d = c % 6
            e = l % 6
            if e == 0:
                e = 6
            if c + e >= l:
                pass
            elif d == 0:
                self.GetPics(self.picurllist, c + 6)

            elif d == 1:
                self.GetPics(self.picurllist, c + 5)

            elif d == 2:
                self.GetPics(self.picurllist, c + 4)

            elif d == 3:
                self.GetPics(self.picurllist, c + 3)

            elif d == 4:
                self.GetPics(self.picurllist, c + 2)

            elif d == 5:
                self.GetPics(self.picurllist, c + 1)

        elif self.current == 'searchmenu':
            self['searchmenu'].pageDown()
        else:
            self['textpage'].pageDown()

    def leftUp(self):
        if self.current == 'menu':
            try:
                c = self['menu'].getSelectedIndex()
            except IndexError:
                return

            self['menu'].pageUp()
            d = c % 6
            if c < 6:
                pass
            elif d == 0:
                self.GetPics(self.picurllist, c - 6, False)

            elif d == 1:
                self.GetPics(self.picurllist, c - 7, False)

            elif d == 2:
                self.GetPics(self.picurllist, c - 8, False)

            elif d == 3:
                self.GetPics(self.picurllist, c - 9, False)

            elif d == 4:
                self.GetPics(self.picurllist, c - 10, False)

            elif d == 5:
                self.GetPics(self.picurllist, c - 11, False)

            self['pic1'].show()
            self['pic2'].show()
            self['pic3'].show()
            self['pic4'].show()
            self['pic5'].show()
            self['pic6'].show()
        elif self.current == 'searchmenu':
            self['searchmenu'].pageUp()
        else:
            self['textpage'].pageUp()

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu':
            self.close()
        elif self.current == 'searchmenu':
            self.search = False
            self.oldsearchindex = 1
            self['searchmenu'].hide()
            self['searchlogo'].hide()
            self['searchtimer'].hide()
            self['searchtext'].hide()
            self.showProgrammPage()
            self.setTitle('')
            self.setTitle(self.titel)
        elif self.current == 'postview' and self.search == False:
            self.postviewready = False
            self.setTitle('')
            self.setTitle(self.titel)
            self.showProgrammPage()
        elif self.current == 'postview' and self.search == True:
            self.postviewready = False
            self.showsearch()
            self.current = 'searchmenu'


class TVGenreView(tvBaseScreen):
    def __init__(self, session, link, genre):
        skin = """
        <screen name="TVGenreView" position="{screenpos}" size="{screensize}" title=" ">
            %s%s%s
        </screen>""" % ( SKHEADTOP, SKMENU, SKHEADBOTTOM )
        tvBaseScreen.__init__(self, session, skin)
        self.current = 'menu'
        self.oldcurrent = 'menu'
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.sref = []
        self.searchlink = []
        self.searchref = []
        self.searchentries = []
        self.start = ''
        self.end = ''
        self.day = ''
        self.name = ''
        self.shortdesc = ''
        self.postlink = link
        self.link = link
        self.trailerurl = ''
        self.POSTtext = ''
        self.EPGtext = ''
        self.genre = genre
        if search('Serie', genre) is not None:
            self.serie = True
        else:
            self.serie = False
        self.titel = ''
        self.hideflag = True
        self.search = False
        self.rec = False
        self.load = True
        self.ready = False
        self.postviewready = False
        self.mehrbilder = False
        self.trailer = False
        self.movie = False
        self.datum = False
        self.filter = True
        self.maxgenrecount = config.plugins.tvspielfilm.maxgenre.value
        self.genrecount = 0
        self.oldindex = 0
        self.oldsearchindex = 1
        self['picpost'] = Pixmap()
        self['tvinfo1'] = Pixmap()
        self['tvinfo2'] = Pixmap()
        self['tvinfo3'] = Pixmap()
        self['tvinfo4'] = Pixmap()
        self['tvinfo5'] = Pixmap()
        self['cinlogo'] = Pixmap()
        self['cinlogo'].hide()
        self['playlogo'] = Pixmap()
        self['playlogo'].hide()
        self['searchlogo'] = Pixmap()
        self['searchlogo'].hide()
        self['searchtimer'] = Pixmap()
        self['searchtimer'].hide()
        self['searchtext'] = Label('')
        self['searchtext'].hide()
        self['textpage'] = ScrollLabel('')
        self['infotext'] = Label('')
        self['infotext'].hide()
        self['infotext2'] = Label('')
        self['infotext2'].hide()
        self['infotext3'] = Label('')
        self['infotext3'].hide()
        self['infotext4'] = Label('')
        self['infotext4'].hide()
        self['infotext5'] = Label('')
        self['infotext5'].hide()
        self['infotext6'] = Label('')
        self['infotext6'].hide()
        self['infotext7'] = Label('')
        self['infotext7'].hide()
        self['infotext8'] = Label('')
        self['infotext8'].hide()
        self['piclabel'] = Label('')
        self['piclabel'].hide()
        self['piclabel2'] = Label('')
        self['piclabel2'].hide()
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['searchmenu'] = ItemList([])
        self['searchmenu'].hide()
        self['menu'] = ItemList([])
        self['label'] = BlinkingLabel('Bitte warten...')
        self['label'].startBlinking()
        self['label2'] = Label('= Timer')
        self['label3'] = Label('= Filter')
        self['label4'] = Label('= Zappen')
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'HelpActions',
         'EPGSelectActions',
         'NumberActions',
         'InfobarTeletextActions',
         'ChannelSelectBaseActions',
         'MoviePlayerActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         '0': self.gotoEnd,
         '1': self.zapUp,
         '2': self.zapDown,
         '7': self.IMDb,
         '8': self.TMDb,
         '9': self.TVDb,
         'info': self.getEPG,
         'epg': self.getEPG,
         'leavePlayer': self.youTube,
         'startTeletext': self.pressText}, -1)
        self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
         'yellow': self.yellow,
         'red': self.makeTimer,
         'blue': self.hideScreen}, -1)
        self.service_db = serviceDB(self.servicefile)
        f = open(self.servicefile, 'r')
        lines = f.readlines()
        f.close()
        self.timer = open('/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/timer.db').read()
        self.date = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        self.nextdate = self.date + one_day
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        if config.plugins.tvspielfilm.genreinfo.value == 'no':
            self.showgenre = False
        else:
            self.showgenre = True
        self.makeTVTimer = eTimer()
        self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        self.makeTVTimer.start(500, True)
        return

    def makeTVView(self, output):
        output = six.ensure_str(output)
        self.titel = '%s - Sendungen der naechsten 14 Tage' % self.genre
        self.setTitle(self.titel)
        bereich = parsePrimeTimeTable(output, self.showgenre)
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 10
        pictopoffset = 0
        picleftoffset = 0
        mh = 40
        if self.picon == True:
            mh = 62
            pictopoffset = 11
            picleftoffset = 40
        for x in a:
            if y == 0:
                res = [x]
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))

                if search('DATUM', x) is not None:
                    if self.datum == True:
                        try:
                            del self.sref[-1]
                            del self.tvlink[-1]
                            del self.tvtitel[-1]
                            del self.tventries[-1]
                            self.datum = True
                        except IndexError:
                            pass

                    else:
                        self.datum = True
                    x = sub('DATUM', '', x)
                    self.datum_string = x
                    res_datum = [x]
                    if self.backcolor == True:
                        res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                    res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
                    self.sref.append('na')
                    self.tvlink.append('na')
                    self.tvtitel.append('na')
                    self.tventries.append(res_datum)
                    self.filter = True
                    y = 9
                else:
                    y = 1
            if y == 1:
                x = sub('TIME', '', x)
                start = x
                res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7 + pictopoffset), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
            if y == 2:
                if search('LOGO', x) is not None:
                    logo = search('LOGO(.*?)">', x)
                    if logo is not None:
                        x = logo.group(1)
                    service = x
                    sref = self.service_db.lookup(service)
                    if sref == 'nope':
                        self.filter = True
                    else:
                        self.filter = False
                        self.sref.append(sref)
                        if self.picon == True:
                            picon = self.findPicon(sref)
                            if picon is not None:
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 1), size=(100, 60), png=LoadPixmap(picon)))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 1), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                        else:
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
                        start = sub(' - ..:..', '', start)
                        daynow = sub('....-..-', '', str(self.date))
                        day = search(', ([0-9]+). ', self.datum_string)
                        if day is not None:
                            day = day.group(1)
                        else:
                            day = daynow
                        if int(day) >= int(daynow) - 1:
                            date = str(self.date) + 'FIN'
                        else:
                            four_weeks = datetime.timedelta(weeks=4)
                            date = str(self.date + four_weeks) + 'FIN'
                        date = sub('[0-9][0-9]FIN', day, date)
                        timer = date + ':::' + start + ':::' + str(sref)
                        if timer in self.timer:
                            self.rec = True
                            png = ICONPATH + 'icon-recHD.png'
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 130, 21 + picontopoffset), size=(60, 20), png=loadPNG(png)))
            if y == 3:
                if self.filter == False:
                    x = sub('LINK', '', x)
                    self.tvlink.append(x)
            if y == 4:
                if self.filter == False:
                    x = sub('TITEL', '', x)
                    self.tvtitel.append(x)
                    titelfilter = x
            if y == 5:
                if self.filter == False:
                    if search('GENRE', x) is None:
                        res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                        y = 6
            if y == 6:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        if self.rec == True:
                            self.rec = False
                        else:
                            x = sub('INFO', '', x)
                            png = '%s%sHD.png' % (ICONPATH, x)
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 130, 10 + pictopoffset), size=(60, 20), png=loadPNG(png)))
                else:
                    y = 9
            if y == 7:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        png = '%s%sHD.png' % (ICONPATH, x)
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 210, 10 + pictopoffset), size=(60, 20), png=loadPNG(png)))
                else:
                    y = 9
            if y == 8:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        png = '%s%sHD.png' % (ICONPATH, x)
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 290, 10 + pictopoffset), size=(60, 20), png=loadPNG(png)))
                else:
                    y = 9
            if y == 9:
                if search('INFO', x) is not None:
                    y = 7
                elif self.filter == False:
                    self.datum = False
                    if search('RATING', x) is not None:
                        x = sub('RATING', '', x)
                        if x != 'rating small':
                            png = '%s%sHD.png' % (ICONPATH, x)
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 65, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                    self.tventries.append(res)
            y += 1
            if y == offset:
                y = 0

        self['menu'].l.setItemHeight(mh)
        self['menu'].l.setList(self.tventries)
        end = len(self.tventries) - 1
        self['menu'].moveToIndex(end)
        self['menu'].show()
        self.genrecount += 1
        if self.genrecount <= self.maxgenrecount and search('class="pagination__link pagination__link--next" >', bereich) is not None and self.load == True:
            nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if nextpage is not None:
                self.downloadFull(nextpage.group(1), self.makeTVView)
            else:
                self.load = False
                self.ready = True
        else:
            self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
            self['label'].stopBlinking()
            self['label'].show()
            try:
                if self.sref[-1] == 'na':
                    del self.sref[-1]
                    del self.tvlink[-1]
                    del self.tvtitel[-1]
                    del self.tventries[-1]
                    self['menu'].l.setList(self.tventries)
            except IndexError:
                pass

            self['menu'].moveToIndex(self.oldindex)
            self.load = False
            self.ready = True
        return

    def makePostviewPage(self, string):
        print("DEBUG makePostviewPage TVGenreView")
        self['menu'].hide()
        self._makePostviewPage(string)

    def makeSearchView(self, url):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        searchrequest = Request(url, None, header)
        try:
            output = urlopen(searchrequest).read()
            output = six.ensure_str(output)
        except (HTTPError,
         URLError,
         HTTPException,
         socket.error,
         AttributeError):
            output = ' '

        title = 'Genre: ' + self.genre.replace(':', ' -') + ', Filter: ' + self.searchstring
        self.setTitle(title)
        bereich = parsePrimeTimeTable(output, self.showgenre)
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 10
        mh = 40
        pictopoffset = 0
        picleftoffset = 0
        if self.picon == True:
            mh = 60
            pictopoffset = 10
            picleftoffset = 40
        for x in a:
            if y == 0:
                res = [x]
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                if search('DATUM', x) is not None:
                    if self.datum == True:
                        try:
                            del self.searchref[-1]
                            del self.searchlink[-1]
                            del self.searchentries[-1]
                        except IndexError:
                            pass

                    else:
                        self.datum = True
                    x = sub('DATUM', '', x)
                    self.datum_string = x
                    res_datum = [x]
                    if self.backcolor == True:
                        res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                    res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
                    self.searchref.append('na')
                    self.searchlink.append('na')
                    self.searchentries.append(res_datum)
                    self.filter = True
                    y = 9
                else:
                    y = 1
            if y == 1:
                x = sub('TIME', '', x)
                start = x
                res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7 + pictopoffset), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
            if y == 2:
                if search('LOGO', x) is not None:
                    logo = search('LOGO(.*?)">', x)
                    if logo is not None:
                        x = logo.group(1)
                    service = x
                    sref = self.service_db.lookup(service)
                    if sref == 'nope':
                        self.filter = True
                    else:
                        self.filter = False
                        self.searchref.append(sref)
                        if self.picon == True:
                            picon = self.findPicon(sref)
                            if picon is not None:
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(100, 60), png=LoadPixmap(picon)))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                        else:
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
                        start = sub(' - ..:..', '', start)
                        daynow = sub('....-..-', '', str(self.date))
                        day = search(', ([0-9]+). ', self.datum_string)
                        if day is not None:
                            day = day.group(1)
                        else:
                            day = daynow
                        if int(day) >= int(daynow) - 1:
                            date = str(self.date) + 'FIN'
                        else:
                            four_weeks = datetime.timedelta(weeks=4)
                            date = str(self.date + four_weeks) + 'FIN'
                        date = sub('[0-9][0-9]FIN', day, date)
                        timer = date + ':::' + start + ':::' + str(sref)
                        if timer in self.timer:
                            self.rec = True
                            rp = self.getRecPNG()
                            if rp != None:
                                res.append(rp)
            if y == 3:
                if self.filter == False:
                    x = sub('LINK', '', x)
                    self.searchlink.append(x)
            if y == 4:
                if self.filter == False:
                    x = sub('TITEL', '', x)
                    titelfilter = x
            if y == 5:
                if self.filter == False:
                    if search('GENRE', x) is None:
                        res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                        y = 6
            if y == 6:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        if self.rec == True:
                            self.rec = False
                        else:
                            x = sub('INFO', '', x)
                            rp = self.getPNG(x, self.menuwidth - 140)
                            if rp != None:
                                res.append(rp)
                else:
                    y = 9
            if y == 7:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 210)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 8:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 280)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 9:
                if search('INFO', x) is not None:
                    y = 7
                elif self.filter == False:
                    self.datum = False
                    if search('RATING', x) is not None:
                        x = sub('RATING', '', x)
                        if x != 'rating small':
                            png = '%s%sHD.png' % (ICONPATH, x)
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(1175, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                    self.searchentries.append(res)
            y += 1
            if y == offset:
                y = 0

        self['searchmenu'].l.setItemHeight(mh)
        self['searchmenu'].l.setList(self.searchentries)
        self['searchmenu'].show()
        self.searchcount += 1
        if self.searchcount <= self.maxsearchcount and search('class="pagination__link pagination__link--next" >', bereich) is not None:
            nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if nextpage is not None:
                self.makeSearchView(nextpage.group(1))
            else:
                self.ready = True
        else:
            try:
                if self.searchref[-1] == 'na':
                    del self.searchref[-1]
                    del self.searchlink[-1]
                    del self.searchentries[-1]
                    self['searchmenu'].l.setList(self.searchentries)
            except IndexError:
                pass

            self['searchmenu'].moveToIndex(self.oldsearchindex)
            self.current = 'searchmenu'
            self.ready = True
        return

    def ok(self):
        if self.hideflag == False:
            return
        if self.current == 'menu' or self.current == 'searchmenu':
            self.selectPage('ok')
        elif self.current == 'postview' and self.postviewready == True:
            if self.trailer == True:
                sref = eServiceReference(4097, 0, self.trailerurl)
                sref.setName(self.name)
                self.session.open(MoviePlayer, sref)
            elif self.mehrbilder == True:
                self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
            else:
                self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)

    def selectPage(self, action):
        if self.current == 'menu' and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                self.postlink = self.tvlink[c]
            except IndexError:
                pass

        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

        if action == 'ok' and self.ready == True:
            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.current = 'postview'
                self.downloadPostPage(self.postlink, self.makePostviewPage)
        return

    def stopLoad(self, answer):
        if answer is True:
            self.load = False
            self.ready = True

    def getEPG(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.showEPG == False:
                self.showEPG = True
                if self.search == False:
                    try:
                        c = self['menu'].getSelectedIndex()
                        sref = self.sref[c]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                else:
                    try:
                        c = self['searchmenu'].getSelectedIndex()
                        sref = self.searchref[c]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                if sref is not None:
                    try:
                        start = self.start
                        s1 = sub(':..', '', start)
                        date = str(self.postdate) + 'FIN'
                        date = sub('..FIN', '', date)
                        date = date + self.day
                        parts = start.split(':')
                        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                        start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                        s2 = sub(':..:..', '', start)
                        if int(s2) > int(s1):
                            start = str(self.date) + ' ' + start
                        else:
                            start = date + ' ' + start
                        start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                        start = int(mktime(start.timetuple()))
                        epgcache = eEPGCache.getInstance()
                        event = epgcache.startTimeQuery(eServiceReference(sref), start)
                        if event == -1:
                            self.EPGText = getEPGText()

                        else:
                            event = epgcache.getNextTimeEntry()
                            self.EPGtext = event.getEventName()
                            short = event.getShortDescription()
                            ext = event.getExtendedDescription()
                            dur = '%d Minuten' % (event.getDuration() / 60)
                            if short and short != self.EPGtext:
                                self.EPGtext += '\n\n' + short
                            if ext:
                                self.EPGtext += '\n\n' + ext
                            if dur:
                                self.EPGtext += '\n\n' + dur
                    except:
                        self.EPGText = getEPGText()

                else:
                    self.EPGtext = NOEPG
                fill = self.getFill(channel)
                self.EPGtext += '\n\n' + fill
                self['textpage'].setText(self.EPGtext)
                self['textpage'].show()
            else:
                self.showEPG = False
                self['textpage'].setText(self.POSTtext)
                self['textpage'].show()
        return

    def red(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.search == False:
                try:
                    c = self['menu'].getSelectedIndex()
                    self.oldindex = c
                    sref = self.sref[c]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.search == True:
                try:
                    c = self['searchmenu'].getSelectedIndex()
                    self.oldsearchindex = c
                    sref = self.searchref[c]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            else:
                self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
        elif self.current == 'menu' and self.ready == True:
            c = self['menu'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink[c]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.download(self.postlink, self.makePostTimer)
        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            self.oldsearchindex = c
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.download(self.postlink, self.makePostTimer)
        return

    def finishedTimer(self, answer):
        if answer[0]:
            entry = answer[1]
            simulTimerList = self.session.nav.RecordTimer.record(entry)
            if simulTimerList is not None:
                for x in simulTimerList:
                    if x.setAutoincreaseEnd(entry):
                        self.session.nav.RecordTimer.timeChanged(x)

                simulTimerList = self.session.nav.RecordTimer.record(entry)
                if simulTimerList is not None:
                    self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
            self.makeTimerDB()
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
            else:
                self.showsearch()
        else:
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
            else:
                self.showsearch()
        return

    def green(self):
        if self.current == 'menu' and self.search == False:
            c = self['menu'].getSelectedIndex()
            try:
                sref = self.sref[c]
                if sref != '':
                    self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

    def yellow(self):
        if self.current == 'postview':
            self.youTube()
        elif self.current == 'menu' and self.search == False and self.ready == True:
            try:
                c = self['menu'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel[c]
                except IndexError:
                    pass

                if titel != 'na':
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Genre: ' + self.genre.replace(':', ' -') + ', Filter:', text=titel)
                else:
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Genre: ' + self.genre.replace(':', ' -') + ', Filter:', text='')
            except IndexError:
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Genre: ' + self.genre.replace(':', ' -') + ', Filter:', text='')

    def searchReturn(self, search):
        if search and search != '':
            self.searchstring = search
            self['menu'].hide()
            self['label'].setText('')
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            self['searchlogo'].show()
            self['searchtimer'].show()
            self.searchlink = []
            self.searchref = []
            self.searchentries = []
            self.search = True
            self.datum = False
            self.filter = True
            search = search.replace(' ', '+')
            searchlink = sub('&q=', '&q=' + search, self.link)
            self.maxsearchcount = config.plugins.tvspielfilm.maxgenre.value
            self.searchcount = 0
            self.makeSearchView(searchlink)

    def pressText(self):
        self._pressText()

    def youTube(self):
        if self.current == 'postview' and self.postviewready == True:
            self.session.open(searchYouTube, self.name, self.movie)
        elif self.current == 'menu' and self.search == False and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                titel = self.tvtitel[c]
                if titel != 'na':
                    self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

    def gotoEnd(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            end = len(self.tventries) - 1
            self['menu'].moveToIndex(end)
        elif self.current != 'postview' and self.ready == True and self.search == True:
            end = len(self.searchentries) - 1
            self['searchmenu'].moveToIndex(end)

    def findPicon(self, sref):
        sref = sref + 'FIN'
        sref = sref.replace(':', '_')
        sref = sref.replace('_FIN', '')
        sref = sref.replace('FIN', '')
        pngname = self.piconfolder + sref + '.png'
        if fileExists(pngname):
            return pngname

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        currPic = loadPic(picpost, 490, 245, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
            self['piclabel'].show()
            self['piclabel2'].show()
            if self.trailer == True:
                self['cinlogo'].show()
                self['playlogo'].show()
        return

    def showPicTVinfoX(self, picinfo, X):
        currPic = loadPic(picinfo, 60, 20, 3, 0, 0, 0)
        if currPic != None:
            self[X].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadFull(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadFullError)

    def downloadFullError(self, output):
        self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
        self['label'].stopBlinking()
        self['label'].show()
        self['menu'].moveToIndex(self.oldindex)
        self.ready = True

    def downloadPostPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

    def downloadPageError(self, output):
        print(output)
        self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
        self['label'].stopBlinking()
        self['label'].show()
        self.ready = True

    def refresh(self):
        self.postviewready = False
        self.ready = False
        self.datum = False
        self.filter = True
        self.current = 'menu'
        self['label'].setText('Bitte warten...')
        self['label'].startBlinking()
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.sref = []
        self.genrecount = 0
        self.makeTVTimer.callback.append(self.downloadFull(self.link, self.makeTVView))

    def showProgrammPage(self):
        self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
        self['label2'].setText('= Timer')
        self['label3'].setText('= Filter')
        self['label4'].setText('= Zappen')
        self['infotext'].hide()
        self['infotext2'].hide()
        self['infotext3'].hide()
        self['infotext4'].hide()
        self['infotext5'].hide()
        self['infotext6'].hide()
        self['infotext7'].hide()
        self['infotext8'].hide()
        self['cinlogo'].hide()
        self['playlogo'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['piclabel'].hide()
        self['piclabel2'].hide()
        self['tvinfo1'].hide()
        self['tvinfo2'].hide()
        self['tvinfo3'].hide()
        self['tvinfo4'].hide()
        self['tvinfo5'].hide()
        self['searchmenu'].hide()
        self['searchlogo'].hide()
        self['searchtimer'].hide()
        self['searchtext'].hide()
        self.current = 'menu'
        self['menu'].show()

    def down(self):
        try:
            if self.current == 'menu':
                self['menu'].down()
            elif self.current == 'searchmenu':
                self['searchmenu'].down()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def up(self):
        try:
            if self.current == 'menu':
                self['menu'].up()
            elif self.current == 'searchmenu':
                self['searchmenu'].up()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def rightDown(self):
        try:
            if self.current == 'menu':
                self['menu'].pageDown()
            elif self.current == 'searchmenu':
                self['searchmenu'].pageDown()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def leftUp(self):
        try:
            if self.current == 'menu':
                self['menu'].pageUp()
            elif self.current == 'searchmenu':
                self['searchmenu'].pageUp()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.load == True:
            self.session.openWithCallback(self.stopLoad, MessageBox, '\nDie Suche ist noch nicht beendet. Soll die Suche abgebrochen und das Ergebnis angezeigt werden?', MessageBox.TYPE_YESNO)
        elif self.current == 'menu' and self.search == False:
            if fileExists(self.picfile):
                os.remove(self.picfile)
            if fileExists(self.localhtml):
                os.remove(self.localhtml)
            if fileExists(self.localhtml2):
                os.remove(self.localhtml2)
            self.close()
        elif self.current == 'searchmenu':
            self.search = False
            self.oldsearchindex = 1
            self['searchmenu'].hide()
            self['searchlogo'].hide()
            self['searchtimer'].hide()
            self['searchtext'].hide()
            self.setTitle('')
            self.setTitle(self.titel)
            self.showProgrammPage()
        elif self.current == 'postview' and self.search == False:
            self.postviewready = False
            self.setTitle('')
            self.setTitle(self.titel)
            self.showProgrammPage()
        elif self.current == 'postview' and self.search == True:
            self.postviewready = False
            self.showsearch()
            self.current = 'searchmenu'


class TVJetztView(tvBaseScreen):
    def __init__(self, session, link, standalone):
        skin = """
        <screen name="TVJetztView" position="{screenpos}" size="{screensize}" title=" ">
            %s%s%s
        </screen>""" % ( SKHEADTOP, SKMENU, SKHEADBOTTOM )
        tvBaseScreen.__init__(self, session, skin)
        self.current = 'menu'
        self.oldcurrent = 'menu'
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.sref = []
        self.searchlink = []
        self.searchref = []
        self.searchentries = []
        self.start = ''
        self.end = ''
        self.day = ''
        self.name = ''
        self.shortdesc = ''
        self.postlink = link
        self.link1 = link
        self.link2 = link
        self.trailerurl = ''
        self.titel = ''
        self.standalone = standalone
        self.POSTtext = ''
        self.EPGtext = ''
        self.hideflag = True
        self.jetzt = False
        self.gleich = False
        self.abends = False
        self.nachts = False
        self.search = False
        self.rec = False
        self.ready = False
        self.postviewready = False
        self.mehrbilder = False
        self.trailer = False
        self.movie = False
        self.datum = False
        self.filter = True
        self.index = 0
        self.oldindex = 0
        self.oldsearchindex = 1
        self['picpost'] = Pixmap()
        self['tvinfo1'] = Pixmap()
        self['tvinfo2'] = Pixmap()
        self['tvinfo3'] = Pixmap()
        self['tvinfo4'] = Pixmap()
        self['tvinfo5'] = Pixmap()
        self['cinlogo'] = Pixmap()
        self['cinlogo'].hide()
        self['playlogo'] = Pixmap()
        self['playlogo'].hide()
        self['searchlogo'] = Pixmap()
        self['searchlogo'].hide()
        self['searchtimer'] = Pixmap()
        self['searchtimer'].hide()
        self['searchtext'] = Label('')
        self['searchtext'].hide()
        self['textpage'] = ScrollLabel('')
        self['infotext'] = Label('')
        self['infotext'].hide()
        self['infotext2'] = Label('')
        self['infotext2'].hide()
        self['infotext3'] = Label('')
        self['infotext3'].hide()
        self['infotext4'] = Label('')
        self['infotext4'].hide()
        self['infotext5'] = Label('')
        self['infotext5'].hide()
        self['infotext6'] = Label('')
        self['infotext6'].hide()
        self['infotext7'] = Label('')
        self['infotext7'].hide()
        self['infotext8'] = Label('')
        self['infotext8'].hide()
        self['piclabel'] = Label('')
        self['piclabel'].hide()
        self['piclabel2'] = Label('')
        self['piclabel2'].hide()
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['searchmenu'] = ItemList([])
        self['searchmenu'].hide()
        self['menu'] = ItemList([])
        self['label'] = BlinkingLabel('Bitte warten...')
        self['label'].startBlinking()
        self['label2'] = Label('= Timer')
        self['label3'] = Label('= Suche')
        self['label4'] = Label('= Zappen')
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'HelpActions',
         'EPGSelectActions',
         'NumberActions',
         'InfobarTeletextActions',
         'ChannelSelectBaseActions',
         'MoviePlayerActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         '0': self.gotoEnd,
         '1': self.zapUp,
         '2': self.zapDown,
         '7': self.IMDb,
         '8': self.TMDb,
         '9': self.TVDb,
         'info': self.getEPG,
         'epg': self.getEPG,
         'leavePlayer': self.youTube,
         'startTeletext': self.pressText}, -1)
        self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
         'yellow': self.yellow,
         'red': self.makeTimer,
         'blue': self.hideScreen}, -1)
        self.service_db = serviceDB(self.servicefile)
        f = open(self.servicefile, 'r')
        lines = f.readlines()
        f.close()
        ordertext = [ '"%s": %d, ' % (line.partition(' ')[0], i) for i, line in enumerate(lines) ]
        self.order = '{' + str(''.join(ordertext)) + '}'
        if self.standalone == True:
            self.movie_stop = config.usage.on_movie_stop.value
            self.movie_eof = config.usage.on_movie_eof.value
            config.usage.on_movie_stop.value = 'quit'
            config.usage.on_movie_eof.value = 'quit'
            self.makeTimerDB()
        else:
            self.timer = open('/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/timer.db').read()
        self.date = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        self.nextdate = self.date + one_day
        self.weekday = makeWeekDay(self.date.weekday())
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        if config.plugins.tvspielfilm.genreinfo.value == 'no':
            self.showgenre = False
        else:
            self.showgenre = True
        self.makeTVTimer = eTimer()
        if search('/sendungen/jetzt.html', link) is not None:
            self.jetzt = True
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        elif search('time=shortly', link) is not None:
            self.gleich = True
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        elif search('/sendungen/abends.html', link) is not None:
            self.abends = True
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        elif search('/sendungen/fernsehprogramm-nachts.html', link) is not None:
            self.nachts = True
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        self.makeTVTimer.start(500, True)
        return

    def makeTVView(self, output):
        output = six.ensure_str(output)
        date = str(self.date.strftime('%d.%m.%Y'))
        if self.jetzt == True:
            self.titel = 'Jetzt im TV - Heute, ' + str(self.weekday) + ', ' + date
        elif self.gleich == True:
            self.titel = 'Gleich im TV - Heute, ' + str(self.weekday) + ', ' + date
        elif self.abends:
            self.titel = '20:15 im TV - Heute, ' + str(self.weekday) + ', ' + date
        else:
            self.titel = '22:00 im TV - Heute, ' + str(self.weekday) + ', ' + date
        self.setTitle(self.titel)
        bereich = parseInfoTable2(output)
        nowhour = datetime.datetime.now().hour
        if self.jetzt == True or self.gleich == True or self.abends == True and nowhour == 20 or self.abends == True and nowhour == 21 or self.nachts == True and nowhour == 22:
            self.progress = True
            nowminute = datetime.datetime.now().minute
            nowsec = int(nowhour) * 3600 + int(nowminute) * 60
        else:
            self.progress = False
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 7
        pictopoffset = 0
        picleftoffset = 0
        mh = 40
        if self.picon == True:
            mh = 62
            pictopoffset = 11
            picleftoffset = 40

        scaleoffset = 0
        if self.fontlarge == True:
            scaleoffset = 10

        for x in a:
            if y == 0:
                x = sub('LOGO', '', x)
                service = x
                sref = self.service_db.lookup(service)
                if sref == 'nope':
                    self.filter = True
                else:
                    self.filter = False
                    res_sref = []
                    res_sref.append(service)
                    res_sref.append(sref)
                    self.sref.append(res_sref)
                    res = [x]
                    

                    if self.backcolor == True:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                    if self.picon == True:
                        picon = self.findPicon(sref)
                        if picon is not None:
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 1), size=(100, 60), png=LoadPixmap(picon)))
                        else:
                            res.append(MultiContentEntryText(pos=(0, 1), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                    else:
                        png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
            if y == 1:
                if self.filter == False:
                    x = sub('TIME', '', x)
                    if self.progress == True:
                        start = sub(' - ..:..', '', x)
                        startparts = start.split(':')
                        startsec = int(startparts[0]) * 3600 + int(startparts[1]) * 60
                        end = sub('..:.. - ', '', x)
                        endparts = end.split(':')
                        endsec = int(endparts[0]) * 3600 + int(endparts[1]) * 60
                        if endsec >= startsec:
                            length = endsec - startsec
                        else:
                            length = 86400 - startsec + endsec
                        if nowsec < startsec and endsec - nowsec > 43200:
                            percent = 100
                        elif nowsec < startsec and endsec > startsec:
                            percent = 0
                        elif endsec < startsec:
                            if nowsec > startsec:
                                passed = nowsec - startsec
                                percent = passed * 100 / length
                            elif nowsec < endsec:
                                passed = 86400 - startsec + nowsec
                                percent = passed * 100 / length
                            elif nowsec - endsec < startsec - nowsec:
                                percent = 100
                            else:
                                percent = 0
                        elif nowsec > endsec and nowsec - endsec > 43200:
                            percent = 0
                        elif nowsec > endsec:
                            percent = 100
                        else:
                            passed = nowsec - startsec
                            percent = passed * 100 / length
                    res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7 + pictopoffset), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                    start = sub(' - ..:..', '', x)
                    hour = sub(':..', '', start)
                    if int(nowhour) - int(hour) > 6:
                        one_day = datetime.timedelta(days=1)
                        date = self.date + one_day
                    else:
                        date = self.date
                    timer = str(date) + ':::' + start + ':::' + str(sref)
                    if timer in self.timer:
                        self.rec = True
                        png = ICONPATH + 'icon-small-recHD.png'
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(1014, pictopoffset), size=(39, 40), png=loadPNG(png)))
            if y == 2:
                if self.filter == False:
                    x = sub('LINK', '', x)
                    res_link = []
                    res_link.append(service)
                    res_link.append(x)
                    self.tvlink.append(res_link)
            if y == 3:
                if self.filter == False:
                    if search('TITEL', x) is not None:
                        t = sub('TITEL', '', x)
                        if self.showgenre == True and search('GENRE', x) is not None:
                            x = t + " " + sub('GENRE', '', x)
                        else:
                            x = t
                        res_titel = []
                        res_titel.append(service)
                        res_titel.append(t)
                        self.tvtitel.append(res_titel)
                        if self.progress == False:
                            res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(self.menuwidth - 400 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                        else:
                            res.append(MultiContentEntryProgress(pos=(235 + picleftoffset, 13 + pictopoffset), size=(70, 14), percent=percent, borderWidth=1, foreColor=16777215))
                            res.append(MultiContentEntryText(pos=(325 + picleftoffset, 7 + pictopoffset), size=(self.menuwidth - 490 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    else:
                        y = 5
                elif search('TITEL', x) is None:
                    y = 5
            if y == 5:
                if search('SPARTE', x) is not None:
                    if self.filter == False:
                        x = sub('SPARTE', '', x)
                        res.append(MultiContentEntryText(pos=(self.menuwidth - 160, 7 + pictopoffset), size=(152 + scaleoffset, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT, text=x))
                else:
                    y = 6
            if y == 6:
                if self.filter == False:
                    x = sub('RATING', '', x)
                    if self.rec == True:
                        self.rec = False
                    elif x != 'rating small':
                        png = '%s%sHD.png' % (ICONPATH, x)
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 210, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    self.tventries.append(res)
            y += 1
            if y == offset:
                y = 0

        order = eval(self.order)
        self.sref = sorted(self.sref, key=lambda x: order[x[0]])
        self.tvlink = sorted(self.tvlink, key=lambda x: order[x[0]])
        self.tvtitel = sorted(self.tvtitel, key=lambda x: order[x[0]])
        self.tventries = sorted(self.tventries, key=lambda x: order[x[0]])
        self['menu'].l.setItemHeight(mh)
        self['menu'].l.setList(self.tventries)
        if self.jetzt == True:
            nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if nextpage is not None:
                self.downloadFull(nextpage.group(1), self.makeTVView)
            else:
                self['menu'].moveToIndex(self.index)
                self.ready = True
                self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
                self['label'].stopBlinking()
                self['label'].show()
        elif self.gleich == True:
            if search('<a href=".*?tvspielfilm.de/tv-programm/sendungen/.*?page=[2-9]', bereich) is not None:
                nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
                if nextpage is not None:
                    self.downloadFull(nextpage.group(1), self.makeTVView)
            else:
                self['menu'].moveToIndex(self.index)
                self.ready = True
                self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
                self['label'].stopBlinking()
                self['label'].show()
        elif search('<a href=".*?tvspielfilm.de/tv-programm/sendungen/.*?page=[2-9]', bereich) is not None:
            nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if nextpage is not None:
                self.downloadFull(nextpage.group(1), self.makeTVView)
        else:
            self['menu'].moveToIndex(self.index)
            self.ready = True
            self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
            self['label'].stopBlinking()
            self['label'].show()
        return

    def makePostviewPage(self, string):
        print("DEBUG makePostviewPage TVJetztView")
        self['menu'].hide()
        self._makePostviewPage(string)

    def makeSearchView(self, url):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        searchrequest = Request(url, None, header)
        try:
            output = urlopen(searchrequest).read()
            output = six.ensure_str(output)
        except (HTTPError,
         URLError,
         HTTPException,
         socket.error,
         AttributeError):
            output = ' '

        title = search('<title>(.*?)</title>', output)
        if title is not None:
            self['searchtext'].setText(title.group(1))
            self['searchtext'].show()
            self.setTitle('')
            self.setTitle(title.group(1))
        bereich = parsePrimeTimeTable(output, self.showgenre)
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 10
        mh = 40
        pictopoffset = 0
        picleftoffset = 0
        if self.picon == True:
            mh = 60
            pictopoffset = 10
            picleftoffset = 40
        for x in a:
            if y == 0:
                res = [x]
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                if search('DATUM', x) is not None:
                    if self.datum == True:
                        try:
                            del self.searchref[-1]
                            del self.searchlink[-1]
                            del self.searchentries[-1]
                        except IndexError:
                            pass

                    else:
                        self.datum = True
                    x = sub('DATUM', '', x)
                    self.datum_string = x
                    res_datum = [x]
                    if self.backcolor == True:
                        res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                    res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
                    self.searchref.append('na')
                    self.searchlink.append('na')
                    self.searchentries.append(res_datum)
                    self.filter = True
                    y = 9
                else:
                    y = 1
            if y == 1:
                x = sub('TIME', '', x)
                start = x
                res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7 + pictopoffset), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
            if y == 2:
                if search('LOGO', x) is not None:
                    logo = search('LOGO(.*?)">', x)
                    if logo is not None:
                        x = logo.group(1)
                    service = x
                    sref = self.service_db.lookup(service)
                    if sref == 'nope':
                        self.filter = True
                    else:
                        self.filter = False
                        self.searchref.append(sref)
                        if self.picon == True:
                            picon = self.findPicon(sref)
                            if picon is not None:
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(100, 60), png=LoadPixmap(picon)))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                        else:
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
                        start = sub(' - ..:..', '', start)
                        daynow = sub('....-..-', '', str(self.date))
                        day = search(', ([0-9]+). ', self.datum_string)
                        if day is not None:
                            day = day.group(1)
                        else:
                            day = daynow
                        if int(day) >= int(daynow) - 1:
                            date = str(self.date) + 'FIN'
                        else:
                            four_weeks = datetime.timedelta(weeks=4)
                            date = str(self.date + four_weeks) + 'FIN'
                        date = sub('[0-9][0-9]FIN', day, date)
                        timer = date + ':::' + start + ':::' + str(sref)
                        if timer in self.timer:
                            self.rec = True
                            rp = self.getRecPNG()
                            if rp != None:
                                res.append(rp)
            if y == 3:
                if self.filter == False:
                    x = sub('LINK', '', x)
                    self.searchlink.append(x)
            if y == 4:
                if self.filter == False:
                    x = sub('TITEL', '', x)
                    titelfilter = x
            if y == 5:
                if self.filter == False:
                    if search('GENRE', x) is None:
                        res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                        y = 6
            if y == 6:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        if self.rec == True:
                            self.rec = False
                        else:
                            x = sub('INFO', '', x)
                            rp = self.getPNG(x, self.menuwidth - 140)
                            if rp != None:
                                res.append(rp)
                else:
                    y = 9
            if y == 7:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 210)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 8:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 280)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 9:
                if search('INFO', x) is not None:
                    y = 7
                elif self.filter == False:
                    self.datum = False
                    if search('RATING', x) is not None:
                        x = sub('RATING', '', x)
                        if x != 'rating small':
                            png = '%s%sHD.png' % (ICONPATH, x)
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(1175, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                    self.searchentries.append(res)
            y += 1
            if y == offset:
                y = 0

        self['searchmenu'].l.setItemHeight(mh)
        self['searchmenu'].l.setList(self.searchentries)
        self['searchmenu'].show()
        self.searchcount += 1
        if self.searchcount <= self.maxsearchcount and search('class="pagination__link pagination__link--next" >', bereich) is not None:
            nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if nextpage is not None:
                self.makeSearchView(nextpage.group(1))
            else:
                self.ready = True
        else:
            try:
                if self.searchref[-1] == 'na':
                    del self.searchref[-1]
                    del self.searchlink[-1]
                    del self.searchentries[-1]
                    self['searchmenu'].l.setList(self.searchentries)
            except IndexError:
                pass

            self['searchmenu'].moveToIndex(self.oldsearchindex)
            self.current = 'searchmenu'
            self.ready = True
        return

    def ok(self):
        if self.hideflag == False:
            return
        if self.current == 'menu' or self.current == 'searchmenu':
            self.selectPage('ok')
        elif self.current == 'postview' and self.postviewready == True:
            if self.trailer == True:
                sref = eServiceReference(4097, 0, self.trailerurl)
                sref.setName(self.name)
                self.session.open(MoviePlayer, sref)
            elif self.mehrbilder == True:
                self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
            else:
                self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)

    def selectPage(self, action):
        if self.current == 'menu' and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                self.postlink = self.tvlink[c][1]
            except IndexError:
                pass

        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

        if action == 'ok' and self.ready == True:
            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.current = 'postview'
                self.downloadPostPage(self.postlink, self.makePostviewPage)
        return

    def getEPG(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.showEPG == False:
                self.showEPG = True
                if self.search == False:
                    try:
                        c = self['menu'].getSelectedIndex()
                        sref = self.sref[c][1]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                else:
                    try:
                        c = self['searchmenu'].getSelectedIndex()
                        sref = self.searchref[c]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                if sref is not None:
                    try:
                        start = self.start
                        s1 = sub(':..', '', start)
                        date = str(self.postdate) + 'FIN'
                        date = sub('..FIN', '', date)
                        date = date + self.day
                        parts = start.split(':')
                        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                        start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                        s2 = sub(':..:..', '', start)
                        if int(s2) > int(s1):
                            start = str(self.date) + ' ' + start
                        else:
                            start = date + ' ' + start
                        start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                        start = int(mktime(start.timetuple()))
                        epgcache = eEPGCache.getInstance()
                        event = epgcache.startTimeQuery(eServiceReference(sref), start)
                        if event == -1:
                            self.EPGText = getEPGText()

                        else:
                            event = epgcache.getNextTimeEntry()
                            self.EPGtext = event.getEventName()
                            short = event.getShortDescription()
                            ext = event.getExtendedDescription()
                            dur = '%d Minuten' % (event.getDuration() / 60)
                            if short and short != self.EPGtext:
                                self.EPGtext += '\n\n' + short
                            if ext:
                                self.EPGtext += '\n\n' + ext
                            if dur:
                                self.EPGtext += '\n\n' + dur
                    except:
                        self.EPGText = getEPGText()

                else:
                    self.EPGtext = NOEPG
                fill = self.getFill(channel)
                self.EPGtext += '\n\n' + fill
                self['textpage'].setText(self.EPGtext)
                self['textpage'].show()
            else:
                self.showEPG = False
                self['textpage'].setText(self.POSTtext)
                self['textpage'].show()
        elif self.current == 'menu' and self.ready == True and self.search == False:
            self.ready = False
            self.tventries = []
            self.tvlink = []
            self.tvtitel = []
            self.sref = []
            if self.jetzt == True:
                self.jetzt = False
                self.gleich = True
                self['label'].setText('Bitte warten...')
                self['label'].startBlinking()
                link = self.baseurl + '/tv-programm/sendungen/?page=1&order=time&time=shortly'
                self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
            else:
                self.jetzt = True
                self.gleich = False
                self.abends = False
                self.nachts = False
                self['label'].setText('Bitte warten...')
                self['label'].startBlinking()
                link = self.baseurl + '/tv-programm/sendungen/jetzt.html'
                self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        return

    def red(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.search == False:
                try:
                    c = self['menu'].getSelectedIndex()
                    self.oldindex = c
                    sref = self.sref[c][1]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.search == True:
                try:
                    c = self['searchmenu'].getSelectedIndex()
                    self.oldsearchindex = c
                    sref = self.searchref[c]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            else:
                self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
        elif self.current == 'menu' and self.ready == True:
            c = self['menu'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink[c][1]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.index = self.oldindex
                self.download(self.postlink, self.makePostTimer)
        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            self.oldsearchindex = c
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.download(self.postlink, self.makePostTimer)
        return

    def finishedTimer(self, answer):
        if answer[0]:
            entry = answer[1]
            simulTimerList = self.session.nav.RecordTimer.record(entry)
            if simulTimerList is not None:
                for x in simulTimerList:
                    if x.setAutoincreaseEnd(entry):
                        self.session.nav.RecordTimer.timeChanged(x)

                simulTimerList = self.session.nav.RecordTimer.record(entry)
                if simulTimerList is not None:
                    self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
            self.makeTimerDB()
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
                self.refresh()
            else:
                self.showsearch()
        else:
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
            else:
                self.showsearch()
        return

    def green(self):
        if self.current == 'menu' and self.search == False:
            c = self['menu'].getSelectedIndex()
            try:
                sref = self.sref[c][1]
                if sref != '':
                    self.session.nav.playService(eServiceReference(sref))
                    if config.plugins.tvspielfilm.zapexit.value == 'yes' and self.standalone == True:
                        self.close()
            except IndexError:
                pass

    def yellow(self):
        if self.current == 'postview':
            self.youTube()
        elif self.current == 'menu' and self.search == False and self.ready == True:
            try:
                c = self['menu'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel[c][1]
                except IndexError:
                    pass
                    titel=''

                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
            except IndexError:
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

    def searchReturn(self, search):
        if search and search != '':
            self.searchstring = search
            self['menu'].hide()
            self['label'].setText('')
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            self['searchlogo'].show()
            self['searchtimer'].show()
            self.searchlink = []
            self.searchref = []
            self.searchentries = []
            self.search = True
            self.datum = False
            self.filter = True
            search = search.replace(' ', '+')
            searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
            self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
            self.searchcount = 0
            self.makeSearchView(searchlink)

    def pressText(self):
        if self.current == 'menu' and self.ready == True:
            try:
                c = self['menu'].getSelectedIndex()
                channel = self.sref[c][0]
                link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
                self.session.open(TVProgrammView, link, True, False)
            except IndexError:
                pass
        else:
            self._pressText()

    def youTube(self):
        if self.current == 'postview' and self.postviewready == True:
            self.session.open(searchYouTube, self.name, self.movie)
        elif self.current == 'menu' and self.search == False and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                titel = self.tvtitel[c][1]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

    def gotoEnd(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            end = len(self.tventries) - 1
            self['menu'].moveToIndex(end)
        elif self.current != 'postview' and self.ready == True and self.search == True:
            end = len(self.searchentries) - 1
            self['searchmenu'].moveToIndex(end)

    def findPicon(self, sref):
        sref = sref + 'FIN'
        sref = sref.replace(':', '_')
        sref = sref.replace('_FIN', '')
        sref = sref.replace('FIN', '')
        pngname = self.piconfolder + sref + '.png'
        if fileExists(pngname):
            return pngname

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        currPic = loadPic(picpost, 490, 245, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
            self['piclabel'].show()
            self['piclabel2'].show()
            if self.trailer == True:
                self['cinlogo'].show()
                self['playlogo'].show()
        return

    def showPicTVinfoX(self, picinfo, X):
        currPic = loadPic(picinfo, 60, 20, 3, 0, 0, 0)
        if currPic != None:
            self[X].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadFull(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadFullError)

    def downloadFullError(self, output):
        self['label'].setText('Text = Sender,        Info = Jetzt im TV/Gleich im TV')
        self['label'].stopBlinking()
        self['label'].show()
        self.ready = True

    def downloadPostPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

    def downloadPageError(self, output):
        print(output)
        self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
        self['label'].stopBlinking()
        self['label'].show()
        self.ready = True

    def refresh(self):
        self.postviewready = False
        self.ready = False
        self.current = 'menu'
        self['label'].setText('Bitte warten...')
        self['label'].startBlinking()
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.sref = []
        if self.jetzt == True:
            link = self.baseurl + '/tv-programm/sendungen/jetzt.html'
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        elif self.gleich == True:
            link = self.baseurl + '/tv-programm/sendungen/?page=1&order=time&time=shortly'
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        elif self.abends == True:
            link = self.baseurl + '/tv-programm/sendungen/abends.html'
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))
        else:
            link = self.baseurl + '/tv-programm/sendungen/fernsehprogramm-nachts.html'
            self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVView))

    def showProgrammPage(self):
        self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
        self['label2'].setText('= Timer')
        self['label3'].setText('= Suche')
        self['label4'].setText('= Zappen')
        self['infotext'].hide()
        self['infotext2'].hide()
        self['infotext3'].hide()
        self['infotext4'].hide()
        self['infotext5'].hide()
        self['infotext6'].hide()
        self['infotext7'].hide()
        self['infotext8'].hide()
        self['cinlogo'].hide()
        self['playlogo'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['piclabel'].hide()
        self['piclabel2'].hide()
        self['tvinfo1'].hide()
        self['tvinfo2'].hide()
        self['tvinfo3'].hide()
        self['tvinfo4'].hide()
        self['tvinfo5'].hide()
        self['searchmenu'].hide()
        self['searchlogo'].hide()
        self['searchtimer'].hide()
        self['searchtext'].hide()
        self.current = 'menu'
        self['menu'].show()

    def down(self):
        try:
            if self.current == 'menu':
                self['menu'].down()
            elif self.current == 'searchmenu':
                self['searchmenu'].down()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def up(self):
        try:
            if self.current == 'menu':
                self['menu'].up()
            elif self.current == 'searchmenu':
                self['searchmenu'].up()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def rightDown(self):
        try:
            if self.current == 'menu':
                self['menu'].pageDown()
            elif self.current == 'searchmenu':
                self['searchmenu'].pageDown()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def leftUp(self):
        try:
            if self.current == 'menu':
                self['menu'].pageUp()
            elif self.current == 'searchmenu':
                self['searchmenu'].pageUp()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu' and self.search == False:
            if fileExists(self.picfile):
                os.remove(self.picfile)
            if fileExists(self.localhtml):
                os.remove(self.localhtml)
            if fileExists(self.localhtml2):
                os.remove(self.localhtml2)
            if self.standalone == True:
                config.usage.on_movie_stop.value = self.movie_stop
                config.usage.on_movie_eof.value = self.movie_eof
            self.close()
        elif self.current == 'searchmenu':
            self.search = False
            self.oldsearchindex = 1
            self['searchmenu'].hide()
            self['searchlogo'].hide()
            self['searchtimer'].hide()
            self['searchtext'].hide()
            self.setTitle('')
            self.setTitle(self.titel)
            self.showProgrammPage()
        elif self.current == 'postview' and self.search == False:
            self.postviewready = False
            self.setTitle('')
            self.setTitle(self.titel)
            self.showProgrammPage()
        elif self.current == 'postview' and self.search == True:
            self.postviewready = False
            self.showsearch()
            self.current = 'searchmenu'


class TVProgrammView(tvBaseScreen):
    def __init__(self, session, link, eventview, tagestipp):
        self.eventview = eventview
        self.tagestipp = tagestipp
        self.service_db = serviceDB(self.servicefile)
        skin = """
        <screen name="TVProgrammView" position="{screenpos}" size="{screensize}" title="TV Programm - TV Spielfilm">
            %s%s%s
        </screen>""" % ( SKHEADTOP, SKMENU, SKHEADBOTTOM )
        tvBaseScreen.__init__(self, session, skin)
        if self.tagestipp == False:
            channel = re.findall(',(.*?).html', link)
            service = channel[0].lower()
            self.sref = self.service_db.lookup(service)
            if self.sref == 'nope':
                self.zap = False
                self.picon = False
            else:
                self.zap = True
                if self.picon == True:
                    self.piconname = self.findPicon(self.sref)
                    if self.piconname is None:
                        self.picon = False
        self.current = 'menu'
        self.oldcurrent = 'menu'
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.searchlink = []
        self.searchref = []
        self.searchentries = []
        self.start = ''
        self.end = ''
        self.day = ''
        self.name = ''
        self.shortdesc = ''
        self.postlink = link
        self.link = link
        self.trailerurl = ''
        self.titel = ''
        self.POSTtext = ''
        self.EPGtext = ''
        self.hideflag = True
        self.primetime = False
        self.search = False
        self.rec = False
        self.ready = False
        self.postviewready = False
        self.mehrbilder = False
        self.trailer = False
        self.movie = False
        self.datum = False
        self.filter = True
        self.oldindex = 0
        self.oldsearchindex = 1
        self['picpost'] = Pixmap()
        self['tvinfo1'] = Pixmap()
        self['tvinfo2'] = Pixmap()
        self['tvinfo3'] = Pixmap()
        self['tvinfo4'] = Pixmap()
        self['tvinfo5'] = Pixmap()
        self['cinlogo'] = Pixmap()
        self['cinlogo'].hide()
        self['playlogo'] = Pixmap()
        self['playlogo'].hide()
        self['searchlogo'] = Pixmap()
        self['searchlogo'].hide()
        self['searchtimer'] = Pixmap()
        self['searchtimer'].hide()
        self['searchtext'] = Label('')
        self['searchtext'].hide()
        self['textpage'] = ScrollLabel('')
        self['infotext'] = Label('')
        self['infotext'].hide()
        self['infotext2'] = Label('')
        self['infotext2'].hide()
        self['infotext3'] = Label('')
        self['infotext3'].hide()
        self['infotext4'] = Label('')
        self['infotext4'].hide()
        self['infotext5'] = Label('')
        self['infotext5'].hide()
        self['infotext6'] = Label('')
        self['infotext6'].hide()
        self['infotext7'] = Label('')
        self['infotext7'].hide()
        self['infotext8'] = Label('')
        self['infotext8'].hide()
        self['piclabel'] = Label('')
        self['piclabel'].hide()
        self['piclabel2'] = Label('')
        self['piclabel2'].hide()
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['searchmenu'] = ItemList([])
        self['searchmenu'].hide()
        self['menu'] = ItemList([])
        self['label'] = BlinkingLabel('Bitte warten...')
        self['label'].startBlinking()
        self['label2'] = Label('= Timer')
        self['label3'] = Label('= Suche')
        if self.eventview == False:
            self['label4'] = Label('= Zappen')
        else:
            self['label4'] = Label('= Refresh')
        self['actions'] = ActionMap(['OkCancelActions',
         'ChannelSelectBaseActions',
         'DirectionActions',
         'HelpActions',
         'EPGSelectActions',
         'InfobarTeletextActions',
         'NumberActions',
         'MoviePlayerActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.nextDay,
         'prevBouquet': self.prevDay,
         'nextMarker': self.nextWeek,
         'prevMarker': self.prevWeek,
         '0': self.gotoEnd,
         '1': self.zapUp,
         '2': self.zapDown,
         '7': self.IMDb,
         '8': self.TMDb,
         '9': self.TVDb,
         'info': self.getEPG,
         'epg': self.getEPG,
         'leavePlayer': self.youTube,
         'startTeletext': self.pressText}, -1)
        self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
         'yellow': self.yellow,
         'red': self.makeTimer,
         'blue': self.hideScreen}, -1)
        self.timer = open('/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/timer.db').read()
        self.date = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        self.nextdate = self.date + one_day
        self.weekday = makeWeekDay(self.date.weekday())
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        if config.plugins.tvspielfilm.genreinfo.value == 'no':
            self.showgenre = False
        else:
            self.showgenre = True
        if self.eventview == True:
            self.movie_stop = config.usage.on_movie_stop.value
            self.movie_eof = config.usage.on_movie_eof.value
            config.usage.on_movie_stop.value = 'quit'
            config.usage.on_movie_eof.value = 'quit'
            from Components.ServiceEventTracker import ServiceEventTracker
            from enigma import iPlayableService
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evUpdatedEventInfo: self.zapRefresh})
            self.channel_db = serviceDB(self.servicefile)
        elif self.tagestipp == False:
            nextday = sub('/sendungen/.*?html', '/sendungen/?page=1&order=time&date=', self.link)
            nextday = nextday + str(self.date)
            nextday = nextday + '&tips=0&time=day&channel=' + channel[0]
            self.link = nextday
        self.makeTVTimer = eTimer()
        if self.tagestipp == False:
            self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
        else:
            self.current = 'postview'
            self['label'].stopBlinking()
            self['label'].show()
            self.makeTVTimer.callback.append(self.downloadPostPage(self.link, self.makePostviewPage))
        self.makeTVTimer.start(500, True)
        return

    def makeTVView(self, string):
        output = open(self.localhtml, 'r').read()
        titel = search('<title>(.*?)von', output)
        date = str(self.date.strftime('%d.%m.%Y'))
        self.titel = str(titel.group(1)) + ' - ' + str(self.weekday) + ', ' + date
        self.setTitle(self.titel)
        bereich = parseInfoTable(output)
        today = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        yesterday = today - one_day
        nowhour = datetime.datetime.now().hour
        if self.date == today and nowhour > 4 or self.date == yesterday and nowhour < 5:
            self.progress = True
            nowminute = datetime.datetime.now().minute
            nowsec = int(nowhour) * 3600 + int(nowminute) * 60
        else:
            self.progress = False
            self.percent = False
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 7
        pictopoffset = 0
        picleftoffset = 0
        mh = 40
        if self.picon == True:
            mh = 62
            pictopoffset = 11
            picleftoffset = 40

        scaleoffset = 0
        if self.fontlarge == True:
            scaleoffset = 10

        for x in a:
            if y == 0:
                x = sub('LOGO', '', x)
                res = [x]
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))

                if self.picon == True:
                    if fileExists(self.piconname):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 1), size=(100, 60), png=LoadPixmap(self.piconname)))
                else:
                    png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
            if y == 1:
                x = sub('TIME', '', x)
                if self.progress == True:
                    start = sub(' - ..:..', '', x)
                    startparts = start.split(':')
                    startsec = int(startparts[0]) * 3600 + int(startparts[1]) * 60
                    end = sub('..:.. - ', '', x)
                    endparts = end.split(':')
                    endsec = int(endparts[0]) * 3600 + int(endparts[1]) * 60
                    if endsec >= startsec:
                        length = endsec - startsec
                    else:
                        length = 86400 - startsec + endsec
                    if nowsec < startsec and endsec > startsec:
                        percent = 0
                        self.percent = False
                    elif endsec < startsec:
                        if nowsec > startsec:
                            passed = nowsec - startsec
                            percent = passed * 100 / length
                            self.percent = True
                        elif nowsec < endsec:
                            passed = 86400 - startsec + nowsec
                            percent = passed * 100 / length
                            self.percent = True
                        elif nowsec - endsec < startsec - nowsec:
                            percent = 100
                            self.percent = False
                        else:
                            percent = 0
                            self.percent = False
                    elif nowsec > endsec:
                        percent = 100
                        self.percent = False
                    else:
                        passed = nowsec - startsec
                        percent = passed * 100 / length
                        self.percent = True
                if search('20:15 -', x) is not None or self.percent == True:
                    self.primetime = True
                else:
                    self.primetime = False
                res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7 + pictopoffset), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                start = sub(' - ..:..', '', x)
                hour = sub(':..', '', start)
                if int(hour) < 5 and len(self.tventries) > 6 or int(hour) < 5 and self.eventview == True:
                    one_day = datetime.timedelta(days=1)
                    date = self.date + one_day
                else:
                    date = self.date
                timer = str(date) + ':::' + start + ':::' + str(self.sref)
                if timer in self.timer:
                    self.rec = True
                    png = ICONPATH + 'icon-small-recHD.png'
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(1014, pictopoffset), size=(39, 40), png=loadPNG(png)))
            if y == 2:
                x = sub('LINK', '', x)
                self.tvlink.append(x)
            if y == 3:
                if search('TITEL', x) is not None:
                    t = sub('TITEL', '', x)
                    if self.showgenre and search('GENRE', x) is not None:
                        x = t + " " + sub('GENRE', '', x)
                    else:
                        x = t
                    self.tvtitel.append(t)
                    if self.progress == False or self.percent == False:
                        res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(self.menuwidth - 400 - picleftoffset - scaleoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    else:
                        res.append(MultiContentEntryProgress(pos=(235 + picleftoffset, 13 + pictopoffset), size=(70, 14), percent=percent, borderWidth=1, foreColor=16777215))
                        res.append(MultiContentEntryText(pos=(325 + picleftoffset, 7 + pictopoffset), size=(self.menuwidth - 490 - picleftoffset - scaleoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                else:
                    y = 5
            if y == 5:
                if search('SPARTE', x) is not None:
                    x = sub('SPARTE', '', x)
                    if self.primetime == False:
                        res.append(MultiContentEntryText(pos=(self.menuwidth - 160 - scaleoffset, 7 + pictopoffset), size=(152 + scaleoffset, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT, text=x))
                    else:
                        res.append(MultiContentEntryText(pos=(self.menuwidth - 160 - scaleoffset, 7 + pictopoffset), size=(152 + scaleoffset, 40), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_RIGHT, text=x))
                else:
                    y = 6
            if y == 6:
                if search('RATING', x) is not None:
                    x = sub('RATING', '', x)
                    if self.rec == True:
                        self.rec = False
                    elif x != 'rating small':
                        png = '%s%sHD.png' % (ICONPATH, x)
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - 210, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    self.tventries.append(res)
                else:
                    self.tventries.append(res)
            y += 1
            if y == offset:
                y = 0

        self['menu'].l.setItemHeight(mh)
        self['menu'].l.setList(self.tventries)
        self['menu'].moveToIndex(self.oldindex)
        if search('class="pagination__link pagination__link--next" >', bereich) is not None:
            link = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if link is not None:
                self.makeTVTimer.callback.append(self.downloadFullPage(link.group(1), self.makeTVView))
            else:
                self.ready = True
        else:
            self.ready = True
            if self.eventview == False:
                self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
                self['label'].stopBlinking()
                self['label'].show()
            else:
                self['label'].setText('Bouquet = +- Tag, <> = +- Woche, 1/2 = Zap Up/Down')
                self['label'].stopBlinking()
                self['label'].show()
        if self.eventview == True and config.plugins.tvspielfilm.eventview.value == 'info':
            self.postlink = self.tvlink[0]
            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.current = 'postview'
                self.downloadPostPage(self.postlink, self.makePostviewPage)
            else:
                self.ready = True
        return

    def makePostviewPage(self, string):
        print("DEBUG makePostviewPage TVProgrammView")
        self['menu'].hide()
        self._makePostviewPage(string)

    def makeSearchView(self, url):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        searchrequest = Request(url, None, header)
        try:
            output = urlopen(searchrequest).read()
            output = six.ensure_str(output)
        except (HTTPError,
         URLError,
         HTTPException,
         socket.error,
         AttributeError):
            output = ' '

        title = search('<title>(.*?)</title>', output)
        if title is not None:
            self['searchtext'].setText(title.group(1))
            self['searchtext'].show()
            self.setTitle('')
            self.setTitle(title.group(1))
        bereich = parsePrimeTimeTable(output, self.showgenre)
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 10
        mh = 40
        pictopoffset = 0
        picleftoffset = 0
        if self.picon == True:
            mh = 60
            pictopoffset = 10
            picleftoffset = 40
        for x in a:
            if y == 0:
                res = [x]
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                if search('DATUM', x) is not None:
                    if self.datum == True:
                        try:
                            del self.searchref[-1]
                            del self.searchlink[-1]
                            del self.searchentries[-1]
                        except IndexError:
                            pass

                    else:
                        self.datum = True
                    x = sub('DATUM', '', x)
                    self.datum_string = x
                    res_datum = [x]

                    if self.backcolor == True:
                        res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                    res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
                    self.searchref.append('na')
                    self.searchlink.append('na')
                    self.searchentries.append(res_datum)
                    self.filter = True
                    y = 9
                else:
                    y = 1
            if y == 1:
                x = sub('TIME', '', x)
                start = x
                res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7 + pictopoffset), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
            if y == 2:
                if search('LOGO', x) is not None:
                    logo = search('LOGO(.*?)">', x)
                    if logo is not None:
                        x = logo.group(1)
                    service = x
                    sref = self.service_db.lookup(service)
                    if sref == 'nope':
                        self.filter = True
                    else:
                        self.filter = False
                        self.searchref.append(sref)
                        if self.picon == True:
                            picon = self.findPicon(sref)
                            if picon is not None:
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(100, 60), png=LoadPixmap(picon)))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                        else:
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
                        start = sub(' - ..:..', '', start)
                        daynow = sub('....-..-', '', str(self.date))
                        day = search(', ([0-9]+). ', self.datum_string)
                        if day is not None:
                            day = day.group(1)
                        else:
                            day = daynow
                        if int(day) >= int(daynow) - 1:
                            date = str(self.date) + 'FIN'
                        else:
                            four_weeks = datetime.timedelta(weeks=4)
                            date = str(self.date + four_weeks) + 'FIN'
                        date = sub('[0-9][0-9]FIN', day, date)
                        timer = date + ':::' + start + ':::' + str(sref)
                        if timer in self.timer:
                            self.rec = True
                            rp = self.getRecPNG()
                            if rp != None:
                                res.append(rp)
            if y == 3:
                if self.filter == False:
                    x = sub('LINK', '', x)
                    self.searchlink.append(x)
            if y == 4:
                if self.filter == False:
                    x = sub('TITEL', '', x)
                    titelfilter = x
            if y == 5:
                if self.filter == False:
                    if search('GENRE', x) is None:
                        res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                        y = 6
            if y == 6:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        if self.rec == True:
                            self.rec = False
                        else:
                            x = sub('INFO', '', x)
                            rp = self.getPNG(x, self.menuwidth - 140)
                            if rp != None:
                                res.append(rp)
                else:
                    y = 9
            if y == 7:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 210)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 8:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 280)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 9:
                if search('INFO', x) is not None:
                    y = 7
                elif self.filter == False:
                    self.datum = False
                    if search('RATING', x) is not None:
                        x = sub('RATING', '', x)
                        if x != 'rating small':
                            png = '%s%sHD.png' % (ICONPATH, x)
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(1175, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                    self.searchentries.append(res)
            y += 1
            if y == offset:
                y = 0

        self['searchmenu'].l.setItemHeight(mh)
        self['searchmenu'].l.setList(self.searchentries)
        self['searchmenu'].show()
        self.searchcount += 1
        if self.searchcount <= self.maxsearchcount and search('class="pagination__link pagination__link--next" >', bereich) is not None:
            nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if nextpage is not None:
                self.makeSearchView(nextpage.group(1))
            else:
                self.ready = True
        else:
            try:
                if self.searchref[-1] == 'na':
                    del self.searchref[-1]
                    del self.searchlink[-1]
                    del self.searchentries[-1]
                    self['searchmenu'].l.setList(self.searchentries)
            except IndexError:
                pass

            self['searchmenu'].moveToIndex(self.oldsearchindex)
            self.current = 'searchmenu'
            self.ready = True
        return

    def ok(self):
        if self.hideflag == False:
            return
        if self.current == 'menu' or self.current == 'searchmenu':
            self.selectPage('ok')
        elif self.current == 'postview' and self.postviewready == True:
            if self.trailer == True:
                sref = eServiceReference(4097, 0, self.trailerurl)
                sref.setName(self.name)
                self.session.open(MoviePlayer, sref)
            elif self.mehrbilder == True:
                self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
            else:
                self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)

    def selectPage(self, action):
        if self.current == 'menu' and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                self.postlink = self.tvlink[c]
            except IndexError:
                pass

        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

        if action == 'ok' and self.ready == True:
            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.current = 'postview'
                self.downloadPostPage(self.postlink, self.makePostviewPage)
        return

    def getEPG(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.showEPG == False:
                self.showEPG = True
                if self.zap == True and self.search == False:
                    sref = self.sref
                    channel = ServiceReference(eServiceReference(sref)).getServiceName()
                elif self.search == True:
                    try:
                        c = self['searchmenu'].getSelectedIndex()
                        sref = self.searchref[c]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                else:
                    sref = None
                    channel = ''
                if sref is not None:
                    try:
                        start = self.start
                        s1 = sub(':..', '', start)
                        date = str(self.postdate) + 'FIN'
                        date = sub('..FIN', '', date)
                        date = date + self.day
                        parts = start.split(':')
                        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                        start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                        s2 = sub(':..:..', '', start)
                        if int(s2) > int(s1):
                            start = str(self.date) + ' ' + start
                        else:
                            start = date + ' ' + start
                        start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                        start = int(mktime(start.timetuple()))
                        epgcache = eEPGCache.getInstance()
                        event = epgcache.startTimeQuery(eServiceReference(sref), start)
                        if event == -1:
                            self.EPGText = getEPGText()

                        else:
                            event = epgcache.getNextTimeEntry()
                            self.EPGtext = event.getEventName()
                            short = event.getShortDescription()
                            ext = event.getExtendedDescription()
                            dur = '%d Minuten' % (event.getDuration() / 60)
                            if short and short != self.EPGtext:
                                self.EPGtext += '\n\n' + short
                            if ext:
                                self.EPGtext += '\n\n' + ext
                            if dur:
                                self.EPGtext += '\n\n' + dur
                    except:
                        self.EPGText = getEPGText()

                else:
                    self.EPGtext = NOEPG
                fill = self.getFill(channel)
                self.EPGtext += '\n\n' + fill
                self['textpage'].setText(self.EPGtext)
                self['textpage'].show()
            else:
                self.showEPG = False
                self['textpage'].setText(self.POSTtext)
                self['textpage'].show()
        return

    def red(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.zap == True and self.search == False:
                try:
                    c = self['menu'].getSelectedIndex()
                    self.oldindex = c
                    sref = self.sref
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.search == True:
                try:
                    c = self['searchmenu'].getSelectedIndex()
                    self.oldsearchindex = c
                    sref = self.searchref[c]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                try:
                    start = self.start
                    s1 = sub(':..', '', start)
                    date = str(self.postdate) + 'FIN'
                    date = sub('..FIN', '', date)
                    date = date + self.day
                    parts = start.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds -= int(config.recording.margin_before.value) * 60
                    start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    s2 = sub(':..:..', '', start)
                    if int(s2) > int(s1):
                        start = str(self.date) + ' ' + start
                    else:
                        start = date + ' ' + start
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = self.end
                    parts = end.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                    seconds += int(config.recording.margin_after.value) * 60
                    end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                    e2 = sub(':..:..', '', end)
                    if int(s2) > int(e2):
                        end = str(self.nextdate) + ' ' + end
                    else:
                        end = date + ' ' + end
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except IndexError:
                    pass

                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            else:
                self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
        elif self.current == 'menu' and self.ready == True and self.zap == True:
            c = self['menu'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink[c]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.download(self.postlink, self.makePostTimer)
        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            self.oldsearchindex = c
            try:
                self.postlink = self.searchlink[c]
            except IndexError:
                pass

            if search('www.tvspielfilm.de', self.postlink) is not None:
                self.oldcurrent = self.current
                self.download(self.postlink, self.makePostTimer)
        else:
            self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
        return

    def finishedTimer(self, answer):
        if answer[0]:
            entry = answer[1]
            simulTimerList = self.session.nav.RecordTimer.record(entry)
            if simulTimerList is not None:
                for x in simulTimerList:
                    if x.setAutoincreaseEnd(entry):
                        self.session.nav.RecordTimer.timeChanged(x)

                simulTimerList = self.session.nav.RecordTimer.record(entry)
                if simulTimerList is not None:
                    self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
            self.makeTimerDB()
            if self.tagestipp == False:
                self.ready = True
                self.postviewready = False
                self.current = self.oldcurrent
                if self.search == False:
                    self.showProgrammPage()
                    self.refresh()
                else:
                    self.showsearch()
        elif self.tagestipp == False:
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
            else:
                self.showsearch()
        return

    def green(self):
        if self.current == 'menu' and self.zap == True and self.eventview == False and self.search == False:
            c = self['menu'].getSelectedIndex()
            try:
                sref = self.sref
                if sref != '':
                    self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

        elif self.current == 'menu' and self.eventview == True and self.search == False:
            sref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
            sref = str(sref) + 'FIN'
            sref = sub(':0:0:0:.*?FIN', ':0:0:0:', sref)
            self.sref = sref
            channel = self.channel_db.lookup(sref)
            if channel == 'nope':
                self.session.open(MessageBox, 'Service not found:\nNo entry for current service reference\n%s' % str(sref), MessageBox.TYPE_INFO, close_on_any_key=True)
            else:
                if self.picon == True:
                    self.piconname = self.findPicon(sref)
                    if self.piconname is None:
                        self.piconname = 'none.png'
                self.link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
                self.refresh()
        return

    def yellow(self):
        if self.current == 'postview':
            self.youTube()
        elif self.current == 'menu' and self.search == False and self.ready == True:
            try:
                c = self['menu'].getSelectedIndex()
                self.oldindex = c
                titel = self.tvtitel[c]
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
            except IndexError:
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

    def searchReturn(self, search):
        if search and search != '':
            self.searchstring = search
            self['menu'].hide()
            self['label'].setText('')
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            self['searchlogo'].show()
            self['searchtimer'].show()
            self.searchlink = []
            self.searchref = []
            self.searchentries = []
            self.search = True
            self.datum = False
            self.filter = True
            search = search.replace(' ', '+')
            searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
            self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
            self.searchcount = 0
            self.makeSearchView(searchlink)

    def pressText(self):
        self._pressText()

    def youTube(self):
        if self.current == 'postview' and self.postviewready == True:
            self.session.open(searchYouTube, self.name, self.movie)
        elif self.current == 'menu' and self.search == False and self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                titel = self.tvtitel[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

    def nextDay(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('time&date', self.link) is not None:
                date1 = re.findall('time&date=(.*?)-..-..&tips', self.link)
                date2 = re.findall('time&date=....-(.*?)-..&tips', self.link)
                date3 = re.findall('time&date=....-..-(.*?)&tips', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

            else:
                self.link = sub('.html', '', self.link)
                self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
                today = datetime.date.today()
            one_day = datetime.timedelta(days=1)
            tomorrow = today + one_day
            self.weekday = makeWeekDay(tomorrow.weekday())
            self.link = self.link + 'FIN'
            channel = re.findall('channel=(.*?)FIN', self.link)
            nextday = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
            nextday = nextday + str(tomorrow)
            nextday = nextday + '&tips=0&time=day&channel=' + channel[0]
            self.date = tomorrow
            one_day = datetime.timedelta(days=1)
            self.nextdate = self.date + one_day
            self.link = nextday
            self.oldindex = 0
            self.refresh()
        elif self.current == 'postview' or self.search == True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)
        return

    def prevDay(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('time&date', self.link) is not None:
                date1 = re.findall('time&date=(.*?)-..-..&tips', self.link)
                date2 = re.findall('time&date=....-(.*?)-..&tips', self.link)
                date3 = re.findall('time&date=....-..-(.*?)&tips', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

            else:
                self.link = sub('.html', '', self.link)
                self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
                today = datetime.date.today()
            one_day = datetime.timedelta(days=1)
            yesterday = today - one_day
            self.weekday = makeWeekDay(yesterday.weekday())
            self.link = self.link + 'FIN'
            channel = re.findall('channel=(.*?)FIN', self.link)
            prevday = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
            prevday = prevday + str(yesterday)
            prevday = prevday + '&tips=0&time=day&channel=' + channel[0]
            self.date = yesterday
            one_day = datetime.timedelta(days=1)
            self.nextdate = self.date + one_day
            self.link = prevday
            self.oldindex = 0
            self.refresh()
        elif self.current == 'postview' or self.search == True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)
        return

    def nextWeek(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('time&date', self.link) is not None:
                date1 = re.findall('time&date=(.*?)-..-..&tips', self.link)
                date2 = re.findall('time&date=....-(.*?)-..&tips', self.link)
                date3 = re.findall('time&date=....-..-(.*?)&tips', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

            else:
                self.link = sub('.html', '', self.link)
                self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
                today = datetime.date.today()
            one_week = datetime.timedelta(days=7)
            tomorrow = today + one_week
            self.weekday = makeWeekDay(tomorrow.weekday())
            self.link = self.link + 'FIN'
            channel = re.findall('channel=(.*?)FIN', self.link)
            nextweek = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
            nextweek = nextweek + str(tomorrow)
            nextweek = nextweek + '&tips=0&time=day&channel=' + channel[0]
            self.date = tomorrow
            one_week = datetime.timedelta(days=7)
            self.nextdate = self.date + one_week
            self.link = nextweek
            self.oldindex = 0
            self.refresh()
        return

    def prevWeek(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('time&date', self.link) is not None:
                date1 = re.findall('time&date=(.*?)-..-..&tips', self.link)
                date2 = re.findall('time&date=....-(.*?)-..&tips', self.link)
                date3 = re.findall('time&date=....-..-(.*?)&tips', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

            else:
                self.link = sub('.html', '', self.link)
                self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
                today = datetime.date.today()
            one_week = datetime.timedelta(days=7)
            yesterday = today - one_week
            self.weekday = makeWeekDay(yesterday.weekday())
            self.link = self.link + 'FIN'
            channel = re.findall('channel=(.*?)FIN', self.link)
            prevweek = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
            prevweek = prevweek + str(yesterday)
            prevweek = prevweek + '&tips=0&time=day&channel=' + channel[0]
            self.date = yesterday
            one_week = datetime.timedelta(days=7)
            self.nextdate = self.date + one_week
            self.link = prevweek
            self.oldindex = 0
            self.refresh()
        return

    def gotoEnd(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            end = len(self.tventries) - 1
            self['menu'].moveToIndex(end)
        elif self.current != 'postview' and self.ready == True and self.search == True:
            end = len(self.searchentries) - 1
            self['searchmenu'].moveToIndex(end)

    def findPicon(self, sref):
        sref = sref + 'FIN'
        sref = sref.replace(':', '_')
        sref = sref.replace('_FIN', '')
        sref = sref.replace('FIN', '')
        pngname = self.piconfolder + sref + '.png'
        if fileExists(pngname):
            return pngname

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        currPic = loadPic(picpost, 490, 245, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
            self['piclabel'].show()
            self['piclabel2'].show()
            if self.trailer == True:
                self['cinlogo'].show()
                self['playlogo'].show()
        return

    def showPicTVinfoX(self, picinfo, X):
        currPic = loadPic(picinfo, 60, 20, 3, 0, 0, 0)
        if currPic != None:
            self[X].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadPostPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

    def downloadPageError(self, output):
        print(output)
        if self.eventview == False:
            self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
            self['label'].stopBlinking()
            self['label'].show()
        else:
            self['label'].setText('Bouquet = +- Tag, <> = +- Woche, 1/2 = Zap Up/Down')
            self['label'].stopBlinking()
            self['label'].show()
        self.ready = True

    def refresh(self):
        self.postviewready = False
        self.ready = False
        self.current = 'menu'
        self['label'].setText('Bitte warten...')
        self['label'].startBlinking()
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))

    def showProgrammPage(self):
        if self.eventview == False:
            self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
            self['label2'].setText('= Timer')
            self['label3'].setText('= Suche')
            self['label4'].setText('= Zappen')
        else:
            self['label'].setText('Bouquet = +- Tag, <> = +- Woche, 1/2 = Zap Up/Down')
            self['label2'].setText('= Timer')
            self['label3'].setText('= Suche')
            self['label4'].setText('= Refresh')
        self['infotext'].hide()
        self['infotext2'].hide()
        self['infotext3'].hide()
        self['infotext4'].hide()
        self['infotext5'].hide()
        self['infotext6'].hide()
        self['infotext7'].hide()
        self['infotext8'].hide()
        self['cinlogo'].hide()
        self['playlogo'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['piclabel'].hide()
        self['piclabel2'].hide()
        self['tvinfo1'].hide()
        self['tvinfo2'].hide()
        self['tvinfo3'].hide()
        self['tvinfo4'].hide()
        self['tvinfo5'].hide()
        self['searchmenu'].hide()
        self['searchlogo'].hide()
        self['searchtimer'].hide()
        self['searchtext'].hide()
        self.current = 'menu'
        self['menu'].show()

    def down(self):
        try:
            if self.current == 'menu':
                self['menu'].down()
            elif self.current == 'searchmenu':
                self['searchmenu'].down()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def up(self):
        try:
            if self.current == 'menu':
                self['menu'].up()
            elif self.current == 'searchmenu':
                self['searchmenu'].up()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def rightDown(self):
        try:
            if self.current == 'menu':
                self['menu'].pageDown()
            elif self.current == 'searchmenu':
                self['searchmenu'].pageDown()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def leftUp(self):
        try:
            if self.current == 'menu':
                self['menu'].pageUp()
            elif self.current == 'searchmenu':
                self['searchmenu'].pageUp()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def zapRefresh(self):
        if self.current == 'menu' and self.eventview == True and self.search == False:
            sref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
            sref = str(sref) + 'FIN'
            sref = sub(':0:0:0:.*?FIN', ':0:0:0:', sref)
            self.sref = sref
            channel = self.channel_db.lookup(sref)
            if channel == 'nope':
                self.session.open(MessageBox, 'Service not found:\nNo entry for current service reference\n%s' % str(sref), MessageBox.TYPE_INFO, close_on_any_key=True)
            else:
                if self.picon == True:
                    self.piconname = self.findPicon(sref)
                    if self.piconname is None:
                        self.piconname = 'none.png'
                self.link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
                self.refresh()
        return

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu':
            if fileExists(self.picfile):
                os.remove(self.picfile)
            if fileExists(self.localhtml):
                os.remove(self.localhtml)
            if fileExists(self.localhtml2):
                os.remove(self.localhtml2)
            if self.eventview == True:
                config.usage.on_movie_stop.value = self.movie_stop
                config.usage.on_movie_eof.value = self.movie_eof
            self.close()
        elif self.current == 'searchmenu':
            self.search = False
            self.oldsearchindex = 1
            self['searchmenu'].hide()
            self['searchlogo'].hide()
            self['searchtimer'].hide()
            self['searchtext'].hide()
            self.showProgrammPage()
            self.setTitle('')
            self.setTitle(self.titel)
        elif self.current == 'postview' and self.search == False:
            if self.tagestipp == True:
                self.close()
            else:
                self.postviewready = False
                self.setTitle('')
                self.setTitle(self.titel)
                self.showProgrammPage()
        elif self.current == 'postview' and self.search == True:
            self.postviewready = False
            self.showsearch()
            self.current = 'searchmenu'


class TVTrailerBilder(tvBaseScreen):
    def __init__(self, session, link, sparte):
        skin = """
        <screen name="TVTrailerBilder" position="{screenpos}" size="{screensize}" title=" ">
            %s%s%s%s
            <widget name="label" position="250,20" size="740,22" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            %s
        </screen>""" % ( SKHEADTOP, SKMENU, SKHEADPIC, SKHEADPLAY, SKTIME )
        tvBaseScreen.__init__(self, session, skin)
        self.sparte = sparte
        self.tventries = []
        self.tvlink = []
        self.tvtitel = []
        self.picurllist = []
        self.hideflag = True
        self.charts = False
        self.ready = False
        self.len = 0
        self.oldindex = 0
        self['pic1'] = Pixmap()
        self['pic2'] = Pixmap()
        self['pic3'] = Pixmap()
        self['pic4'] = Pixmap()
        self['pic5'] = Pixmap()
        self['pic6'] = Pixmap()
        self['play1'] = Pixmap()
        self['play2'] = Pixmap()
        self['play3'] = Pixmap()
        self['play4'] = Pixmap()
        self['play5'] = Pixmap()
        self['play6'] = Pixmap()
        self['menu'] = ItemList([])
        self['label'] = Label('OK = Zum Video')
        if sparte == '_pic':
            self['label'] = Label('OK = Zur Bildergalerie')
            self.title = 'Bildergalerien - TV Spielfilm'
        else:
            self.title = 'Trailer - Video - TV Spielfilm'
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'NumberActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'blue': self.hideScreen,
         '0': self.gotoEnd}, -1)
        self.date = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        self.nextdate = self.date + one_day
        self.weekday = makeWeekDay(self.date.weekday())
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        self.makeTVTimer = eTimer()
        if sparte == '_pic':
            self.makeTVTimer.callback.append(self.downloadFullPage(link, self.makeTVGalerie))
        else:
            self.makeTVTimer.callback.append(self.downloadFullPage(link, self.makeTVTrailer))
        self.makeTVTimer.start(500, True)

    def makestart(self):
        self['pic1'].hide()
        self['pic2'].hide()
        self['pic3'].hide()
        self['pic4'].hide()
        self['pic5'].hide()
        self['pic6'].hide()
        self['play1'].hide()
        self['play2'].hide()
        self['play3'].hide()
        self['play4'].hide()
        self['play5'].hide()
        self['play6'].hide()


    def makeTVGalerie(self, string):
            output = open(self.localhtml, 'r').read()
            self.makestart()
            startpos = output.find('<p class="headline headline--section">')
            endpos = output.find('<div id="gtm-livetv-footer"></div>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
            date = str(self.date.strftime('%d.%m.%Y'))
            self.titel = str(self.weekday) + ', ' + date
            self.setTitle(self.titel)
            bereich = sub('<a href="', '<td>LINK', bereich)
            bereich = sub('" target="', '</td>', bereich)
            bereich = sub('<img src="', '<td>PIC', bereich)
            bereich = sub('jpg">', 'jpg</td>', bereich)
            bereich = sub('png">', 'png</td>', bereich)
            bereich = sub('<span class="headline">', '<td>TITEL', bereich)
            bereich = sub('</span>', '</td>', bereich)
            a = findall('<td>(.*?)</td>', bereich)
            y = 0
            offset = 3
            for x in a:
                if y == 0:
                    res = [x]
                    if self.backcolor == True:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(923, 90), font=-1, backcolor_sel=self.back_color, text=''))
                    x = sub('LINK', '', x)
                    self.tvlink.append(x)
                if y == 1:
                    x = sub('PIC', '', x)
                    self.picurllist.append(x)
                if y == 2:
                    x = sub('TITEL', '', x)
                    res.append(MultiContentEntryText(pos=(5, 17), size=(913, 30), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    png = ICONPATH + 'icon-picHD.png'
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(843, 20), size=(60, 20), png=loadPNG(png)))
                    self.tventries.append(res)
                y += 1
                if y == offset:
                    y = 0

            self['menu'].l.setItemHeight(90)
            self['menu'].l.setList(self.tventries)
            self['menu'].moveToIndex(self.oldindex)
            if self.oldindex > 5:
                self.leftUp()
                self.rightDown()
            self.len = len(self.tventries)
            self.ready = True
            playlogo = ICONPATH + 'play.png'
            if fileExists(playlogo):
                self.showPlay1(playlogo)
                self['play1'].show()
                self.showPlay2(playlogo)
                self['play2'].show()
                self.showPlay3(playlogo)
                self['play3'].show()
                self.showPlay4(playlogo)
                self['play4'].show()
                self.showPlay5(playlogo)
                self['play5'].show()
                self.showPlay6(playlogo)
                self['play6'].show()

            self.GetPics(self.picurllist, 0)

    def makeTVTrailer(self, string):
        output = open(self.localhtml, 'r').read()
        self.makestart()
        if self.sparte == 'Kino Neustarts':
            startpos = output.find('<p class="headline headline--section">Kino Neustarts</p>')
            endpos = output.find('<div class="OUTBRAIN"')
        elif self.sparte == 'Kino Vorschau':
            startpos = output.find('<h2 class="headline headline--section">Neustarts')
            endpos = output.find('<div id="gtm-livetv-footer"></div>')
        elif self.sparte == 'Neueste Trailer':
            startpos = output.find('<p class="headline headline--section">Neueste Trailer</p>')
            endpos = output.find('<p class="headline headline--section">Kino Neustarts</p>')
        elif self.sparte == 'Kino Charts':
            self.charts = True
            startpos = output.find('<ul class="chart-content charts-list-content">')
            endpos = output.find('<div id="gtm-livetv-footer"></div>')
        elif self.sparte == 'DVD Charts':
            self.charts = True
            startpos = output.find('<ul class="chart-content charts-list-content">')
            endpos = output.find('<div id="gtm-livetv-footer"></div>')
        bereich = output[startpos:endpos]
        bereich = re.sub('<ul class="btns">.*?</ul>', '', bereich, flags=re.S)
        bereich = transHTML(bereich)
        date = str(self.date.strftime('%d.%m.%Y'))
        self.titel = str(self.sparte) + ' - ' + str(self.weekday) + ', ' + date
        self.setTitle(self.titel)
        if self.sparte == 'Neueste Trailer':
            bereich = sub('<span class="badge">', '<span class="subline ">', bereich)
            bereich = sub('<div class="badge-holder">\n\\s+</div>', '<span class="subline ">Trailer</span>', bereich)
            bereich = sub('<a href="', '<td>LINK', bereich)
            bereich = sub('" target="', '</td>', bereich)
            bereich = sub('<img src="', '<td>PIC', bereich)
            bereich = sub('jpg">', 'jpg</td>', bereich)
            bereich = sub('png">', 'png</td>', bereich)
            bereich = sub('<span class="headline">', '<td>TITEL', bereich)
            bereich = sub('<span class="subline .*?">', '<td>TEXT', bereich)
            bereich = sub('</span>', '</td>', bereich)
            a = findall('<td>(.*?)</td>', bereich)
            y = 0
            offset = 4
            for x in a:
                if y == 0:
                    res = [x]
                    if self.backcolor == True:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(923, 90), font=-1, backcolor_sel=self.back_color, text=''))
                    x = sub('LINK', '', x)
                    self.tvlink.append(x)
                if y == 1:
                    x = sub('PIC', '', x)
                    self.picurllist.append(x)
                if y == 2:
                    x = sub('TEXT', '', x)
                    res.append(MultiContentEntryText(pos=(5, 48), size=(913, 30), font=-1, color=10857646, color_sel=10857646, flags=RT_HALIGN_LEFT, text=x))
                if y == 3:
                    x = sub('TITEL', '', x)
                    titel = search('"(.*?)"', x)
                    if titel is not None:
                        self.tvtitel.append(titel.group(1))
                    else:
                        self.tvtitel.append(x)
                    res.append(MultiContentEntryText(pos=(5, 17), size=(913, 30), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    png = ICONPATH + 'cin.png'
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(843, 20), size=(60, 29), png=loadPNG(png)))
                    self.tventries.append(res)
                y += 1
                if y == offset:
                    y = 0

            self['menu'].l.setItemHeight(90)
            self['menu'].l.setList(self.tventries)
            self['menu'].moveToIndex(self.oldindex)
        elif self.charts == False:
            if self.sparte == 'Kino Vorschau':
                bereich = sub('<a href="https://www.cinema.de.*?</a>', '', bereich)
            bereich = sub('<a href="', '<td>LINK', bereich)
            bereich = sub('" target="', '</td>', bereich)
            bereich = sub('<img src="', '<td>PIC', bereich)
            bereich = sub('jpg">', 'jpg</td>', bereich)
            bereich = sub('png">', 'png</td>', bereich)
            bereich = sub('<span class="headline">', '<td>TITEL', bereich)
            bereich = sub('<span class="subline .*?">', '<td>TEXT', bereich)
            bereich = sub('</span>', '</td>', bereich)
            a = findall('<td>(.*?)</td>', bereich)
            y = 0
            offset = 4
            for x in a:
                if y == 0:
                    res = [x]
                    if self.backcolor == True:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(923, 90), font=-1, backcolor_sel=self.back_color, text=''))
                    x = sub('LINK', '', x)
                    self.tvlink.append(x)
                if y == 1:
                    x = sub('PIC', '', x)
                    self.picurllist.append(x)
                if y == 2:
                    x = sub('TITEL', '', x)
                    titel = search('"(.*?)"', x)
                    if titel is not None:
                        self.tvtitel.append(titel.group(1))
                    else:
                        self.tvtitel.append(x)
                    res.append(MultiContentEntryText(pos=(5, 17), size=(913, 30), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    png = ICONPATH + 'cin.png'
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(843, 20), size=(60, 29), png=loadPNG(png)))
                if y == 3:
                    x = sub('TEXT', '', x)
                    res.append(MultiContentEntryText(pos=(5, 48), size=(913, 30), font=-1, color=10857646, color_sel=10857646, flags=RT_HALIGN_LEFT, text=x))
                    self.tventries.append(res)
                y += 1
                if y == offset:
                    y = 0

            self['menu'].l.setItemHeight(90)
            self['menu'].l.setList(self.tventries)
            self['menu'].moveToIndex(self.oldindex)
        elif self.charts == True:
            bereich = sub('<li class="active">\n\\s+<a href="', '<td>LINK', bereich)
            bereich = sub('<li class="inactive ">\n\\s+<a href="', '<td>LINK', bereich)
            bereich = sub('" target="', '</td>', bereich)
            bereich = sub('<p class="title">', '<td>TITEL', bereich)
            bereich = sub('</p>', '</td>', bereich)
            bereich = sub('<img src="', '<td>PIC', bereich)
            bereich = sub('jpg">', 'jpg</td>', bereich)
            bereich = sub('png">', 'png</td>', bereich)
            bereich = sub('<span class="country">', '<td>TEXT', bereich)
            bereich = sub('</span>', '</td>', bereich)
            a = findall('<td>(.*?)</td>', bereich)
            y = 0
            offset = 4
            for x in a:
                if y == 0:
                    res = [x]
                    if self.backcolor == True:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(923, 90), font=-1, backcolor_sel=self.back_color, text=''))
                    x = sub('LINK', '', x)
                    self.tvlink.append(x)
                if y == 1:
                    x = sub('TITEL', '', x)
                    titel = search('"(.*?)"', x)
                    if titel is not None:
                        self.tvtitel.append(titel.group(1))
                    else:
                        self.tvtitel.append(x)
                    res.append(MultiContentEntryText(pos=(5, 2), size=(913, 30), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    png = ICONPATH + 'cin.png'
                    if fileExists(png):
                        res.append(MultiContentEntryPixmapAlphaTest(pos=(843, 20), size=(60, 29), png=loadPNG(png)))
                if y == 2:
                    x = sub('TEXT', '', x)
                    res.append(MultiContentEntryText(pos=(5, 34), size=(833, 56), font=0, color=10857646, color_sel=10857646, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                if y == 3:
                    x = sub('PIC', '', x)
                    self.picurllist.append(x)
                    self.tventries.append(res)
                y += 1
                if y == offset:
                    y = 0

            self['menu'].l.setItemHeight(90)
            self['menu'].l.setList(self.tventries)
            self['menu'].moveToIndex(self.oldindex)
        if self.oldindex > 5:
            self.leftUp()
            self.rightDown()
        self.len = len(self.tventries)
        self.ready = True
        playlogo = ICONPATH + 'play.png'
        if fileExists(playlogo):
            self.showPlay1(playlogo)
            self['play1'].show()
            self.showPlay2(playlogo)
            self['play2'].show()
            self.showPlay3(playlogo)
            self['play3'].show()
            self.showPlay4(playlogo)
            self['play4'].show()
            self.showPlay5(playlogo)
            self['play5'].show()
            self.showPlay6(playlogo)
            self['play6'].show()

            self.GetPics(self.picurllist, 0)

        return

    def ok(self):
        if self.hideflag == False:
            return
        if self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                self.link = self.tvlink[c]
                if sparte == '_pic':
                    self.session.openWithCallback(self.picReturn, TVNewsPicShow, self.link)
                    return

                self.titel = self.tvtitel[c]
                self.download(self.link, self.playTrailer)
            except IndexError:
                pass

    def playTrailer(self, output):
        if search('rl: .https://video.tvspielfilm.de/.*?mp4', output) is not None:
            trailer = search('rl: .https://video.tvspielfilm.de/(.*?).mp4', output)
            self.trailer = 'https://video.tvspielfilm.de/' + trailer.group(1) + '.mp4'
            try:
                sref = eServiceReference(4097, 0, self.trailer)
                sref.setName(self.titel)
                self.session.open(MoviePlayer, sref)
            except IndexError:
                pass

        elif search('rl: .https://video.tvspielfilm.de/.*?flv', output) is not None:
            self.session.open(MessageBox, 'Der Trailer kann nicht abgespielt werden:\nnicht unterstuetzter Video-Codec: On2 VP6/Flash', MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            self.session.open(MessageBox, '\nKein Trailer vorhanden', MessageBox.TYPE_INFO, close_on_any_key=True)
        return

    def gotoEnd(self):
        if self.ready == True:
            end = self.len - 1
            self['menu'].moveToIndex(end)
            if end > 5:
                self.leftUp()
                self.rightDown()


    def showPlay1(self, playlogo):
        currPic = loadPic(playlogo, 109, 58, 3, 0, 0, 0)
        if currPic != None:
            self['play1'].instance.setPixmap(currPic)
        return

    def showPlay2(self, playlogo):
        currPic = loadPic(playlogo, 109, 58, 3, 0, 0, 0)
        if currPic != None:
            self['play2'].instance.setPixmap(currPic)
        return

    def showPlay3(self, playlogo):
        currPic = loadPic(playlogo, 109, 58, 3, 0, 0, 0)
        if currPic != None:
            self['play3'].instance.setPixmap(currPic)
        return

    def showPlay4(self, playlogo):
        currPic = loadPic(playlogo, 109, 58, 3, 0, 0, 0)
        if currPic != None:
            self['play4'].instance.setPixmap(currPic)
        return

    def showPlay5(self, playlogo):
        currPic = loadPic(playlogo, 109, 58, 3, 0, 0, 0)
        if currPic != None:
            self['play5'].instance.setPixmap(currPic)
        return

    def showPlay6(self, playlogo):
        currPic = loadPic(playlogo, 109, 58, 3, 0, 0, 0)
        if currPic != None:
            self['play6'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def down(self):
        try:
            c = self['menu'].getSelectedIndex()
        except IndexError:
            return

        self['menu'].down()
        if c + 1 == len(self.tventries):
            self.GetPics(self.picurllist, 0, True, True)

        elif c % 6 == 5:
            self.GetPics(self.picurllist, c + 1, True, True)

    def up(self):
        try:
            c = self['menu'].getSelectedIndex()
        except IndexError:
            return

        self['menu'].up()
        if c == 0:
            l = len(self.tventries)
            d = l % 6
            if d == 0:
                d = 6
            self.GetPics(self.picurllist, l - d, True, True)

        elif c % 6 == 0:
            self.GetPics(self.picurllist, c - 6, True, True)

    def rightDown(self):
        try:
            c = self['menu'].getSelectedIndex()
        except IndexError:
            return

        self['menu'].pageDown()
        l = len(self.tventries)
        d = c % 6
        e = l % 6
        if e == 0:
            e = 6
        if c + e >= l:
            pass
        elif d == 0:
            self.GetPics(self.picurllist, c + 6, True, True)

        elif d == 1:
            self.GetPics(self.picurllist, c + 5, True, True)

        elif d == 2:
            self.GetPics(self.picurllist, c + 4, True, True)

        elif d == 3:
            self.GetPics(self.picurllist, c + 3, True, True)

        elif d == 4:
            self.GetPics(self.picurllist, c + 2, True, True)

        elif d == 5:
            self.GetPics(self.picurllist, c + 1, True, True)

    def leftUp(self):
        try:
            c = self['menu'].getSelectedIndex()
        except IndexError:
            return

        self['menu'].pageUp()
        d = c % 6
        if c < 6:
            pass
        elif d == 0:
            self.GetPics(self.picurllist, c - 6, False)

        elif d == 1:
            self.GetPics(self.picurllist, c - 7, False)

        elif d == 2:
            self.GetPics(self.picurllist, c - 8, False)

        elif d == 3:
            self.GetPics(self.picurllist, c - 9, False)

        elif d == 4:
            self.GetPics(self.picurllist, c - 10, False)

        elif d == 5:
            self.GetPics(self.picurllist, c - 11, False)

        self['pic1'].show()
        self['pic2'].show()
        self['pic3'].show()
        self['pic4'].show()
        self['pic5'].show()
        self['pic6'].show()
        self['play1'].show()
        self['play2'].show()
        self['play3'].show()
        self['play4'].show()
        self['play5'].show()
        self['play6'].show()

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class TVNews(tvBaseScreen):
    skin = '<screen name="TVNews" position="center,center" size="{screensize}" title="TV-News - TV Spielfilm"> ' + SKHEADTOP + """
            <widget name="menu" position="10,70" size="475,540" scrollbarMode="showAlways" zPosition="1" />
            <widget name="slider_menu" position="469,70" size="22,540" pixmap="{picpath}slider/slider_540.png" alphatest="blend" zPosition="2" />
            <widget name="picture" position="600,70" size="525,350" alphatest="blend" zPosition="1" />
            <widget name="picturetext" position="490,420" size="745,60" font="Regular;20" valign="center" halign="center" zPosition="1" />
            <widget name="picpost" position="_375,70" size="490,245" alphatest="blend" zPosition="1" />
            <widget name="cinlogo" position="_325,70" size="60,29" pixmap="{picpath}icons/cin.png" alphatest="blend" zPosition="1" />
            <widget name="playlogo" position="_565,163" size="109,58" pixmap="{picpath}icons/playHD.png" alphatest="blend" zPosition="2" />
            <widget name="textpage" position="10,325" size="_1220,{slider}" font="Regular;20" halign="left" zPosition="0" />
            <widget name="slider_textpage" position="_1214,325" size="22,{slider}" pixmap="{picpath}slider/slider_{slider}.png" alphatest="blend" zPosition="1" />
            <widget name="label" position="364,20" size="512,20" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />""" + SKTIME + """
            <widget name="statuslabel" position="250,610" size="740,20" font="Regular;20" foregroundColor="#858A95" halign="center" zPosition="2" />
        </screen>"""
    def __init__(self, session, link):
        tvBaseScreen.__init__(self, session, TVNews.skin)
        self.current = 'menu'
        self.menulist = []
        self.menulink = []
        self.picurllist = []
        self.pictextlist = []
        self.postlink = link
        self.link = link
        self.trailerurl = ''
        self.titel = ''
        self.hideflag = True
        self.mehrbilder = False
        self.trailer = False
        self.ready = False
        self.postviewready = False
        self['picture'] = Pixmap()
        self['picpost'] = Pixmap()
        self['cinlogo'] = Pixmap()
        self['cinlogo'].hide()
        self['playlogo'] = Pixmap()
        self['playlogo'].hide()
        self['statuslabel'] = Label('')
        self['statuslabel'].hide()
        self['picturetext'] = Label('')
        self['textpage'] = ScrollLabel('')
        self['slider_menu'] = Pixmap()
        self['slider_menu'].hide()
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['menu'] = ItemList([])
        self['label'] = Label('')
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'blue': self.hideScreen}, -1)
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        self.getInfoTimer = eTimer()
        self.getInfoTimer.callback.append(self.downloadFullPage(link, self.makeTVNews))
        self.getInfoTimer.start(500, True)

    def makeTVNews(self, string):
        output = open(self.localhtml, 'r').read()
        titel = search('<title>(.*?)</title>', output)
        self.titel = titel.group(1).replace('&amp;', '&')
        self.setTitle(self.titel)
        startpos = output.find('<div class="content-area">')
        endpos = output.find('<div class="widget-box tvsearch">')
        bereich = output[startpos:endpos]
        bereich = re.sub('<ul class=".*?</ul>', '', bereich, flags=re.S)
        bereich = re.sub('<script.*?</script>', '', bereich, flags=re.S)
        bereich = re.sub('<section id="content">.*?</section>', '', bereich, flags=re.S)
        bereich = sub('<a href="https://tvspielfilm-abo.de.*?\n', '', bereich)
        bereich = sub('<a href="https://www.tvspielfilm.de/news".*?\n', '', bereich)
        bereich = transHTML(bereich)
        link = re.findall('<a href="(.*?)" target="_self"', bereich)
        picurl = re.findall('<img src="(.*?)"', bereich)
        picurltvsp = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
        name = re.findall('<span class="headline">(.*?)</span>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                self.picurllist.append(picurl[i])
            except IndexError:
                self.picurllist.append(picurltvsp)

            try:
                self.pictextlist.append(name[i])
            except IndexError:
                self.pictextlist.append(' ')

            try:
                res = ['']
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(475, 30), font=-1, backcolor_sel=self.back_color, text=''))
                res.append(MultiContentEntryText(pos=(0, 1), size=(475, 28), font=-1, flags=RT_HALIGN_LEFT, text=name[i]))
                self.menulist.append(res)
                self.menulink.append(link[i])
            except IndexError:
                pass

        self['menu'].l.setItemHeight(30)
        self['menu'].l.setList(self.menulist)
        self['slider_menu'].show()
        try:
            self.download(picurl[0], self.getPic)
        except IndexError:
            self.download(picurltvsp, self.getPic)

        try:
            self['picturetext'].setText(name[0])
        except IndexError:
            self['picturetext'].setText('')

        self.ready = True

    def makePostviewPageNews(self, string):
        print("DEBUG makePostviewPageNews")
        output = open(self.localhtml2, 'r').read()
        output = six.ensure_str(output)
        self['picture'].hide()
        self['picturetext'].hide()
        self['statuslabel'].hide()
        self['menu'].hide()
        self['slider_menu'].hide()
        if search('<title>', output) is not None:
            titel = search('<title>(.*?)</title>', output)
            titel = titel.group(1).replace('&amp;', '&')
            self.title = sub(' - TV Spielfilm', '', titel)
            self.setTitle(self.title)
        output = sub('</dl>.\n\\s+</div>.\n\\s+</section>', '</cast>', output)
        startpos = output.find('<div class="content-area">')
        endpos = output.find('>Weitere Bildergalerien<')
        if endpos == -1:
            endpos = output.find('</cast>')
            if endpos == -1:
                endpos = output.find('<h2 class="broadcast-info">')
                if endpos == -1:
                    endpos = output.find('<div class="OUTBRAIN"')
                    if endpos == -1:
                        endpos = output.find('</footer>')
        bereich = output[startpos:endpos]
        bereich = cleanHTML(bereich)
        if search('rl: .https://video.tvspielfilm.de/.*?mp4', output) is not None:
            trailerurl = search('rl: .https://video.tvspielfilm.de/(.*?).mp4', output)
            self.trailerurl = 'https://video.tvspielfilm.de/' + trailerurl.group(1) + '.mp4'
            self.trailer = True
        else:
            self.trailer = False
        bereich = sub('" alt=".*?" width="', '" width="', bereich)
        picurl = search('<img src="(.*?)" width="', bereich)
        if picurl is not None:
            self.download(picurl.group(1), self.getPicPost)
            self['picpost'].show()
        else:
            picurl = search('<meta property="og:image" content="(.*?)"', output)
            if picurl is not None:
                self.download(picurl.group(1), self.getPicPost)
                self['picpost'].show()
            else:
                picurl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
                self.download(picurl, self.getPicPost)
                self['picpost'].show()
        if search('<div class="film-gallery">', output) is not None:
            self.mehrbilder = True
            if self.trailer == True:
                self['label'].setText('OK = Zum Video')
            else:
                self['label'].setText('OK = Fotostrecke')
        else:
            self.mehrbilder = False
            if self.trailer == True:
                self['label'].setText('OK = Zum Video')
            else:
                self['label'].setText('OK = Vollbild')
                
        text = parsedetail(bereich)

        fill = self.getFill('TV Spielfilm Online')
        self.POSTtext = text + fill
        self['textpage'].setText(self.POSTtext)
        self['textpage'].show()
        self['slider_textpage'].show()
        self.showEPG = False
        self.postviewready = True
        return

    def ok(self):
        if self.hideflag == False:
            return
        else:
            if self.current == 'menu' and self.ready == True:
                self.selectPage('ok')
            elif self.current == 'postview' and self.postviewready == True:
                if self.trailer == True:
                    sref = eServiceReference(4097, 0, self.trailerurl)
                    sref.setName(self.title)
                    self.session.open(MoviePlayer, sref)
                elif self.mehrbilder == True:
                    if search('/playboy/', self.postlink) is None:
                        self.session.openWithCallback(self.picReturn, TVNewsPicShow, self.postlink)
                    else:
                        self.session.openWithCallback(self.picReturn, PlayboyPicShow, self.postlink)
                else:
                    self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)
            return

    def selectPage(self, action):
        try:
            c = self['menu'].getSelectedIndex()
        except IndexError:
            pass

        try:
            self.postlink = self.menulink[c]
            if action == 'ok':
                if search('/playboy/', self.postlink) is not None:
                    self.session.openWithCallback(self.picReturn, PlayboyPicShow, self.postlink)
                elif search('blog.tvspielfilm.de', self.postlink) is not None:
                    self.session.openWithCallback(self.picReturn, TVBlog, self.postlink, True)
                elif search('www.tvspielfilm.de', self.postlink) is not None:
                    self.current = 'postview'
                    self.downloadPostPage(self.postlink, self.makePostviewPageNews)
                else:
                    self['statuslabel'].setText('Kein Artikel verfuegbar')
                    self['statuslabel'].show()
        except IndexError:
            pass

        return

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.picfile)

    def showPic(self, picture):
        currPic = loadPic(picture, 525, 350, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        currPic = loadPic(picpost, 490, 245, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
            if self.trailer == True:
                self['cinlogo'].show()
                self['playlogo'].show()
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadPostPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        try:
            error = output.getErrorMessage()
            self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
        except AttributeError:
            self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

        self['statuslabel'].setText('Download Fehler')
        self['statuslabel'].show()

    def showTVNews(self):
        self.current = 'menu'
        self['menu'].show()
        self['slider_menu'].show()
        self['label'].setText('OK = Zum Artikel')
        self['picture'].show()
        self['picturetext'].show()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['cinlogo'].hide()
        self['playlogo'].hide()
        self['statuslabel'].hide()

    def down(self):
        try:
            if self.current == 'menu':
                self['menu'].down()
                c = self['menu'].getSelectedIndex()
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                pictext = self.pictextlist[c]
                self['picturetext'].setText(pictext)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def up(self):
        try:
            if self.current == 'menu':
                self['menu'].up()
                c = self['menu'].getSelectedIndex()
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                pictext = self.pictextlist[c]
                self['picturetext'].setText(pictext)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def rightDown(self):
        try:
            if self.current == 'menu':
                self['menu'].pageDown()
                c = self['menu'].getSelectedIndex()
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                pictext = self.pictextlist[c]
                self['picturetext'].setText(pictext)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def leftUp(self):
        try:
            if self.current == 'menu':
                self['menu'].pageUp()
                c = self['menu'].getSelectedIndex()
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                pictext = self.pictextlist[c]
                self['picturetext'].setText(pictext)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu':
            self.close()
        else:
            self.postviewready = False
            self.setTitle('')
            self.setTitle(self.titel)
            self.showTVNews()

class TVBlog(tvBaseScreen):
    skin = """
        <screen name="TVBlog" position="center,center" size="{screensize}" title="TV Spielfilm Blog">
            <eLabel position="0,0" size="{headw},60" backgroundColor="#FFFFFF" />
            <ePixmap position="0,0" size="{headw},60" pixmap="{picpath}blogHD.png" alphatest="blend" zPosition="1" />
            <widget name="menu" position="950,150" size="250,250" scrollbarMode="showNever" zPosition="1" />
            <widget name="meta" position="10,70" size="300,55" font="Regular;18" foregroundColor="#F2A5BC" halign="left" zPosition="1" />
            <widget name="item" position="10,445" size="120,25" font="Regular;18" foregroundColor="#F2A5BC" halign="left" zPosition="1" />
            <widget name="picture" position="320,70" size="600,400" alphatest="blend" zPosition="1" />
            <widget name="topictext" position="10,475" size="1220,25" font="Regular;20" halign="left" zPosition="1" />
            <widget name="previewtext" position="10,510" size="1220,130" font="Regular;20" halign="left" zPosition="1" />
            <widget name="picpost" position="375,70" size="490,245" alphatest="blend" zPosition="1" />
            <widget name="playlogo" position="565,163" size="109,58" pixmap="{picpath}icons/playHD.png" alphatest="blend" zPosition="2" />
            <widget name="textpage" position="10,325" size="1220,{slider}" font="Regular;20" halign="left" zPosition="0" />
            <widget name="slider_textpage" position="1214,325" size="22,{slider}" pixmap="{picpath}slider/slider_{slider}.png" alphatest="blend" zPosition="1" />
            <widget name="label" position="364,10" size="512,40" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" valign="center" transparent="1" zPosition="2" />""" + SKTIME + """
            <widget name="statuslabel" position="250,610" size="740,20" font="Regular;18" foregroundColor="#858A95" halign="center" zPosition="2" />
        </screen>"""
    def __init__(self, session, link, post):
        tvBaseScreen.__init__(self, session, TVBlog.skin)
        self.baseurl = 'https://blog.tvspielfilm.de'
        self.current = 'menu'
        self.menulist = []
        self.menulink = []
        self.picurllist = []
        self.toptextlist = []
        self.textlist = []
        self.metalist = []
        self.post = post
        self.postlink = link
        self.link = link
        self.trailerurl = ''
        self.titel = ''
        self.hideflag = True
        self.trailer = False
        self.ready = False
        self.postviewready = False
        self.count = 1
        self.max = 1
        self['picture'] = Pixmap()
        self['picpost'] = Pixmap()
        self['playlogo'] = Pixmap()
        self['playlogo'].hide()
        self['statuslabel'] = Label('')
        self['statuslabel'].hide()
        self['item'] = Label('')
        self['meta'] = Label('')
        self['topictext'] = Label('')
        self['previewtext'] = Label('')
        self['textpage'] = ScrollLabel('')
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['menu'] = MenuList([])
        self['menu'].hide()
        self['label'] = Label('OK = Post, Up/Down = Blog\nBouquet = +- Seite')
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.nextPage,
         'prevBouquet': self.prevPage,
         'blue': self.hideScreen}, -1)
        self.getInfoTimer = eTimer()
        if self.post == False:
            self.getInfoTimer.callback.append(self.downloadFullPage(link, self.makeTVBlog))
        else:
            self.current = 'postview'
            self.getInfoTimer.callback.append(self.downloadPostPage(link, self.makePostviewPageBlog))
        self.getInfoTimer.start(500, True)

    def makeTVBlog(self, string):
        output = open(self.localhtml, 'r').read()
        titel = search('<title>(.*?)</title>', output)
        self.titel = titel.group(1).replace('TV Spielfilm Blog | ', '')
        self.setTitle(self.titel)
        startpos = output.find('<div id="content">')
        endpos = output.find('<!-- end #content-->')
        bereich = output[startpos:endpos]
        bereich = sub('<iframe width="[0-9]+" height="[0-9]+" src="//www.youtube.com/embed/', '<img width="785" height="510" src="https://img.youtube.com/vi/', bereich)
        bereich = sub('" frameborder="0"', '/0.jpg"', bereich)
        bereich = sub('<img class="replacement" src="">', '<img width="630" height="404" src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/630px-TV-Spielfilm-Logo.svg.png">', bereich)
        bereich = sub('<i class="fa fa-heart-o">', 'Likes: ', bereich)
        bereich = sub('&bull;', '\xb7', bereich)
        bereich = sub('<a href=".*?>', '', bereich)
        bereich = sub('<a title=".*?>', '', bereich)
        bereich = sub('<span class=".*?>', '', bereich)
        bereich = sub('</span>', '', bereich)
        bereich = sub('<strong>', '', bereich)
        bereich = sub('</strong', '', bereich)
        bereich = sub('</a>', ' ', bereich)
        bereich = sub('<i>', '', bereich)
        bereich = sub('</i>', '', bereich)
        bereich = sub('<b>', '', bereich)
        bereich = sub('</b>', '', bereich)
        bereich = sub('<del>', '', bereich)
        bereich = sub('</del>', '', bereich)
        bereich = sub('<br />\n', '', bereich)
        bereich = sub('<div><em>', '<p>', bereich)
        bereich = sub('</em></div>', '</p>', bereich)
        bereich = sub('<em>', '', bereich)
        bereich = sub('</em>', '', bereich)
        bereich = sub('</p></blockquote>\n<p>', '', bereich)
        bereich = transHTML(bereich)
        picurl = re.findall('<img width="[0-9]+" height="[0-9]+" src="(.*?)"', bereich)
        picurlblog = 'https://blog.tvspielfilm.de/wp-content/themes/tvspielfilm/images/header.png'
        metatext = re.findall('<p class="meta">(.*?)</p>', bereich, flags=re.S)
        toptext = re.findall('<h2 class="upperfont">(.*?)</h2>', bereich)
        text = re.findall('<div class="entry">.*?<p>(.*?)</p>', bereich, flags=re.S)
        lnk = re.findall('<a class="mainbutton" href="(.*?)"', bereich)
        idx = 0
        for x in toptext:
            idx += 1

        for i in range(idx):
            try:
                self.toptextlist.append(toptext[i])
            except IndexError:
                self.toptextlist.append(' ')

            try:
                self.textlist.append(text[i])
            except IndexError:
                self.textlist.append(' ')

            try:
                self.picurllist.append(picurl[i])
            except IndexError:
                self.picurllist.append(picurlblog)

            try:
                meta = sub('\n', '', metatext[i])
                meta = sub('[ ]+', ' ', meta)
                meta = sub('\t', '', meta)
                self.metalist.append(meta)
            except IndexError:
                self.metalist.append(' ')

            self.menulist.append(toptext[i])
            self.menulink.append(lnk[i])

        self['menu'].l.setList(self.menulist)
        self['menu'].moveToIndex(0)
        self.max = len(self.menulist)
        item = 'Post 1/%s' % str(self.max)
        self['item'].setText(item)
        try:
            self.download(picurl[0], self.getPic)
        except IndexError:
            self.download(picurlblog, self.getPic)

        try:
            meta = sub('\n', '', metatext[0])
            meta = sub('[ ]+', ' ', meta)
            meta = sub('\t', '', meta)
            self['meta'].setText(meta)
        except IndexError:
            self['meta'].setText('')

        try:
            self['topictext'].setText(toptext[0])
        except IndexError:
            self['topictext'].setText('')

        try:
            self['previewtext'].setText(text[0])
        except IndexError:
            self['previewtext'].setText('')

        if search('<a class="next page-numbers"', output) is not None:
            self['label'].setText('OK = Post, Up/Down = Blog\nBouquet = +- Seite')
        else:
            self['label'].setText('OK = Post, Up/Down = Blog\nLetzte Blog Seite')
        self.ready = True
        return

    def makePostviewPageBlog(self, string):
        print("DEBUG makePostviewPageBlog")
        output = open(self.localhtml2, 'r').read()
        output = six.ensure_str(output)
        self['item'].hide()
        self['picture'].hide()
        self['topictext'].hide()
        self['previewtext'].hide()
        self['statuslabel'].hide()
        if search('<title>', output) is not None:
            titel = search('<title>(.*?)</title>', output)
            self.title = transHTML(titel.group(1)).replace(' | TV Spielfilm Blog | TV SPIELFILM bloggt aus Hollywood, aus dem Kino und von der Wohnzimmercouch', '')
            self.setTitle(self.title)
        startpos = output.find('<div id="content">')
        endpos = output.find('<!-- #homecontent -->')
        bereich = output[startpos:endpos]
        if search('<source type="video/mp4" src=".*?mp4"', bereich) is not None:
            trailerurl = search('<source type="video/mp4" src="(.*?)"', bereich)
            self.trailerurl = trailerurl.group(1)
            self['label'].setText('OK = Zum Video')
            self.trailer = True
        elif search('src="//www.youtube.com/embed/', bereich) is not None:
            trailerurl = search('src="//www.youtube.com/embed/(.*?)"', bereich)
            self.trailerurl = trailerurl.group(1)
            self['label'].setText('OK = Zum Video')
            self.trailer = True
        else:
            self['label'].setText('OK = Vollbild')
            self.trailer = False
        bereich = sub('<iframe width="[0-9]+" height="[0-9]+" src="//www.youtube.com/embed/', '<img width="785" height="510" src="https://img.youtube.com/vi/', bereich)
        bereich = sub('" frameborder="0"', '/0.jpg"', bereich)
        picurl = search('<img width="[0-9]+" height="[0-9]+" src="(.*?)"', bereich)
        if picurl is not None:
            self.download(picurl.group(1), self.getPicPost)
            self['picpost'].show()
        else:
            picurl = 'https://blog.tvspielfilm.de/wp-content/themes/tvspielfilm/images/header.png'
            self.download(picurl, self.getPicPost)
            self['picpost'].show()
        meta = search('<p class="meta">(.*?)</p>', bereich, flags=re.S)
        if meta is not None:
            meta = sub('\n', '', meta.group(1))
            meta = sub('[ ]+', ' ', meta)
            meta = sub('\t', '', meta)
            meta = sub('[ ]+von', 'Von', meta)
            meta = sub('&bull;', '\xb7', meta)
            meta = sub('<i class="fa fa-heart-o">', 'Likes: ', meta)
            meta = '<p>' + meta + '</p>'
        bereich = sub('<div>', '<p>', bereich)
        bereich = sub('</div>', '</p>', bereich)
        bereich = sub('<p><b>[^A-Za-z0-9]+</b></p>', '', bereich)
        bereich = sub('<h1 class="heading">', '<p>', bereich)
        bereich = sub('<h3 id="comments-title">', '<p>', bereich)
        bereich = sub('</h[0-9]+>', '</p>', bereich)
        bereich = sub('<cite class="fn">', '<p>', bereich)
        bereich = sub('</cite> <span class="says">', ' ', bereich)
        bereich = sub('<span.*?></span>', '', bereich)
        bereich = sub('</span>', '</p>', bereich)
        bereich = sub('class="wp-smiley" />', '>:-)', bereich)
        bereich = sub('<div class="comment-meta commentmetadata">', '<p>', bereich)
        bereich = transHTML(bereich)
        text = meta
        a = findall('<p>(.*?)</p>', bereich.replace('\r', '').replace('\n', ''))
        for x in a:
            if x != '':
                text = text + x + '\n\n'

        text = sub('<[^>]*>', '', text)
        text = sub('</p<<p<', '\n\n', text)
        text = sub('\n\\s+\n*', '\n\n', text)
        fill = self.getFill('TV Spielfilm Blog')
        text = text + fill
        self['textpage'].setText(text)
        self['textpage'].show()
        self['slider_textpage'].show()
        self.postviewready = True
        return

    def ok(self):
        if self.hideflag == False:
            return
        else:
            if self.current == 'menu' and self.ready == True:
                self.selectPage('ok')
            elif self.current == 'postview' and self.postviewready == True:
                if self.trailer == True:
                    if search('blog.tvspielfilm.de', self.trailerurl) is not None:
                        sref = eServiceReference(4097, 0, self.trailerurl)
                        sref.setName(self.title)
                        self.session.open(MoviePlayer, sref)
                    else:
                        video = self.getYouTubeURL(self.trailerurl)
                        if video is not None:
                            sref = eServiceReference(4097, 0, video)
                            sref.setName(self.title)
                            self.session.open(MoviePlayer, sref)
                        else:
                            self.session.open(MessageBox, '\nYouTube Video nicht gefunden', MessageBox.TYPE_ERROR)
                else:
                    self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)
            return

    def selectPage(self, action):
        try:
            c = self['menu'].getSelectedIndex()
        except IndexError:
            pass

        try:
            self.postlink = self.menulink[c]
            if action == 'ok':
                if search('blog.tvspielfilm.de', self.postlink) is not None:
                    self.current = 'postview'
                    self.downloadPostPage(self.postlink, self.makePostviewPageBlog)
                else:
                    self['statuslabel'].setText('Kein Artikel verfuegbar')
                    self['statuslabel'].show()
        except IndexError:
            pass

        return

    def nextPage(self):
        if self.ready == True:
            self.ready = False
            self.count += 1
            self.link = sub('/page/[0-9]+', '/page/' + str(self.count), self.link)
            self.menulist = []
            self.menulink = []
            self.picurllist = []
            self.metalist = []
            self.toptextlist = []
            self.textlist = []
            self['statuslabel'].hide()
            self.getInfoTimer.callback.append(self.downloadFullPage(self.link, self.makeTVBlog))

    def prevPage(self):
        if self.ready == True:
            self.ready = False
            self.count -= 1
            self.link = sub('/page/[0-9]+', '/page/' + str(self.count), self.link)
            self.menulist = []
            self.menulink = []
            self.picurllist = []
            self.metalist = []
            self.toptextlist = []
            self.textlist = []
            self['statuslabel'].hide()
            self.getInfoTimer.callback.append(self.downloadFullPage(self.link, self.makeTVBlog))

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.picfile)

    def showPic(self, picture):
        currPic = loadPic(picture, 600, 400, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        currPic = loadPic(picpost, 490, 245, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
            if self.trailer == True:
                self['playlogo'].show()
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadPostPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self['statuslabel'].setText('Download Fehler')
        self['statuslabel'].show()
        self.ready = True

    def showTVBlog(self):
        self.current = 'menu'
        self['label'].setText('OK = Post, Up/Down = Blog\nBouquet = +- Seite')
        self['item'].show()
        self['picture'].show()
        self['topictext'].show()
        self['previewtext'].show()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['playlogo'].hide()
        self['statuslabel'].hide()

    def down(self):
        try:
            if self.current == 'menu':
                self['menu'].down()
                c = self['menu'].getSelectedIndex()
                item = 'Post %s/%s' % (str(c + 1), str(self.max))
                self['item'].setText(item)
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                meta = self.metalist[c]
                self['meta'].setText(meta)
                toptext = self.toptextlist[c]
                self['topictext'].setText(toptext)
                text = self.textlist[c]
                self['previewtext'].setText(text)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def up(self):
        try:
            if self.current == 'menu':
                self['menu'].up()
                c = self['menu'].getSelectedIndex()
                item = 'Post %s/%s' % (str(c + 1), str(self.max))
                self['item'].setText(item)
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                meta = self.metalist[c]
                self['meta'].setText(meta)
                toptext = self.toptextlist[c]
                self['topictext'].setText(toptext)
                text = self.textlist[c]
                self['previewtext'].setText(text)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def rightDown(self):
        try:
            if self.current == 'menu':
                self['menu'].pageDown()
                c = self['menu'].getSelectedIndex()
                item = 'Post %s/%s' % (str(c + 1), str(self.max))
                self['item'].setText(item)
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                meta = self.metalist[c]
                self['meta'].setText(meta)
                toptext = self.toptextlist[c]
                self['topictext'].setText(toptext)
                text = self.textlist[c]
                self['previewtext'].setText(text)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def leftUp(self):
        try:
            if self.current == 'menu':
                self['menu'].pageUp()
                c = self['menu'].getSelectedIndex()
                item = 'Post %s/%s' % (str(c + 1), str(self.max))
                self['item'].setText(item)
                picurl = self.picurllist[c]
                self.download(picurl, self.getPic)
                meta = self.metalist[c]
                self['meta'].setText(meta)
                toptext = self.toptextlist[c]
                self['topictext'].setText(toptext)
                text = self.textlist[c]
                self['previewtext'].setText(text)
                self['statuslabel'].hide()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def getYouTubeURL(self, trailer_id):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        VIDEO_FMT_PRIORITY_MAP = {'38': 3,
         '37': 1,
         '22': 2,
         '35': 5,
         '18': 4,
         '34': 6}
        trailer_url = None
        watch_url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en' % trailer_id
        watchrequest = Request(watch_url, None, header)
        try:
            watchvideopage = urlopen(watchrequest).read()
        except (HTTPError,
         URLError,
         HTTPException,
         socket.error,
         AttributeError):
            return trailer_url

        for el in ['&el=embedded',
         '&el=detailpage',
         '&el=vevo',
         '']:
            info_url = 'https://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (trailer_id, el)
            request = Request(info_url, None, header)
            try:
                infopage = urlopen(request).read()
                videoinfo = parse_qs(infopage)
                if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
                    break
            except (HTTPError,
             URLError,
             HTTPException,
             socket.error,
             AttributeError):
                return trailer_url

        if ('url_encoded_fmt_stream_map' or 'fmt_url_map') not in videoinfo:
            return trailer_url
        else:
            video_fmt_map = {}
            fmt_infomap = {}
            if 'url_encoded_fmt_stream_map' in videoinfo:
                tmp_fmtUrlDATA = videoinfo['url_encoded_fmt_stream_map'][0].split(',')
            else:
                tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
            for fmtstring in tmp_fmtUrlDATA:
                fmturl = fmtid = ''
                if 'url_encoded_fmt_stream_map' in videoinfo:
                    try:
                        for arg in fmtstring.split('&'):
                            if arg.find('=') >= 0:
                                key, value = arg.split('=')
                                if key == 'itag':
                                    if len(value) > 3:
                                        value = value[:2]
                                    fmtid = value
                                elif key == 'url':
                                    fmturl = value

                        if fmtid != '' and fmturl != '' and fmtid in VIDEO_FMT_PRIORITY_MAP:
                            video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid,
                             'fmturl': unquote_plus(fmturl)}
                            fmt_infomap[int(fmtid)] = '%s' % unquote_plus(fmturl)
                        fmturl = fmtid = ''
                    except:
                        return trailer_url

                else:
                    fmtid, fmturl = fmtstring.split('|')
                if fmtid in VIDEO_FMT_PRIORITY_MAP and fmtid != '':
                    video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid,
                     'fmturl': unquote_plus(fmturl)}
                    fmt_infomap[int(fmtid)] = unquote_plus(fmturl)

            if video_fmt_map and len(video_fmt_map):
                best_video = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]
                trailer_url = '%s' % best_video['fmturl'].split(';')[0]
            return trailer_url

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu':
            self.close()
        else:
            self.postviewready = False
            self.setTitle('')
            self.setTitle(self.titel)
            self.showTVBlog()


class TVNewsPicShow(tvBaseScreen):
    skin = '<screen name="TVNewsPicShow" position="center,center" size="{screensize}" title="Fotostrecke - TV Spielfilm">' + SKHEADTOP + """
            <widget name="label" position="364,10" size="512,44" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />""" + SKTIME + """
            <widget name="picture" position="175,70" size="889,500" alphatest="blend" zPosition="1" />
            <widget name="picindex" position="1065,70" size="165,24" font="Regular;20" halign="right" zPosition="1" />
            <widget name="pictext" position="10,577" size="1220,63" font="Regular;20" halign="center" zPosition="1" />
        </screen>"""

    def __init__(self, session, link):
        tvBaseScreen.__init__(self, session, TVNewsPicShow.skin)
        self.hideflag = True
        self.link = link
        self.pixlist = []
        self.topline = []
        self.titel = ''
        self.picmax = 1
        self.count = 0
        self['picture'] = Pixmap()
        self['picindex'] = Label('')
        self['pictext'] = ScrollLabel('')
        self['label'] = Label(OKZV)
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.picup,
         'left': self.picdown,
         'up': self.up,
         'down': self.down,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'blue': self.hideScreen,
         '0': self.gotoPic,
         '1': self.gotoPic,
         '2': self.gotoPic,
         '3': self.gotoPic,
         '4': self.gotoPic,
         '5': self.gotoPic,
         '6': self.gotoPic,
         '7': self.gotoPic,
         '8': self.gotoPic,
         '9': self.gotoPic}, -1)
        self.getInfoTimer = eTimer()
        self.getInfoTimer.callback.append(self.download(link, self.getPixPage))
        self.getInfoTimer.start(500, True)

    def getPixPage(self, output):
        if search('<title>', output) is not None:
            titel = search('<title>(.*?)</title>', output)
            titel = titel.group(1).replace('&amp;', '&')
            self.titel = sub(' - TV Spielfilm', '', titel)
            self.setTitle(self.titel)
        startpos = output.find('<div class="film-gallery">')
        if startpos == -1:
            startpos = output.find('class="film-gallery paragraph')
        endpos = output.find('<div class="swiper-slide more-galleries">')
        if endpos == -1:
            endpos = output.find('<div class="paragraph clear film-gallery"')
        bereich = output[startpos:endpos]
        bereich = sub('<br />\r\n<br />\r\n', ' \x95 ', bereich)
        bereich = sub('<br />\r\n<br />', ' \x95 ', bereich)
        bereich = sub('<br />', '', bereich)
        bereich = sub('<br/>', '', bereich)
        bereich = sub('<b>', '', bereich)
        bereich = sub('</b>', '', bereich)
        bereich = sub('<i>', '', bereich)
        bereich = sub('</i>', '', bereich)
        bereich = sub('<a href.*?</a>', '', bereich)
        bereich = sub('</h2>\n\\s+<p>', '', bereich)
        bereich = sub('&copy;', '', bereich)
        bereich = transHTML(bereich)
        self.pixlist = re.findall('<img src="(.*?)"', bereich)
        try:
            self.download(self.pixlist[0], self.getPic)
        except IndexError:
            pass

        self.picmax = len(self.pixlist)
        try:
            picnumber = self.count + 1
            self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
        except IndexError:
            pass

        self.topline = re.findall('<div class="image-text">\n\\s+(.*?)</div>', bereich, flags=re.S)
        try:
            self['pictext'].setText(self.topline[0])
        except IndexError:
            self.topline = re.findall('<span class="credit">(.*?)</span>', bereich, flags=re.S)
            try:
                self['pictext'].setText(self.topline[0])
            except IndexError:
                self.topline = re.findall('<p>(.*?)</p>', bereich, flags=re.S)
                try:
                    self['pictext'].setText(self.topline[0])
                except IndexError:
                    pass

        return

    def ok(self):
        self.session.openWithCallback(self.exit, PicShowFull, self.link, self.count, False)

    def picup(self):
        self.count += 1
        if self.count < self.picmax:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
                self['pictext'].setText(self.topline[self.count])
            except IndexError:
                pass

        else:
            self.count = 0
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
                self['pictext'].setText(self.topline[self.count])
            except IndexError:
                pass

    def picdown(self):
        self.count -= 1
        if self.count >= 0:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
                self['pictext'].setText(self.topline[self.count])
            except IndexError:
                pass

        else:
            self.count = self.picmax - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
                self['pictext'].setText(self.topline[self.count])
            except IndexError:
                pass

    def gotoPic(self, number):
        self.session.openWithCallback(self.numberEntered, getNumber, number)

    def numberEntered(self, number):
        if number is None or number == 0:
            pass
        else:
            if number > self.picmax:
                number = self.picmax
            self.count = number - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
                self['pictext'].setText(self.topline[self.count])
            except IndexError:
                pass

        return

    def up(self):
        self['pictext'].pageUp()

    def down(self):
        self['pictext'].pageDown()

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.picfile)

    def showPic(self, picture):
        currPic = loadPic(picture, 889, 500, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class PlayboyPicShow(tvBaseScreen):
    skin = '<screen name="PlayboyPicShow" position="center,center" size="{screensize}" title="Erotische Playmates - TV Spielfilm">' + SKHEADTOP + """
            <widget name="label" position="364,10" size="512,44" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />""" + SKTIME + """
            <widget name="textpage" position="10,70" size="250,560" font="Regular;20" halign="left" zPosition="1" />
            <widget name="picture" position="175,70" size="889,500" alphatest="blend" zPosition="1" />
            <widget name="picindex" position="1065,70" size="165,24" font="Regular;20" halign="right" zPosition="1" />
            <widget name="pictext" position="10,577" size="1220,63" font="Regular;20" halign="center" zPosition="1" />
        </screen>"""

    def __init__(self, session, link):
        tvBaseScreen.__init__(self, session, PlayboyPicShow.skin)
        self.hideflag = True
        self.link = link
        self.pixlist = []
        self.picmax = ''
        self.count = 0
        self['picture'] = Pixmap()
        self['picindex'] = Label('')
        self['pictext'] = ScrollLabel('')
        self['textpage'] = ScrollLabel('')
        self['label'] = Label(OKZV)
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.picup,
         'left': self.picdown,
         'up': self.up,
         'down': self.down,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'blue': self.hideScreen,
         '0': self.gotoPic,
         '1': self.gotoPic,
         '2': self.gotoPic,
         '3': self.gotoPic,
         '4': self.gotoPic,
         '5': self.gotoPic,
         '6': self.gotoPic,
         '7': self.gotoPic,
         '8': self.gotoPic,
         '9': self.gotoPic}, -1)
        self.getInfoTimer = eTimer()
        self.getInfoTimer.callback.append(self.download(link, self.getPicPage))
        self.getInfoTimer.start(500, True)

    def getPicPage(self, output):
        title = search('<title>(.*?)</title>', output)
        title = sub(' - TV Spielfilm', '', title.group(1))
        self.setTitle(title)
        startpos = output.find('<div class="content-area">')
        endpos = output.find('Mehr Girls bei Playboy</a>')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        self.pixlist = re.findall('<img src="(.*?)" alt=""', bereich)
        try:
            self.download(self.pixlist[0], self.getPic)
        except IndexError:
            pass

        self.picmax = len(self.pixlist)
        try:
            picnumber = self.count + 1
            self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
        except IndexError:
            pass

        topline = search('<p><b>(.*?)</b><br/>', output)
        if topline is not None:
            self['pictext'].setText(transHTML(topline.group(1)))
        bereich = sub('<p class="headline2">.*?</p>', '', bereich)
        bereich = sub('<br/>\n', '', bereich)
        bereich = sub('<b>', '', bereich)
        bereich = sub('</b>', '', bereich)
        text = ''
        a = findall('<p.*?>(.*?)</p>', bereich, re.S)
        for x in a:
            if x != '':
                text = text + x + '\n\n'

        text = sub('<[^>]*>', '', text)
        text = sub('</p<<p<', '\n\n', text)
        self['textpage'].setText(text)
        return

    def ok(self):
        self.session.openWithCallback(self.exit, PicShowFull, self.link, self.count, True)

    def picup(self):
        self.count += 1
        if self.count < self.picmax:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = 0
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def picdown(self):
        self.count -= 1
        if self.count >= 0:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = self.picmax - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def gotoPic(self, number):
        self.session.openWithCallback(self.numberEntered, getNumber, number)

    def numberEntered(self, number):
        if number is None or number == 0:
            pass
        else:
            if number > self.picmax:
                number = self.picmax
            self.count = number - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        return

    def up(self):
        self['pictext'].pageUp()

    def down(self):
        self['pictext'].pageDown()

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.picfile)

    def showPic(self, picture):
        currPic = loadPic(picture, 700, 500, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self['pictext'].setText('Download Fehler')

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class TVPicShow(tvBaseScreen):
    skin = '<screen name="TVPicShow" position="center,center" size="{screensize}" title="Fotostrecke - TV Spielfilm">' + SKHEADTOP + """
            <widget name="label" position="364,10" size="512,44" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />""" + SKTIME + """
            <widget name="infotext" position="10,70" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
            <widget name="infotext2" position="10,105" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
            <widget name="infotext3" position="10,140" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
            <widget name="infotext4" position="10,175" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
            <widget name="infotext5" position="980,70" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
            <widget name="infotext6" position="980,105" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
            <widget name="infotext7" position="980,140" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
            <widget name="infotext8" position="980,175" size="250,25" font="Regular;20" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
            <widget name="picture" position="270,70" size="700,525" alphatest="blend" zPosition="1" />
            <widget name="pictext" position="10,595" size="1220,48" font="Regular;18" halign="center" valign="center" zPosition="1" />
        </screen>"""

    def __init__(self, session, link):
        tvBaseScreen.__init__(self, session, TVPicShow.skin)
        self.hideflag = True
        self.link = link
        self.pixlist = []
        self.description = []
        self.titel = ''
        self.picmax = 1
        self.count = 0
        self['infotext'] = Label('')
        self['infotext2'] = Label('')
        self['infotext3'] = Label('')
        self['infotext4'] = Label('')
        self['infotext5'] = Label('')
        self['infotext6'] = Label('')
        self['infotext7'] = Label('')
        self['infotext8'] = Label('')
        self['picture'] = Pixmap()
        self['pictext'] = Label('')
        self['label'] = Label(OKZV)
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.picup,
         'left': self.picdown,
         'up': self.picup,
         'down': self.picdown,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'blue': self.hideScreen,
         '0': self.gotoPic,
         '1': self.gotoPic,
         '2': self.gotoPic,
         '3': self.gotoPic,
         '4': self.gotoPic,
         '5': self.gotoPic,
         '6': self.gotoPic,
         '7': self.gotoPic,
         '8': self.gotoPic,
         '9': self.gotoPic}, -1)
        self.getPicTimer = eTimer()
        self.getPicTimer.callback.append(self.download(link, self.getPicPage))
        self.getPicTimer.start(500, True)

    def getPicPage(self, output):
        output = transHTML(output)
        if search('<title>', output) is not None:
            titel = search('<title>(.*?)</title>', output)
            titel = titel.group(1)
            self.titel = sub(' - TV Spielfilm', '', titel)
            self.setTitle(self.titel)
        startpos = output.find('<div class="film-gallery">')
        endpos = output.find('<div class="swiper-slide more-galleries">')
        bereich = output[startpos:endpos]
        bereich = sub('<span class="credit">', '', bereich)
        bereich = sub('<span class="counter">.*?</span>\n\\s+', '', bereich)
        bereich = sub('</span>\n\\s+', '', bereich)
        self.pixlist = re.findall('<img src="(.*?)"', bereich)
        try:
            self.download(self.pixlist[0], self.getPic)
        except IndexError:
            pass

        self.description = re.findall('<div class="description">\n\\s+(.*?)</div>', bereich, flags=re.S)
        self.picmax = len(self.pixlist)
        try:
            picnumber = self.count + 1
            self['pictext'].setText(self.description[0] + '\n%s von %s' % (picnumber, self.picmax))
        except IndexError:
            pass

        infotext = re.findall('<span class="text-row">(.*?)<', output)
        try:
            parts = infotext[0].split(', ')
            self['infotext'].setText(parts[0])
            self['infotext'].show()
        except IndexError:
            self['infotext'].setText('')

        try:
            parts = infotext[0].split(', ')
            self['infotext2'].setText(parts[1])
            self['infotext2'].show()
        except IndexError:
            self['infotext2'].setText('')

        try:
            parts = infotext[0].split(', ')
            self['infotext3'].setText(parts[2])
            self['infotext3'].show()
        except IndexError:
            self['infotext3'].setText('')

        try:
            parts = infotext[1].split(', ')
            self['infotext4'].setText(parts[0])
            self['infotext4'].show()
        except IndexError:
            self['infotext4'].setText('')

        try:
            parts = infotext[1].split(', ')
            self['infotext5'].setText(parts[1])
            self['infotext5'].show()
        except IndexError:
            self['infotext5'].setText('')

        try:
            parts = infotext[1].split(', ')
            self['infotext6'].setText(parts[2])
            self['infotext6'].show()
        except IndexError:
            self['infotext6'].setText('')

        try:
            parts = infotext[2].split(', ')
            self['infotext7'].setText(parts[0])
            self['infotext7'].show()
        except IndexError:
            self['infotext7'].setText('')

        try:
            parts = infotext[3].split(', ')
            self['infotext8'].setText(parts[0])
            self['infotext8'].show()
        except IndexError:
            self['infotext8'].setText('')

        return

    def ok(self):
        self.session.openWithCallback(self.exit, PicShowFull, self.link, self.count, False)

    def picup(self):
        self.count += 1
        if self.count < self.picmax:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['pictext'].setText(self.description[self.count] + '\n%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = 0
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['pictext'].setText(self.description[self.count] + '\n%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def picdown(self):
        self.count -= 1
        if self.count >= 0:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['pictext'].setText(self.description[self.count] + '\n%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = self.picmax - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['pictext'].setText(self.description[self.count] + '\n%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def gotoPic(self, number):
        self.session.openWithCallback(self.numberEntered, getNumber, number)

    def numberEntered(self, number):
        if number is None or number == 0:
            pass
        else:
            if number > self.picmax:
                number = self.picmax
            self.count = number - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['pictext'].setText(self.description[self.count] + '\n%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        return

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.picfile)

    def showPic(self, picture):
        currPic = loadPic(picture, 700, 525, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class PicShowFull(tvBaseScreen):

    skin = """
        <screen name="PicShowFull" position="center,center" size="{fullsize}" title=" ">
            <eLabel position="0,0" size="{fullsize}" backgroundColor="#000000" zPosition="1" />
            <widget name="picture" position="0,0" size="{fullsize}" alphatest="blend" zPosition="2" />
            <widget name="picindex" position="10,10" size="120,22" font="Regular;20" foregroundColor="#A5ACAE" halign="left" transparent="1" zPosition="3" />
        </screen>"""

    def __init__(self, session, link, count, playboy):
        tvBaseScreen.__init__(self, session, PicShowFull.skin)
        self.hideflag = True
        self.playboy = playboy
        self.pixlist = []
        self.count = count
        self.picmax = 1
        self['picture'] = Pixmap()
        self['picindex'] = Label('')
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions'], {'ok': self.picup,
         'cancel': self.exit,
         'right': self.picup,
         'left': self.picdown,
         'up': self.picup,
         'down': self.picdown,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'blue': self.hideScreen,
         '0': self.gotoPic,
         '1': self.gotoPic,
         '2': self.gotoPic,
         '3': self.gotoPic,
         '4': self.gotoPic,
         '5': self.gotoPic,
         '6': self.gotoPic,
         '7': self.gotoPic,
         '8': self.gotoPic,
         '9': self.gotoPic}, -1)
        self.getPicTimer = eTimer()
        self.getPicTimer.callback.append(self.download(link, self.getPicPage))
        self.getPicTimer.start(500, True)

    def getPicPage(self, output):
        if self.playboy == False:
            startpos = output.find('<div class="film-gallery">')
            if startpos == -1:
                startpos = output.find('class="film-gallery paragraph')
            endpos = output.find('<div class="swiper-slide more-galleries">')
            if endpos == -1:
                endpos = output.find('<div class="paragraph clear film-gallery"')
            bereich = output[startpos:endpos]
            self.pixlist = re.findall('<img src="(.*?)"', bereich)
        else:
            startpos = output.find('<div class="content-area">')
            endpos = output.find('Mehr Girls bei Playboy</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
            self.pixlist = re.findall('<img src="(.*?)" alt=""', bereich)
        try:
            self.download(self.pixlist[self.count], self.getPic)
        except IndexError:
            pass

        self.picmax = len(self.pixlist)
        try:
            picnumber = self.count + 1
            self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
        except IndexError:
            pass

    def picup(self):
        self.count += 1
        if self.count < self.picmax:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = 0
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def picdown(self):
        self.count -= 1
        if self.count >= 0:
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = self.picmax - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def gotoPic(self, number):
        self.session.openWithCallback(self.numberEntered, getNumber, number)

    def numberEntered(self, number):
        if number is None or number == 0:
            pass
        else:
            if number > self.picmax:
                number = self.picmax
            self.count = number - 1
            try:
                link = self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('%s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        return

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.picfile)

    def showPic(self, picture):
        currPic = loadPic(picture, DESKTOP_WIDTH, DESKTOP_HEIGHT, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class FullScreen(tvAllScreen):
    skin = """
        <screen position="center,center" size="{size}" flags="wfNoBorder" title="  " >
        <eLabel position="0,0" size="{size}" backgroundColor="#000000" zPosition="1" />
        <widget name="picture" position="{ppos}" size="{psize}" alphatest="blend" zPosition="2" />
        </screen>"""

    def __init__(self, session):
        size = "%s,%s" % (DESKTOP_WIDTH,DESKTOP_HEIGHT)
        psize = "%s,%s" % (DESKTOP_WIDTH * 0.75,DESKTOP_HEIGHT)
        ppos = "%s,%s" % (DESKTOP_WIDTH * 0.125,0)
        dic = {'size' : size , 'psize' : psize , 'ppos' : ppos}
        tvAllScreen.__init__(self, session, FullScreen.skin, dic)
        self.picfile = '/tmp/tvspielfilm.jpg'
        self.hideflag = True
        self['picture'] = Pixmap()
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.exit,
         'cancel': self.exit,
         'blue': self.hideScreen}, -1)
        self.onShown.append(self.showPic)

    def showPic(self):
        currPic = loadPic(self.picfile, DESKTOP_WIDTH * 0.75, DESKTOP_HEIGHT, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class searchYouTube(tvAllScreen):
    def __init__(self, session, name, movie):
        skin = """
        <screen name="searchYouTube" position="center,center" size="1000,560" title=" ">
            <ePixmap position="0,0" size="1000,50" pixmap="{picpath}youtube.png" alphatest="blend" zPosition="1" />
            <ePixmap position="10,6" size="18,18" pixmap="{picpath}buttons/blue.png" alphatest="blend" zPosition="2" />
            <ePixmap position="10,26" size="18,18" pixmap="{picpath}buttons/yellow.png" alphatest="blend" zPosition="2" />
            <widget name="label" position="34,6" size="200,20" font="Regular;16" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label2" position="34,26" size="200,20" font="Regular;16" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />""" + SKTIME + """
            <widget name="poster1" position="10,55" size="215,120" alphatest="blend" zPosition="1" />
            <widget name="poster2" position="10,180" size="215,120" alphatest="blend" zPosition="1" />
            <widget name="poster3" position="10,305" size="215,120" alphatest="blend" zPosition="1" />
            <widget name="poster4" position="10,430" size="215,120" alphatest="blend" zPosition="1" />
            <widget name="list" position="235,55" size="755,500" scrollbarMode="showOnDemand" zPosition="1" />
        </screen>"""

        tvAllScreen.__init__(self, session, skin)
        if movie == True:
            self.name = name + ' Trailer'
        else:
            self.name = name
        name = self.name.replace(' ', '+').replace(':', '+').replace('_', '+').replace('\xc3\x84', 'Ae').replace('\xc3\x96', 'Oe').replace('\xc3\x9c', 'Ue').replace('\xc3\x9f', 'ss').replace('\xc3\xa4', 'ae').replace('\xc3\xb6', 'oe').replace('\xc3\xbc', 'ue').replace('\xc4', 'Ae').replace('\xd6', 'Oe').replace('\xdc', 'Ue').replace('\xe4', 'ae').replace('\xf6', 'oe').replace('\xfc', 'ue')
        self.link = 'https://www.youtube.com/results?filters=video&search_query=' + name
        self.titel = 'YouTube Trailer Suche | Seite '
        self.poster = []
        self.trailer_id = []
        self.trailer_list = []
        self.localhtml = '/tmp/youtube.html'
        self.poster1 = '/tmp/youtube1.jpg'
        self.poster2 = '/tmp/youtube2.jpg'
        self.poster3 = '/tmp/youtube3.jpg'
        self.poster4 = '/tmp/youtube4.jpg'
        self['poster1'] = Pixmap()
        self['poster2'] = Pixmap()
        self['poster3'] = Pixmap()
        self['poster4'] = Pixmap()
        self.ready = False
        self.hideflag = True
        self.count = 1
        self['list'] = ItemList([])
        self['label'] = Label('= Hide')
        self['label2'] = Label('= YouTube Search')
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions',
         'NumberActions',
         'MovieSelectionActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.nextPage,
         'prevBouquet': self.prevPage,
         'yellow': self.search,
         'blue': self.hideScreen,
         '0': self.gotoEnd,
         'bluelong': self.showHelp,
         'showEventInfo': self.showHelp}, -1)
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        self.makeTrailerTimer = eTimer()
        self.makeTrailerTimer.callback.append(self.downloadFullPage(self.link, self.makeTrailerList))
        self.makeTrailerTimer.start(500, True)

    def makeTrailerList(self, string):
        self.setTitle(self.titel + str(self.count))
        output = open(self.localhtml, 'r').read()
        startpos = output.find('class="section-list">')
        endpos = output.find('\n</ol>\n\n')
        bereich = output[startpos:endpos]
        bereich = sub('</a>', '', bereich)
        bereich = sub('<b>', '', bereich)
        bereich = sub('</b>', '', bereich)
        bereich = sub('<wbr>', '', bereich)
        bereich = sub('</li><li>', ' \xb7 ', bereich)
        bereich = sub('&quot;', "'", bereich)
        bereich = transHTML(bereich)
        self.poster = re.findall('i.ytimg.com/(.*?)default.jpg', bereich)
        self.trailer_id = re.findall('<h3 class="yt-lockup-title.*?"><a href="/watch.v=(.*?)"', bereich)
        self.trailer_titel = re.findall('<h3 class="yt-lockup-title.*?"><a href=".*?">(.*?)<', bereich)
        trailer_time = re.findall('<span class="accessible-description" id="description-id.*?: (.*?)</span>', bereich)
        trailer_info = re.findall('<ul class="yt-lockup-meta-info">(.*?)</div>(.*?)</div>', bereich)
        for x in range(len(self.trailer_id)):
            res = ['']
            if self.backcolor == True:
                res.append(MultiContentEntryText(pos=(0, 0), size=(755, 125), font=-1, backcolor_sel=self.back_color, text=''))
            try:
                res.append(MultiContentEntryText(pos=(5, 13), size=(730, 30), font=-1, color=16777215, flags=RT_HALIGN_LEFT, text=self.trailer_titel[x]))
            except IndexError:
                pass

            try:
                res.append(MultiContentEntryText(pos=(5, 48), size=(75, 25), font=1, color=16777215, flags=RT_HALIGN_RIGHT, text=trailer_time[x] + ' \xb7 '))
            except IndexError:
                pass

            try:
                info = sub('<.*?>', '', trailer_info[x][0])
                res.append(MultiContentEntryText(pos=(85, 48), size=(650, 25), font=1, color=16777215, flags=RT_HALIGN_LEFT, text=info))
            except IndexError:
                pass

            try:
                desc = sub('<.*?>', '', trailer_info[x][1])
                res.append(MultiContentEntryText(pos=(5, 75), size=(730, 50), font=1, color=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=desc))
            except IndexError:
                pass

            self.trailer_list.append(res)

        self['list'].l.setList(self.trailer_list)
        self['list'].l.setItemHeight(125)
        self['list'].moveToIndex(0)
        self.ready = True
        try:
            poster1 = 'https://i.ytimg.com/' + self.poster[0] + 'default.jpg'
            self.download(poster1, self.getPoster1)
            self['poster1'].show()
        except IndexError:
            self['poster1'].hide()

        try:
            poster2 = 'https://i.ytimg.com/' + self.poster[1] + 'default.jpg'
            self.download(poster2, self.getPoster2)
            self['poster2'].show()
        except IndexError:
            self['poster2'].hide()

        try:
            poster3 = 'https://i.ytimg.com/' + self.poster[2] + 'default.jpg'
            self.download(poster3, self.getPoster3)
            self['poster3'].show()
        except IndexError:
            self['poster3'].hide()

        try:
            poster4 = 'https://i.ytimg.com/' + self.poster[3] + 'default.jpg'
            self.download(poster4, self.getPoster4)
            self['poster4'].show()
        except IndexError:
            self['poster4'].hide()

    def ok(self):
        if self.ready == True:
            try:
                c = self['list'].getSelectedIndex()
                trailer_id = self.trailer_id[c]
                trailer_titel = self.trailer_titel[c]
                trailer_url = self.getTrailerURL(trailer_id)
                if trailer_url is not None:
                    sref = eServiceReference(4097, 0, trailer_url)
                    sref.setName(trailer_titel)
                    self.session.open(MoviePlayer, sref)
                else:
                    self.session.open(MessageBox, '\nYouTube Video nicht gefunden', MessageBox.TYPE_ERROR)
            except IndexError:
                pass

        return

    def getTrailerURL(self, trailer_id):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        VIDEO_FMT_PRIORITY_MAP = {'38': 3,
         '37': 1,
         '22': 2,
         '35': 5,
         '18': 4,
         '34': 6}
        trailer_url = None
        watch_url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en' % trailer_id
        watchrequest = Request(watch_url, None, header)
        try:
            watchvideopage = urlopen(watchrequest).read()
        except (HTTPError,
         URLError,
         HTTPException,
         socket.error,
         AttributeError):
            return trailer_url

        for el in ['&el=embedded',
         '&el=detailpage',
         '&el=vevo',
         '']:
            info_url = 'https://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (trailer_id, el)
            request = Request(info_url, None, header)
            try:
                infopage = urlopen(request).read()
                videoinfo = parse_qs(infopage)
                if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
                    break
            except (HTTPError,
             URLError,
             HTTPException,
             socket.error,
             AttributeError):
                return trailer_url

        if ('url_encoded_fmt_stream_map' or 'fmt_url_map') not in videoinfo:
            return trailer_url
        else:
            video_fmt_map = {}
            fmt_infomap = {}
            if 'url_encoded_fmt_stream_map' in videoinfo:
                tmp_fmtUrlDATA = videoinfo['url_encoded_fmt_stream_map'][0].split(',')
            else:
                tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
            for fmtstring in tmp_fmtUrlDATA:
                fmturl = fmtid = ''
                if 'url_encoded_fmt_stream_map' in videoinfo:
                    try:
                        for arg in fmtstring.split('&'):
                            if arg.find('=') >= 0:
                                key, value = arg.split('=')
                                if key == 'itag':
                                    if len(value) > 3:
                                        value = value[:2]
                                    fmtid = value
                                elif key == 'url':
                                    fmturl = value

                        if fmtid != '' and fmturl != '' and fmtid in VIDEO_FMT_PRIORITY_MAP:
                            video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid,
                             'fmturl': unquote_plus(fmturl)}
                            fmt_infomap[int(fmtid)] = '%s' % unquote_plus(fmturl)
                        fmturl = fmtid = ''
                    except:
                        return trailer_url

                else:
                    fmtid, fmturl = fmtstring.split('|')
                if fmtid in VIDEO_FMT_PRIORITY_MAP and fmtid != '':
                    video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid,
                     'fmturl': unquote_plus(fmturl)}
                    fmt_infomap[int(fmtid)] = unquote_plus(fmturl)

            if video_fmt_map and len(video_fmt_map):
                best_video = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]
                trailer_url = '%s' % best_video['fmturl'].split(';')[0]
            return trailer_url

    def search(self):
        if self.ready == True:
            self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='YouTube Trailer Suche:', text=self.name)

    def searchReturn(self, name):
        if name and name != '':
            self.name = name
            name = name.replace(' ', '+').replace(':', '+').replace('_', '+').replace('\xc4', 'Ae').replace('\xd6', 'Oe').replace('\xdc', 'Ue').replace('\xe4', 'ae').replace('\xf6', 'oe').replace('\xfc', 'ue')
            self.link = 'https://www.youtube.com/results?filters=video&search_query=' + name
            self.count = 1
            self.poster = []
            self.trailer_id = []
            self.trailer_list = []
            self.makeTrailerTimer.callback.append(self.downloadFullPage(self.link, self.makeTrailerList))

    def nextPage(self):
        if self.ready == True:
            self.count += 1
            if self.count >= 10:
                self.count = 9
            link = self.link + '&page=' + str(self.count)
            self.poster = []
            self.trailer_id = []
            self.trailer_list = []
            self.makeTrailerTimer.callback.append(self.downloadFullPage(link, self.makeTrailerList))

    def prevPage(self):
        if self.ready == True:
            self.count -= 1
            if self.count <= 0:
                self.count = 1
            link = self.link + '&page=' + str(self.count)
            self.poster = []
            self.trailer_id = []
            self.trailer_list = []
            self.makeTrailerTimer.callback.append(self.downloadFullPage(link, self.makeTrailerList))

    def down(self):
        if self.ready == True:
            try:
                c = self['list'].getSelectedIndex()
            except IndexError:
                return

            self['list'].down()
            if c + 1 == len(self.trailer_id):
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[0] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[1] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[2] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[3] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

            elif c % 4 == 3:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 1] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 2] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

    def up(self):
        if self.ready == True:
            try:
                c = self['list'].getSelectedIndex()
            except IndexError:
                return

            self['list'].up()
            if c == 0:
                l = len(self.trailer_list)
                d = l % 4
                if d == 0:
                    d = 4
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[l - d] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[l - d + 1] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[l - d + 2] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[l - d + 3] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

            elif c % 4 == 0:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c - 2] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c - 1] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

    def rightDown(self):
        if self.ready == True:
            try:
                c = self['list'].getSelectedIndex()
            except IndexError:
                return

            self['list'].pageDown()
            l = len(self.trailer_list)
            d = c % 4
            e = l % 4
            if e == 0:
                e = 4
            if c + e >= l:
                pass
            elif d == 0:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 5] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 6] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 7] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

            elif d == 1:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 5] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 6] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

            elif d == 2:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 2] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 5] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

            elif d == 3:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 1] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 2] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

    def leftUp(self):
        if self.ready == True:
            try:
                c = self['list'].getSelectedIndex()
            except IndexError:
                return

            self['list'].pageUp()
            d = c % 4
            if c < 4:
                pass
            elif d == 0:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    poster2 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    poster3 = 'https://i.ytimg.com/' + self.poster[c - 2] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    poster4 = 'https://i.ytimg.com/' + self.poster[c - 1] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    pass

            elif d == 1:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c - 5] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    poster2 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    poster3 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    poster4 = 'https://i.ytimg.com/' + self.poster[c - 2] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    pass

            elif d == 2:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c - 6] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    poster2 = 'https://i.ytimg.com/' + self.poster[c - 5] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    poster3 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    poster4 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    pass

            elif d == 3:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c - 7] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    poster2 = 'https://i.ytimg.com/' + self.poster[c - 6] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    poster3 = 'https://i.ytimg.com/' + self.poster[c - 5] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    poster4 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    pass

            self['poster1'].show()
            self['poster2'].show()
            self['poster3'].show()
            self['poster4'].show()

    def gotoEnd(self):
        if self.ready == True:
            end = len(self.trailer_list) - 1
            if end > 4:
                self['list'].moveToIndex(end)
                self.leftUp()
                self.rightDown()

    def getPoster1(self, output):
        f = open(self.poster1, 'wb')
        f.write(output)
        f.close()
        self.showPoster1(self.poster1)

    def showPoster1(self, poster1):
        currPic = loadPic(poster1, 215, 120, 3, 0, 0, 0)
        if currPic != None:
            self['poster1'].instance.setPixmap(currPic)
        return

    def getPoster2(self, output):
        f = open(self.poster2, 'wb')
        f.write(output)
        f.close()
        self.showPoster2(self.poster2)

    def showPoster2(self, poster2):
        currPic = loadPic(poster2, 215, 120, 3, 0, 0, 0)
        if currPic != None:
            self['poster2'].instance.setPixmap(currPic)
        return

    def getPoster3(self, output):
        f = open(self.poster3, 'wb')
        f.write(output)
        f.close()
        self.showPoster3(self.poster3)

    def showPoster3(self, poster3):
        currPic = loadPic(poster3, 215, 120, 3, 0, 0, 0)
        if currPic != None:
            self['poster3'].instance.setPixmap(currPic)
        return

    def getPoster4(self, output):
        f = open(self.poster4, 'wb')
        f.write(output)
        f.close()
        self.showPoster4(self.poster4)

    def showPoster4(self, poster4):
        currPic = loadPic(poster4, 215, 120, 3, 0, 0, 0)
        if currPic != None:
            self['poster4'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadFullPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

    def downloadPageError(self, output):
        try:
            error = output.getErrorMessage()
            self.session.open(MessageBox, 'The YouTube Server is not reachable:\n%s' % error, MessageBox.TYPE_ERROR)
        except AttributeError:
            self.session.open(MessageBox, '\nThe YouTube Server is not reachable.', MessageBox.TYPE_ERROR)

        self.close()

    def showHelp(self):
        self.session.open(MessageBox, '\n%s' % 'Bouquet = +- Seite\nGelb = Neue YouTube Suche', MessageBox.TYPE_INFO, close_on_any_key=True)

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if fileExists(self.localhtml):
            os.remove(self.localhtml)
        if fileExists(self.poster1):
            os.remove(self.poster1)
        if fileExists(self.poster2):
            os.remove(self.poster2)
        if fileExists(self.poster3):
            os.remove(self.poster3)
        if fileExists(self.poster4):
            os.remove(self.poster4)
        self.close()


class tvMain(tvBaseScreen):
    skin = """
        <screen name="tvMain" position="center,_20" size="_310,_640" flags="wfNoBorder" title="TV Spielfilm">
            <eLabel position="0,0" size="310,30" backgroundColor="#000000" zPosition="1" />
            <eLabel position="0,30" size="20,590" backgroundColor="#000000" zPosition="1" />
            <eLabel position="290,30" size="20,590" backgroundColor="#000000" zPosition="1" />
            <eLabel position="0,620" size="310,20" backgroundColor="#000000" zPosition="1" />
            <ePixmap position="20,30" size="_270,60" pixmap="{picpath}tvspielfilmHD.png" alphatest="blend" zPosition="1" />
            <ePixmap position="_262,40" size="18,18" pixmap="{picpath}buttons/red.png" alphatest="blend" zPosition="2" />
            <widget name="green" position="_262,62" size="18,18" pixmap="{picpath}buttons/green.png" alphatest="blend" zPosition="2" />
            <widget name="label" position="176,40" size="80,20" font="Regular;16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label2" position="176,62" size="80,20" font="Regular;16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="mainmenu" position="_30,100" size="_250,_390" scrollbarMode="showNever" zPosition="2" />
            <widget name="secondmenu" position="_30,100" size="_250,_510" scrollbarMode="showNever" zPosition="2" />
            <widget name="thirdmenu" position="_30,100" size="_250,_510" scrollbarMode="showNever" zPosition="2" />
        </screen>"""

    def __init__(self, session):
        tvBaseScreen.__init__(self, session, tvMain.skin)
        self.senderhtml = '/tmp/tvssender.html'
        if config.plugins.tvspielfilm.tipps.value == 'false':
            self.tipps = False
            self.hidetipps = True
        elif config.plugins.tvspielfilm.tipps.value == 'no':
            self.tipps = True
            self.hidetipps = True
        else:
            self.tipps = True
            self.hidetipps = False
        self.hideflag = True
        self.ready = False
        self.sparte = []
        self.genre = []
        self.sender = []
        self.mainmenulist = []
        self.mainmenulink = []
        self.secondmenulist = []
        self.secondmenulink = []
        self.thirdmenulist = []
        self.thirdmenulink = []
        self['mainmenu'] = ItemList([])
        self['secondmenu'] = ItemList([])
        self['thirdmenu'] = ItemList([])
        self.actmenu = 'mainmenu'
        self['green'] = Pixmap()
        self['label'] = Label('Import = ')
        if self.tipps == True:
            self['label2'] = Label('Tipp = ')
        else:
            self['label2'] = Label('')
            self['green'].hide()
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'MovieSelectionActions',
         'ChannelSelectBaseActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'yellow': self.config,
         'red': self.red,
         'green': self.green,
         'blue': self.hideScreen,
         'contextMenu': self.config}, -1)
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        if self.tipps == True:
            self.TagesTipps = self.session.instantiateDialog(tvTipps)
            if self.hidetipps == False:
                self.TagesTipps.start()
                self.TagesTipps.show()
        if config.plugins.tvspielfilm.meintvs.value == 'yes':
            self.MeinTVS = True
            self.error = False
            self.loginerror = False
            self.baseurl = 'https://my.tvspielfilm.de'
            self.login = config.plugins.tvspielfilm.login.value
            self.password = config.plugins.tvspielfilm.password.value
            if config.plugins.tvspielfilm.encrypt.value == 'yes':
                try:
                    self.password = b64decode(self.password)
                except TypeError:
                    config.plugins.tvspielfilm.encrypt.value = 'no'
                    config.plugins.tvspielfilm.encrypt.save()
                    configfile.save()

            self.cookiefile = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/cookie'
            self.cookie = MozillaCookieJar(self.cookiefile)
            if fileExists(self.cookiefile):
                self.cookie.load()
            self.opener = build_opener(HTTPRedirectHandler(), HTTPHandler(debuglevel=0), HTTPCookieProcessor(self.cookie))
            self.opener.addheaders = [('Host', 'member.tvspielfilm.de'),
             ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:27.0) Gecko/20100101 Firefox/27.0'),
             ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
             ('Referer', 'https://member.tvspielfilm.de/login/70.html'),
             ('Connection', 'keep-alive')]
            self.loginToTVSpielfilm()
        else:
            self.MeinTVS = False
            self.opener = False
            self.AnzTimer = eTimer()
            self.AnzTimer.callback.append(self.makeTimerDB)
            self.AnzTimer.callback.append(self.checkMainMenu)
            self.AnzTimer.start(500, True)

    def loginToTVSpielfilm(self):
        values = urlencode({'email': self.login,
         'pw': self.password,
         'perma_login': '1',
         'done': '1',
         'checkErrors': '1'})
        try:
            response = self.opener.open('https://member.tvspielfilm.de/login/70.html', values, timeout=60)
            result = response.read()
            if search('"error":"', result) is not None:
                error = search('"error":"(.*?)\\.', result)
                self.error = 'Mein TV SPIELFILM: ' + error.group(1) + '!'
                self.loginerror = True
                if fileExists(self.cookiefile):
                    os.remove(self.cookiefile)
            else:
                self.cookie.save()
            response.close()
        except HTTPException as e:
            self.error = 'HTTP Exception Error ' + str(e)
        except HTTPError as e:
            self.error = 'HTTP Error: ' + str(e.code)
        except URLError as e:
            self.error = 'URL Error: ' + str(e.reason)
        except socket.error as e:
            self.error = 'Socket Error: ' + str(e)
        except AttributeError as e:
            self.error = 'Attribute Error: ' + str(e.message)

        self.onLayoutFinish.append(self.onLayoutFinished)
        return

    def onLayoutFinished(self):
        if self.error == False:
            self.AnzTimer = eTimer()
            self.AnzTimer.callback.append(self.makeTimerDB)
            self.AnzTimer.callback.append(self.checkMainMenu)
            self.AnzTimer.start(500, True)
        else:
            self.makeErrorTimer = eTimer()
            self.makeErrorTimer.callback.append(self.displayError)
            self.makeErrorTimer.start(500, True)

    def displayError(self):
        self.ready = True
        if self.loginerror == True:
            self.session.openWithCallback(self.configError, MessageBox, '%s\n\nSetup aufrufen und Einstellungen anpassen?' % self.error, MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, '\n%s' % self.error, MessageBox.TYPE_ERROR)

    def configError(self, answer):
        if answer is True:
            self.config()
        else:
            self.MeinTVS = False
            self.AnzTimer = eTimer()
            self.AnzTimer.callback.append(self.makeTimerDB)
            self.AnzTimer.callback.append(self.checkMainMenu)
            self.AnzTimer.start(500, True)

    def ok(self):
        if self.ready == True:
            try:
                c = self.getIndex(self[self.actmenu])
            except IndexError:
                c = 0

            if self.actmenu == 'mainmenu':
                try:
                    if search('jetzt', self.mainmenulink[c]) is not None or search('time=shortly', self.mainmenulink[c]) is not None or search('abends', self.mainmenulink[c]) is not None or search('nachts', self.mainmenulink[c]) is not None:
                        if self.tipps == True:
                            self.stopTipps()
                        link = self.mainmenulink[c]
                        self.session.openWithCallback(self.selectMainMenu, TVJetztView, link, False)
                    elif search('page=1', self.mainmenulink[c]) is not None:
                        if self.tipps == True:
                            self.stopTipps()
                        link = self.mainmenulink[c]
                        self.session.openWithCallback(self.selectMainMenu, TVHeuteView, link, self.opener)
                    elif search('/bilder', self.mainmenulink[c]) is not None:
                        if self.tipps == True:
                            self.stopTipps()
                        link = self.mainmenulink[c]
                        self.session.openWithCallback(self.selectMainMenu, TVTrailerBilder, link, '_pic')
                    elif search('/tv-tipps//', self.mainmenulink[c]) is not None:
                        if self.tipps == True:
                            self.stopTipps()
                        link = self.mainmenulink[c]
                        self.session.openWithCallback(self.selectMainMenu, TVTippsView, link, 'neu')
                    elif search('/blog', self.mainmenulink[c]) is not None:
                        if self.tipps == True:
                            self.stopTipps()
                        link = self.mainmenulink[c]
                        self.session.openWithCallback(self.selectMainMenu, TVBlog, link, False)
                    elif search('/tv-tipps/', self.mainmenulink[c]) is not None or search('/tv-genre/', self.mainmenulink[c]) is not None or search('/trailer-und-clips/', self.mainmenulink[c]) is not None or search('/news-und-specials/', self.mainmenulink[c]) is not None:
                        link = self.mainmenulink[c]
                        self.makeSecondMenu(None, link)
                    else:
                        self.ready = False
                        link = self.mainmenulink[c]
                        if fileExists(self.senderhtml):
                            self.makeSecondMenu('string', link)
                        else:
                            self.downloadSender(link)
                except IndexError:
                    self.ready = True

            elif self.actmenu == 'secondmenu':
                if search('/tv-tipps/', self.secondmenulink[c]) is not None:
                    try:
                        if self.tipps == True:
                            self.stopTipps()
                        sparte = self.sparte[c]
                        link = self.secondmenulink[c]
                        self.session.openWithCallback(self.selectSecondMenu, TVTippsView, link, sparte)
                    except IndexError:
                        pass

                elif search('/trailer-und-clips/', self.secondmenulink[c]) is not None or search('/kino/charts/', self.secondmenulink[c]) is not None or search('/dvd/charts/', self.secondmenulink[c]) is not None or search('/kino/kino-vorschau/', self.secondmenulink[c]) is not None:
                    try:
                        if self.tipps == True:
                            self.stopTipps()
                        sparte = self.sparte[c]
                        link = self.secondmenulink[c]
                        self.session.openWithCallback(self.selectSecondMenu, TVTrailerBilder, link, sparte)
                    except IndexError:
                        pass

                elif search('/news-und-specials/|/tatort|/kids-tv', self.secondmenulink[c]) is not None:
                    try:
                        if self.tipps == True:
                            self.stopTipps()
                        link = self.secondmenulink[c]
                        if search('/playboy/', link) is not None:
                            self.session.openWithCallback(self.selectSecondMenu, PlayboyPicShow, link)
                        else:
                            self.session.openWithCallback(self.selectSecondMenu, TVNews, link)
                    except IndexError:
                        pass

                elif search('/tv-genre/', self.secondmenulink[c]) is not None:
                    try:
                        self.ready = False
                        sparte = self.sparte[c]
                        link = self.secondmenulink[c]
                        self.makeThirdMenu(None, sparte)
                    except IndexError:
                        self.ready = True

                else:
                    try:
                        self.ready = False
                        sender = self.sender[c]
                        link = self.secondmenulink[c]
                        self.makeThirdMenu('string', sender)
                    except IndexError:
                        self.ready = True

            elif self.actmenu == 'thirdmenu':
                if search('/suche/', self.thirdmenulink[c]) is not None:
                    try:
                        if self.tipps == True:
                            self.stopTipps()
                        genre = self.genre[c]
                        link = self.thirdmenulink[c]
                        self.session.openWithCallback(self.selectThirdMenu, TVGenreView, link, genre)
                    except IndexError:
                        pass

                elif search('/tv-tipps/', self.thirdmenulink[c]) is not None:
                    try:
                        if self.tipps == True:
                            self.stopTipps()
                        sparte = self.genre[c]
                        link = self.thirdmenulink[c]
                        self.session.openWithCallback(self.selectThirdMenu, TVTippsView, link, sparte)
                    except IndexError:
                        pass

                else:
                    try:
                        if self.tipps == True:
                            self.stopTipps()
                        link = self.thirdmenulink[c].replace('my.tvspielfilm.de', 'www.tvspielfilm.de')
                        self.session.openWithCallback(self.selectThirdMenu, TVProgrammView, link, False, False)
                    except IndexError:
                        pass

        return

    def makeMenuItem(self, text, link):
        res = ['']
        if self.backcolor == True:
            res.append(MultiContentEntryText(pos=(0, 0), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
        res.append(MultiContentEntryText(pos=(0, 1), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, flags=RT_HALIGN_CENTER, text=text))
        self.mainmenulist.append(res)
        self.mainmenulink.append(self.baseurl + link)

    def makeSecondMenuItem(self, text):
        self.makeSecondMenuItem3(text, '')
        self.sender.append(text)

    def makeSecondMenuItem2(self, text, link):
        self.makeSecondMenuItem3(text, link)
        self.sparte.append(text)

    def makeSecondMenuItem3(self, text, link):
        res = ['']
        if self.backcolor == True:
            res.append(MultiContentEntryText(pos=(0, 0), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
        res.append(MultiContentEntryText(pos=(0, 1), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, flags=RT_HALIGN_CENTER, text=text))
        self.secondmenulist.append(res)
        self.secondmenulink.append(self.baseurl + link)

    def makeMainMenu(self):
        self.makeMenuItem('Heute im TV', '/tv-programm/tv-sender/?page=1')
        self.makeMenuItem('TV-Tipps', '/tv-tipps/')
        self.makeMenuItem('Neu im TV', '/tv-tipps//')
        self.makeMenuItem('TV-Genre', '/tv-genre/')
        self.makeMenuItem('Jetzt im TV', '/tv-programm/sendungen/jetzt.html')
        self.makeMenuItem('Gleich im TV', '/tv-programm/sendungen/?page=1&order=time&time=shortly')
        self.makeMenuItem('20:15 im TV', '/tv-programm/sendungen/abends.html')
        self.makeMenuItem('22:00 im TV', '/tv-programm/sendungen/fernsehprogramm-nachts.html')
        self.makeMenuItem('TV-Programm', '/tv-programm/tv-sender/')
        self.makeMenuItem('TV-Trailer', '/kino/trailer-und-clips/')
        self.makeMenuItem('TV-Bilder', '/bilder/')
        self.makeMenuItem('TV-News', '/news-und-specials/')
        self.makeMenuItem('TV-Blog', '/page/1/')
        self['mainmenu'].l.setList(self.mainmenulist)
        self['mainmenu'].l.setItemHeight(int(30 * skinFactor))
        self.selectMainMenu()

    def makeSecondMenu(self, string, link):
        if fileExists(self.senderhtml):
            output = open(self.senderhtml, 'r').read()
        else:
            output = ''
        self.secondmenulist = []
        self.secondmenulink = []
        self.sender = []
        self.sparte = []
        if search('/tv-sender/', link) is not None:
            startpos = output.find('<option value="" label="Alle Sender">Alle Sender</option>')
            endpos = output.find('<div class="button-toggle">')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
            bereich = sub('verschl\xc3\xbcsselte ', '', bereich)
            bereich = sub(' .deutschspr..', '', bereich)
            bereich = sub('Spartensender ARD', 'Digitale ARD', bereich)
            bereich = sub('Meine Lieblingssender', 'Lieblingssender', bereich)
            name = re.findall('<optgroup label="(.*?)">', bereich)
            idx = 0
            for x in name:
                idx += 1

            for i in range(idx):
                try:
                    if name[i] == 'Lieblingssender':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Hauptsender':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Dritte Programme':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Digitale ARD & ZDF':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Sky Cinema':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Sky 3D HD':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Sky Sport':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Sky Entertainment':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Sky Select':
                        self.makeSecondMenuItem(name[i])
                    elif name[i] == 'Pay-TV':
                        self.makeSecondMenuItem(name[i])
                except IndexError:
                    pass

            for mi in ['Kindersender','Sportsender','Musiksender','News','Ausland','Spartensender','Auslandssender','Regionalsender']:
                self.makeSecondMenuItem(mi)

            self['secondmenu'].l.setList(self.secondmenulist)
            self['secondmenu'].l.setItemHeight(int(30 * skinFactor))
            self['secondmenu'].moveToIndex(0)
            self.selectSecondMenu()
            if self.tipps == True:
                self.hideTipps()
        elif search('/tv-tipps/', link) is not None:
            for mi in ['Spielfilm','Serie','Report','Unterhaltung','Kinder','Sport']:
                self.makeSecondMenuItem2(mi, '/tv-tipps/')
            self['secondmenu'].l.setList(self.secondmenulist)
            self['secondmenu'].l.setItemHeight(int(30 * skinFactor))
            self['secondmenu'].moveToIndex(0)
            self.selectSecondMenu()
        elif search('/tv-genre/', link) is not None:
            for mi in ['Spielfilm','Serie','Report','Unterhaltung','Kinder','Sport']:
                self.makeSecondMenuItem2(mi, '/tv-genre/')
            self['secondmenu'].l.setList(self.secondmenulist)
            self['secondmenu'].l.setItemHeight(int(30 * skinFactor))
            self['secondmenu'].moveToIndex(0)
            self.selectSecondMenu()
        elif search('/trailer-und-clips/', link) is not None:
            self.makeSecondMenuItem2('Kino Neustarts', '/kino/trailer-und-clips/')
            self.makeSecondMenuItem2('Kino Vorschau', '/kino/trailer-und-clips/')
            self.makeSecondMenuItem2('Neueste Trailer', '/kino/kino-vorschau/')
            self.makeSecondMenuItem2('Kino Charts', '/kino/charts/')
            self.makeSecondMenuItem2('DVD Charts', '/kino/dvd/charts/')
            self['secondmenu'].l.setList(self.secondmenulist)
            self['secondmenu'].l.setItemHeight(int(30 * skinFactor))
            self['secondmenu'].moveToIndex(0)
            self.selectSecondMenu()
        elif search('/news-und-specials/', link) is not None:
            self.makeSecondMenuItem3('Interviews & Stories', '/news-und-specials/interviewsundstories/')
            self.makeSecondMenuItem3('Tatort', '/tatort/')
            self.makeSecondMenuItem3('Kids TV', '/kids-tv/')
            self.makeSecondMenuItem3('Playboy Girl', '/news-und-specials/playboy/')
            self['secondmenu'].l.setList(self.secondmenulist)
            self['secondmenu'].l.setItemHeight(int(30 * skinFactor))
            self['secondmenu'].moveToIndex(0)
            self.selectSecondMenu()
        return

    def makeThirdMenuItem(self, output, start, end):
        startpos = output.find('<optgroup label="%s' % start)
        endpos = output.find('<optgroup label="%s' % end)
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        lnk = re.findall('value="(.*?)">', bereich)
        name = re.findall('<option label="(.*?)"', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                res = ['']
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
                res.append(MultiContentEntryText(pos=(0, 1), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, flags=RT_HALIGN_CENTER, text=name[i]))
                self.thirdmenulist.append(res)
                self.thirdmenulink.append(lnk[i])
            except IndexError:
                pass

        self['thirdmenu'].l.setList(self.thirdmenulist)
        self['thirdmenu'].l.setItemHeight(int(30 * skinFactor))
        self['thirdmenu'].moveToIndex(0)
        self.selectThirdMenu()

    def makeThirdMenuItem2(self, text, genre, link=None, cat='SP'):
        res = ['']
        if self.backcolor == True:
            res.append(MultiContentEntryText(pos=(0, 0), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
        res.append(MultiContentEntryText(pos=(0, 1), size=(int(250 * skinFactor), int(30 * skinFactor)), font=-2, flags=RT_HALIGN_CENTER, text=text))
        self.thirdmenulist.append(res)
        if link == None:
            link = text
        self.thirdmenulink.append(self.baseurl + '/suche/?tab=TV-Sendungen&ext=1&q=&cat[]=' + cat + '&genre' + cat + '=' + link + '&time=day&date=&channel=')
        self.genre.append(genre + ':' + text)

    def makeThirdMenu(self, string, sender):
        if string != None:
            output = open(self.senderhtml, 'r').read()
        self.thirdmenulist = []
        self.thirdmenulink = []
        self.genre = []
        if sender == 'Lieblingssender':
            self.makeThirdMenuItem(output, 'Meine Lieblingssender">', 'Hauptsender">')
        elif sender == 'Hauptsender':
            self.makeThirdMenuItem(output, 'Hauptsender">', 'Dritte Programme">')
        elif sender == 'Dritte Programme':
            self.makeThirdMenuItem(output, 'Dritte Programme">', 'Sportsender">')
        elif sender == 'Kindersender':
            self.makeThirdMenuItem(output, 'Kindersender">', 'Ausland ')
        elif sender == 'Digitale ARD & ZDF':
            self.makeThirdMenuItem(output, 'Spartensender ARD', 'News')
        elif sender == 'Ausland':
            self.makeThirdMenuItem(output, 'Ausland (deutschspr.)">', 'Regionalsender">')
        elif sender == 'Regionalsender':
            self.makeThirdMenuItem(output, 'Regionalsender">', 'Musiksender">')
        elif sender == 'News':
            self.makeThirdMenuItem(output, 'News', 'Kindersender">')
        elif sender == 'Sportsender':
            self.makeThirdMenuItem(output, 'Sportsender">', 'Spartensender ARD')
        elif sender == 'Musiksender':
            self.makeThirdMenuItem(output, 'Musiksender">', 'Spartensender">')
        elif sender == 'Spartensender':
            self.makeThirdMenuItem(output, 'Spartensender">', 'Shopping">')
        elif sender == 'Sky Cinema':
            self.makeThirdMenuItem(output, 'Sky Cinema">', 'Sky Sport">')
        elif sender == 'Sky Sport':
            self.makeThirdMenuItem(output, 'Sky Sport">', 'Sky Sport">')
        elif sender == 'Sky Entertainment':
            self.makeThirdMenuItem(output, 'Sky Entertainment">', 'Blue Movie">')
        elif sender == 'Sky Select':
            self.makeThirdMenuItem(output, 'Sky Select">', 'Pay-TV">')
        elif sender == 'Pay-TV':
            self.makeThirdMenuItem(output, 'Pay-TV">', 'Auslandssender">')
        elif sender == 'Auslandssender':
            self.makeThirdMenuItem(output, 'Auslandssender">', 'alle Sender')
        elif sender == 'Spielfilm':
            self.makeThirdMenuItem2('Alle Genres', sender, '')
            self.makeThirdMenuItem2('Abenteuer', sender)
            self.makeThirdMenuItem2('Action', sender)
            self.makeThirdMenuItem2('Dokumentation', sender)
            self.makeThirdMenuItem2('Drama', sender)
            self.makeThirdMenuItem2('Episodenfilm', sender)
            self.makeThirdMenuItem2('Erotik', sender)
            self.makeThirdMenuItem2('Familie/Kinder', sender, 'Familie%2FKinder')
            self.makeThirdMenuItem2('Fantasy', sender)
            self.makeThirdMenuItem2('Filmkunst', sender)
            self.makeThirdMenuItem2('Heimat', sender)
            self.makeThirdMenuItem2('Historie', sender)
            self.makeThirdMenuItem2('Horror', sender)
            self.makeThirdMenuItem2('Klassiker', sender)
            self.makeThirdMenuItem2('Komödie', sender, 'Kom%C3%B6die')
            self.makeThirdMenuItem2('Kriegsfilm', sender)
            self.makeThirdMenuItem2('Krimi', sender)
            self.makeThirdMenuItem2('Literatur/Theater', sender, 'Literatur%2FTheater')
            self.makeThirdMenuItem2('Love Story', sender, 'Love+Story')
            self.makeThirdMenuItem2('Märchen', sender, 'M%C3%A4rchen')
            self.makeThirdMenuItem2('Musikfilm', sender)
            self.makeThirdMenuItem2('Porträt', sender, 'Portr%C3%A4t')
            self.makeThirdMenuItem2('Road Movie', sender, 'Road+Movie')
            self.makeThirdMenuItem2('SciFi', sender)
            self.makeThirdMenuItem2('Thriller', sender)
            self.makeThirdMenuItem2('Trickfilm', sender)
            self.makeThirdMenuItem2('Western', sender)
            self['thirdmenu'].l.setList(self.thirdmenulist)
            self['thirdmenu'].l.setItemHeight(int(30 * skinFactor))
            self['thirdmenu'].moveToIndex(0)
            self.selectThirdMenu()
        elif sender == 'Serie':
            self.makeThirdMenuItem2('Alle Genres', sender, '', 'SE')
            self.makeThirdMenuItem2('Action', sender, None, 'SE')
            self.makeThirdMenuItem2('Arzt', sender, None, 'SE')
            self.makeThirdMenuItem2('Comedy', sender, None, 'SE')
            self.makeThirdMenuItem2('Daily Soap', sender, 'Daily+Soap', 'SE')
            self.makeThirdMenuItem2('Dokuserie', sender, None, 'SE')
            self.makeThirdMenuItem2('Familienserie', sender, None, 'SE')
            self.makeThirdMenuItem2('Horror', sender, None, 'SE')
            self.makeThirdMenuItem2('Kinder-/Jugend', sender, 'Kinder-%2FJugend', 'SE')
            self.makeThirdMenuItem2('Krimi', sender, None, 'SE')
            self.makeThirdMenuItem2('Science Fiction', sender, 'Science+Fiction', 'SE')
            self.makeThirdMenuItem2('Soap', sender, None, 'SE')
            self.makeThirdMenuItem2('Western', sender, None, 'SE')
            self['thirdmenu'].l.setList(self.thirdmenulist)
            self['thirdmenu'].l.setItemHeight(int(30 * skinFactor))
            self['thirdmenu'].moveToIndex(0)
            self.selectThirdMenu()
        elif sender == 'Report':
            self.makeThirdMenuItem2('Alle Genres', sender, '', 'RE')
            self.makeThirdMenuItem2('Gesellschaft', sender, None, 'RE')
            self.makeThirdMenuItem2('Justiz', sender, None, 'RE')
            self.makeThirdMenuItem2('Magazin', sender, None, 'RE')
            self.makeThirdMenuItem2('Natur', sender, None, 'RE')
            self.makeThirdMenuItem2('Politik', sender, None, 'RE')
            self.makeThirdMenuItem2('Ratgeber', sender, None, 'RE')
            self.makeThirdMenuItem2('Technik', sender, None, 'RE')
            self.makeThirdMenuItem2('Wissenschaft', sender, None, 'RE')
            self['thirdmenu'].l.setList(self.thirdmenulist)
            self['thirdmenu'].l.setItemHeight(int(30 * skinFactor))
            self['thirdmenu'].moveToIndex(0)
            self.selectThirdMenu()
        elif sender == 'Unterhaltung':
            self.makeThirdMenuItem2('Alle Genres', sender, '', 'U')
            self.makeThirdMenuItem2('Comedy', sender, None, 'U')
            self.makeThirdMenuItem2('Familie', sender, None, 'U')
            self.makeThirdMenuItem2('Kultur', sender, None, 'U')
            self.makeThirdMenuItem2('Late Night', sender, 'Late+Night', 'U')
            self.makeThirdMenuItem2('Musik', sender, None, 'U')
            self.makeThirdMenuItem2('Quiz', sender, None, 'U')
            self.makeThirdMenuItem2('Show', sender, None, 'U')
            self.makeThirdMenuItem2('Talk', sender, None, 'U')
            self['thirdmenu'].l.setList(self.thirdmenulist)
            self['thirdmenu'].l.setItemHeight(int(30 * skinFactor))
            self['thirdmenu'].moveToIndex(0)
            self.selectThirdMenu()
        elif sender == 'Kinder':
            self.makeThirdMenuItem2('Alle Genres', sender, '', 'KIN')
            self.makeThirdMenuItem2('Bildung', sender, None, 'KIN')
            self.makeThirdMenuItem2('Magazin', sender, None, 'KIN')
            self.makeThirdMenuItem2('Reportage', sender, None, 'KIN')
            self.makeThirdMenuItem2('Serie', sender, None, 'KIN')
            self.makeThirdMenuItem2('Show', sender, None, 'KIN')
            self['thirdmenu'].l.setList(self.thirdmenulist)
            self['thirdmenu'].l.setItemHeight(int(30 * skinFactor))
            self['thirdmenu'].moveToIndex(0)
            self.selectThirdMenu()
        elif sender == 'Sport':
            self.makeThirdMenuItem2('Alle Genres', sender, '', 'SPO')
            self.makeThirdMenuItem2('Basketball', sender, None, 'SPO')
            self.makeThirdMenuItem2('Billard', sender, None, 'SPO')
            self.makeThirdMenuItem2('Boxen', sender, None, 'SPO')
            self.makeThirdMenuItem2('Formel 1', sender, 'Formel+1', 'SPO')
            self.makeThirdMenuItem2('Funsport', sender, None, 'SPO')
            self.makeThirdMenuItem2('Fußball', sender, 'Fu%C3%9Fball', 'SPO')
            self.makeThirdMenuItem2('Golf', sender, None, 'SPO')
            self.makeThirdMenuItem2('Handball', sender, None, 'SPO')
            self.makeThirdMenuItem2('Kampfsport', sender, None, 'SPO')
            self.makeThirdMenuItem2('Leichtathletik', sender, None, 'SPO')
            self.makeThirdMenuItem2('Motorsport', sender, None, 'SPO')
            self.makeThirdMenuItem2('Poker', sender, None, 'SPO')
            self.makeThirdMenuItem2('Radsport', sender, None, 'SPO')
            self.makeThirdMenuItem2('Tennis', sender, None, 'SPO')
            self.makeThirdMenuItem2('US Sport', sender, 'US+Sport', 'SPO')
            self.makeThirdMenuItem2('Wassersport', sender, None, 'SPO')
            self.makeThirdMenuItem2('Wintersport', sender, None, 'SPO')
            self['thirdmenu'].l.setList(self.thirdmenulist)
            self['thirdmenu'].l.setItemHeight(int(30 * skinFactor))
            self['thirdmenu'].moveToIndex(0)
            self.selectThirdMenu()
        return

    def selectMainMenu(self):
        self.actmenu = 'mainmenu'
        self['mainmenu'].show()
        self['secondmenu'].hide()
        self['thirdmenu'].hide()
        self['mainmenu'].selectionEnabled(1)
        self['secondmenu'].selectionEnabled(0)
        self['thirdmenu'].selectionEnabled(0)
        if self.tipps == True:
            if self.hidetipps == False:
                self.showTipps()
            else:
                self['label2'].show()
                self['green'].show()
        self.ready = True

    def selectSecondMenu(self):
        if len(self.secondmenulist) > 0:
            self.actmenu = 'secondmenu'
            self['mainmenu'].hide()
            self['secondmenu'].show()
            self['thirdmenu'].hide()
            self['mainmenu'].selectionEnabled(0)
            self['secondmenu'].selectionEnabled(1)
            self['thirdmenu'].selectionEnabled(0)
            if self.tipps == True and self.hidetipps == False:
                self.showTipps()
        self.ready = True

    def selectThirdMenu(self):
        if len(self.thirdmenulist) > 0:
            self.actmenu = 'thirdmenu'
            self['mainmenu'].hide()
            self['secondmenu'].hide()
            self['thirdmenu'].show()
            self['mainmenu'].selectionEnabled(0)
            self['secondmenu'].selectionEnabled(0)
            self['thirdmenu'].selectionEnabled(1)
            if self.tipps == True:
                self.hideTipps()
        self.ready = True

    def green(self):
        if self.tipps == True and self.ready == True:
            if self.hidetipps == False:
                self.TagesTipps.ok()
            elif self.actmenu == 'mainmenu' or self.actmenu == 'secondmenu' and self.hidetipps == True:
                self.startTipps()

    def hideTipps(self):
        self.TagesTipps.hide()
        self['label2'].hide()
        self['green'].hide()
        self.hidetipps = True

    def showTipps(self):
        self.TagesTipps.show()
        self['label2'].show()
        self['green'].show()
        self.hidetipps = False

    def startTipps(self):
        self.TagesTipps.start()
        self.TagesTipps.show()
        self.hidetipps = False

    def stopTipps(self):
        self.TagesTipps.stop()
        self.TagesTipps.hide()
        self.hidetipps = True

    def up(self):
        self[self.actmenu].up()

    def down(self):
        self[self.actmenu].down()

    def leftUp(self):
        self[self.actmenu].pageUp()

    def rightDown(self):
        self[self.actmenu].pageDown()

    def downloadError(self, output):
        try:
            error = output.getErrorMessage()
            self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
            self.ready = True
        except AttributeError:
            self.ready = True

    def checkMainMenu(self):
        if fileExists(self.servicefile):
            self.makeMainMenu()
        else:
            self.session.openWithCallback(self.returnFirstRun, makeServiceFile)

    def downloadSender(self, link):
        if self.MeinTVS == True:
            try:
                response = self.opener.open(link, timeout=60)
                data = response.read()
                f = open(self.senderhtml, 'wb')
                f.write(data)
                f.close()
                response.close()
            except HTTPException as e:
                self.error = 'HTTP Exception Error ' + str(e)
            except HTTPError as e:
                self.error = 'HTTP Error: ' + str(e.code)
            except URLError as e:
                self.error = 'URL Error: ' + str(e.reason)
            except socket.error as e:
                self.error = 'Socket Error: ' + str(e)
            except AttributeError as e:
                self.error = 'Attribute Error: ' + str(e.message)

            if self.error == False:
                self.makeSecondMenu('string', link)
            else:
                self.makeErrorTimer = eTimer()
                self.makeErrorTimer.callback.append(self.displayError)
                self.makeErrorTimer.start(500, True)
        else:
            downloadPage(six.ensure_binary(link), self.senderhtml).addCallback(self.makeSecondMenu, link).addErrback(self.downloadError)

    def getIndex(self, list):
        return list.getSelectedIndex()

    def red(self):
        if self.ready == True:
            if self.tipps == True:
                self.stopTipps()
            self.session.openWithCallback(self.returnRed, MessageBox, '\nImportiere TV Spielfilm Sender?', MessageBox.TYPE_YESNO)

    def returnRed(self, answer):
        if answer is True:
            if fileExists(self.servicefile):
                os.remove(self.servicefile)
            self.session.openWithCallback(self.returnServiceFile, makeServiceFile)

    def returnServiceFile(self, result):
        if result == True:
            self.selectMainMenu()
        else:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
            self.close()

    def returnFirstRun(self, result):
        if result == True:
            self.checkMainMenu()
        else:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
            self.close()

    def config(self):
        if self.ready == True:
            if self.tipps == True:
                self.stopTipps()
                self.session.deleteDialog(self.TagesTipps)
            if fileExists(self.senderhtml):
                os.remove(self.senderhtml)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.session.openWithCallback(self.closeconf, tvsConfig)

    def closeconf(self):
        if fileExists(self.picfile):
            os.remove(self.picfile)
        if fileExists(self.pic1):
            os.remove(self.pic1)
        if fileExists(self.pic2):
            os.remove(self.pic2)
        if fileExists(self.pic3):
            os.remove(self.pic3)
        if fileExists(self.pic4):
            os.remove(self.pic4)
        if fileExists(self.pic5):
            os.remove(self.pic5)
        if fileExists(self.pic6):
            os.remove(self.pic6)
        if fileExists(self.senderhtml):
            os.remove(self.senderhtml)
        if fileExists(self.localhtml):
            os.remove(self.localhtml)
        if fileExists(self.localhtml2):
            os.remove(self.localhtml2)
        self.close()

    def zap(self):
        if self.ready == True:
            if self.tipps == True:
                self.stopTipps()
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.actmenu == 'mainmenu':
            if self.tipps == True:
                self.TagesTipps.stop()
                self.session.deleteDialog(self.TagesTipps)
            if fileExists(self.picfile):
                os.remove(self.picfile)
            if fileExists(self.pic1):
                os.remove(self.pic1)
            if fileExists(self.pic2):
                os.remove(self.pic2)
            if fileExists(self.pic3):
                os.remove(self.pic3)
            if fileExists(self.pic4):
                os.remove(self.pic4)
            if fileExists(self.pic5):
                os.remove(self.pic5)
            if fileExists(self.pic6):
                os.remove(self.pic6)
            if fileExists(self.senderhtml):
                os.remove(self.senderhtml)
            if fileExists(self.localhtml):
                os.remove(self.localhtml)
            if fileExists(self.localhtml2):
                os.remove(self.localhtml2)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.close()
        elif self.actmenu == 'secondmenu':
            self.selectMainMenu()
        elif self.actmenu == 'thirdmenu':
            self.selectSecondMenu()


class makeServiceFile(Screen):
    skin = '\n\t\t\t<screen position="center,180" size="565,195" backgroundColor="#20000000" title="Import TV Spielfilm Sender: TV Bouquet Auswahl">\n\t\t\t\t<ePixmap position="0,0" size="565,50" pixmap="' + TVSPNG + '" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="list" position="10,60" size="545,125" scrollbarMode="showOnDemand" zPosition="1" />\n\t\t\t</screen>'
    def __init__(self, session):
        self.skin = makeServiceFile.skin
        self.session = session
        Screen.__init__(self, session)
        self['list'] = MenuList([])
        self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok,
         'cancel': self.exit}, -1)
        self.servicefile = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/service.references'
        self.ready = False
        self.bouquetsTimer = eTimer()
        self.bouquetsTimer.callback.append(self.getBouquets)
        self.bouquetsTimer.start(500, True)

    def getBouquets(self):
        bouquets = []
        if config.usage.multibouquet.value:
            bouquet_rootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
        else:
            bouquet_rootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
        bouquet_root = eServiceReference(bouquet_rootstr)
        serviceHandler = eServiceCenter.getInstance()
        if config.usage.multibouquet.value:
            list = serviceHandler.list(bouquet_root)
            if list:
                while True:
                    s = list.getNext()
                    if not s.valid():
                        break
                    if s.flags & eServiceReference.isDirectory:
                        info = serviceHandler.info(s)
                        if info:
                            bouquets.append((info.getName(s), s))

        else:
            info = serviceHandler.info(bouquet_root)
            if info:
                bouquets.append((info.getName(bouquet_root), bouquet_root))
        entrys = [ (x[0], x[1]) for x in bouquets ]
        self['list'].l.setList(entrys)
        try:
            self['list'].l.setFont(gFont('Regular', 20))
        except (AttributeError, TypeError):
            pass

        self.ready = True

    def ok(self):
        if self.ready == True:
            self.ready = False
            try:
                bouquet = self.getCurrent()
                from Components.Sources.ServiceList import ServiceList
                slist = ServiceList(bouquet, validate_commands=False)
                services = slist.getServicesAsList(format='S')
                search = ['IBDCTSERNX']
                search.extend([ (service, 0, -1) for service in services ])
                self.epgcache = eEPGCache.getInstance()
                events = self.epgcache.lookupEvent(search)
                eventlist = []
                for eventinfo in events:
                    eventlist.append((eventinfo[8], eventinfo[7]))

            except Exception:
                bouquet = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
                bouquet = eServiceReference(bouquet)
                from Components.Sources.ServiceList import ServiceList
                slist = ServiceList(bouquet, validate_commands=False)
                services = slist.getServicesAsList(format='S')
                search = ['IBDCTSERNX']
                search.extend([ (service, 0, -1) for service in services ])
                self.epgcache = eEPGCache.getInstance()
                events = self.epgcache.lookupEvent(search)
                eventlist = []
                for eventinfo in events:
                    eventlist.append((eventinfo[8], eventinfo[7]))

            data = str(eventlist)
            if six.PY2:
                data = data.decode('latin1').encode('utf-8')
            data = sub('[[]', '', data)
            data = sub('[)][]]', '', data)
            data = sub('[(]', '', data)
            data = sub('[/]', ' ', data)
            data = sub(':0:0:0:.*?[)], ', ':0:0:0:\n', data)
            data = sub(':0:0:0::[a-zA-Z0-9_-]+', ':0:0:0:', data)
            data = sub("'", '', data)
            data = sub('HITRADIO.*?\n', '', data)
            data = transCHANNEL(data)
            f = open(self.servicefile, 'a')
            f.write(data)
            f.close()
            fnew = open(self.servicefile + '.new', 'w')
            newdata = ''
            count = 0
            search = re.compile(' [a-z0-9-]+ ').search
            for line in open(self.servicefile):
                if search(line):
                    line = ''
                elif 'nickcc' in line:
                    line = line.replace('nickcc', 'nick') + line.replace('nickcc', 'cc')
                    count += 1
                elif 'vivacc' in line:
                    line = line.replace('vivacc', 'viva') + line.replace('vivacc', 'cc')
                    count += 1
                line = line.strip()
                if not line == '' and ',' not in line and '/' not in line and ' 1:64:' not in line and '#' + line[0:5] not in newdata:
                    count += 1
                    fnew.write(line)
                    fnew.write(os.linesep)
                    newdata = newdata + '#' + str(line[0:5])

            f.close()
            fnew.close()
            os.rename(self.servicefile + '.new', self.servicefile)
            self.ready = True
            if newdata == '':
                self.session.openWithCallback(self.noBouquet, MessageBox, '\nKeine TV Spielfilm Sender gefunden.\nBitte waehlen Sie ein anderes TV Bouquet.', MessageBox.TYPE_YESNO)
            else:
                self.session.openWithCallback(self.otherBouquet, MessageBox, '\nInsgesamt %s TV Spielfilm Sender importiert.\nMoechten Sie ein weiteres TV Bouquet importieren?' % str(count), MessageBox.TYPE_YESNO)

    def otherBouquet(self, answer):
        if answer is True:
            self.bouquetsTimer.callback.append(self.getBouquets)
        else:
            self.close(True)

    def noBouquet(self, answer):
        if answer is True:
            self.bouquetsTimer.callback.append(self.getBouquets)
        else:
            if fileExists(self.servicefile):
                os.remove(self.servicefile)
            self.close(False)

    def getCurrent(self):
        cur = self['list'].getCurrent()
        return cur and cur[1]

    def up(self):
        if self.ready == True:
            self['list'].up()

    def down(self):
        if self.ready == True:
            self['list'].down()

    def exit(self):
        if self.ready == True:
            self.close(False)


class getNumber(Screen):
    skin = """
    <screen name="getNumber" position="center,center" size="175,70" backgroundColor="#000000" flags="wfNoBorder" title=" ">
        <widget name="number" position="0,0" size="175,70" font="Regular;40" halign="center" valign="center" transparent="1" zPosition="1"/>
    </screen>"""

    def __init__(self, session, number):
        self.skin = getNumber.skin
        self.session = session
        Screen.__init__(self, session)
        self.field = str(number)
        self['number'] = Label(self.field)
        self['actions'] = NumberActionMap(['SetupActions'], {'cancel': self.quit,
         'ok': self.keyOK,
         '1': self.keyNumber,
         '2': self.keyNumber,
         '3': self.keyNumber,
         '4': self.keyNumber,
         '5': self.keyNumber,
         '6': self.keyNumber,
         '7': self.keyNumber,
         '8': self.keyNumber,
         '9': self.keyNumber,
         '0': self.keyNumber})
        self.Timer = eTimer()
        self.Timer.callback.append(self.keyOK)
        self.Timer.start(2500, True)

    def keyNumber(self, number):
        self.Timer.start(2000, True)
        self.field = self.field + str(number)
        self['number'].setText(self.field)
        if len(self.field) >= 2:
            self.keyOK()

    def keyOK(self):
        self.Timer.stop()
        self.close(int(self['number'].getText()))

    def quit(self):
        self.Timer.stop()
        self.close(0)


class gotoPageMenu(tvAllScreen):
    skin = """
    <screen name="gotoPageMenu" position="center,center" size="436,560" title=" ">
        <widget name="pagemenu" position="10,10" size="416,540" scrollbarMode="showNever" zPosition="1" />
    </screen>"""

    def __init__(self, session, count, maxpages):
        self.skin = gotoPageMenu.skin
        self.session = session
        tvAllScreen.__init__(self, session)
        self.localhtml = '/tmp/tvspielfilm.html'
        self.hideflag = True
        self.index = count - 1
        self.maxpages = maxpages
        self.pagenumber = []
        self.pagemenulist = []
        self['pagemenu'] = ItemList([])
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
         'DirectionActions',
         'ColorActions'], {'ok': self.ok,
         'cancel': self.exit,
         'down': self.down,
         'up': self.up,
         'blue': self.hideScreen,
         '0': self.gotoPage,
         '1': self.gotoPage,
         '2': self.gotoPage,
         '3': self.gotoPage,
         '4': self.gotoPage,
         '5': self.gotoPage,
         '6': self.gotoPage,
         '7': self.gotoPage,
         '8': self.gotoPage,
         '9': self.gotoPage}, -1)
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        self.makeMenuTimer = eTimer()
        self.makeMenuTimer.callback.append(self.makePageMenu)
        self.makeMenuTimer.start(500, True)

    def makePageMenu(self):
        self.setTitle('Senderliste')
        output = open(self.localhtml, 'r').read()
        startpos = output.find('label="Alle Sender">Alle Sender</option>')
        if config.plugins.tvspielfilm.meintvs.value == 'yes':
            endpos = output.find('<optgroup label="Hauptsender">')
        else:
            endpos = output.find('<optgroup label="alle Sender alphabetisch">')
        bereich = output[startpos:endpos]
        bereich = bereich.lower()
        sender = re.findall(' value=".*?,(.*?).html">', bereich)
        count = 0
        page = 1
        while page <= self.maxpages:
            res = ['']
            if self.backcolor == True:
                res.append(MultiContentEntryText(pos=(0, 0), size=(416, 36), font=-1, backcolor_sel=self.back_color, text=''))
            res.append(MultiContentEntryText(pos=(0, 5), size=(28, 36), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT, text=str(page)))
            try:
                png1 = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % sender[count]
                if fileExists(png1):
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(34, 0), size=(59, 36), png=loadPNG(png1)))
            except IndexError:
                pass

            count += 1
            try:
                png2 = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % sender[count]
                if fileExists(png2):
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(93, 0), size=(59, 36), png=loadPNG(png2)))
            except IndexError:
                pass

            count += 1
            try:
                png3 = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % sender[count]
                if fileExists(png3):
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(152, 0), size=(59, 36), png=loadPNG(png3)))
            except IndexError:
                pass

            count += 1
            try:
                png4 = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % sender[count]
                if fileExists(png4):
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(211, 0), size=(59, 36), png=loadPNG(png4)))
            except IndexError:
                pass

            count += 1
            try:
                png5 = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % sender[count]
                if fileExists(png5):
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(270, 0), size=(59, 36), png=loadPNG(png5)))
            except IndexError:
                pass

            count += 1
            try:
                png6 = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % sender[count]
                if fileExists(png6):
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(329, 0), size=(59, 36), png=loadPNG(png6)))
            except IndexError:
                pass

            count += 1
            self.pagemenulist.append(res)
            self.pagenumber.append(str(page))
            page += 1

        self['pagemenu'].l.setItemHeight(36)
        self['pagemenu'].l.setList(self.pagemenulist)
        self['pagemenu'].moveToIndex(self.index)

    def ok(self):
        try:
            c = self.getIndex(self['pagemenu'])
            number = int(self.pagenumber[c])
            self.close(number)
        except IndexError:
            pass

    def gotoPage(self, number):
        self.session.openWithCallback(self.numberEntered, getNumber, number)

    def numberEntered(self, number):
        if number is None or number == 0:
            pass
        elif number >= 29:
            number = 29
        self.close(number)
        return

    def getIndex(self, list):
        return list.getSelectedIndex()

    def down(self):
        self['pagemenu'].down()

    def up(self):
        self['pagemenu'].up()

    def download(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close(0)


class tvTipps(tvAllScreen):
    skin = """
        <screen position="{position}" size="740,270" flags="wfNoBorder" title=" ">
        <widget name="picture" position="0,0" size="387,270" alphatest="blend" zPosition="1" />
        <widget name="elabel" position="387,0" size="{size},150" font="Regular;18" backgroundColor="#FF000000" zPosition="1" />
        <widget name="elabel2" position="{position2},0" size="{size2}" font="Regular;18" backgroundColor="#000000" zPosition="1" />
        <widget name="elabel3" position="387,150" size="353,125" font="Regular;18" backgroundColor="#FFFFFF" zPosition="1" />
        <widget name="label" position="402,151" size="288,24" font="Regular;20" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" zPosition="2" />
        <widget name="label2" position="402,176" size="288,48" font="Regular;22" foregroundColor="#{color}" backgroundColor="#FFFFFF" halign="left" zPosition="2" />
        <widget name="label3" position="402,225" size="328,42" font="Regular;18" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" zPosition="2" />
        <widget name="thumb" position="695,160" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/rating small1HD.png" alphatest="blend" zPosition="2" />
        <widget name="label4" position="40,220" size="100,25" font="Regular;22" foregroundColor="#FFFFFF" backgroundColor="#CD006C" halign="center" valign="center" zPosition="2" />
        <widget name="label5" position="40,245" size="100,25" font="Regular;18" foregroundColor="#CD006C" backgroundColor="#FFFFFF" halign="center" valign="center" zPosition="2" />
        </screen>"""

    def __init__(self, session):
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            color = '4176B6'
        else:
            color = str(config.plugins.tvspielfilm.color.value)
            color = sub('0x00', '', color)
        deskWidth = getDesktop(0).size().width()
        if deskWidth >= 1280:
            position = '0,450'
            size = '98'
            position2 = '485'
            size2 = '20,150'
        else:
            position = '0,306'
            size = '0'
            position2 = '387'
            size2 = '0,0'
        self.dict = {'position': position,
         'size': size,
         'position2': position2,
         'size2': size2,
         'color': color}
        self.skin = applySkinVars(tvTipps.skin, self.dict)
        tvAllScreen.__init__(self, session)
        self.baseurl = 'http://www.tvspielfilm.de'
        self.pic1 = '/tmp/tvspielfilm1.jpg'
        self.pic2 = '/tmp/tvspielfilm2.jpg'
        self.pic3 = '/tmp/tvspielfilm3.jpg'
        self.pic4 = '/tmp/tvspielfilm4.jpg'
        self.pic5 = '/tmp/tvspielfilm5.jpg'
        self.max = 6
        self.count = 0
        self.ready = False
        self.hideflag = True
        self.infolink = ''
        self.tippsinfo = []
        self.tippslink = []
        self.tippschannel = []
        self.tippspicture = []
        self['picture'] = Pixmap()
        self['thumb'] = Pixmap()
        self['picture'].hide()
        self['thumb'].hide()
        self['label'] = Label('')
        self['label2'] = Label('')
        self['label3'] = Label('')
        self['label4'] = Label('')
        self['label5'] = Label('')
        self['elabel'] = Label('')
        self['elabel2'] = Label('')
        self['elabel3'] = Label('')
        self['label'].hide()
        self['label2'].hide()
        self['label3'].hide()
        self['label4'].hide()
        self['label5'].hide()
        self['elabel'].hide()
        self['elabel2'].hide()
        self['elabel3'].hide()
        self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok,
         'cancel': self.exit}, -1)
        self.onLayoutFinish.append(self.start)

    def start(self):
        self.getTippsTimer = eTimer()
        self.getTippsTimer.callback.append(self.downloadFirst(self.baseurl, self.getTagesTipps))
        self.getTippsTimer.start(500, True)
        self.getNextTimer = eTimer()
        self.getNextTimer.callback.append(self.nextTipp)
        self.getNextTimer.start(5000, False)

    def stop(self):
        self.getTippsTimer.stop()
        self.getNextTimer.stop()
        if self.nextTipp in self.getNextTimer.callback:
            self.getNextTimer.callback.remove(self.nextTipp)
        self.hide()

    def getTagesTipps(self, output):
        self.ready = False
        output = six.ensure_str(output)
        startpos = output.find('teaser-top">')
        endpos = output.find('<div class="block-rotation">')
        bereich = output[startpos:endpos]
        bereich = re.sub('<ul.*?</ul>', '', bereich, flags=re.S)
        if search('/news-und-specials/', bereich) is not None:
            bereich = re.sub('<a href="https://my.tvspielfilm.de/news-und-specials/.*?</a>', '', bereich, flags=re.S)
            bereich = re.sub('<a href="https://www.tvspielfilm.de/news-und-specials/.*?</a>', '', bereich, flags=re.S)
        if search('pdf.tvspielfilm.de', bereich) is not None:
            bereich = re.sub('<a href="https://pdf.tvspielfilm.de/.*?</a>', '', bereich, flags=re.S)
        self.tippspicture = re.findall('<img src="(.*?)"', bereich, flags=re.S)
        try:
            self.download(self.tippspicture[0], self.getPic)
        except IndexError:
            pass

        self.tippschannel = re.findall('<span class="subline .*?">(.*?)</span>', bereich)
        try:
            parts = self.tippschannel[0].split(' | ')
            times = parts[1]
            channel = parts[2]
            channel = shortenChannel(channel)
            self['label4'].setText(times)
            self['label4'].show()
            self['label5'].setText(channel[0:10])
            self['label5'].show()
        except IndexError:
            self['label4'].hide()
            self['label5'].hide()

        self.tippsinfo = re.findall('<span class="headline">(.*?)</span>', bereich)
        self.tippslink = re.findall('<a href="(.*?)" target', bereich)
        try:
            self.infolink = self.tippslink[0]
            tipp = 'Tipp des Tages'
            titel = self.tippsinfo[0]
            text = self.tippschannel[0]
        except IndexError:
            tipp = ''
            titel = ''
            text = ''

        self['label'].setText(tipp)
        self['label2'].setText(titel)
        self['label3'].setText(text)
        self['label'].show()
        self['label2'].show()
        self['label3'].show()
        self['elabel'].show()
        self['elabel2'].show()
        self['elabel3'].show()
        self['thumb'].show()
        try:
            self.download(self.tippspicture[1], self.getPic2)
            self.download(self.tippspicture[2], self.getPic3)
            self.download(self.tippspicture[3], self.getPic4)
            self.download(self.tippspicture[4], self.getPic5)
        except IndexError:
            pass

        self.ready = True
        return

    def ok(self):
        if self.ready == True and search('/tv-programm/sendung/', self.infolink) is not None:
            self.hide()
            self.getNextTimer.stop()
            self.session.openWithCallback(self.returnInfo, TVProgrammView, self.infolink, False, True)
        return

    def returnInfo(self):
        self.show()
        self.getNextTimer.start(5000, False)

    def nextTipp(self):
        if self.ready == True:
            self.count += 1
            if self.count < self.max:
                pic = '/tmp/tvspielfilm%s.jpg' % str(self.count + 1)
                if fileExists(pic):
                    self.showPic(pic)
                try:
                    self.infolink = self.tippslink[self.count]
                    tipp = 'Tipp des Tages'
                    titel = self.tippsinfo[self.count]
                    text = self.tippschannel[self.count]
                except IndexError:
                    tipp = ''
                    titel = ''
                    text = ''

                self['label'].setText(tipp)
                self['label2'].setText(titel)
                self['label3'].setText(text)
                try:
                    parts = self.tippschannel[self.count].split(' | ')
                    times = parts[1]
                    channel = parts[2]
                    channel = shortenChannel(channel)
                    self['label4'].setText(times)
                    self['label4'].show()
                    self['label5'].setText(channel[0:10])
                    self['label5'].show()
                except IndexError:
                    self['label4'].hide()
                    self['label5'].hide()

            else:
                self.count = 0
                pic = '/tmp/tvspielfilm1.jpg'
                if fileExists(pic):
                    self.showPic(pic)
                try:
                    self.infolink = self.tippslink[self.count]
                    tipp = 'Tipp des Tages'
                    titel = self.tippsinfo[self.count]
                    text = self.tippschannel[self.count]
                except IndexError:
                    tipp = ''
                    titel = ''
                    text = ''

                self['label'].setText(tipp)
                self['label2'].setText(titel)
                self['label3'].setText(text)
                try:
                    parts = self.tippschannel[self.count].split(' | ')
                    times = parts[1]
                    channel = parts[2]
                    channel = shortenChannel(channel)
                    self['label4'].setText(times)
                    self['label4'].show()
                    self['label5'].setText(channel[0:10])
                    self['label5'].show()
                except IndexError:
                    self['label4'].hide()
                    self['label5'].hide()

    def getPic(self, output):
        f = open(self.pic1, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.pic1)

    def showPic(self, picture):
        currPic = loadPic(picture, 387, 270, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
            self['picture'].show()
        return

    def getPic2(self, output):
        f = open(self.pic2, 'wb')
        f.write(output)
        f.close()

    def getPic3(self, output):
        f = open(self.pic3, 'wb')
        f.write(output)
        f.close()

    def getPic4(self, output):
        f = open(self.pic4, 'wb')
        f.write(output)
        f.close()

    def getPic5(self, output):
        f = open(self.pic5, 'wb')
        f.write(output)
        f.close()

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self.ready = True

    def downloadFirst(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadFirstError)

    def downloadFirstError(self, output):
        try:
            error = output.getErrorMessage()
            self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
        except AttributeError:
            self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar.', MessageBox.TYPE_ERROR)

        self.ready = True

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class tvsConfig(ConfigListScreen, tvAllScreen):
    skin = """
        <screen name="tvsConfig" position="center,center" size="545,500" backgroundColor="#20000000" title="TV Spielfilm Setup">
            <ePixmap position="0,0" size="545,50" pixmap="{picpath}tvspielfilmHD.png" alphatest="blend" zPosition="1" />
            <ePixmap position="10,59" size="525,1" pixmap="{picpath}setup/seperator.png" alphatest="off" zPosition="1" />
            <widget name="config" position="10,60" size="525,100" itemHeight="25" scrollbarMode="showOnDemand" zPosition="1" />
            <ePixmap position="10,161" size="525,1" pixmap="{picpath}setup/seperator.png" alphatest="off" zPosition="1" />
            <ePixmap position="125,171" size="18,18" pixmap="{picpath}buttons/green.png" alphatest="blend" zPosition="1" />
            <ePixmap position="350,171" size="18,18" pixmap="{picpath}buttons/red.png" alphatest="blend" zPosition="1" />
            <eLabel position="150,170" size="180,20" font="Regular;18" halign="left" text="Speichern" transparent="1" zPosition="1" />
            <eLabel position="375,170" size="180,20" font="Regular;18" halign="left" text="Abbrechen" transparent="1" zPosition="1" />
            <widget name="plugin" position="10,200" size="525,295" alphatest="blend" zPosition="1" />
        </screen>"""

    def __init__(self, session):
        tvAllScreen.__init__(self, session, tvsConfig.skin)
        self.password = config.plugins.tvspielfilm.password.value
        self.encrypt = config.plugins.tvspielfilm.encrypt.value
        self['plugin'] = Pixmap()
        list = []
        #list.append(getConfigListEntry('Plugin Gr\xc3\xb6\xc3\x9fe:', config.plugins.tvspielfilm.plugin_size))
        #list.append(getConfigListEntry('Plugin Position:', config.plugins.tvspielfilm.position))
        list.append(getConfigListEntry('Plugin Schriftgroesse:', config.plugins.tvspielfilm.font_size))
        #list.append(getConfigListEntry('Plugin Sans Serif Schrift:', config.plugins.tvspielfilm.font))
        list.append(getConfigListEntry('Benutze Mein TV SPIELFILM:', config.plugins.tvspielfilm.meintvs))
        list.append(getConfigListEntry('Login (E-mail):', config.plugins.tvspielfilm.login))
        list.append(getConfigListEntry('Passwort:', config.plugins.tvspielfilm.password))
        list.append(getConfigListEntry('Passwort Verschluesselung:', config.plugins.tvspielfilm.encrypt))
        list.append(getConfigListEntry('Benutze eigene Picons (100x60):', config.plugins.tvspielfilm.picon))
        self.foldername = getConfigListEntry('Picon Ordner:', config.plugins.tvspielfilm.piconfolder)
        list.append(self.foldername)
        list.append(getConfigListEntry('Farbe Listen Auswahl:', config.plugins.tvspielfilm.color))
        list.append(getConfigListEntry('Zeige Tipp des Tages:', config.plugins.tvspielfilm.tipps))
        list.append(getConfigListEntry('Starte Heute im TV mit:', config.plugins.tvspielfilm.primetime))
        list.append(getConfigListEntry('Starte TVS EventView mit:', config.plugins.tvspielfilm.eventview))
        list.append(getConfigListEntry('Beende TVS Jetzt nach dem Zappen:', config.plugins.tvspielfilm.zapexit))
        list.append(getConfigListEntry('Zeige Genre/Episode/Jahr am Ende des Titels:', config.plugins.tvspielfilm.genreinfo))
        list.append(getConfigListEntry('Max. Seiten TV-Suche:', config.plugins.tvspielfilm.maxsearch))
        list.append(getConfigListEntry('Max. Seiten TV-Genre Suche:', config.plugins.tvspielfilm.maxgenre))
        list.append(getConfigListEntry('Benutze AutoTimer Plugin:', config.plugins.tvspielfilm.autotimer))
        ConfigListScreen.__init__(self, list, on_change=self.UpdateComponents)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.save,
         'cancel': self.cancel,
         'red': self.cancel,
         'green': self.save}, -1)
        self.onLayoutFinish.append(self.UpdateComponents)

    def UpdateComponents(self):
        png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/setup/' + str(config.plugins.tvspielfilm.color.value) + '.png'
        if fileExists(png):
            self['plugin'].instance.setPixmapFromFile(png)
        current = self['config'].getCurrent()
        if current == self.foldername:
            self.session.openWithCallback(self.folderSelected, FolderSelection, config.plugins.tvspielfilm.piconfolder.value)

    def folderSelected(self, folder):
        if folder is not None:
            config.plugins.tvspielfilm.piconfolder.value = folder
            config.plugins.tvspielfilm.piconfolder.save()
        return

    def save(self):
        #config.plugins.tvspielfilm.plugin_size.save()
        #config.plugins.tvspielfilm.position.save()
        config.plugins.tvspielfilm.font_size.save()
        #config.plugins.tvspielfilm.font.save()
        config.plugins.tvspielfilm.meintvs.save()
        config.plugins.tvspielfilm.login.save()
        if config.plugins.tvspielfilm.password.value != self.password:
            if config.plugins.tvspielfilm.encrypt.value == 'yes':
                password = b64encode(str(config.plugins.tvspielfilm.password.value))
                config.plugins.tvspielfilm.password.value = password
            config.plugins.tvspielfilm.password.save()
        elif config.plugins.tvspielfilm.encrypt.value != self.encrypt:
            if self.encrypt == 'yes':
                try:
                    password = b64decode(str(config.plugins.tvspielfilm.password.value))
                    config.plugins.tvspielfilm.password.value = password
                except TypeError:
                    pass

            else:
                password = b64encode(str(config.plugins.tvspielfilm.password.value))
                config.plugins.tvspielfilm.password.value = password
            config.plugins.tvspielfilm.password.save()
            config.plugins.tvspielfilm.encrypt.save()
        config.plugins.tvspielfilm.picon.save()
        config.plugins.tvspielfilm.piconfolder.save()
        config.plugins.tvspielfilm.color.save()
        config.plugins.tvspielfilm.tipps.save()
        config.plugins.tvspielfilm.primetime.save()
        config.plugins.tvspielfilm.eventview.save()
        config.plugins.tvspielfilm.zapexit.save()
        config.plugins.tvspielfilm.genreinfo.save()
        config.plugins.tvspielfilm.maxsearch.save()
        config.plugins.tvspielfilm.maxgenre.save()
        config.plugins.tvspielfilm.autotimer.save()
        configfile.save()
        self.exit()

    def cancel(self):
        for x in self['config'].list:
            x[1].cancel()

        self.exit()

    def exit(self):
        if config.plugins.tvspielfilm.meintvs.value == 'yes' and config.plugins.tvspielfilm.login.value == '' or config.plugins.tvspielfilm.meintvs.value == 'yes' and config.plugins.tvspielfilm.password.value == '':
            self.session.openWithCallback(self.nologin_return, MessageBox, 'Sie haben den Mein TV SPIELFILM Login aktiviert, aber unvollstaendige Login-Daten angegeben.\n\nMoechten Sie die Mein TV SPIELFILM Login-Daten jetzt angeben oder Mein TV SPIELFILM deaktivieren?', MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.close, tvMain)

    def nologin_return(self, answer):
        if answer is True:
            pass
        else:
            config.plugins.tvspielfilm.meintvs.value = 'no'
            config.plugins.tvspielfilm.meintvs.save()
            configfile.save()
            self.session.openWithCallback(self.close, tvMain)


class FolderSelection(tvAllScreen):
    skin = """
        <screen name="FolderSelection" position="center,center" size="545,510" backgroundColor="#20000000" title="TV Spielfilm Setup">
            <ePixmap position="0,0" size="545,50" pixmap="{picpath}tvspielfilmHD.png" alphatest="blend" zPosition="1" />
            <ePixmap position="10,59" size="525,1" pixmap="{picpath}setup/seperator.png" alphatest="off" zPosition="1" />
            <widget name="folderlist" position="10,60" size="525,100" itemHeight="25" scrollbarMode="showNever" zPosition="1" />
            <ePixmap position="10,161" size="525,1" pixmap="{picpath}setup/seperator.png" alphatest="off" zPosition="1" />
            <ePixmap position="125,171" size="18,18" pixmap="{picpath}buttons/green.png" alphatest="blend" zPosition="1" />
            <ePixmap position="350,171" size="18,18" pixmap="{picpath}buttons/red.png" alphatest="blend" zPosition="1" />
            <eLabel position="150,170" size="180,20" font="Regular;18" halign="left" text="Speichern" transparent="1" zPosition="1" />
            <eLabel position="375,170" size="180,20" font="Regular;18" halign="left" text="Abbrechen" transparent="1" zPosition="1" />
            <widget name="plugin" position="10,200" size="525,300" alphatest="blend" zPosition="1" />
        </screen>"""

    def __init__(self, session, folder):
        tvAllScreen.__init__(self, session, FolderSelection.skin)
        self['plugin'] = Pixmap()
        noFolder = ['/bin',
         '/boot',
         '/dev',
         '/etc',
         '/proc',
         '/sbin',
         '/sys']
        self['folderlist'] = FileList(folder, showDirectories=True, showFiles=False, inhibitDirs=noFolder)
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions'], {'ok': self.ok,
         'cancel': self.cancel,
         'right': self.right,
         'left': self.left,
         'down': self.down,
         'up': self.up,
         'red': self.cancel,
         'green': self.green}, -1)
        self.onLayoutFinish.append(self.pluginPic)

    def pluginPic(self):
        png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/setup/' + str(config.plugins.tvspielfilm.color.value) + '.png'
        if fileExists(png):
            self['plugin'].instance.setPixmapFromFile(png)

    def ok(self):
        if self['folderlist'].canDescent():
            self['folderlist'].descent()

    def right(self):
        self['folderlist'].pageDown()

    def left(self):
        self['folderlist'].pageUp()

    def down(self):
        self['folderlist'].down()

    def up(self):
        self['folderlist'].up()

    def green(self):
        self.close(self['folderlist'].getSelection()[0])

    def cancel(self):
        self.close(None)
        return


class tvJetzt(tvAllScreenFull):
    def __init__(self, session, link):
        self.link = link
        tvAllScreenFull.__init__(self, session)
        self.channel_db = serviceDB(self.servicefile)
        self.JetztTimer = eTimer()
        self.JetztTimer.callback.append(self.makeTimerDB)
        self.JetztTimer.callback.append(self.makeCheck)
        self.JetztTimer.start(200, True)

    def makeCheck(self):
        if fileExists(self.servicefile):
            self.session.openWithCallback(self.exit, TVJetztView, self.link, True)
        else:
            self.session.openWithCallback(self.returnServiceFile, makeServiceFile)

    def returnServiceFile(self, result):
        if result == True:
            self.session.openWithCallback(self.exit, TVJetztView, self.link, True)
        else:
            self.close()

    def exit(self):
        self.close()


class tvEvent(tvAllScreenFull):
    def __init__(self, session):
        tvAllScreenFull.__init__(self, session)
        self.channel_db = serviceDB(self.servicefile)
        self.EventTimer = eTimer()
        self.EventTimer.callback.append(self.makeTimerDB)
        self.EventTimer.callback.append(self.makeChannelLink)
        self.EventTimer.start(200, True)

    def makeChannelLink(self):
        if fileExists(self.servicefile):
            sref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
            sref = str(sref) + 'FIN'
            sref = sub(':0:0:0:.*?FIN', ':0:0:0:', sref)
            channel = self.channel_db.lookup(sref)
            if channel == 'nope':
                self.session.open(MessageBox, 'Service not found:\nNo entry for current service reference\n%s' % str(sref), MessageBox.TYPE_INFO, close_on_any_key=True)
                self.close()
            else:
                link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
                self.session.openWithCallback(self.exit, TVProgrammView, link, True, False)
        else:
            self.session.openWithCallback(self.returnServiceFile, makeServiceFile)

    def returnServiceFile(self, result):
        if result == True:
            self.EventTimer.callback.append(self.makeChannelLink)
        else:
            self.close()

    def exit(self):
        self.close()


class TVHeuteView(tvBaseScreen):
    skin = """
        <screen position="{screenpos}" size="{screensize}" title="TV Programm - TV Spielfilm">""" + SKHEADTOP + """
        <widget name="sender1" position="_7,63" size="_151,_24" font="Regular;{fontsize2}" halign="left" zPosition="1" />
        <widget name="sender2" position="_212,63" size="_151,_24" font="Regular;{fontsize2}" halign="left" zPosition="1" />
        <widget name="sender3" position="_417,63" size="_151,_24" font="Regular;{fontsize2}" halign="left" zPosition="1" />
        <widget name="sender4" position="_622,63" size="_151,_24" font="Regular;{fontsize2}" halign="left" zPosition="1" />
        <widget name="sender5" position="_827,63" size="_151,_24" font="Regular;{fontsize2}" halign="left" zPosition="1" />
        <widget name="sender6" position="_1032,63" size="_151,_24" font="Regular;{fontsize2}" halign="left" zPosition="1" />
        <widget name="logo1" position="_163,60" size="44,27" alphatest="blend" zPosition="1" /> 
        <widget name="logo2" position="_368,60" size="44,27" alphatest="blend" zPosition="1" /> 
        <widget name="logo3" position="_573,60" size="44,27" alphatest="blend" zPosition="1" /> 
        <widget name="logo4" position="_778,60" size="44,27" alphatest="blend" zPosition="1" /> 
        <widget name="logo5" position="_983,60" size="44,27" alphatest="blend" zPosition="1" /> 
        <widget name="logo6" position="_1188,60" size="44,27" alphatest="blend" zPosition="1" /> 
        <widget name="pic1" position="_7,87" size="200,133" alphatest="blend" zPosition="1" /> 
        <widget name="pic2" position="_212,87" size="200,133" alphatest="blend" zPosition="1" /> 
        <widget name="pic3" position="_417,87" size="200,133" alphatest="blend" zPosition="1" /> 
        <widget name="pic4" position="_622,87" size="200,133" alphatest="blend" zPosition="1" /> 
        <widget name="pic5" position="_827,87" size="200,133" alphatest="blend" zPosition="1" /> 
        <widget name="pic6" position="_1032,87" size="200,133" alphatest="blend" zPosition="1" /> 
        <widget name="pictime1" position="_7,225" size="_60,_20" font="Regular;{fontsize2}" valign="top" halign="center" zPosition="1" />
        <widget name="pictime2" position="_212,225" size="_60,_20" font="Regular;{fontsize2}" valign="top" halign="center" zPosition="1" />
        <widget name="pictime3" position="_417,225" size="_60,_20" font="Regular;{fontsize2}" valign="top" halign="center" zPosition="1" />
        <widget name="pictime4" position="_622,225" size="_60,_20" font="Regular;{fontsize2}" valign="top" halign="center" zPosition="1" />
        <widget name="pictime5" position="_827,225" size="_60,_20" font="Regular;{fontsize2}" valign="top" halign="center" zPosition="1" />
        <widget name="pictime6" position="_1032,225" size="_60,_20" font="Regular;{fontsize2}" valign="top" halign="center" zPosition="1" />
        <widget name="pictext1" position="_72,225" size="{psize}" font="Regular;{fontsize2}" valign="top" halign="left" zPosition="1" />
        <widget name="pictext2" position="_277,225" size="{psize}" font="Regular;{fontsize2}" valign="top" halign="left" zPosition="1" />
        <widget name="pictext3" position="_482,225" size="{psize}" font="Regular;{fontsize2}" valign="top" halign="left" zPosition="1" />
        <widget name="pictext4" position="_687,225" size="{psize}" font="Regular;{fontsize2}" valign="top" halign="left" zPosition="1" />
        <widget name="pictext5" position="_892,225" size="{psize}" font="Regular;{fontsize2}" valign="top" halign="left" zPosition="1" />
        <widget name="pictext6" position="_1097,225" size="{psize}" font="Regular;{fontsize2}" valign="top" halign="left" zPosition="1" />
        <widget name="menu1" position="_7,273" size="_200,367" scrollbarMode="showNever" zPosition="1" /> 
        <widget name="menu2" position="_212,273" size="_200,367" scrollbarMode="showNever" zPosition="1" /> 
        <widget name="menu3" position="_417,273" size="_200,367" scrollbarMode="showNever" zPosition="1" /> 
        <widget name="menu4" position="_622,273" size="_200,367" scrollbarMode="showNever" zPosition="1" /> 
        <widget name="menu5" position="_827,273" size="_200,367" scrollbarMode="showNever" zPosition="1" /> 
        <widget name="menu6" position="_1032,273" size="_200,367" scrollbarMode="showNever" zPosition="1" />""" + SKHEADBOTTOM + "</screen>"

    def __init__(self, session, link, opener):
        if config.plugins.tvspielfilm.font_size.value == 'verylarge':
            psize = '50'
        elif config.plugins.tvspielfilm.font_size.value == 'large':
            psize = '48'
        else:
            psize = '42'
        dic = {"psize": "%s,%s" % (int(135 * skinFactor) , psize)}
        tvBaseScreen.__init__(self, session, TVHeuteView.skin, dic)
        if config.plugins.tvspielfilm.meintvs.value == 'yes':
            self.MeinTVS = True
            self.error = False
            self.opener = opener
            page = sub('https://my.tvspielfilm.de/tv-programm/tv-sender/.page=', '', link)
            self.count = int(page)
        else:
            self.MeinTVS = False
            page = sub('https://www.tvspielfilm.de/tv-programm/tv-sender/.page=', '', link)
            self.count = int(page)
        if config.plugins.tvspielfilm.picon.value == 'yes':
            self.picon = True
            self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
        else:
            self.picon = False
        self.tventries1 = []
        self.tventries2 = []
        self.tventries3 = []
        self.tventries4 = []
        self.tventries5 = []
        self.tventries6 = []
        self.tvlink1 = []
        self.tvlink2 = []
        self.tvlink3 = []
        self.tvlink4 = []
        self.tvlink5 = []
        self.tvlink6 = []
        self.tvtitel1 = []
        self.tvtitel2 = []
        self.tvtitel3 = []
        self.tvtitel4 = []
        self.tvtitel5 = []
        self.tvtitel6 = []
        self.sref1 = []
        self.sref2 = []
        self.sref3 = []
        self.sref4 = []
        self.sref5 = []
        self.sref6 = []
        self.searchlink = []
        self.searchref = []
        self.searchentries = []
        self.start = ''
        self.end = ''
        self.day = ''
        self.name = ''
        self.shortdesc = ''
        self.link = link
        self.postlink = link
        self.trailerurl = ''
        self.titel = ''
        self.POSTtext = ''
        self.EPGtext = ''
        self.hideflag = True
        self.search = False
        self.zap1 = True
        self.zap2 = True
        self.zap3 = True
        self.zap4 = True
        self.zap5 = True
        self.zap6 = True
        self.rec = False
        self.first = True
        self.ready = False
        self.postviewready = False
        self.mehrbilder = False
        self.trailer = False
        self.movie = False
        self.datum = False
        self.filter = True
        self.oldindex = 0
        self.oldsearchindex = 1
        self['logo1'] = Pixmap()
        self['logo2'] = Pixmap()
        self['logo3'] = Pixmap()
        self['logo4'] = Pixmap()
        self['logo5'] = Pixmap()
        self['logo6'] = Pixmap()
        self['pic1'] = Pixmap()
        self['pic2'] = Pixmap()
        self['pic3'] = Pixmap()
        self['pic4'] = Pixmap()
        self['pic5'] = Pixmap()
        self['pic6'] = Pixmap()
        self['picpost'] = Pixmap()
        self['tvinfo1'] = Pixmap()
        self['tvinfo2'] = Pixmap()
        self['tvinfo3'] = Pixmap()
        self['tvinfo4'] = Pixmap()
        self['tvinfo5'] = Pixmap()
        self['cinlogo'] = Pixmap()
        self['cinlogo'].hide()
        self['playlogo'] = Pixmap()
        self['playlogo'].hide()
        self['searchlogo'] = Pixmap()
        self['searchlogo'].hide()
        self['searchtimer'] = Pixmap()
        self['searchtimer'].hide()
        self['searchtext'] = Label('')
        self['searchtext'].hide()
        self['sender1'] = Label('')
        self['sender2'] = Label('')
        self['sender3'] = Label('')
        self['sender4'] = Label('')
        self['sender5'] = Label('')
        self['sender6'] = Label('')
        self['pictime1'] = Label('')
        self['pictime2'] = Label('')
        self['pictime3'] = Label('')
        self['pictime4'] = Label('')
        self['pictime5'] = Label('')
        self['pictime6'] = Label('')
        self['pictext1'] = Label('')
        self['pictext2'] = Label('')
        self['pictext3'] = Label('')
        self['pictext4'] = Label('')
        self['pictext5'] = Label('')
        self['pictext6'] = Label('')
        self['textpage'] = ScrollLabel('')
        self['infotext'] = Label('')
        self['infotext'].hide()
        self['infotext2'] = Label('')
        self['infotext2'].hide()
        self['infotext3'] = Label('')
        self['infotext3'].hide()
        self['infotext4'] = Label('')
        self['infotext4'].hide()
        self['infotext5'] = Label('')
        self['infotext5'].hide()
        self['infotext6'] = Label('')
        self['infotext6'].hide()
        self['infotext7'] = Label('')
        self['infotext7'].hide()
        self['infotext8'] = Label('')
        self['infotext8'].hide()
        self['piclabel'] = Label('')
        self['piclabel'].hide()
        self['piclabel2'] = Label('')
        self['piclabel2'].hide()
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['searchmenu'] = ItemList([])
        self['searchmenu'].hide()
        self['menu1'] = ItemList([])
        self['menu2'] = ItemList([])
        self['menu3'] = ItemList([])
        self['menu4'] = ItemList([])
        self['menu5'] = ItemList([])
        self['menu6'] = ItemList([])
        self.oldcurrent = 'menu1'
        self.currentsearch = 'menu1'
        self.current = 'menu1'
        self.menu = 'menu1'
        self['label'] = BlinkingLabel('Bitte warten...')
        self['label'].startBlinking()
        self['label2'] = Label('= Timer')
        self['label3'] = Label('= Suche')
        self['label4'] = Label('= Zappen')
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
         'ChannelSelectBaseActions',
         'DirectionActions',
         'EPGSelectActions',
         'InfobarTeletextActions',
         'MoviePlayerActions',
         'MovieSelectionActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.nextDay,
         'prevBouquet': self.prevDay,
         'nextMarker': self.nextWeek,
         'prevMarker': self.prevWeek,
         '0': self.gotoPage,
         '1': self.gotoPage,
         '2': self.gotoPage,
         '3': self.gotoPage,
         '4': self.gotoPage,
         '5': self.gotoPage,
         '6': self.gotoPage,
         '7': self.gotoPage,
         '8': self.gotoPage,
         '9': self.gotoPage,
         'contextMenu': self.gotoPageMenu,
         'info': self.getEPG,
         'epg': self.getEPG,
         'leavePlayer': self.youTube,
         'startTeletext': self.pressText}, -1)
        self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
         'yellow': self.yellow,
         'red': self.makeTimer,
         'blue': self.hideScreen}, -1)
        self.service_db = serviceDB(self.servicefile)
        self.timer = open('/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/db/timer.db').read()
        self.date = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        self.nextdate = self.date + one_day
        self.weekday = makeWeekDay(self.date.weekday())
        self.morgens = False
        self.mittags = False
        self.vorabend = False
        self.abends = True
        self.nachts = False
        if config.plugins.tvspielfilm.primetime.value == 'now':
            self.abends = False
            hour = datetime.datetime.now().hour
            if hour >= 5 and hour < 14:
                self.morgens = True
            elif hour >= 14 and hour < 18:
                self.mittags = True
            elif hour >= 18 and hour < 20:
                self.vorabend = True
            elif hour >= 20 and hour <= 23:
                self.abends = True
            else:
                self.nachts = True
        if config.plugins.tvspielfilm.color.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
        if config.plugins.tvspielfilm.genreinfo.value == 'no':
            self.showgenre = False
        else:
            self.showgenre = True
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        self.makeTVTimer = eTimer()
        self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
        self.makeTVTimer.start(500, True)

    def makeTVView(self, string):
        output = open(self.localhtml, 'r').read()
        output = six.ensure_str(output)
        if self.first == True:
            self.first = False
            startpos = output.find('label="Alle Sender">Alle Sender</option>')
            if self.MeinTVS == True:
                endpos = output.find('<optgroup label="Hauptsender">')
            else:
                endpos = output.find('<optgroup label="alle Sender alphabetisch">')
            bereich = output[startpos:endpos]
            sender = re.findall('<option label="(.*?)"', bereich)
            self.maxpages = len(sender) // 6
            if len(sender) % 6 != 0:
                self.maxpages += 1
        self.zap1 = True
        self.zap2 = True
        self.zap3 = True
        self.zap4 = True
        self.zap5 = True
        self.zap6 = True
        self.sref1 = []
        self.sref2 = []
        self.sref3 = []
        self.sref4 = []
        self.sref5 = []
        self.sref6 = []
        date = str(self.date.strftime('%d.%m.%Y'))
        self.titel = 'Heute im TV  - ' + str(self.weekday) + ', ' + date
        self.setTitle(self.titel)
        startpostop = output.find('<div class="gallery-area">')
        endpostop = output.find('<div class="info-block">')
        bereichtop = output[startpostop:endpostop]
        bereichtop = transHTML(bereichtop)
        bereichtop = sub('<wbr/>', '', bereichtop)
        bereichtop = sub('<div class="first-program block-1">\n.*?</div>', '<div class="first-program block-1"><img src="http://a2.tvspielfilm.de/imedia/8461/5218461,qfQElNSTpxAGvxxuSsPkPjQRIrO6vJjPQCu3KaA_RQPfIknB77GUEYh_MB053lNvumg7bMd+vkJk3F+_CzBZSQ==.jpg" width="149" height="99" border="0" /><span class="time"> </span><strong class="title"> </strong></div>', bereichtop)
        logos = re.findall('<span class="logotype chl_bg_. c-(.*?)">', bereichtop)
        if logos is not None:
            try:
                service = logos[0]
                sref = self.service_db.lookup(service)
                if sref == 'nope':
                    self.sref1.append('')
                    self.zap1 = False
                else:
                    self.sref1.append(sref)
                logo = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/' + service + '.png'
                self.showLogo1(logo)
                self['logo1'].show()
            except IndexError:
                pass

            try:
                service = logos[1]
                sref = self.service_db.lookup(service)
                if sref == 'nope':
                    self.sref2.append('')
                    self.zap2 = False
                else:
                    self.sref2.append(sref)
                logo = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/' + service + '.png'
                self.showLogo2(logo)
                self['logo2'].show()
            except IndexError:
                pass

            try:
                service = logos[2]
                sref = self.service_db.lookup(service)
                if sref == 'nope':
                    self.sref3.append('')
                    self.zap3 = False
                else:
                    self.sref3.append(sref)
                logo = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/' + service + '.png'
                self.showLogo3(logo)
                self['logo3'].show()
            except IndexError:
                pass

            try:
                service = logos[3]
                sref = self.service_db.lookup(service)
                if sref == 'nope':
                    self.sref4.append('')
                    self.zap4 = False
                else:
                    self.sref4.append(sref)
                logo = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/' + service + '.png'
                self.showLogo4(logo)
                self['logo4'].show()
            except IndexError:
                pass

            try:
                service = logos[4]
                sref = self.service_db.lookup(service)
                if sref == 'nope':
                    self.sref5.append('')
                    self.zap5 = False
                else:
                    self.sref5.append(sref)
                logo = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/' + service + '.png'
                self.showLogo5(logo)
                self['logo5'].show()
            except IndexError:
                pass

            try:
                service = logos[5]
                sref = self.service_db.lookup(service)
                if sref == 'nope':
                    self.sref6.append('')
                    self.zap6 = False
                else:
                    self.sref6.append(sref)
                logo = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/' + service + '.png'
                self.showLogo6(logo)
                self['logo6'].show()
            except IndexError:
                pass

        sender = re.findall('<h3>(.*?)</h3>', bereichtop)
        if sender is not None:
            self['sender1'].setText(sender[0])
            self['sender2'].setText(sender[1])
            self['sender3'].setText(sender[2])
            self['sender4'].setText(sender[3])
            self['sender5'].setText(sender[4])
            self['sender6'].setText(sender[5])
            self['sender1'].show()
            self['sender2'].show()
            self['sender3'].show()
            self['sender4'].show()
            self['sender5'].show()
            self['sender6'].show()
        else:
            self['sender1'].setText('')
            self['sender2'].setText('')
            self['sender3'].setText('')
            self['sender4'].setText('')
            self['sender5'].setText('')
            self['sender6'].setText('')
        pic = re.findall('<img src="(.*?)" width="', bereichtop)
        if pic is not None:
            try:
                self.download(fiximgLink(pic[0]), self.getPic1)
                self['pic1'].show()
            except IndexError:
                pass

            try:
                self.download(fiximgLink(pic[1]), self.getPic2)
                self['pic2'].show()
            except IndexError:
                pass

            try:
                self.download(fiximgLink(pic[2]), self.getPic3)
                self['pic3'].show()
            except IndexError:
                pass

            try:
                self.download(fiximgLink(pic[3]), self.getPic4)
                self['pic4'].show()
            except IndexError:
                pass

            try:
                self.download(fiximgLink(pic[4]), self.getPic5)
                self['pic5'].show()
            except IndexError:
                pass

            try:
                self.download(fiximgLink(pic[5]), self.getPic6)
                self['pic6'].show()
            except IndexError:
                pass

        pictime = re.findall('<span class="time">(.*?)</span>', bereichtop)
        if pictime is not None:
            self['pictime1'].setText(pictime[0])
            self['pictime2'].setText(pictime[1])
            self['pictime3'].setText(pictime[2])
            self['pictime4'].setText(pictime[3])
            self['pictime5'].setText(pictime[4])
            self['pictime6'].setText(pictime[5])
            self['pictime1'].show()
            self['pictime2'].show()
            self['pictime3'].show()
            self['pictime4'].show()
            self['pictime5'].show()
            self['pictime6'].show()
        else:
            self['pictime1'].setText('')
            self['pictime2'].setText('')
            self['pictime3'].setText('')
            self['pictime4'].setText('')
            self['pictime5'].setText('')
            self['pictime6'].setText('')
        pictext = re.findall('<strong class="title">(.*?)</strong>', bereichtop)
        if pictext is not None:
            self['pictext1'].setText(pictext[0])
            self['pictext2'].setText(pictext[1])
            self['pictext3'].setText(pictext[2])
            self['pictext4'].setText(pictext[3])
            self['pictext5'].setText(pictext[4])
            self['pictext6'].setText(pictext[5])
            self['pictext1'].show()
            self['pictext2'].show()
            self['pictext3'].show()
            self['pictext4'].show()
            self['pictext5'].show()
            self['pictext6'].show()
        else:
            self['pictext1'].setText('')
            self['pictext2'].setText('')
            self['pictext3'].setText('')
            self['pictext4'].setText('')
            self['pictext5'].setText('')
            self['pictext6'].setText('')
        if self.abends == True:
            startpos = output.find('<div id="toggleslot-20-p"')
            endpos = output.find('<div id="toggleslot-0-p"')
        elif self.nachts == True:
            startpos = output.find('<div id="toggleslot-0-p"')
            endpos = output.find('<div class="block-now-stations">')
        elif self.morgens == True:
            startpos = output.find('<div id="toggleslot-5-p"')
            endpos = output.find('<div id="toggleslot-14-p"')
        elif self.mittags == True:
            startpos = output.find('<div id="toggleslot-14-p"')
            endpos = output.find('<div id="toggleslot-18-p"')
        elif self.vorabend == True:
            startpos = output.find('<div id="toggleslot-18-p"')
            endpos = output.find('<div id="toggleslot-20-p"')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        bereich = sub('<a href="javascript://".*?\n', '', bereich)
        bereich = sub('<a title="Sendung jetzt.*?\n', '', bereich)
        bereich = sub('<span class="add-info icon-livetv"></span>', '', bereich)
        bereich = sub('<span class="time"></span>', '<td>TIME00:00</span>', bereich)
        bereich = sub('<span class="time">', '<td>TIME', bereich)
        bereich = sub('<span class="add-info editorial-rating small"></span>', '', bereich)
        bereich = sub('<span class="add-info editorial-', '<td>RATING', bereich)
        bereich = sub('<span class="add-info ', '<td>LOGO', bereich)
        bereich = sub('<a href="http://my', '<td>LINKhttp://www', bereich)
        bereich = sub('<a href="http://www', '<td>LINKhttp://www', bereich)
        bereich = sub('<a href="https://my', '<td>LINKhttp://www', bereich)
        bereich = sub('<a href="https://www', '<td>LINKhttp://www', bereich)
        bereich = sub('" target="_self"', '</td>', bereich)
        bereich = sub('<strong class="title">', '<td>TITEL', bereich)
        bereich = sub('<span class="subtitle">', '<td>SUBTITEL', bereich)
        bereich = sub('</strong>', '</td>', bereich)
        bereich = sub('">TIPP</span>', '</td>', bereich)
        bereich = sub('">LIVE</span>', '</td>', bereich)
        bereich = sub('">HDTV</span>', '</td>', bereich)
        bereich = sub('">NEU</span>', '</td>', bereich)
        bereich = sub('">OMU</span>', '</td>', bereich)
        bereich = sub('"></span>', '</td>', bereich)
        bereich = sub('</span>', '</td>', bereich)
        bereich = sub('<wbr/>', '', bereich)
        bereich = sub('<div class="program-block">', '<td>BLOCK</td>', bereich)
        self.tventries1 = []
        self.tvlink1 = []
        self.tvtitel1 = []
        self.tventries2 = []
        self.tvlink2 = []
        self.tvtitel2 = []
        self.tventries3 = []
        self.tvlink3 = []
        self.tvtitel3 = []
        self.tventries4 = []
        self.tvlink4 = []
        self.tvtitel4 = []
        self.tventries5 = []
        self.tvlink5 = []
        self.tvtitel5 = []
        self.tventries6 = []
        self.tvlink6 = []
        self.tvtitel6 = []
        self.menu = 'menu6'
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 9
        for x in a:
            if y == 0:
                logo3 = False
                if search('BLOCK', x) is not None:
                    if self.menu == 'menu1':
                        self.menu = 'menu2'
                    elif self.menu == 'menu2':
                        self.menu = 'menu3'
                    elif self.menu == 'menu3':
                        self.menu = 'menu4'
                    elif self.menu == 'menu4':
                        self.menu = 'menu5'
                    elif self.menu == 'menu5':
                        self.menu = 'menu6'
                    elif self.menu == 'menu6':
                        self.menu = 'menu1'
                else:
                    y = 1
            if y == 1:
                if search('BLOCK', x) is not None:
                    res1 = ''
                    res2 = ''
                    res3 = ''
                    res4 = ''
                    res5 = ''
                    res6 = ''
                    y = 7
                elif search('TIME', x) is not None:
                    x = sub('TIME', '', x)
                    if self.menu == 'menu1':
                        res1 = [x]
                        if self.backcolor == True:
                            res1.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                        res1.append(MultiContentEntryText(pos=(0, 0), size=(55, 22), font=1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                        hour = sub(':..', '', x)
                        if int(hour) < 5:
                            one_day = datetime.timedelta(days=1)
                            date = self.date + one_day
                        else:
                            date = self.date
                        timer = str(date) + ':::' + x + ':::' + str(self.sref1[0])
                        if timer in self.timer:
                            self.rec = True
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/icon-small-rec.png'
                            if fileExists(png):
                                res1.append(MultiContentEntryPixmapAlphaTest(pos=(167, 87), size=(28, 29), png=loadPNG(png)))
                    elif self.menu == 'menu2':
                        res2 = [x]
                        if self.backcolor == True:
                            res2.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                        res2.append(MultiContentEntryText(pos=(0, 0), size=(55, 22), font=1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                        hour = sub(':..', '', x)
                        if int(hour) < 5:
                            one_day = datetime.timedelta(days=1)
                            date = self.date + one_day
                        else:
                            date = self.date
                        timer = str(date) + ':::' + x + ':::' + str(self.sref2[0])
                        if timer in self.timer:
                            self.rec = True
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/icon-small-rec.png'
                            if fileExists(png):
                                res2.append(MultiContentEntryPixmapAlphaTest(pos=(167, 87), size=(28, 29), png=loadPNG(png)))
                    elif self.menu == 'menu3':
                        res3 = [x]
                        if self.backcolor == True:
                            res3.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                        res3.append(MultiContentEntryText(pos=(0, 0), size=(55, 22), font=1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                        hour = sub(':..', '', x)
                        if int(hour) < 5:
                            one_day = datetime.timedelta(days=1)
                            date = self.date + one_day
                        else:
                            date = self.date
                        timer = str(date) + ':::' + x + ':::' + str(self.sref3[0])
                        if timer in self.timer:
                            self.rec = True
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/icon-small-rec.png'
                            if fileExists(png):
                                res3.append(MultiContentEntryPixmapAlphaTest(pos=(167, 87), size=(28, 29), png=loadPNG(png)))
                    elif self.menu == 'menu4':
                        res4 = [x]
                        if self.backcolor == True:
                            res4.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                        res4.append(MultiContentEntryText(pos=(0, 0), size=(55, 22), font=1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                        hour = sub(':..', '', x)
                        if int(hour) < 5:
                            one_day = datetime.timedelta(days=1)
                            date = self.date + one_day
                        else:
                            date = self.date
                        timer = str(date) + ':::' + x + ':::' + str(self.sref4[0])
                        if timer in self.timer:
                            self.rec = True
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/icon-small-rec.png'
                            if fileExists(png):
                                res4.append(MultiContentEntryPixmapAlphaTest(pos=(167, 87), size=(28, 29), png=loadPNG(png)))
                    elif self.menu == 'menu5':
                        res5 = [x]
                        if self.backcolor == True:
                            res5.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                        res5.append(MultiContentEntryText(pos=(0, 0), size=(55, 22), font=1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                        hour = sub(':..', '', x)
                        if int(hour) < 5:
                            one_day = datetime.timedelta(days=1)
                            date = self.date + one_day
                        else:
                            date = self.date
                        timer = str(date) + ':::' + x + ':::' + str(self.sref5[0])
                        if timer in self.timer:
                            self.rec = True
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/icon-small-rec.png'
                            if fileExists(png):
                                res5.append(MultiContentEntryPixmapAlphaTest(pos=(167, 87), size=(28, 29), png=loadPNG(png)))
                    elif self.menu == 'menu6':
                        res6 = [x]
                        if self.backcolor == True:
                            res6.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                        res6.append(MultiContentEntryText(pos=(0, 0), size=(55, 22), font=1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                        hour = sub(':..', '', x)
                        if int(hour) < 5:
                            one_day = datetime.timedelta(days=1)
                            date = self.date + one_day
                        else:
                            date = self.date
                        timer = str(date) + ':::' + x + ':::' + str(self.sref6[0])
                        if timer in self.timer:
                            self.rec = True
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/icon-small-rec.png'
                            if fileExists(png):
                                res6.append(MultiContentEntryPixmapAlphaTest(pos=(167, 87), size=(28, 29), png=loadPNG(png)))
                else:
                    if self.menu == 'menu1':
                        res1 = [x]
                        if self.backcolor == True:
                            res1.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                    elif self.menu == 'menu2':
                        res2 = [x]
                        if self.backcolor == True:
                            res2.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                    elif self.menu == 'menu3':
                        res3 = [x]
                        if self.backcolor == True:
                            res3.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                    elif self.menu == 'menu4':
                        res4 = [x]
                        if self.backcolor == True:
                            res4.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                    elif self.menu == 'menu5':
                        res5 = [x]
                        if self.backcolor == True:
                            res5.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                    elif self.menu == 'menu6':
                        res6 = [x]
                        if self.backcolor == True:
                            res6.append(MultiContentEntryText(pos=(0, 0), size=(200, 115), font=1, backcolor_sel=self.back_color, text=''))
                    y = 2
            if y == 2:
                if search('LOGO', x) is not None:
                    x = sub('LOGO', '', x)
                    png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/%s.png' % x
                    if fileExists(png):
                        if self.menu == 'menu1':
                            res1.append(MultiContentEntryPixmapAlphaTest(pos=(0, 25), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu2':
                            res2.append(MultiContentEntryPixmapAlphaTest(pos=(0, 25), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu3':
                            res3.append(MultiContentEntryPixmapAlphaTest(pos=(0, 25), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu4':
                            res4.append(MultiContentEntryPixmapAlphaTest(pos=(0, 25), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu5':
                            res5.append(MultiContentEntryPixmapAlphaTest(pos=(0, 25), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu6':
                            res6.append(MultiContentEntryPixmapAlphaTest(pos=(0, 25), size=(45, 15), png=loadPNG(png)))
                else:
                    y = 3
            if y == 3:
                if search('LOGO', x) is not None:
                    x = sub('LOGO', '', x)
                    png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/%s.png' % x
                    if fileExists(png):
                        if self.menu == 'menu1':
                            res1.append(MultiContentEntryPixmapAlphaTest(pos=(0, 45), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu2':
                            res2.append(MultiContentEntryPixmapAlphaTest(pos=(0, 45), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu3':
                            res3.append(MultiContentEntryPixmapAlphaTest(pos=(0, 45), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu4':
                            res4.append(MultiContentEntryPixmapAlphaTest(pos=(0, 45), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu5':
                            res5.append(MultiContentEntryPixmapAlphaTest(pos=(0, 45), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu6':
                            res6.append(MultiContentEntryPixmapAlphaTest(pos=(0, 45), size=(45, 15), png=loadPNG(png)))
                else:
                    y = 4
            if y == 4:
                if search('LOGO', x) is not None:
                    x = sub('LOGO', '', x)
                    logo3 = True
                    png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/%s.png' % x
                    if fileExists(png):
                        if self.menu == 'menu1':
                            res1.append(MultiContentEntryPixmapAlphaTest(pos=(0, 65), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu2':
                            res2.append(MultiContentEntryPixmapAlphaTest(pos=(0, 65), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu3':
                            res3.append(MultiContentEntryPixmapAlphaTest(pos=(0, 65), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu4':
                            res4.append(MultiContentEntryPixmapAlphaTest(pos=(0, 65), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu5':
                            res5.append(MultiContentEntryPixmapAlphaTest(pos=(0, 65), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu6':
                            res6.append(MultiContentEntryPixmapAlphaTest(pos=(0, 65), size=(45, 15), png=loadPNG(png)))
                else:
                    y = 5
            if y == 5:
                if search('RATING', x) is not None:
                    x = sub('RATING', '', x)
                    png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/%s.png' % x
                    if fileExists(png):
                        if self.menu == 'menu1':
                            if logo3 == False:
                                res1.append(MultiContentEntryPixmapAlphaTest(pos=(5, 65), size=(29, 29), png=loadPNG(png)))
                            else:
                                res1.append(MultiContentEntryPixmapAlphaTest(pos=(5, 80), size=(29, 29), png=loadPNG(png)))
                        elif self.menu == 'menu2':
                            if logo3 == False:
                                res2.append(MultiContentEntryPixmapAlphaTest(pos=(5, 65), size=(29, 29), png=loadPNG(png)))
                            else:
                                res2.append(MultiContentEntryPixmapAlphaTest(pos=(5, 80), size=(29, 29), png=loadPNG(png)))
                        elif self.menu == 'menu3':
                            if logo3 == False:
                                res3.append(MultiContentEntryPixmapAlphaTest(pos=(5, 65), size=(29, 29), png=loadPNG(png)))
                            else:
                                res3.append(MultiContentEntryPixmapAlphaTest(pos=(5, 80), size=(29, 29), png=loadPNG(png)))
                        elif self.menu == 'menu4':
                            if logo3 == False:
                                res4.append(MultiContentEntryPixmapAlphaTest(pos=(5, 65), size=(29, 29), png=loadPNG(png)))
                            else:
                                res4.append(MultiContentEntryPixmapAlphaTest(pos=(5, 80), size=(29, 29), png=loadPNG(png)))
                        elif self.menu == 'menu5':
                            if logo3 == False:
                                res5.append(MultiContentEntryPixmapAlphaTest(pos=(5, 65), size=(29, 29), png=loadPNG(png)))
                            else:
                                res5.append(MultiContentEntryPixmapAlphaTest(pos=(5, 80), size=(29, 29), png=loadPNG(png)))
                        elif self.menu == 'menu6':
                            if logo3 == False:
                                res6.append(MultiContentEntryPixmapAlphaTest(pos=(5, 65), size=(29, 29), png=loadPNG(png)))
                            else:
                                res6.append(MultiContentEntryPixmapAlphaTest(pos=(5, 80), size=(29, 29), png=loadPNG(png)))
                elif search('LOGO', x) is not None:
                    x = sub('LOGO', '', x)
                    png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/%s.png' % x
                    if fileExists(png):
                        if self.menu == 'menu1':
                            res1.append(MultiContentEntryPixmapAlphaTest(pos=(0, 85), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu2':
                            res2.append(MultiContentEntryPixmapAlphaTest(pos=(0, 85), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu3':
                            res3.append(MultiContentEntryPixmapAlphaTest(pos=(0, 85), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu4':
                            res4.append(MultiContentEntryPixmapAlphaTest(pos=(0, 85), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu5':
                            res5.append(MultiContentEntryPixmapAlphaTest(pos=(0, 85), size=(45, 15), png=loadPNG(png)))
                        elif self.menu == 'menu6':
                            res6.append(MultiContentEntryPixmapAlphaTest(pos=(0, 85), size=(45, 15), png=loadPNG(png)))
                    y = 4
                else:
                    y = 6
            if y == 6:
                if search('LINK', x) is not None:
                    x = sub('LINK', '', x)
                    if self.menu == 'menu1':
                        self.tvlink1.append(x)
                    elif self.menu == 'menu2':
                        self.tvlink2.append(x)
                    elif self.menu == 'menu3':
                        self.tvlink3.append(x)
                    elif self.menu == 'menu4':
                        self.tvlink4.append(x)
                    elif self.menu == 'menu5':
                        self.tvlink5.append(x)
                    elif self.menu == 'menu6':
                        self.tvlink6.append(x)
                else:
                    if self.menu == 'menu1':
                        self.tvlink1.append('na')
                    elif self.menu == 'menu2':
                        self.tvlink2.append('na')
                    elif self.menu == 'menu3':
                        self.tvlink3.append('na')
                    elif self.menu == 'menu4':
                        self.tvlink4.append('na')
                    elif self.menu == 'menu5':
                        self.tvlink5.append('na')
                    elif self.menu == 'menu6':
                        self.tvlink6.append('na')
                    y = 7
            if y == 7:
                if search('TITEL', x) is not None:
                    x = sub('TITEL', '', x)
                    titel = x
                else:
                    titel = ''
                    y = 8
            if y == 8:
                if search('SUBTITEL', x) is not None:
                    x = sub('SUBTITEL', '', x)
                    if x != '':
                        x = titel + ', ' + x
                    else:
                        x = titel
                    if self.menu == 'menu1':
                        self.tvtitel1.append(titel)
                        if self.rec == True:
                            self.rec = False
                            if self.fontlarge == True:
                                res1.append(MultiContentEntryText(pos=(60, 0), size=(140, 94), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                            else:
                                res1.append(MultiContentEntryText(pos=(60, 0), size=(140, 84), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        elif self.fontlarge == True:
                            res1.append(MultiContentEntryText(pos=(60, 0), size=(140, 115), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        else:
                            res1.append(MultiContentEntryText(pos=(60, 0), size=(140, 108), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        self.tventries1.append(res1)
                    elif self.menu == 'menu2':
                        self.tvtitel2.append(titel)
                        if self.rec == True:
                            self.rec = False
                            if self.fontlarge == True:
                                res2.append(MultiContentEntryText(pos=(60, 0), size=(140, 94), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                            else:
                                res2.append(MultiContentEntryText(pos=(60, 0), size=(140, 84), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        elif self.fontlarge == True:
                            res2.append(MultiContentEntryText(pos=(60, 0), size=(140, 115), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        else:
                            res2.append(MultiContentEntryText(pos=(60, 0), size=(140, 108), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        self.tventries2.append(res2)
                    elif self.menu == 'menu3':
                        self.tvtitel3.append(titel)
                        if self.rec == True:
                            self.rec = False
                            if self.fontlarge == True:
                                res3.append(MultiContentEntryText(pos=(60, 0), size=(140, 94), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                            else:
                                res3.append(MultiContentEntryText(pos=(60, 0), size=(140, 84), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        elif self.fontlarge == True:
                            res3.append(MultiContentEntryText(pos=(60, 0), size=(140, 115), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        else:
                            res3.append(MultiContentEntryText(pos=(60, 0), size=(140, 108), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        self.tventries3.append(res3)
                    elif self.menu == 'menu4':
                        self.tvtitel4.append(titel)
                        if self.rec == True:
                            self.rec = False
                            if self.fontlarge == True:
                                res4.append(MultiContentEntryText(pos=(60, 0), size=(140, 94), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                            else:
                                res4.append(MultiContentEntryText(pos=(60, 0), size=(140, 84), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        elif self.fontlarge == True:
                            res4.append(MultiContentEntryText(pos=(60, 0), size=(140, 115), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        else:
                            res4.append(MultiContentEntryText(pos=(60, 0), size=(140, 108), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        self.tventries4.append(res4)
                    elif self.menu == 'menu5':
                        self.tvtitel5.append(titel)
                        if self.rec == True:
                            self.rec = False
                            if self.fontlarge == True:
                                res5.append(MultiContentEntryText(pos=(60, 0), size=(140, 94), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                            else:
                                res5.append(MultiContentEntryText(pos=(60, 0), size=(140, 84), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        elif self.fontlarge == True:
                            res5.append(MultiContentEntryText(pos=(60, 0), size=(140, 115), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        else:
                            res5.append(MultiContentEntryText(pos=(60, 0), size=(140, 108), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        self.tventries5.append(res5)
                    elif self.menu == 'menu6':
                        self.tvtitel6.append(titel)
                        if self.rec == True:
                            self.rec = False
                            if self.fontlarge == True:
                                res6.append(MultiContentEntryText(pos=(60, 0), size=(140, 94), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                            else:
                                res6.append(MultiContentEntryText(pos=(60, 0), size=(140, 84), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        elif self.fontlarge == True:
                            res6.append(MultiContentEntryText(pos=(60, 0), size=(140, 115), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        else:
                            res6.append(MultiContentEntryText(pos=(60, 0), size=(140, 108), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                        self.tventries6.append(res6)
                elif search('BLOCK', x) is not None:
                    if self.menu == 'menu1':
                        self.menu = 'menu2'
                    elif self.menu == 'menu2':
                        self.menu = 'menu3'
                    elif self.menu == 'menu3':
                        self.menu = 'menu4'
                    elif self.menu == 'menu4':
                        self.menu = 'menu5'
                    elif self.menu == 'menu5':
                        self.menu = 'menu6'
                    elif self.menu == 'menu6':
                        self.menu = 'menu1'
            y += 1
            if y == offset:
                y = 0

        self['menu1'].l.setItemHeight(115)
        self['menu1'].l.setList(self.tventries1)
        self['menu2'].l.setItemHeight(115)
        self['menu2'].l.setList(self.tventries2)
        self['menu3'].l.setItemHeight(115)
        self['menu3'].l.setList(self.tventries3)
        self['menu4'].l.setItemHeight(115)
        self['menu4'].l.setList(self.tventries4)
        self['menu5'].l.setItemHeight(115)
        self['menu5'].l.setList(self.tventries5)
        self['menu6'].l.setItemHeight(115)
        self['menu6'].l.setList(self.tventries6)
        self['menu1'].moveToIndex(self.oldindex)
        self['menu2'].moveToIndex(self.oldindex)
        self['menu3'].moveToIndex(self.oldindex)
        self['menu4'].moveToIndex(self.oldindex)
        self['menu5'].moveToIndex(self.oldindex)
        self['menu6'].moveToIndex(self.oldindex)
        if self.current == 'menu1':
            self['menu1'].selectionEnabled(1)
            self['menu2'].selectionEnabled(0)
            self['menu3'].selectionEnabled(0)
            self['menu4'].selectionEnabled(0)
            self['menu5'].selectionEnabled(0)
            self['menu6'].selectionEnabled(0)
        elif self.current == 'menu2':
            self['menu1'].selectionEnabled(0)
            self['menu2'].selectionEnabled(1)
            self['menu3'].selectionEnabled(0)
            self['menu4'].selectionEnabled(0)
            self['menu5'].selectionEnabled(0)
            self['menu6'].selectionEnabled(0)
        elif self.current == 'menu3':
            self['menu1'].selectionEnabled(0)
            self['menu2'].selectionEnabled(0)
            self['menu3'].selectionEnabled(1)
            self['menu4'].selectionEnabled(0)
            self['menu5'].selectionEnabled(0)
            self['menu6'].selectionEnabled(0)
        elif self.current == 'menu4':
            self['menu1'].selectionEnabled(0)
            self['menu2'].selectionEnabled(0)
            self['menu3'].selectionEnabled(0)
            self['menu4'].selectionEnabled(1)
            self['menu5'].selectionEnabled(0)
            self['menu6'].selectionEnabled(0)
        elif self.current == 'menu5':
            self['menu1'].selectionEnabled(0)
            self['menu2'].selectionEnabled(0)
            self['menu3'].selectionEnabled(0)
            self['menu4'].selectionEnabled(0)
            self['menu5'].selectionEnabled(1)
            self['menu6'].selectionEnabled(0)
        elif self.current == 'menu6':
            self['menu1'].selectionEnabled(0)
            self['menu2'].selectionEnabled(0)
            self['menu3'].selectionEnabled(0)
            self['menu4'].selectionEnabled(0)
            self['menu5'].selectionEnabled(0)
            self['menu6'].selectionEnabled(1)
        self['label'].setText('Info = +- Tageszeit, Bouquet = +- Tag, <> = +- Woche, Menue = Senderliste')
        self['label'].stopBlinking()
        self['label'].show()
        self.ready = True
        return

    def makePostviewPage(self, string):
        print("DEBUG makePostviewPage TVHeuteView")
        self['sender1'].hide()
        self['sender2'].hide()
        self['sender3'].hide()
        self['sender4'].hide()
        self['sender5'].hide()
        self['sender6'].hide()
        self['logo1'].hide()
        self['logo2'].hide()
        self['logo3'].hide()
        self['logo4'].hide()
        self['logo5'].hide()
        self['logo6'].hide()
        self['pic1'].hide()
        self['pic2'].hide()
        self['pic3'].hide()
        self['pic4'].hide()
        self['pic5'].hide()
        self['pic6'].hide()
        self['pictime1'].hide()
        self['pictime2'].hide()
        self['pictime3'].hide()
        self['pictime4'].hide()
        self['pictime5'].hide()
        self['pictime6'].hide()
        self['pictext1'].hide()
        self['pictext2'].hide()
        self['pictext3'].hide()
        self['pictext4'].hide()
        self['pictext5'].hide()
        self['pictext6'].hide()
        self['menu1'].hide()
        self['menu2'].hide()
        self['menu3'].hide()
        self['menu4'].hide()
        self['menu5'].hide()
        self['menu6'].hide()
        self._makePostviewPage(string)

    def makeSearchView(self, url):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        searchrequest = Request(url, None, header)
        try:
            output = urlopen(searchrequest).read()
            output = six.ensure_str(output)
        except (HTTPError,
         URLError,
         HTTPException,
         socket.error,
         AttributeError):
            output = ' '

        title = search('<title>(.*?)</title>', output)
        if title is not None:
            self['searchtext'].setText(title.group(1))
            self['searchtext'].show()
            self.setTitle('')
            self.setTitle(title.group(1))
        bereich = parsePrimeTimeTable(output, self.showgenre)
        a = findall('<td>(.*?)</td>', bereich)
        y = 0
        offset = 10
        mh = 40
        pictopoffset = 0
        picleftoffset = 0
        if self.picon == True:
            mh = 60
            pictopoffset = 10
            picleftoffset = 40
        for x in a:
            if y == 0:
                res = [x]
                if self.backcolor == True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))

                if search('DATUM', x) is not None:
                    if self.datum == True:
                        try:
                            del self.searchref[-1]
                            del self.searchlink[-1]
                            del self.searchentries[-1]
                        except IndexError:
                            pass

                    else:
                        self.datum = True
                    x = sub('DATUM', '', x)
                    self.datum_string = x
                    res_datum = [x]
                    if self.backcolor == True:
                        res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, backcolor_sel=self.back_color, text=''))
                    res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
                    self.searchref.append('na')
                    self.searchlink.append('na')
                    self.searchentries.append(res_datum)
                    self.filter = True
                    y = 9
                else:
                    y = 1
            if y == 1:
                x = sub('TIME', '', x)
                start = x
                res.append(MultiContentEntryText(pos=(60 + picleftoffset, 7 + pictopoffset), size=(175, 40), font=-1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
            if y == 2:
                if search('LOGO', x) is not None:
                    logo = search('LOGO(.*?)">', x)
                    if logo is not None:
                        x = logo.group(1)
                    service = x
                    sref = self.service_db.lookup(service)
                    if sref == 'nope':
                        self.filter = True
                    else:
                        self.filter = False
                        self.searchref.append(sref)
                        if self.picon == True:
                            picon = self.findPicon(sref)
                            if picon is not None:
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(100, 60), png=LoadPixmap(picon)))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(100, 60), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
                        else:
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/logos/%sHD.png' % x
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
                        start = sub(' - ..:..', '', start)
                        daynow = sub('....-..-', '', str(self.date))
                        day = search(', ([0-9]+). ', self.datum_string)
                        if day is not None:
                            day = day.group(1)
                        else:
                            day = daynow
                        if int(day) >= int(daynow) - 1:
                            date = str(self.date) + 'FIN'
                        else:
                            four_weeks = datetime.timedelta(weeks=4)
                            date = str(self.date + four_weeks) + 'FIN'
                        date = sub('[0-9][0-9]FIN', day, date)
                        timer = date + ':::' + start + ':::' + str(sref)
                        if timer in self.timer:
                            self.rec = True
                            rp = self.getRecPNG()
                            if rp != None:
                                res.append(rp)
            if y == 3:
                if self.filter == False:
                    x = sub('LINK', '', x)
                    self.searchlink.append(x)
            if y == 4:
                if self.filter == False:
                    x = sub('TITEL', '', x)
                    titelfilter = x
            if y == 5:
                if self.filter == False:
                    if search('GENRE', x) is None:
                        res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                        y = 6
            if y == 6:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        if self.rec == True:
                            self.rec = False
                        else:
                            x = sub('INFO', '', x)
                            rp = self.getPNG(x, self.menuwidth - 140)
                            if rp != None:
                                res.append(rp)
                else:
                    y = 9
            if y == 7:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 210)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 8:
                if search('INFO', x) is not None:
                    if self.filter == False:
                        x = sub('INFO', '', x)
                        rp = self.getPNG(x, self.menuwidth - 280)
                        if rp != None:
                            res.append(rp)
                else:
                    y = 9
            if y == 9:
                if search('INFO', x) is not None:
                    y = 7
                elif self.filter == False:
                    self.datum = False
                    if search('RATING', x) is not None:
                        x = sub('RATING', '', x)
                        if x != 'rating small':
                            png = '/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pic/icons/%sHD.png' % x
                            if fileExists(png):
                                res.append(MultiContentEntryPixmapAlphaTest(pos=(1175, pictopoffset), size=(40, 40), png=loadPNG(png)))
                    res.append(MultiContentEntryText(pos=(235 + picleftoffset, 7 + pictopoffset), size=(715 - picleftoffset, 40), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
                    self.searchentries.append(res)
            y += 1
            if y == offset:
                y = 0

        self['searchmenu'].l.setItemHeight(mh)
        self['searchmenu'].l.setList(self.searchentries)
        self['searchmenu'].show()
        self.searchcount += 1
        if self.searchcount <= self.maxsearchcount and search('class="pagination__link pagination__link--next" >', bereich) is not None:
            nextpage = search('<a href="(.*?)"\\n\\s+class="pagination__link pagination__link--next" >', bereich)
            if nextpage is not None:
                self.makeSearchView(nextpage.group(1))
            else:
                self.ready = True
        else:
            try:
                if self.searchref[-1] == 'na':
                    del self.searchref[-1]
                    del self.searchlink[-1]
                    del self.searchentries[-1]
                    self['searchmenu'].l.setList(self.searchentries)
            except IndexError:
                pass

            self['searchmenu'].moveToIndex(self.oldsearchindex)
            self.current = 'searchmenu'
            self.ready = True
        return

    def ok(self):
        if self.hideflag == False:
            return
        if self.current == 'postview' and self.postviewready == True:
            if self.trailer == True:
                sref = eServiceReference(4097, 0, self.trailerurl)
                sref.setName(self.name)
                self.session.open(MoviePlayer, sref)
            elif self.mehrbilder == True:
                self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
            else:
                self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)
        elif self.current == 'postview' and self.postviewready == False:
            pass
        else:
            self.selectPage('ok')

    def selectPage(self, action):
        self.oldcurrent = self.current
        if self.current == 'menu1' and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            try:
                self.postlink = self.tvlink1[c]
                if action == 'ok':
                    if search('www.tvspielfilm.de', self.postlink) is not None:
                        self.current = 'postview'
                        self.downloadPostPage(self.postlink, self.makePostviewPage)
            except IndexError:
                pass

        elif self.current == 'menu2' and self.ready == True:
            c = self['menu2'].getSelectedIndex()
            try:
                self.postlink = self.tvlink2[c]
                if action == 'ok':
                    if search('www.tvspielfilm.de', self.postlink) is not None:
                        self.current = 'postview'
                        self.downloadPostPage(self.postlink, self.makePostviewPage)
            except IndexError:
                pass

        elif self.current == 'menu3' and self.ready == True:
            c = self['menu3'].getSelectedIndex()
            try:
                self.postlink = self.tvlink3[c]
                if action == 'ok':
                    if search('www.tvspielfilm.de', self.postlink) is not None:
                        self.current = 'postview'
                        self.downloadPostPage(self.postlink, self.makePostviewPage)
            except IndexError:
                pass

        elif self.current == 'menu4' and self.ready == True:
            c = self['menu4'].getSelectedIndex()
            try:
                self.postlink = self.tvlink4[c]
                if action == 'ok':
                    if search('www.tvspielfilm.de', self.postlink) is not None:
                        self.current = 'postview'
                        self.downloadPostPage(self.postlink, self.makePostviewPage)
            except IndexError:
                pass

        elif self.current == 'menu5' and self.ready == True:
            c = self['menu5'].getSelectedIndex()
            try:
                self.postlink = self.tvlink5[c]
                if action == 'ok':
                    if search('www.tvspielfilm.de', self.postlink) is not None:
                        self.current = 'postview'
                        self.downloadPostPage(self.postlink, self.makePostviewPage)
            except IndexError:
                pass

        elif self.current == 'menu6' and self.ready == True:
            c = self['menu6'].getSelectedIndex()
            try:
                self.postlink = self.tvlink6[c]
                if action == 'ok':
                    if search('www.tvspielfilm.de', self.postlink) is not None:
                        self.current = 'postview'
                        self.downloadPostPage(self.postlink, self.makePostviewPage)
            except IndexError:
                pass

        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            try:
                self.postlink = self.searchlink[c]
                if action == 'ok':
                    if search('www.tvspielfilm.de', self.postlink) is not None:
                        self.current = 'postview'
                        self.downloadPostPage(self.postlink, self.makePostviewPage)
            except IndexError:
                pass

        return

    def getEPG(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.showEPG == False:
                self.showEPG = True
                if self.search == False:
                    if self.oldcurrent == 'menu1' and self.zap1 == True:
                        try:
                            c = self['menu1'].getSelectedIndex()
                            sref = self.sref1[0]
                            channel = ServiceReference(eServiceReference(sref)).getServiceName()
                        except IndexError:
                            sref = None
                            channel = ''

                    elif self.oldcurrent == 'menu2' and self.zap2 == True:
                        try:
                            c = self['menu2'].getSelectedIndex()
                            sref = self.sref2[0]
                            channel = ServiceReference(eServiceReference(sref)).getServiceName()
                        except IndexError:
                            sref = None
                            channel = ''

                    elif self.oldcurrent == 'menu3' and self.zap3 == True:
                        try:
                            c = self['menu3'].getSelectedIndex()
                            sref = self.sref3[0]
                            channel = ServiceReference(eServiceReference(sref)).getServiceName()
                        except IndexError:
                            sref = None
                            channel = ''

                    elif self.oldcurrent == 'menu4' and self.zap4 == True:
                        try:
                            c = self['menu4'].getSelectedIndex()
                            sref = self.sref4[0]
                            channel = ServiceReference(eServiceReference(sref)).getServiceName()
                        except IndexError:
                            sref = None
                            channel = ''

                    elif self.oldcurrent == 'menu5' and self.zap5 == True:
                        try:
                            c = self['menu5'].getSelectedIndex()
                            sref = self.sref5[0]
                            channel = ServiceReference(eServiceReference(sref)).getServiceName()
                        except IndexError:
                            sref = None
                            channel = ''

                    elif self.oldcurrent == 'menu6' and self.zap6 == True:
                        try:
                            c = self['menu6'].getSelectedIndex()
                            sref = self.sref6[0]
                            channel = ServiceReference(eServiceReference(sref)).getServiceName()
                        except IndexError:
                            sref = None
                            channel = ''

                    else:
                        sref = None
                        channel = ''
                else:
                    try:
                        c = self['searchmenu'].getSelectedIndex()
                        sref = self.searchref[c]
                        channel = ServiceReference(eServiceReference(sref)).getServiceName()
                    except IndexError:
                        sref = None
                        channel = ''

                if sref is not None:
                    try:
                        start = self.start
                        s1 = sub(':..', '', start)
                        date = str(self.postdate) + 'FIN'
                        date = sub('..FIN', '', date)
                        date = date + self.day
                        parts = start.split(':')
                        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                        start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                        s2 = sub(':..:..', '', start)
                        if int(s2) > int(s1):
                            start = str(self.date) + ' ' + start
                        else:
                            start = date + ' ' + start
                        start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                        start = int(mktime(start.timetuple()))
                        epgcache = eEPGCache.getInstance()
                        event = epgcache.startTimeQuery(eServiceReference(sref), start)
                        if event == -1:
                            self.EPGText = getEPGText()

                        else:
                            event = epgcache.getNextTimeEntry()
                            self.EPGtext = event.getEventName()
                            short = event.getShortDescription()
                            ext = event.getExtendedDescription()
                            dur = '%d Minuten' % (event.getDuration() / 60)
                            if short and short != self.EPGtext:
                                self.EPGtext += '\n\n' + short
                            if ext:
                                self.EPGtext += '\n\n' + ext
                            if dur:
                                self.EPGtext += '\n\n' + dur
                    except:
                        self.EPGText = getEPGText()

                else:
                    self.EPGtext = NOEPG
                fill = self.getFill(channel)
                self.EPGtext += '\n\n' + fill
                self['textpage'].setText(self.EPGtext)
                self['textpage'].show()
            else:
                self.showEPG = False
                self['textpage'].setText(self.POSTtext)
                self['textpage'].show()
        elif self.current != 'postview' and self.ready == True and self.search == False:
            self.oldindex = 0
            if self.abends == True:
                self.morgens = False
                self.mittags = False
                self.vorabend = False
                self.abends = False
                self.nachts = True
                self.makeTVView('')
            elif self.nachts == True:
                self.morgens = True
                self.mittags = False
                self.vorabend = False
                self.abends = False
                self.nachts = False
                self.makeTVView('')
            elif self.morgens == True:
                self.morgens = False
                self.mittags = True
                self.vorabend = False
                self.abends = False
                self.nachts = False
                self.makeTVView('')
            elif self.mittags == True:
                self.morgens = False
                self.mittags = False
                self.vorabend = True
                self.abends = False
                self.nachts = False
                self.makeTVView('')
            elif self.vorabend == True:
                self.morgens = False
                self.mittags = False
                self.vorabend = False
                self.abends = True
                self.nachts = False
                self.makeTVView('')
        return

    def red(self):
        if self.current == 'postview' and self.postviewready == True:
            if self.oldcurrent == 'menu1' and self.zap1 == True:
                c = self['menu1'].getSelectedIndex()
                self.oldindex = c
                try:
                    sref = self.sref1[0]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                start = self.start
                s1 = sub(':..', '', start)
                date = str(self.postdate) + 'FIN'
                date = sub('..FIN', '', date)
                date = date + self.day
                parts = start.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds -= int(config.recording.margin_before.value) * 60
                start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                s2 = sub(':..:..', '', start)
                if int(s2) > int(s1):
                    start = str(self.date) + ' ' + start
                else:
                    start = date + ' ' + start
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = self.end
                parts = end.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds += int(config.recording.margin_after.value) * 60
                end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                e2 = sub(':..:..', '', end)
                if int(s2) > int(e2):
                    end = str(self.nextdate) + ' ' + end
                else:
                    end = date + ' ' + end
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.oldcurrent == 'menu2' and self.zap2 == True:
                c = self['menu2'].getSelectedIndex()
                self.oldindex = c
                try:
                    sref = self.sref2[0]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                start = self.start
                s1 = sub(':..', '', start)
                date = str(self.postdate) + 'FIN'
                date = sub('..FIN', '', date)
                date = date + self.day
                parts = start.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds -= int(config.recording.margin_before.value) * 60
                start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                s2 = sub(':..:..', '', start)
                if int(s2) > int(s1):
                    start = str(self.date) + ' ' + start
                else:
                    start = date + ' ' + start
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = self.end
                parts = end.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds += int(config.recording.margin_after.value) * 60
                end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                e2 = sub(':..:..', '', end)
                if int(s2) > int(e2):
                    end = str(self.nextdate) + ' ' + end
                else:
                    end = date + ' ' + end
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.oldcurrent == 'menu3' and self.zap3 == True:
                c = self['menu3'].getSelectedIndex()
                self.oldindex = c
                try:
                    sref = self.sref3[0]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                start = self.start
                s1 = sub(':..', '', start)
                date = str(self.postdate) + 'FIN'
                date = sub('..FIN', '', date)
                date = date + self.day
                parts = start.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds -= int(config.recording.margin_before.value) * 60
                start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                s2 = sub(':..:..', '', start)
                if int(s2) > int(s1):
                    start = str(self.date) + ' ' + start
                else:
                    start = date + ' ' + start
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = self.end
                parts = end.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds += int(config.recording.margin_after.value) * 60
                end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                e2 = sub(':..:..', '', end)
                if int(s2) > int(e2):
                    end = str(self.nextdate) + ' ' + end
                else:
                    end = date + ' ' + end
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.oldcurrent == 'menu4' and self.zap4 == True:
                c = self['menu4'].getSelectedIndex()
                self.oldindex = c
                try:
                    sref = self.sref4[0]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                start = self.start
                s1 = sub(':..', '', start)
                date = str(self.postdate) + 'FIN'
                date = sub('..FIN', '', date)
                date = date + self.day
                parts = start.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds -= int(config.recording.margin_before.value) * 60
                start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                s2 = sub(':..:..', '', start)
                if int(s2) > int(s1):
                    start = str(self.date) + ' ' + start
                else:
                    start = date + ' ' + start
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = self.end
                parts = end.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds += int(config.recording.margin_after.value) * 60
                end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                e2 = sub(':..:..', '', end)
                if int(s2) > int(e2):
                    end = str(self.nextdate) + ' ' + end
                else:
                    end = date + ' ' + end
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.oldcurrent == 'menu5' and self.zap5 == True:
                c = self['menu5'].getSelectedIndex()
                self.oldindex = c
                try:
                    sref = self.sref5[0]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                start = self.start
                s1 = sub(':..', '', start)
                date = str(self.postdate) + 'FIN'
                date = sub('..FIN', '', date)
                date = date + self.day
                parts = start.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds -= int(config.recording.margin_before.value) * 60
                start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                s2 = sub(':..:..', '', start)
                if int(s2) > int(s1):
                    start = str(self.date) + ' ' + start
                else:
                    start = date + ' ' + start
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = self.end
                parts = end.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds += int(config.recording.margin_after.value) * 60
                end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                e2 = sub(':..:..', '', end)
                if int(s2) > int(e2):
                    end = str(self.nextdate) + ' ' + end
                else:
                    end = date + ' ' + end
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.oldcurrent == 'menu6' and self.zap6 == True:
                c = self['menu6'].getSelectedIndex()
                self.oldindex = c
                try:
                    sref = self.sref6[0]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                start = self.start
                s1 = sub(':..', '', start)
                date = str(self.postdate) + 'FIN'
                date = sub('..FIN', '', date)
                date = date + self.day
                parts = start.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds -= int(config.recording.margin_before.value) * 60
                start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                s2 = sub(':..:..', '', start)
                if int(s2) > int(s1):
                    start = str(self.date) + ' ' + start
                else:
                    start = date + ' ' + start
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = self.end
                parts = end.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds += int(config.recording.margin_after.value) * 60
                end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                e2 = sub(':..:..', '', end)
                if int(s2) > int(e2):
                    end = str(self.nextdate) + ' ' + end
                else:
                    end = date + ' ' + end
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            elif self.oldcurrent == 'searchmenu':
                c = self['searchmenu'].getSelectedIndex()
                self.oldsearchindex = c
                try:
                    c = self['searchmenu'].getSelectedIndex()
                    sref = self.searchref[c]
                    serviceref = ServiceReference(sref)
                except IndexError:
                    serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())

                start = self.start
                s1 = sub(':..', '', start)
                date = str(self.postdate) + 'FIN'
                date = sub('..FIN', '', date)
                date = date + self.day
                parts = start.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds -= int(config.recording.margin_before.value) * 60
                start = time.strftime('%H:%M:%S', time.gmtime(seconds))
                s2 = sub(':..:..', '', start)
                if int(s2) > int(s1):
                    start = str(self.date) + ' ' + start
                else:
                    start = date + ' ' + start
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = self.end
                parts = end.split(':')
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                seconds += int(config.recording.margin_after.value) * 60
                end = time.strftime('%H:%M:%S', time.gmtime(seconds))
                e2 = sub(':..:..', '', end)
                if int(s2) > int(e2):
                    end = str(self.nextdate) + ' ' + end
                else:
                    end = date + ' ' + end
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                name = self.name
                shortdesc = self.shortdesc
                if search('Staffel [0-9]+, Folge [0-9]+', shortdesc) is not None:
                    episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
                    episode = sub('Staffel ', 'S', episode.group(1))
                    episode = sub(', Folge ', 'E', episode)
                    name = name + ' ' + episode
                data = (int(mktime(start.timetuple())),
                 int(mktime(end.timetuple())),
                 name,
                 shortdesc,
                 None)
                newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
                if self.autotimer == False:
                    self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
                else:
                    from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
                    from Plugins.Extensions.AutoTimer.plugin import autotimer
                    if autotimer is None:
                        from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                        autotimer = AutoTimer()
                    autotimer.readXml()
                    newTimer = autotimer.defaultTimer.clone()
                    newTimer.id = autotimer.getUniqueId()
                    newTimer.name = self.name
                    newTimer.match = ''
                    newTimer.enabled = True
                    self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
            else:
                self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
        elif self.current == 'menu1' and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink1[c]
                if search('www.tvspielfilm.de', self.postlink) is not None:
                    self.oldcurrent = self.current
                    self.download(self.postlink, self.makePostTimer)
            except IndexError:
                pass

        elif self.current == 'menu2' and self.ready == True:
            c = self['menu2'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink2[c]
                if search('www.tvspielfilm.de', self.postlink) is not None:
                    self.oldcurrent = self.current
                    self.download(self.postlink, self.makePostTimer)
            except IndexError:
                pass

        elif self.current == 'menu3' and self.ready == True:
            c = self['menu3'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink3[c]
                if search('www.tvspielfilm.de', self.postlink) is not None:
                    self.oldcurrent = self.current
                    self.download(self.postlink, self.makePostTimer)
            except IndexError:
                pass

        elif self.current == 'menu4' and self.ready == True:
            c = self['menu4'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink4[c]
                if search('www.tvspielfilm.de', self.postlink) is not None:
                    self.oldcurrent = self.current
                    self.download(self.postlink, self.makePostTimer)
            except IndexError:
                pass

        elif self.current == 'menu5' and self.ready == True:
            c = self['menu5'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink5[c]
                if search('www.tvspielfilm.de', self.postlink) is not None:
                    self.oldcurrent = self.current
                    self.download(self.postlink, self.makePostTimer)
            except IndexError:
                pass

        elif self.current == 'menu6' and self.ready == True:
            c = self['menu6'].getSelectedIndex()
            self.oldindex = c
            try:
                self.postlink = self.tvlink6[c]
                if search('www.tvspielfilm.de', self.postlink) is not None:
                    self.oldcurrent = self.current
                    self.download(self.postlink, self.makePostTimer)
            except IndexError:
                pass

        elif self.current == 'searchmenu':
            c = self['searchmenu'].getSelectedIndex()
            self.oldsearchindex = c
            try:
                self.postlink = self.searchlink[c]
                if search('www.tvspielfilm.de', self.postlink) is not None:
                    self.oldcurrent = self.current
                    self.download(self.postlink, self.makePostTimer)
            except IndexError:
                pass

        return

    def finishedTimer(self, answer):
        if answer[0]:
            entry = answer[1]
            simulTimerList = self.session.nav.RecordTimer.record(entry)
            if simulTimerList is not None:
                for x in simulTimerList:
                    if x.setAutoincreaseEnd(entry):
                        self.session.nav.RecordTimer.timeChanged(x)

                simulTimerList = self.session.nav.RecordTimer.record(entry)
                if simulTimerList is not None:
                    self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
            self.makeTimerDB()
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
                self.makeTVView('')
            else:
                self.showsearch()
        else:
            self.ready = True
            self.postviewready = False
            self.current = self.oldcurrent
            if self.search == False:
                self.showProgrammPage()
            else:
                self.showsearch()
        return

    def green(self):
        if self.current == 'menu1' and self.zap1 == True and self.search == False:
            try:
                sref = self.sref1[0]
                self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

        elif self.current == 'menu2' and self.zap2 == True and self.search == False:
            try:
                sref = self.sref2[0]
                self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

        elif self.current == 'menu3' and self.zap3 == True and self.search == False:
            try:
                sref = self.sref3[0]
                self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

        elif self.current == 'menu4' and self.zap4 == True and self.search == False:
            try:
                sref = self.sref4[0]
                self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

        elif self.current == 'menu5' and self.zap5 == True and self.search == False:
            try:
                sref = self.sref5[0]
                self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

        elif self.current == 'menu6' and self.zap6 == True and self.search == False:
            try:
                sref = self.sref6[0]
                self.session.nav.playService(eServiceReference(sref))
            except IndexError:
                pass

    def yellow(self):
        if self.current == 'postview':
            self.youTube()
        elif self.search == False and self.ready == True:
            self.currentsearch = self.current
            if self.current == 'menu1':
                c = self['menu1'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel1[c]
                except IndexError:
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

            elif self.current == 'menu2':
                c = self['menu2'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel2[c]
                except IndexError:
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

            elif self.current == 'menu3':
                c = self['menu3'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel3[c]
                except IndexError:
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

            elif self.current == 'menu4':
                c = self['menu4'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel4[c]
                except IndexError:
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

            elif self.current == 'menu5':
                c = self['menu5'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel5[c]
                except IndexError:
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

            elif self.current == 'menu6':
                c = self['menu6'].getSelectedIndex()
                self.oldindex = c
                try:
                    titel = self.tvtitel6[c]
                except IndexError:
                    self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

            self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)

    def searchReturn(self, search):
        if search and search != '':
            self.searchstring = search
            self['sender1'].hide()
            self['sender2'].hide()
            self['sender3'].hide()
            self['sender4'].hide()
            self['sender5'].hide()
            self['sender6'].hide()
            self['logo1'].hide()
            self['logo2'].hide()
            self['logo3'].hide()
            self['logo4'].hide()
            self['logo5'].hide()
            self['logo6'].hide()
            self['pic1'].hide()
            self['pic2'].hide()
            self['pic3'].hide()
            self['pic4'].hide()
            self['pic5'].hide()
            self['pic6'].hide()
            self['pictime1'].hide()
            self['pictime2'].hide()
            self['pictime3'].hide()
            self['pictime4'].hide()
            self['pictime5'].hide()
            self['pictime6'].hide()
            self['pictext1'].hide()
            self['pictext2'].hide()
            self['pictext3'].hide()
            self['pictext4'].hide()
            self['pictext5'].hide()
            self['pictext6'].hide()
            self['menu1'].hide()
            self['menu2'].hide()
            self['menu3'].hide()
            self['menu4'].hide()
            self['menu5'].hide()
            self['menu6'].hide()
            self['label'].setText('')
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            self['searchlogo'].show()
            self['searchtimer'].show()
            self.searchlink = []
            self.searchref = []
            self.searchentries = []
            self.search = True
            self.datum = False
            self.filter = True
            search = search.replace(' ', '+')
            searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
            self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
            self.searchcount = 0
            self.makeSearchView(searchlink)

    def pressText(self):
        self._pressText()

    def youTube(self):
        if self.current == 'postview' and self.postviewready == True:
            self.session.open(searchYouTube, self.name, self.movie)
        elif self.current == 'menu1' and self.search == False and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            try:
                titel = self.tvtitel1[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

        elif self.current == 'menu2' and self.search == False and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            try:
                titel = self.tvtitel2[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

        elif self.current == 'menu3' and self.search == False and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            try:
                titel = self.tvtitel3[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

        elif self.current == 'menu4' and self.search == False and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            try:
                titel = self.tvtitel4[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

        elif self.current == 'menu5' and self.search == False and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            try:
                titel = self.tvtitel5[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

        elif self.current == 'menu6' and self.search == False and self.ready == True:
            c = self['menu1'].getSelectedIndex()
            try:
                titel = self.tvtitel6[c]
                self.session.open(searchYouTube, titel, self.movie)
            except IndexError:
                pass

    def gotoPageMenu(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.session.openWithCallback(self.numberEntered, gotoPageMenu, self.count, self.maxpages)

    def gotoPage(self, number):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.session.openWithCallback(self.numberEntered, getNumber, number)
        elif self.current == 'searchmenu' and self.search == True and self.ready == True and number == 0:
            end = len(self.searchentries) - 1
            self['searchmenu'].moveToIndex(end)
        elif self.current == 'postview' and number == 1:
            self.zapDown()
        elif self.current == 'postview' and number == 2:
            self.zapUp()
        elif self.current == 'postview' and number == 7:
            self.IMDb()
        elif self.current == 'postview' and number == 8:
            self.TMDb()
        elif self.current == 'postview' and number == 9:
            self.TVDb()

    def numberEntered(self, number):
        if self.current != 'postview' and self.ready == True and self.search == False:
            if number is None or number == 0:
                pass
            else:
                if number >= self.maxpages:
                    number = self.maxpages
                self.count = number
                if search('date', self.link) is not None:
                    self.link = self.link + 'FIN'
                    date = re.findall('date=(.*?)FIN', self.link)
                    self.link = sub('page=.*?FIN', '', self.link)
                    self.link = self.link + 'page=' + str(self.count) + '&date=' + date[0]
                else:
                    self.link = self.link + 'FIN'
                    self.link = sub('page=.*?FIN', '', self.link)
                    self.link = self.link + 'page=' + str(self.count)
                self['label'].setText('Bitte warten...')
                self['label'].startBlinking()
                self.ready = False
                self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
        return

    def nextDay(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_day = datetime.timedelta(days=1)
                tomorrow = today + one_day
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextday = sub('date=(.*?FIN)', 'date=', self.link)
                nextday = nextday + str(tomorrow)
                self.date = tomorrow
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            else:
                today = datetime.date.today()
                one_day = datetime.timedelta(days=1)
                tomorrow = today + one_day
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextday = self.link + '&date=' + str(tomorrow)
                self.date = tomorrow
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            self.link = nextday
            self.oldindex = 0
            self['label'].setText('Bitte warten...')
            self['label'].startBlinking()
            self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
        elif self.current == 'postview' or self.search == True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)
        return

    def prevDay(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_day = datetime.timedelta(days=1)
                yesterday = today - one_day
                self.weekday = makeWeekDay(yesterday.weekday())
                prevday = sub('date=(.*?FIN)', 'date=', self.link)
                prevday = prevday + str(yesterday)
                self.date = yesterday
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            else:
                today = datetime.date.today()
                one_day = datetime.timedelta(days=1)
                yesterday = today - one_day
                self.weekday = makeWeekDay(yesterday.weekday())
                prevday = self.link + '&date=' + str(yesterday)
                self.date = yesterday
                one_day = datetime.timedelta(days=1)
                self.nextdate = self.date + one_day
            self.link = prevday
            self.oldindex = 0
            self['label'].setText('Bitte warten...')
            self['label'].startBlinking()
            self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
        elif self.current == 'postview' or self.search == True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)
        return

    def nextWeek(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_week = datetime.timedelta(days=7)
                tomorrow = today + one_week
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextweek = sub('date=(.*?FIN)', 'date=', self.link)
                nextweek = nextweek + str(tomorrow)
                self.date = tomorrow
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            else:
                today = datetime.date.today()
                one_week = datetime.timedelta(days=7)
                tomorrow = today + one_week
                self.weekday = makeWeekDay(tomorrow.weekday())
                nextweek = self.link + '&date=' + str(tomorrow)
                self.date = tomorrow
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            self.link = nextweek
            self.oldindex = 0
            self['label'].setText('Bitte warten...')
            self['label'].startBlinking()
            self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
        return

    def prevWeek(self):
        if self.current != 'postview' and self.ready == True and self.search == False:
            self.ready = False
            if search('date', self.link) is not None:
                self.link = self.link + 'FIN'
                date1 = re.findall('date=(.*?)-..-..FIN', self.link)
                date2 = re.findall('date=....-(.*?)-..FIN', self.link)
                date3 = re.findall('date=....-..-(.*?)FIN', self.link)
                try:
                    today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
                except IndexError:
                    today = datetime.date.today()

                one_week = datetime.timedelta(days=7)
                yesterday = today - one_week
                self.weekday = makeWeekDay(yesterday.weekday())
                prevweek = sub('date=(.*?FIN)', 'date=', self.link)
                prevweek = prevweek + str(yesterday)
                self.date = yesterday
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            else:
                today = datetime.date.today()
                one_week = datetime.timedelta(days=7)
                yesterday = today - one_week
                self.weekday = makeWeekDay(yesterday.weekday())
                prevweek = self.link + '&date=' + str(yesterday)
                self.date = yesterday
                one_week = datetime.timedelta(days=7)
                self.nextdate = self.date + one_week
            self.link = prevweek
            self.oldindex = 0
            self['label'].setText('Bitte warten...')
            self['label'].startBlinking()
            self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
        return

    def rightDown(self):
        try:
            if self.current == 'menu1':
                self['menu1'].selectionEnabled(0)
                self['menu2'].selectionEnabled(1)
                self.current = 'menu2'
            elif self.current == 'menu2':
                self['menu2'].selectionEnabled(0)
                self['menu3'].selectionEnabled(1)
                self.current = 'menu3'
            elif self.current == 'menu3':
                self['menu3'].selectionEnabled(0)
                self['menu4'].selectionEnabled(1)
                self.current = 'menu4'
            elif self.current == 'menu4':
                self['menu4'].selectionEnabled(0)
                self['menu5'].selectionEnabled(1)
                self.current = 'menu5'
            elif self.current == 'menu5':
                self['menu5'].selectionEnabled(0)
                self['menu6'].selectionEnabled(1)
                self.current = 'menu6'
            elif self.current == 'menu6':
                self['menu6'].selectionEnabled(0)
                self['menu1'].selectionEnabled(1)
                self.current = 'menu1'
                self.count += 1
                if self.count > self.maxpages:
                    self.count = 1
                if search('date', self.link) is not None:
                    self.link = self.link + 'FIN'
                    date = re.findall('date=(.*?)FIN', self.link)
                    self.link = sub('page=.*?FIN', '', self.link)
                    self.link = self.link + 'page=' + str(self.count) + '&date=' + date[0]
                else:
                    self.link = self.link + 'FIN'
                    self.link = sub('page=.*?FIN', '', self.link)
                    self.link = self.link + 'page=' + str(self.count)
                self['label'].setText('Bitte warten...')
                self['label'].startBlinking()
                self.ready = False
                self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
            elif self.current == 'searchmenu':
                self['searchmenu'].pageDown()
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

        return

    def leftUp(self):
        try:
            if self.current == 'menu6':
                self['menu6'].selectionEnabled(0)
                self['menu5'].selectionEnabled(1)
                self.current = 'menu5'
            elif self.current == 'menu5':
                self['menu5'].selectionEnabled(0)
                self['menu4'].selectionEnabled(1)
                self.current = 'menu4'
            elif self.current == 'menu4':
                self['menu4'].selectionEnabled(0)
                self['menu3'].selectionEnabled(1)
                self.current = 'menu3'
            elif self.current == 'menu3':
                self['menu3'].selectionEnabled(0)
                self['menu2'].selectionEnabled(1)
                self.current = 'menu2'
            elif self.current == 'menu2':
                self['menu2'].selectionEnabled(0)
                self['menu1'].selectionEnabled(1)
                self.current = 'menu1'
            elif self.current == 'menu1':
                self['menu1'].selectionEnabled(0)
                self['menu6'].selectionEnabled(1)
                self.current = 'menu6'
                self.count -= 1
                if self.count == 0:
                    self.count = self.maxpages
                if search('date', self.link) is not None:
                    self.link = self.link + 'FIN'
                    date = re.findall('date=(.*?)FIN', self.link)
                    self.link = sub('page=.*?FIN', '', self.link)
                    self.link = self.link + 'page=' + str(self.count) + '&date=' + date[0]
                else:
                    self.link = self.link + 'FIN'
                    self.link = sub('page=.*?FIN', '', self.link)
                    self.link = self.link + 'page=' + str(self.count)
                self['label'].setText('Bitte warten...')
                self['label'].startBlinking()
                self.ready = False
                self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVView))
            elif self.current == 'searchmenu':
                self['searchmenu'].pageUp()
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

        return

    def down(self):
        try:
            if self.current == 'searchmenu':
                self['searchmenu'].down()
            elif self.current.startswith("menu"):
                for i in range(6):
                    if self.current == 'menu' + str(i + 1):
                        start = i + 1
                        for x in range(6):
                            self['menu' + str(start)].down()
                            start = start + 1
                            if start > 6:
                                start = 1
                        break
            else:
                self['textpage'].pageDown()
        except IndexError:
            pass

    def up(self):
        try:
            if self.current == 'searchmenu':
                self['searchmenu'].up()
            elif self.current.startswith("menu"):
                for i in range(6):
                    if self.current == 'menu' + str(i + 1):
                        start = i + 1
                        for x in range(6):
                            self['menu' + str(start)].up()
                            start = start + 1
                            if start > 6:
                                start = 1
                        break
            else:
                self['textpage'].pageUp()
        except IndexError:
            pass

    def findPicon(self, sref):
        sref = sref + 'FIN'
        sref = sref.replace(':', '_')
        sref = sref.replace('_FIN', '')
        sref = sref.replace('FIN', '')
        pngname = self.piconfolder + sref + '.png'
        if fileExists(pngname):
            return pngname

    def showLogo1(self, logo):
        currPic = loadPic(logo, 44, 27, 3, 0, 0, 0)
        if currPic != None:
            self['logo1'].instance.setPixmap(currPic)
        return

    def showLogo2(self, logo):
        currPic = loadPic(logo, 44, 27, 3, 0, 0, 0)
        if currPic != None:
            self['logo2'].instance.setPixmap(currPic)
        return

    def showLogo3(self, logo):
        currPic = loadPic(logo, 44, 27, 3, 0, 0, 0)
        if currPic != None:
            self['logo3'].instance.setPixmap(currPic)
        return

    def showLogo4(self, logo):
        currPic = loadPic(logo, 44, 27, 3, 0, 0, 0)
        if currPic != None:
            self['logo4'].instance.setPixmap(currPic)
        return

    def showLogo5(self, logo):
        currPic = loadPic(logo, 44, 27, 3, 0, 0, 0)
        if currPic != None:
            self['logo5'].instance.setPixmap(currPic)
        return

    def showLogo6(self, logo):
        currPic = loadPic(logo, 44, 27, 3, 0, 0, 0)
        if currPic != None:
            self['logo6'].instance.setPixmap(currPic)
        return

    def getPic1(self, output):
        f = open(self.pic1, 'wb')
        f.write(output)
        f.close()
        self.showPic1(self.pic1)

    def showPic1(self, tvpic):
        currPic = loadPic(tvpic, 200, 133, 3, 0, 0, 0)
        if currPic != None:
            self['pic1'].instance.setPixmap(currPic)
        return

    def getPic2(self, output):
        f = open(self.pic2, 'wb')
        f.write(output)
        f.close()
        self.showPic2(self.pic2)

    def showPic2(self, tvpic):
        currPic = loadPic(tvpic, 200, 133, 3, 0, 0, 0)
        if currPic != None:
            self['pic2'].instance.setPixmap(currPic)
        return

    def getPic3(self, output):
        f = open(self.pic3, 'wb')
        f.write(output)
        f.close()
        self.showPic3(self.pic3)

    def showPic3(self, tvpic):
        currPic = loadPic(tvpic, 200, 133, 3, 0, 0, 0)
        if currPic != None:
            self['pic3'].instance.setPixmap(currPic)
        return

    def getPic4(self, output):
        f = open(self.pic4, 'wb')
        f.write(output)
        f.close()
        self.showPic4(self.pic4)

    def showPic4(self, tvpic):
        currPic = loadPic(tvpic, 200, 133, 3, 0, 0, 0)
        if currPic != None:
            self['pic4'].instance.setPixmap(currPic)
        return

    def getPic5(self, output):
        f = open(self.pic5, 'wb')
        f.write(output)
        f.close()
        self.showPic5(self.pic5)

    def showPic5(self, tvpic):
        currPic = loadPic(tvpic, 200, 133, 3, 0, 0, 0)
        if currPic != None:
            self['pic5'].instance.setPixmap(currPic)
        return

    def getPic6(self, output):
        f = open(self.pic6, 'wb')
        f.write(output)
        f.close()
        self.showPic6(self.pic6)

    def showPic6(self, tvpic):
        currPic = loadPic(tvpic, 200, 133, 3, 0, 0, 0)
        if currPic != None:
            self['pic6'].instance.setPixmap(currPic)
        return

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        currPic = loadPic(picpost, 490, 245, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
            self['piclabel'].show()
            self['piclabel2'].show()
            if self.trailer == True:
                self['cinlogo'].show()
                self['playlogo'].show()
        return

    def showPicTVinfoX(self, picinfo, X):
        currPic = loadPic(picinfo, 60, 20, 3, 0, 0, 0)
        if currPic != None:
            self[X].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(six.ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadPostPage(self, link, name):
        downloadPage(six.ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        if self.MeinTVS == True:
            try:
                response = self.opener.open(link, timeout=60)
                data = response.read()
                f = open(self.localhtml, 'wb')
                f.write(data)
                f.close()
                response.close()
            except HTTPException as e:
                self.error = 'HTTP Exception Error ' + str(e)
            except HTTPError as e:
                self.error = 'HTTP Error: ' + str(e.code)
            except URLError as e:
                self.error = 'URL Error: ' + str(e.reason)
            except socket.error as e:
                self.error = 'Socket Error: ' + str(e)
            except AttributeError as e:
                self.error = 'Attribute Error: ' + str(e.message)

            if self.error == False:
                self.makeTVView('')
            else:
                self.makeErrorTimer = eTimer()
                self.makeErrorTimer.callback.append(self.displayError)
                self.makeErrorTimer.start(500, True)
        else:
            downloadPage(six.ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

    def displayError(self):
        self.session.openWithCallback(self.closeError, MessageBox, '%s' % self.error, MessageBox.TYPE_ERROR)

    def closeError(self, retval):
        self.close()

    def downloadPageError(self, output):
        print(output)
        self['label'].setText('Info = +- Tageszeit, Bouquet = +- Tag, <> = +- Woche, Menue = Senderliste')
        self['label'].stopBlinking()
        self['label'].show()
        self.ready = True

    def showProgrammPage(self):
        self['label'].setText('Info = +- Tageszeit, Bouquet = +- Tag, <> = +- Woche, Menue = Senderliste')
        self['label2'].setText('= Timer')
        self['label3'].setText('= Suche')
        self['label4'].setText('= Zappen')
        self['infotext'].hide()
        self['infotext2'].hide()
        self['infotext3'].hide()
        self['infotext4'].hide()
        self['infotext5'].hide()
        self['infotext6'].hide()
        self['infotext7'].hide()
        self['infotext8'].hide()
        self['cinlogo'].hide()
        self['playlogo'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
        self['piclabel'].hide()
        self['piclabel2'].hide()
        self['tvinfo1'].hide()
        self['tvinfo2'].hide()
        self['tvinfo3'].hide()
        self['tvinfo4'].hide()
        self['tvinfo5'].hide()
        self['searchmenu'].hide()
        self['searchlogo'].hide()
        self['searchtimer'].hide()
        self['searchtext'].hide()
        self['sender1'].show()
        self['sender2'].show()
        self['sender3'].show()
        self['sender4'].show()
        self['sender5'].show()
        self['sender6'].show()
        self['logo1'].show()
        self['logo2'].show()
        self['logo3'].show()
        self['logo4'].show()
        self['logo5'].show()
        self['logo6'].show()
        self['pic1'].show()
        self['pic2'].show()
        self['pic3'].show()
        self['pic4'].show()
        self['pic5'].show()
        self['pic6'].show()
        self['pictime1'].show()
        self['pictime2'].show()
        self['pictime3'].show()
        self['pictime4'].show()
        self['pictime5'].show()
        self['pictime6'].show()
        self['pictext1'].show()
        self['pictext2'].show()
        self['pictext3'].show()
        self['pictext4'].show()
        self['pictext5'].show()
        self['pictext6'].show()
        self['menu1'].show()
        self['menu2'].show()
        self['menu3'].show()
        self['menu4'].show()
        self['menu5'].show()
        self['menu6'].show()

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu1' or self.current == 'menu2' or self.current == 'menu3' or self.current == 'menu4' or self.current == 'menu5' or self.current == 'menu6':
            self.close()
        elif self.current == 'searchmenu':
            self.search = False
            self.oldsearchindex = 1
            self['searchmenu'].hide()
            self['searchlogo'].hide()
            self['searchtimer'].hide()
            self['searchtext'].hide()
            self.setTitle('')
            self.setTitle(self.titel)
            self.current = self.currentsearch
            self.showProgrammPage()
        elif self.current == 'postview' and self.search == False:
            self.postviewready = False
            self.setTitle('')
            self.setTitle(self.titel)
            self.current = self.oldcurrent
            self.showProgrammPage()
        elif self.current == 'postview' and self.search == True:
            self.postviewready = False
            self.showsearch()
            self.current = 'searchmenu'

def main(session, **kwargs):
    session.open(tvMain)

def mainjetzt(session, **kwargs):
    session.open(tvJetzt, 'https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html')

def mainprime(session, **kwargs):
    session.open(tvJetzt, 'https://www.tvspielfilm.de/tv-programm/sendungen/abends.html')

def mainevent(session, **kwargs):
    session.open(tvEvent)

def Plugins(**kwargs):
    return [PluginDescriptor(name='TV Spielfilm', description='TV Spielfilm', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main),
     PluginDescriptor(name='TV Spielfilm 20:15', description='TV Spielfilm Prime Time', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=mainprime),
     PluginDescriptor(name='TV Spielfilm Jetzt', description='TV Spielfilm Jetzt im TV', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='jetzt.png', fnc=mainjetzt),
     PluginDescriptor(name='TV Spielfilm EventView', description='TV Spielfilm EventView', where=[PluginDescriptor.WHERE_EVENTINFO], fnc=mainevent)]
    
