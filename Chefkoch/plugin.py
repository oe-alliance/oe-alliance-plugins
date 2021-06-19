from __future__ import print_function
# Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/Chefkoch.py
from base64 import b64encode, b64decode
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, configfile, ConfigSubsection, ConfigInteger, ConfigPassword, ConfigSelection, ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Input import Input
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap, MovingPixmap
from Components.ScrollLabel import ScrollLabel
from Components.Slider import Slider
from Components.Sources.List import List
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from enigma import eConsoleAppContainer, eListboxPythonMultiContent, eListbox, eServiceReference, ePicLoad, eTimer, getDesktop, gFont, loadPic, loadPNG, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
from Plugins.Plugin import PluginDescriptor
from re import findall, match, search, split, sub
from Screens.ChannelSelection import ChannelSelection
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from string import find
from Tools.Directories import fileExists
from twisted.web import client, error
from twisted.web.client import getPage, downloadPage
import os
import re
import smtplib
import sys
import time
import urllib
from os import path
from urllib import unquote_plus
from urllib2 import Request, urlopen, URLError
from urlparse import parse_qs
config.plugins.chefkoch = ConfigSubsection()
deskWidth = getDesktop(0).size().width()
if deskWidth >= 1280:
    config.plugins.chefkoch.plugin_size = ConfigSelection(default='full', choices=[('full', '1280x720'), ('normal', '1024x576')])
    config.plugins.chefkoch.position = ConfigInteger(60, (0, 80))
else:
    config.plugins.chefkoch.plugin_size = ConfigSelection(default='normal', choices=[('full', '1280x720'), ('normal', '1024x576')])
    config.plugins.chefkoch.position = ConfigInteger(40, (0, 160))
config.plugins.chefkoch.font_size = ConfigSelection(default='large', choices=[('large', 'Gro\xc3\x9f'), ('normal', 'Normal')])
config.plugins.chefkoch.font = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
if config.plugins.chefkoch.font.value == 'yes':
    from enigma import addFont
    try:
        addFont('/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/font/Sans.ttf', 'Sans', 100, False)
    except Exception as ex:
        addFont('/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/font/Sans.ttf', 'Sans', 100, False, 0)

config.plugins.chefkoch.fhd = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
if config.plugins.chefkoch.fhd.value == 'yes':
    from enigma import eSize, gMainDC
config.plugins.chefkoch.autoupdate = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.chefkoch.paypal = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.chefkoch.mail = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.chefkoch.mailfrom = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.mailto = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.login = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.password = ConfigPassword(default='', fixed_size=False)
config.plugins.chefkoch.server = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.port = ConfigInteger(465, (0, 99999))
config.plugins.chefkoch.ssl = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])


def applySkinVars(skin, dict):
    for key in dict.keys():
        try:
            skin = skin.replace('{' + key + '}', dict[key])
        except Exception as e:
            print(e, '@key=', key)

    return skin


def transHTML(text):
    text = text.replace('&nbsp;', ' ').replace('&#034;', '"').replace('&#039;', "'").replace('&szlig;', 'ss').replace('&quot;', '"').replace('&ndash;', '-').replace('&Oslash;', '').replace('&bdquo;', '"').replace('&ldquo;', '"').replace('&rsquo;', "'")
    text = text.replace('&copy;.*', ' ').replace('&amp;', '&').replace('&uuml;', '\xc3\xbc').replace('&auml;', '\xc3\xa4').replace('&ouml;', '\xc3\xb6').replace('&acute;', "'").replace('&eacute;', '\xe9').replace('&hellip;', '...').replace('&egrave;', '\xe8').replace('&agrave;', '\xe0')
    text = text.replace('&Uuml;', 'Ue').replace('&Auml;', 'Ae').replace('&Ouml;', 'Oe').replace('&#34;', '"').replace('&#38;', 'und').replace('&#39;', "'").replace('&#196;', 'Ae').replace('&#214;', 'Oe').replace('&#220;', 'Ue').replace('&#223;', 'ss').replace('&#228;', '\xc3\xa4').replace('&#246;', '\xc3\xb6').replace('&#252;', '\xc3\xbc')
    text = text.replace('&#188;', '1/4').replace('&#189;', '1/2').replace('&#190;', '3/4').replace('&#8531;', '1/3').replace('&#8532;', '2/3').replace('&#8533;', '1/5').replace('&#8534;', '2/5').replace('&#8535;', '3/5').replace('&#8536;', '4/5').replace('&#8537;', '1/6').replace('&#8538;', '5/6').replace('&#8539;', '1/8').replace('&#8540;', '3/8').replace('&#8541;', '5/8').replace('&#8542;', '7/8').replace('&#9829;', '').replace('&#9834;', '')
    return text


class ChefkochView(Screen):
    skin = '\n\t\t\t<screen position="center,{position}" size="1012,516" title="Chefkoch">\n\t\t\t\t<ePixmap position="0,0" size="1012,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/chefkoch.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="menu" position="10,60" size="880,450" scrollbarMode="showNever" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="890,60" size="112,75" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic2" position="890,135" size="112,75" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic3" position="890,210" size="112,75" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic4" position="890,285" size="112,75" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic5" position="890,360" size="112,75" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic6" position="890,435" size="112,75" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="picpost" position="393,60" size="225,150" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="score" position="6,60" size="157,24" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="scoretext" position="10,90" size="317,100" font="{font};{fontsize}" halign="left" zPosition="1" />\n\t\t\t\t<widget name="textpage" position="10,220" size="992,285" font="{font};{fontsize}" halign="left" zPosition="0" />\n\t\t\t\t<widget name="slider_textpage" position="986,220" size="22,285" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/slider/slider_285.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="250,7" size="512,20" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label2" position="485,27" size="150,20" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label3" position="415,27" size="350,20" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label4" position="71,0" size="175,50" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" valign="center" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label5" position="307,27" size="250,50" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label6" position="544,27" size="250,50" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget render="Label" source="global.CurrentTime" position="782,0" size="210,50" font="{font};24" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">\n\t\t\t\t\t<convert type="ClockToText">Format:%H:%M:%S</convert>\n\t\t\t\t</widget>\n\t\t\t\t<widget name="greenbutton" position="283,27" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="greenbutton2" position="391,27" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="redbutton" position="520,27" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="redbutton2" position="391,27" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="yellowbutton" position="461,27" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,{position}" size="1240,640" title="Chefkoch">\n\t\t\t\t<ePixmap position="0,0" size="1240,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/chefkochHD.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="menu" position="10,75" size="1085,540" scrollbarMode="showNever" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="1095,75" size="135,90" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic2" position="1095,165" size="135,90" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic3" position="1095,255" size="135,90" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic4" position="1095,345" size="135,90" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic5" position="1095,435" size="135,90" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="pic6" position="1095,525" size="135,90" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="picpost" position="470,70" size="300,200" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="score" position="3,70" size="236,36" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="scoretext" position="10,113" size="375,100" font="{font};{fontsize}" halign="left" zPosition="1" />\n\t\t\t\t<widget name="textpage" position="10,280" size="1220,365" font="{font};{fontsize}" halign="left" zPosition="0" />\n\t\t\t\t<widget name="slider_textpage" position="1214,280" size="22,360" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/slider/slider_360.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="300,10" size="640,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label2" position="595,31" size="150,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label3" position="514,31" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label4" position="98,0" size="180,60" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" valign="center" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label5" position="386,31" size="350,60" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label6" position="662,31" size="350,60" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget render="Label" source="global.CurrentTime" position="950,0" size="275,60" font="{font};26" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">\n\t\t\t\t\t<convert type="ClockToText">Format:%H:%M:%S</convert>\n\t\t\t\t</widget>\n\t\t\t\t<widget name="greenbutton" position="362,32" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="greenbutton2" position="490,32" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="redbutton" position="638,32" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="redbutton2" position="490,32" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="yellowbutton" position="571,32" size="18,18" alphatest="blend" zPosition="2" />\n\t\t\t</screen>'

    def __init__(self, session, link, fav, zufall, search, magazin, chefkochtv):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        if config.plugins.chefkoch.plugin_size.value == 'full':
            self.xd = False
            position = str(config.plugins.chefkoch.position.value)
            if config.plugins.chefkoch.font_size.value == 'large':
                self.fontlarge = True
                fontsize = '22'
            else:
                self.fontlarge = False
                fontsize = '20'
            self.dict = {'position': position,
             'font': font,
             'fontsize': fontsize}
            self.skin = applySkinVars(ChefkochView.skinHD, self.dict)
        else:
            self.xd = True
            deskWidth = getDesktop(0).size().width()
            if deskWidth >= 1280:
                position = 'center'
            else:
                position = str(config.plugins.chefkoch.position.value)
            if config.plugins.chefkoch.font_size.value == 'large':
                self.fontlarge = True
                fontsize = '20'
            else:
                self.fontlarge = False
                fontsize = '18'
            self.dict = {'position': position,
             'font': font,
             'fontsize': fontsize}
            self.skin = applySkinVars(ChefkochView.skin, self.dict)
        Screen.__init__(self, session)
        self.baseurl = 'http://www.chefkoch.de'
        self.picfile = '/tmp/chefkoch.jpg'
        self.pic1 = '/tmp/chefkoch1.jpg'
        self.pic2 = '/tmp/chefkoch2.jpg'
        self.pic3 = '/tmp/chefkoch3.jpg'
        self.pic4 = '/tmp/chefkoch4.jpg'
        self.pic5 = '/tmp/chefkoch5.jpg'
        self.pic6 = '/tmp/chefkoch6.jpg'
        self.rezeptfile = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/db/rezept.html'
        self.postlink = link
        self.link = link
        self.fav = fav
        self.zufall = zufall
        self.search = search
        self.magazin = magazin
        self.chefkochtv = chefkochtv
        self.hideflag = True
        self.ready = False
        self.postviewready = False
        self.morePic = False
        self.chefVideo = False
        self.youTube = False
        self.morerezepte = False
        self.comment = False
        self.downVideo = False
        self.len = 0
        self.count = 0
        self.maxpage = 0
        self.current = 'menu'
        self.titel = ''
        self.name = ''
        self.seitenlabel = ''
        self.searchtext = ''
        self.output = ''
        self.chefvideo = ''
        self.youtube = ''
        self.score = ''
        self.scoretext = ''
        self.kochentries = []
        self.kochlink = []
        self.picurllist = []
        self.titellist = []
        self.rezeptelist = []
        self.rezeptelinks = []
        self['pic1'] = Pixmap()
        self['pic2'] = Pixmap()
        self['pic3'] = Pixmap()
        self['pic4'] = Pixmap()
        self['pic5'] = Pixmap()
        self['pic6'] = Pixmap()
        self['picpost'] = Pixmap()
        self['score'] = Pixmap()
        self['scoretext'] = Label('')
        self['scoretext'].hide()
        self['redbutton'] = Pixmap()
        self['redbutton2'] = Pixmap()
        self['greenbutton'] = Pixmap()
        self['greenbutton2'] = Pixmap()
        self['yellowbutton'] = Pixmap()
        self['textpage'] = ScrollLabel('')
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['menu'] = ItemList([])
        self['label'] = Label('')
        self['label2'] = Label('')
        self['label3'] = Label('')
        self['label4'] = Label('')
        self['label5'] = Label('')
        self['label6'] = Label('')
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
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
         'red': self.red,
         'yellow': self.yellow,
         'green': self.green,
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
         '9': self.gotoPage,
         'displayHelp': self.infoScreen}, -1)
        self.makeChefkochTimer = eTimer()
        if self.fav == True:
            if self.chefkochtv == True:
                self.makeChefkochTimer.callback.append(self.download(link, self.makeVideoURL))
            elif self.magazin == True:
                self.maxpage = 50
                self.current = 'postview'
                self.makeChefkochTimer.callback.append(self.download(link, self.makePostviewPage))
            else:
                self.current = 'postview'
                self.makeChefkochTimer.callback.append(self.download(link, self.makePostviewPage))
        elif self.zufall == True:
            self.current = 'postview'
            self.makeChefkochTimer.callback.append(self.download(link, self.makePostviewPage))
        elif self.search == True:
            self.searchtext = sub('http://www.chefkoch.de/rs/s0/', '', link)
            self.searchtext = sub('/Rezepte.html', '', self.searchtext)
            self.makeChefkochTimer.callback.append(self.downloadSearch(link, self.makeChefkoch))
        elif self.magazin == True:
            self.maxpage = 50
            self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))
        else:
            self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))
        self.makeChefkochTimer.start(500, True)

    def makeChefkoch(self, output):
        self['pic1'].hide()
        self['pic2'].hide()
        self['pic3'].hide()
        self['pic4'].hide()
        self['pic5'].hide()
        self['pic6'].hide()
        self.kochentries = []
        self.kochlink = []
        self.titellist = []
        self.picurllist = []
        if self.magazin == False:
            self['label'].setText('Bouquet +- = Seite vor/zur\xfcck')
            self['label2'].setText('= Suche')
            seiten = search('pagination-pagelink-last"\\n\\s+rel="nofollow">(.*?)</a>', output)
            self.maxpage = int(seiten.group(1))
            seite = search('qa-pagination-current">\\n\\s+Seite (.*?)\\n', output)
            self.seitenlabel = 'Seite ' + seite.group(1) + ' von ' + seiten.group(1)
            self['label4'].setText('%s' % self.seitenlabel)
            yellowbutton = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/yellow.png'
            if fileExists(yellowbutton):
                self.showYellowButton(yellowbutton)
                self['yellowbutton'].show()
        if self.magazin == False:
            title = search('<meta name="description" content="(.*?)">', output)
        else:
            title = search('<title>(.*?)</title>', output)
        title = transHTML(title.group(1))
        self.titel = title
        self.setTitle(title)
        if self.magazin == False:
            startpos = find(output, '<ul class="search-list">')
            endpos = find(output, '<div class="js-show-more-recipes')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
            bereich = sub('<a href="', '<td>LINKhttp://www.chefkoch.de', bereich)
            bereich = sub('.html"', '.html</td>', bereich)
            bereich = sub('<div class="image-placeholder"></div>', '<img srcset="https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQQ2kfGpEH5kiDFjCeO_HUwJCITFgmB2oUzOgOph3mWdYm98mBv" alt=""', bereich)
            bereich = sub('<img srcset="', '<td>PIC', bereich)
            bereich = sub('" alt="', '</td>', bereich)
            bereich = sub('<div class="search-list-item-title">', '<td>TITEL', bereich)
            bereich = sub('</div>\n', '</td>', bereich)
            bereich = sub('uservotes-stars star', '<td>LOGOsuche-scrore', bereich)
            bereich = sub('uservotes-count">', '<td>COUNT', bereich)
            bereich = sub('" title="', '</td>" title="', bereich)
            bereich = sub('<p class="search-list-item-subtitle">\\s+', '<td>TEXT', bereich)
            bereich = sub('\\s+</p>', '</td>', bereich)
            bereich = sub('span class="search-list-item-preptime">', '<td>TIME', bereich)
            bereich = sub('min.</span>', 'min.</td>', bereich)
            bereich = sub('</span>\n\\s+</span>', '</td>', bereich)
        else:
            startpos = find(output, '<article class="teaser-box')
            endpos = find(output, '</main')
            bereich = output[startpos:endpos]
            bereich = re.sub('<section class="teaser-box".*?</section>', '', bereich, flags=re.S)
            bereich = transHTML(bereich)
            if self.chefkochtv == False:
                redbutton = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/red.png'
                if fileExists(redbutton):
                    self.showRedButton2(redbutton)
                    self['redbutton2'].show()
                self['label3'].setText('= Rubrik zu Favoriten hinzuf\xfcgen')
            else:
                greenbutton = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/green.png'
                if fileExists(greenbutton):
                    self.showGreenButton2(greenbutton)
                    self['greenbutton2'].show()
                self['label'].setText('OK = Video starten')
                self['label3'].setText('= Download Chefkoch TV Video')
            bereich = sub('<div class="views-rows">\n\\s+\n<a href="', '<td>LINKhttp://www.chefkoch.de', bereich)
            bereich = sub('<div class="views-rows">\n\\s+<a href="', '<td>LINKhttp://www.chefkoch.de', bereich)
            bereich = sub('" title="', '</td>" title="', bereich)
            bereich = sub('<img .*? data-src="', '<td>PIC', bereich)
            bereich = sub('" class="lazyload"', '</td>', bereich)
            bereich = sub('" /><noscript>', '</td>', bereich)
            if self.chefkochtv == False:
                bereich = sub('<h2>', '<td>TITELChefkoch Magazin: ', bereich)
            else:
                bereich = sub('<h2>', '<td>TITELChefkoch TV: ', bereich)
            bereich = sub('</h2>', '</td>', bereich)
            bereich = sub('<p>\n\\s+', '<td>TEXT', bereich)
            bereich = sub('<p>\\s+', '<td>TEXT', bereich)
            bereich = sub('\n</p>', '</td>', bereich)
            bereich = sub('</p>', '</td>', bereich)
        if self.magazin == False:
            a = findall('<td>(.*?)</td>', bereich, flags=re.S)
            y = 0
            offset = 7
            for x in a:
                if y == 0:
                    res = [x]
                    x = sub('LINK', '', x)
                    self.kochlink.append(x)
                if y == 1:
                    x = sub('PIC', '', x)
                    self.picurllist.append(x)
                if y == 2:
                    x = sub('TITEL', '', x)
                    x = sub('<span class="highlighting">', '', x)
                    x = sub('</span>', '', x)
                    self.titellist.append(x)
                    if self.xd == True:
                        res.append(MultiContentEntryText(pos=(95, 0), size=(780, 25), font=0, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    else:
                        res.append(MultiContentEntryText(pos=(110, 0), size=(965, 30), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                if y == 3:
                    x = sub('LOGO', '', x)
                    if self.xd == True:
                        png = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/logos/%s.png' % x
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(19, 30), size=(48, 9), png=loadPNG(png)))
                    else:
                        png = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/logos/%sHD.png' % x
                        if fileExists(png):
                            res.append(MultiContentEntryPixmapAlphaTest(pos=(12, 33), size=(72, 14), png=loadPNG(png)))
                if y == 4:
                    x = sub('COUNT', '', x)
                    if self.xd == True:
                        res.append(MultiContentEntryText(pos=(0, 42), size=(85, 23), font=0, color=16777215, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                    else:
                        res.append(MultiContentEntryText(pos=(0, 52), size=(95, 25), font=-1, color=16777215, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                if y == 5:
                    x = sub('TEXT', '', x)
                    x = sub('\n', '', x)
                    x = sub('<span class="highlighting">', '', x)
                    x = sub('</span>', '', x)
                    if self.xd == True:
                        res.append(MultiContentEntryText(pos=(95, 24), size=(780, 51), font=0, color=10857646, color_sel=13817818, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                    else:
                        res.append(MultiContentEntryText(pos=(111, 30), size=(965, 60), font=-1, color=10857646, color_sel=13817818, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                if y == 6:
                    x = sub('TIME', '', x)
                    if self.xd == True:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(85, 23), font=0, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                    else:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(95, 25), font=-1, backcolor=12255304, color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
                    self.kochentries.append(res)
                y += 1
                if y == offset:
                    y = 0

        else:
            a = findall('<td>(.*?)</td>', bereich, re.S)
            y = 0
            offset = 4
            for x in a:
                if y == 0:
                    res = [x]
                    x = sub('LINK', '', x)
                    self.kochlink.append(x)
                if y == 1:
                    x = sub('PIC', '', x)
                    self.picurllist.append(x)
                if y == 2:
                    x = sub('TITEL', '', x)
                    x = sub('Chefkoch TV: Chefkoch TV: ', 'Chefkoch TV: ', x)
                    self.titellist.append(x)
                    if self.xd == True:
                        res.append(MultiContentEntryText(pos=(10, 0), size=(865, 23), font=0, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                    else:
                        res.append(MultiContentEntryText(pos=(10, 0), size=(1065, 30), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
                if y == 3:
                    x = sub('TEXT', '', x)
                    if self.xd == True:
                        res.append(MultiContentEntryText(pos=(10, 23), size=(865, 45), font=0, color=10857646, color_sel=13817818, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                    else:
                        res.append(MultiContentEntryText(pos=(10, 28), size=(1065, 52), font=-1, color=10857646, color_sel=13817818, flags=RT_HALIGN_LEFT | RT_WRAP, text=x))
                    self.kochentries.append(res)
                y += 1
                if y == offset:
                    y = 0

        if self.xd == True:
            self['menu'].l.setItemHeight(75)
        else:
            self['menu'].l.setItemHeight(90)
        self['menu'].l.setList(self.kochentries)
        self['menu'].moveToIndex(0)
        self.len = len(self.kochentries)
        self.ready = True
        try:
            picurl1 = self.picurllist[0]
            self.download(picurl1, self.getPic1)
            self['pic1'].show()
        except IndexError:
            self['pic1'].hide()

        try:
            picurl2 = self.picurllist[1]
            self.download(picurl2, self.getPic2)
            self['pic2'].show()
        except IndexError:
            self['pic2'].hide()

        try:
            picurl3 = self.picurllist[2]
            self.download(picurl3, self.getPic3)
            self['pic3'].show()
        except IndexError:
            self['pic3'].hide()

        try:
            picurl4 = self.picurllist[3]
            self.download(picurl4, self.getPic4)
            self['pic4'].show()
        except IndexError:
            self['pic4'].hide()

        try:
            picurl5 = self.picurllist[4]
            self.download(picurl5, self.getPic5)
            self['pic5'].show()
        except IndexError:
            self['pic5'].hide()

        try:
            picurl6 = self.picurllist[5]
            self.download(picurl6, self.getPic6)
            self['pic6'].show()
        except IndexError:
            self['pic6'].hide()

    def makePostviewPage(self, output):
        self.output = ''
        self.morerezepte = False
        self.morepages = False
        self['menu'].hide()
        self['pic1'].hide()
        self['pic2'].hide()
        self['pic3'].hide()
        self['pic4'].hide()
        self['pic5'].hide()
        self['pic6'].hide()
        self['yellowbutton'].hide()
        self['redbutton2'].hide()
        redbutton = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/red.png'
        if fileExists(redbutton):
            self.showRedButton(redbutton)
            self['redbutton'].show()
        greenbutton = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/green.png'
        if fileExists(greenbutton):
            self.showGreenButton(greenbutton)
            self['greenbutton'].show()
        if search('<div id="recipe-buttons">', output) is not None:
            rezept = search('<a class="sg-button sg-button--standard" href="(.*?)"', output)
            self.rezept = 'http://www.chefkoch.de' + rezept.group(1)
        else:
            self.rezept = 'http://www.chefkoch.de'
        if search('<p class="recipe-no-picture__text desktop-only">', output) is not None:
            self['label'].setText('Kein Rezeptbild vorhanden')
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            self['label5'].setText('= Rezept per E-mail senden')
            self['label6'].setText('= Zu Favoriten hinzuf\xfcgen')
            self.morePic = False
        elif self.magazin == True:
            if search('<meta itemprop="contentUrl" content="http://video.chefkoch', output) is not None:
                chefvideo = search('<meta itemprop="contentUrl" content="(.*?)"', output)
                self.chefvideo = chefvideo.group(1)
                self['label'].setText('OK = Chefkoch Video')
                self.chefVideo = True
            elif search('src="//www.youtube.com/embed/.*?"', output) is not None:
                youtube = search('src="//www.youtube.com/embed/(.*?)"', output)
                self.youtube = youtube.group(1)
                self['label'].setText('OK = YouTube Video')
                self.youTube = True
            else:
                self['label'].setText('OK = Vollbild')
                self.youTube = False
                self.chefVideo = False
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            if search('class="button-green nextpage">', output) is not None:
                nextpage = search('<a href="(.*?)" class="button-green nextpage">', output)
                self.nextlink = 'http://www.chefkoch.de' + nextpage.group(1)
                self.morepages = True
                if search('class="button-green prevpage">', output) is not None:
                    prevpage = search('<a href="(.*?)" class="button-green prevpage">', output)
                    self.prevlink = 'http://www.chefkoch.de' + prevpage.group(1)
                    self['label4'].setText('Bouquet +- = Weiterlesen/Zur\xfcck')
                else:
                    self.prevlink = self.postlink
                    self['label4'].setText('Bouquet + = Weiterlesen')
            elif search('class="button-green prevpage">', output) is not None:
                prevpage = search('<a href="(.*?)" class="button-green prevpage">', output)
                self.prevlink = 'http://www.chefkoch.de' + prevpage.group(1)
                self['label4'].setText('Bouquet - = Zur\xfcck')
                self.nextlink = self.postlink
            else:
                self.nextlink = self.postlink
                self.prevlink = self.postlink
            if search('<select class="photo_chooser"', output) is not None:
                self.youTube = False
                self.chefVideo = False
                self.morerezepte = True
                startpos = output.find('<select class="photo_chooser"')
                endpos = output.find('<div class="photobox-titlebox clearfix">')
                bereich = output[startpos:endpos]
                bereich = transHTML(bereich)
                self.rezeptelinks = re.findall('<option value="(.*?)"', bereich)
                self.rezeptelist = re.findall('<option value=".*?>(.*?)</option>', bereich)
                self['label'].setText('OK = Alle Rezepte')
            self['label5'].setText('= Artikel per E-mail senden')
            self['label6'].setText('= Zu Favoriten hinzuf\xfcgen')
            self.morePic = False
        else:
            self['label'].setText('OK = Mehr Rezeptbilder')
            self['label2'].setText('')
            self['label3'].setText('')
            self['label4'].setText('')
            self['label5'].setText('= Rezept per E-mail senden')
            self['label6'].setText('= Zu Favoriten hinzuf\xfcgen')
            self.morePic = True
        self.output = output
        if self.magazin == False:
            if search('<span class="rating-big"><span class="rating rating', output) is not None:
                score = search('<span class="rating-big"><span class="rating rating(.*?)"></span>', output)
                if self.xd == True:
                    self.score = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/logos/score' + score.group(1) + '.png'
                else:
                    self.score = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/logos/score' + score.group(1) + 'HD.png'
                if fileExists(self.score):
                    self.showScore(self.score)
                    self['score'].show()
            if search('Durchschnittliche Wertung:', output) is not None:
                scoretext1 = search('Wertung:</td>\\s+<td>(.*?)</td>', output)
                scoretext = 'Wertung i.D.: ' + scoretext1.group(1)
                self.scoretext = scoretext
                if search('<td>gelesen:</td>', output) is not None:
                    scoretext2 = search('<td>gelesen:</td>\\s+<td>(.*?)</td>', output)
                    scoretext = scoretext + '\nGelesen: ' + scoretext2.group(1)
                if search('<td>gedruckt:</td>', output) is not None:
                    scoretext3 = search('<td>gedruckt:</td>\\s+<td>(.*?)</td>', output)
                    scoretext = scoretext + '\nGedruckt: ' + scoretext3.group(1) + '\n* nur in diesem Monat'
                self['scoretext'].setText(scoretext)
                self['scoretext'].show()
            startpos1 = output.find('<div id="recipe-incredients">')
            endpos1 = output.find('<span id="recipe-com-user-footer">')
            bereich1 = output[startpos1:endpos1]
            startpos2 = find(output, '<div id="slideshow">')
            endpos2 = find(output, '<div id="recipe-image-voting')
            bereich2 = output[startpos2:endpos2]
            bereich = bereich1 + bereich2
        else:
            startpos = output.find('<article class="article-content">')
            endpos = output.find('</article>')
            bereich = output[startpos:endpos]
        title = search('<title>(.*?)</title>', output)
        title = transHTML(title.group(1))
        self.title = title.replace(' (Rezept mit Bild)', '')
        self.setTitle(self.title)
        if self.magazin == True:
            picurl = search('<meta name="og:image" content="(.*?)"', output)
            if picurl is not None:
                self.download(picurl.group(1), self.getPicPost)
            else:
                picurl = search('<img src="(.*?)" name="', bereich)
                if picurl is not None:
                    self.download(picurl.group(1), self.getPicPost)
                else:
                    picurl = search(' src="(.*?)" alt="', bereich)
                    if picurl is not None:
                        self.download(picurl.group(1), self.getPicPost)
                    else:
                        picurl = 'http://img.chefkoch-cdn.de/img/default/layout/recipe-nopicture.jpg'
                        self.download(picurl, self.getPicPost)
            self['picpost'].show()
        elif search('<a href="https://static.chefkoch-cdn.de/ck.de/rezepte/', output) is not None:
            pics = re.findall('<a href="https://static.chefkoch-cdn.de/ck.de/rezepte/(.*?)" id="', bereich)
            picurl = 'https://static.chefkoch-cdn.de/ck.de/rezepte/' + pics[0]
            self.download(picurl, self.getPicPost)
            self['picpost'].show()
        elif search('<a href="https://cdn.chefkoch.de/ck.de/rezepte/', output) is not None:
            pics = re.findall('<a href="https://cdn.chefkoch.de/ck.de/rezepte/(.*?)" id="', bereich)
            picurl = 'https://cdn.chefkoch.de/ck.de/rezepte/' + pics[0]
            self.download(picurl, self.getPicPost)
            self['picpost'].show()
        elif search('src="https://cdn.chefkoch.de/ck.de/rezepte/', output) is not None:
            pics = re.findall('src="https://cdn.chefkoch.de/ck.de/rezepte/(.*?)"', bereich)
            picurl = 'https://cdn.chefkoch.de/ck.de/rezepte/' + pics[0]
            self.download(picurl, self.getPicPost)
            self['picpost'].show()
        else:
            picurl = 'https://img.chefkoch-cdn.de/img/default/layout/recipe-nopicture.jpg'
            self.download(picurl, self.getPicPost)
            self['picpost'].show()
        if self.zufall == True:
            link = search('<link rel="canonical" href="(.*?)">', output)
            if link is not None:
                self.postlink = link.group(1)
            self.name = self.title.replace(' | Chefkoch.de', '')
        if self.magazin == True:
            bereich = re.sub('<!-- Video-Player -->.*?</script>', '', bereich, flags=re.S)
            bereich = sub('<p>\n<script', '<script', bereich)
            bereich = re.sub('<script.*?</script>', '', bereich, flags=re.S)
            bereich = sub('<h1.*?>', '<p>', bereich)
            bereich = sub('</h1>', '</p>', bereich)
            bereich = sub('<h2.*?>', '<p>', bereich)
            bereich = sub('</h2>', '</p>', bereich)
            bereich = sub('<h3.*?>', '<p>', bereich)
            bereich = sub('</h3>', '</p>', bereich)
            bereich = transHTML(bereich)
        else:
            bereich1 = sub('<p>\n<script', '<script', bereich1)
            bereich1 = re.sub('<script.*?</script>', '', bereich1, flags=re.S)
            bereich1 = re.sub('<form name="zutatenform".*?<h2.*?>', '<p>', bereich1, flags=re.S)
            bereich1 = sub('<div id="rezept-zubereitung" class="instructions m-b-200">\n\n\\s+', '<p>', bereich1)
            bereich1 = sub('<a href="http://www.chefkoch.de/magazin/artikel/.*?>', '', bereich1)
            bereich1 = sub('<h3.*?>', '<p>', bereich1)
            bereich1 = sub('</h3>', '</p>', bereich1)
            bereich1 = sub('<h2.*?>', '<p>', bereich1)
            bereich1 = sub('</h2>', '</p>', bereich1)
            bereich1 = sub('<td class="amount">\\s+', '<p>', bereich1)
            bereich1 = sub('\\s+</td>\n\\s+<td>\n\n\\s+', '<p> ', bereich1)
            bereich1 = sub('\\s+</td>', '</p>', bereich1)
            bereich1 = sub('\n\\s+', ' ', bereich1)
            bereich1 = sub('<strong>Portionen</strong>', '<p>\xae</p>', bereich1)
            bereich1 = sub('\\s+/ <strong>', '</p><p>', bereich1)
            bereich1 = sub('\\s+<strong>', '</p><p>', bereich1)
            bereich1 = sub('</strong>\\s+', ' ', bereich1)
            bereich1 = sub('class="instructions">\\s+', '<p>', bereich1)
            bereich1 = sub('</div>', '</p>', bereich1)
            bereich1 = sub('<br />\r\n<br />', '</p><p>', bereich1)
            bereich1 = sub('<br>.<br>', '</p><p>', bereich1)
            bereich1 = sub('<br>', ' ', bereich1)
            bereich1 = sub('  ', ' ', bereich1)
            bereich1 = sub('\t', '', bereich1)
            bereich1 = transHTML(bereich1)
        text = ''
        if self.magazin == False:
            a = findall('<p.*?>(.*?)</p>', bereich1.replace('\r', '').replace('\n', ''))
        else:
            a = findall('<p.*?>(.*?)</p>', bereich.replace('\r', '').replace('\n', ''))
        for x in a:
            if x != '':
                text = text + x + '\n\n'

        text = sub('<br />', '\n', text)
        text = sub('<[^>]*>', '', text)
        text = sub('</p<<p<', '\n\n', text)
        text = sub('\n\\s+\n*', '\n\n', text)
        if self.fontlarge == True:
            if self.xd == True:
                if self.magazin == False:
                    fill = '________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Kommentare einblenden'
                elif self.morerezepte == True and self.morepages == True:
                    fill = '________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen\n*Bouquet + = Weiterlesen'
                elif self.morerezepte == True:
                    fill = '________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen'
                elif self.morepages == True:
                    fill = '________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Bouquet + = Weiterlesen'
                else:
                    fill = '________________________________________________________________________________________________________________________\nChefkoch.de'
            elif self.magazin == False:
                fill = '____________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Kommentare einblenden'
            elif self.morerezepte == True and self.morepages == True:
                fill = '____________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen\n*Bouquet + = Weiterlesen'
            elif self.morerezepte == True:
                fill = '____________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen'
            elif self.morepages == True:
                fill = '____________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Bouquet + = Weiterlesen'
            else:
                fill = '____________________________________________________________________________________________________________________________________\nChefkoch.de'
        elif self.xd == True:
            if self.magazin == False:
                fill = '_________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Kommentare einblenden'
            elif self.morerezepte == True and self.morepages == True:
                fill = '_________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen\n*Bouquet + = Weiterlesen'
            elif self.morerezepte == True:
                fill = '_________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen'
            elif self.morepages == True:
                fill = '_________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Bouquet + = Weiterlesen'
            else:
                fill = '_________________________________________________________________________________________________________________________________________\nChefkoch.de'
        elif self.magazin == False:
            fill = '____________________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Kommentare einblenden'
        elif self.morerezepte == True and self.morepages == True:
            fill = '____________________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen\n*Bouquet + = Weiterlesen'
        elif self.morerezepte == True:
            fill = '____________________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*OK = Alle Rezepte anzeigen'
        elif self.morepages == True:
            fill = '____________________________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Bouquet + = Weiterlesen'
        else:
            fill = '____________________________________________________________________________________________________________________________________________________\nChefkoch.de'
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
            if self.current == 'menu':
                self.selectPage('ok')
            elif self.current == 'postview' and self.postviewready == True:
                if self.morePic == True:
                    self.session.openWithCallback(self.returnPicShow, ChefkochPicShow, self.postlink, self.score, self.scoretext)
                elif self.chefVideo == True:
                    c = self['menu'].getSelectedIndex()
                    name = self.titellist[c]
                    sref = eServiceReference(4097, 0, self.chefvideo)
                    sref.setName(name)
                    self.session.openWithCallback(self.returnVideo, MoviePlayer, sref)
                elif self.youTube == True:
                    videolink = self.getYouTubeURL(self.youtube)
                    if videolink is not None:
                        c = self['menu'].getSelectedIndex()
                        name = self.titellist[c]
                        sref = eServiceReference(4097, 0, videolink)
                        sref.setName(name)
                        self.session.openWithCallback(self.returnVideo, MoviePlayer, sref)
                    else:
                        self.session.open(MessageBox, '\nYouTube Video nicht gefunden', MessageBox.TYPE_ERROR)
                elif self.morerezepte == True:
                    self.session.open(rezepteList, self.rezeptelist, self.rezeptelinks, self.title)
                else:
                    self.session.openWithCallback(self.showPicPost(self.picfile), FullScreen)
            return

    def selectPage(self, action):
        if self.ready == True:
            c = self['menu'].getSelectedIndex()
            try:
                self.postlink = self.kochlink[c]
            except IndexError:
                self.postlink = self.link

            if self.chefkochtv == True:
                if search('http://www.chefkoch.de', self.postlink) is not None:
                    self.download(self.postlink, self.makeVideoURL)
                else:
                    self.kochentries = []
                    self.kochlink = []
                    self.picurllist = []
                    self.titellist = []
                    self.postlink = 'http://www.chefkoch.de' + self.postlink
                    self.download(self.postlink, self.makeChefkoch)
            elif search('http://www.chefkoch.de', self.postlink) is None:
                self.count += 1
                if self.count >= self.maxpage:
                    self.count = self.maxpage
                    self.session.open(MessageBox, '\nLetzte Seite erreicht.', MessageBox.TYPE_INFO, close_on_any_key=True)
                self.kochentries = []
                self.kochlink = []
                self.picurllist = []
                self.titellist = []
                self.postlink = 'http://www.chefkoch.de' + self.postlink
                link = self.postlink + '?comments=all'
                self.download(link, self.makeChefkoch)
            else:
                self.current = 'postview'
                link = self.postlink + '?comments=all'
                self.download(link, self.makePostviewPage)
        return

    def makeVideoURL(self, output):
        link = search('<meta itemprop="contentUrl" content="(.*?)"', output)
        if link is not None:
            videolink = link.group(1)
            if self.fav == False:
                c = self['menu'].getSelectedIndex()
                name = self.titellist[c]
            else:
                name = search('<title>(.*?)</title>', output)
                name = transHTML(name.group(1))
                name = sub(' | Chefkoch.de Video', '', name)
                name = 'Chefkoch TV' + name
            if self.downVideo == True:
                self.downVideo = False
                self.ready = False
                self.session.openWithCallback(self.returnVideo, DownloadVideo, videolink, name)
            else:
                sref = eServiceReference(4097, 0, videolink)
                sref.setName(name)
                self.session.openWithCallback(self.returnVideo, MoviePlayer, sref)
        else:
            link = search('<a href="https://www.chefkoch.de/video/(.*?)"', output)
            if link is not None:
                self.link = 'https://www.chefkoch.de/video/' + link.group(1)
                self.download(self.link, self.makeVideoURL)
        return

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
        watch_url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en' % trailer_id
        watchrequest = Request(watch_url, None, header)
        try:
            watchvideopage = urlopen(watchrequest).read()
        except URLError:
            return trailer_url

        for el in ['&el=embedded',
         '&el=detailpage',
         '&el=vevo',
         '']:
            info_url = 'http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (trailer_id, el)
            request = Request(info_url, None, header)
            try:
                infopage = urlopen(request).read()
                videoinfo = parse_qs(infopage)
                if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
                    break
            except URLError:
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

    def red(self):
        if self.ready == True or self.postviewready == True:
            if self.zufall == False:
                c = self['menu'].getSelectedIndex()
                name = self.titellist[c]
            else:
                name = self.name
            if self.chefkochtv == True:
                self.session.openWithCallback(self.red_return, MessageBox, "\nVideo '%s' zu den Favoriten hinzuf\xfcgen?" % name, MessageBox.TYPE_YESNO)
            elif self.magazin == True:
                self.session.openWithCallback(self.red_return, MessageBox, "\nMagazin Beitrag '%s' zu den Favoriten hinzuf\xfcgen?" % name, MessageBox.TYPE_YESNO)
            else:
                self.session.openWithCallback(self.red_return, MessageBox, "\nRezept '%s' zu den Favoriten hinzuf\xfcgen?" % name, MessageBox.TYPE_YESNO)

    def red_return(self, answer):
        if answer is True:
            if self.zufall == False:
                c = self['menu'].getSelectedIndex()
                favoriten = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/db/favoriten'
                if fileExists(favoriten):
                    f = open(favoriten, 'a')
                    data = self.titellist[c] + ':::' + self.kochlink[c]
                    if self.magazin == True and self.chefkochtv == False:
                        data = 'Magazin: ' + data
                    elif self.chefkochtv == False:
                        data = 'Rezept: ' + data
                    f.write(data)
                    f.write(os.linesep)
                    f.close()
                self.session.open(chefkochFav)
            else:
                favoriten = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/db/favoriten'
                if fileExists(favoriten):
                    f = open(favoriten, 'a')
                    data = 'Rezept: ' + self.name + ':::' + self.postlink
                    f.write(data)
                    f.write(os.linesep)
                    f.close()
                self.session.open(chefkochFav)

    def green(self):
        if self.ready == True and self.chefkochtv == True or self.magazin == True:
            c = self['menu'].getSelectedIndex()
            try:
                self.postlink = self.kochlink[c]
                self.downVideo = True
                self.download(self.postlink, self.makeVideoURL)
            except IndexError:
                pass

        elif self.postviewready == True:
            if config.plugins.chefkoch.mail.value == 'yes':
                self.download(self.rezept, self.getRezept)
            else:
                self.session.open(MessageBox, '\nDie E-mail Funktion ist nicht aktiviert. Aktivieren Sie die E-mail Funktion im Setup des Plugins.', MessageBox.TYPE_INFO, close_on_any_key=True)

    def getRezept(self, output):
        output = sub('<a href="/rezepte/.*?\n', '', output)
        output = sub('<li><a href="mailto.*?\n', '', output)
        output = sub('<li><a href="javascript:open_window.*?\n', '', output)
        output = sub('<li><a href="#" class="button-green.*?\n', '', output)
        output = sub('<a href="#" class="toggle-top-picture dontprint">.*?\n', '', output)
        output = sub('<p><a href="#" class="dontprint".*?\n', '', output)
        output = re.sub('<li>\n\\s+<div class="button-green button-change-size">.*?</div>\n\\s+</li>', '', output, flags=re.S)
        output = re.sub('<div id="morepictures".*?<ul class="innerbuttons dontprint">', '<ul class="innerbuttons dontprint">', output, flags=re.S)
        f = open(self.rezeptfile, 'wb')
        f.write(output)
        f.close()
        self.sendRezept(self.title)

    def sendRezept(self, name):
        mailFrom = config.plugins.chefkoch.mailfrom.value
        mailTo = config.plugins.chefkoch.mailto.value
        mailLogin = config.plugins.chefkoch.login.value
        mailPassword = b64decode(config.plugins.chefkoch.password.value)
        mailServer = config.plugins.chefkoch.server.value
        mailPort = config.plugins.chefkoch.port.value
        msg = MIMEMultipart()
        msg.set_charset('utf-8')
        msg['Subject'] = 'Chefkoch Rezept: %s' % name
        msg['From'] = mailFrom
        msg['To'] = mailTo
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(self.rezeptfile).read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="Rezept.html"')
        msg.attach(part)
        try:
            if config.plugins.chefkoch.ssl.value == 'yes':
                server = smtplib.SMTP_SSL(mailServer, mailPort)
            else:
                server = smtplib.SMTP(mailServer, mailPort)
            server.login(mailLogin, mailPassword)
            server.sendmail(mailFrom, mailTo, msg.as_string())
            server.quit()
            self.session.open(MessageBox, 'E-mail erfolgreich gesendet an %s!' % str(mailTo), MessageBox.TYPE_INFO, close_on_any_key=True)
        except Exception as e:
            self.session.open(MessageBox, 'E-mail kann nicht gesendet werden: %s' % str(e), MessageBox.TYPE_INFO, close_on_any_key=True)

    def nextPage(self):
        if self.magazin == False:
            self.count += 30
            if self.count / 30 >= self.maxpage:
                self.count = self.maxpage
                self.session.open(MessageBox, '\nLetzte Seite erreicht.', MessageBox.TYPE_INFO, close_on_any_key=True)
            if self.search == False:
                link = sub('http://www.chefkoch.de/rs/s.*?g', '', self.link)
                link = 'http://www.chefkoch.de/rs/s' + str(self.count) + 'g' + link
            else:
                link = sub('http://www.chefkoch.de/rs/s.*?/', '', self.link)
                link = 'http://www.chefkoch.de/rs/s' + str(self.count) + '/' + link
            self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))
        elif self.magazin == True and self.current == 'postview':
            self.postlink = self.nextlink
            self.download(self.postlink, self.makePostviewPage)
        elif self.chefkochtv == False:
            self.count += 1
            if self.count >= self.maxpage:
                self.count = self.maxpage
                self.session.open(MessageBox, '\nLetzte Seite erreicht.', MessageBox.TYPE_INFO, close_on_any_key=True)
            link = 'http://www.chefkoch.de/magazin/6,0,' + str(self.count) + '/Chefkoch/'
            self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))

    def prevPage(self):
        if self.magazin == False:
            self.count -= 30
            if self.count < 0:
                self.count = 0
                self.session.open(MessageBox, '\nErste Seite erreicht.', MessageBox.TYPE_INFO, close_on_any_key=True)
            if self.search == False:
                link = sub('http://www.chefkoch.de/rs/s.*?g', '', self.link)
                link = 'http://www.chefkoch.de/rs/s' + str(self.count) + 'g' + link
            else:
                link = sub('http://www.chefkoch.de/rs/s.*?/', '', self.link)
                link = 'http://www.chefkoch.de/rs/s' + str(self.count) + '/' + link
            self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))
        elif self.magazin == True and self.current == 'postview':
            self.postlink = self.prevlink
            self.download(self.postlink, self.makePostviewPage)
        elif self.chefkochtv == False:
            self.count -= 1
            if self.count < 0:
                self.count = 0
                self.session.open(MessageBox, '\nErste Seite erreicht.', MessageBox.TYPE_INFO, close_on_any_key=True)
            link = 'http://www.chefkoch.de/magazin/6,0,' + str(self.count) + '/Chefkoch/'
            self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))

    def gotoPage(self, number):
        if self.current != 'postview' and self.ready == True:
            if self.magazin == False:
                self.session.openWithCallback(self.numberEntered, getNumber, number, 5)
            elif self.chefkochtv == False:
                self.session.openWithCallback(self.numberEntered, getNumber, number, 3)
        elif self.current == 'postview':
            if number == 0:
                self['textpage'].lastPage()
            elif number == 1:
                if self.comment == True:
                    self.makeKommentar()
                else:
                    self.makeRezept()

    def numberEntered(self, number):
        if number is None or number == 0:
            pass
        else:
            self.count = int(number)
            if self.magazin == False:
                if self.count > self.maxpage:
                    self.count = self.maxpage
                    self.session.open(MessageBox, '\nNur %s Seiten verf\xfcgbar. Gehe zu Seite %s.' % (str(self.count), str(self.count)), MessageBox.TYPE_INFO, close_on_any_key=True)
                self.count = self.count * 30
                self.count = self.count - 30
                if self.search == False:
                    link = sub('http://www.chefkoch.de/rs/s.*?g', '', self.link)
                    link = 'http://www.chefkoch.de/rs/s' + str(self.count) + 'g' + link
                else:
                    link = sub('http://www.chefkoch.de/rs/s.*?/', '', self.link)
                    link = 'http://www.chefkoch.de/rs/s' + str(self.count) + '/' + link
                self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))
            else:
                if self.count > self.maxpage:
                    self.count = self.maxpage
                    self.session.open(MessageBox, '\nNur %s Seiten verf\xfcgbar. Gehe zu Seite %s.' % (str(self.count), str(self.count)), MessageBox.TYPE_INFO, close_on_any_key=True)
                link = 'http://www.chefkoch.de/magazin/6,0,' + str(self.count - 1) + '/Chefkoch/'
                self.makeChefkochTimer.callback.append(self.download(link, self.makeChefkoch))
        return

    def yellow(self):
        if self.current == 'menu' and self.magazin == False:
            try:
                c = self['menu'].getSelectedIndex()
                titel = self.kochlink[c]
                titel = sub('http://www.chefkoch.de/rezepte/.*?/', '', titel)
                titel = sub('.html', '', titel)
                titel = titel.replace(' - ', ' ').replace('-', ' ')
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Chefkoch - Suche Rezepte:', text=titel)
            except IndexError:
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Chefkoch - Suche Rezepte:', text='')

        elif self.current == 'postview' and self.postviewready == True and self.magazin == False:
            if self.comment == False:
                self.comment = True
                self.makeKommentar()
            else:
                self.comment = False
                self.makeRezept()

    def searchReturn(self, search):
        if search and search != '':
            self.search = True
            self.searchtext = search.replace(' ', '+')
            self.link = 'http://www.chefkoch.de/rs/s0/' + self.searchtext + '/Rezepte.html'
            self.makeChefkochTimer.callback.append(self.downloadSearch(self.link, self.makeChefkoch))

    def makeKommentar(self):
        self.postviewready = False
        self['label4'].setText('1/0 = Erster/Letzer Kommentar')
        self['textpage'].setText('')
        startpos = self.output.find('class="recipe-comments">')
        endpos = self.output.find('<div id="kommentarform">')
        bereich = self.output[startpos:endpos]
        bereich = transHTML(bereich)
        bereich = sub('<h2.*?>', '<p>', bereich)
        bereich = sub('</h2>', '</p>', bereich)
        bereich = sub('<div class="comment-content">', '<p>', bereich)
        bereich = sub('<div class="comment-text".*?">', '<p>', bereich)
        bereich = sub('<a href="/user/profil.*?">', '<p>', bereich)
        bereich = sub('<a href="/userrank.php".*?" title="', ', ', bereich)
        bereich = sub('</td>\n', '</p>', bereich)
        bereich = sub('"></a>\n', '</p>', bereich)
        bereich = sub('<strong>', '', bereich)
        bereich = sub('</strong>', '', bereich)
        bereich = sub('</div>', '</p>', bereich)
        bereich = sub('<br />\r\n<br />', '</p><p>', bereich)
        bereich = sub('<br>.<br>', '</p><p>', bereich)
        bereich = sub('<br>', ' ', bereich)
        bereich = sub('  ', ' ', bereich)
        bereich = sub('\t', '', bereich)
        bereich = sub('<div class="comment-helpfultext">', '<p>\xae</p>', bereich)
        text = ''
        a = findall('<p.*?>(.*?)</p>', bereich.replace('\r', '').replace('\n', ''))
        for x in a:
            if x != '':
                text = text + x + '\n\n'

        text = sub('<br />', '\n', text)
        text = sub('<[^>]*>', '', text)
        text = sub('</p<<p<', '\n\n', text)
        text = sub('\n\\s+\n*', '\n\n', text)
        if self.xd == True:
            fill = '________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Rezept einblenden'
        else:
            fill = '____________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Rezept einblenden'
        text = text + fill
        self['textpage'].setText(text)
        self.postviewready = True

    def makeRezept(self):
        self.postviewready = False
        self['label4'].setText('')
        self['textpage'].setText('')
        startpos = self.output.find('<div id="recipe-incredients">')
        endpos = self.output.find('<span id="recipe-com-user-footer">')
        bereich = self.output[startpos:endpos]
        bereich = sub('<p>\n<script', '<script', bereich)
        bereich = re.sub('<script.*?</script>', '', bereich, flags=re.S)
        bereich = re.sub('<form name="zutatenform".*?<h2.*?>', '<p>', bereich, flags=re.S)
        bereich = sub('<a href="http://www.chefkoch.de/magazin/artikel/.*?>', '', bereich)
        bereich = sub('<h2.*?>', '<p>', bereich)
        bereich = sub('</h2>', '</p>', bereich)
        bereich = sub('<td class="amount">\\s+', '<p>', bereich)
        bereich = sub('\\s+</td>\n\\s+<td>\n\n\\s+', '<p> ', bereich)
        bereich = sub('\\s+</td>', '</p>', bereich)
        bereich = sub('<strong>Portionen</strong>', '<p>\xae</p>', bereich)
        bereich = sub('\\s+/ <strong>', '</p><p>', bereich)
        bereich = sub('\\s+<strong>', '</p><p>', bereich)
        bereich = sub('</strong>\\s+', ' ', bereich)
        bereich = sub('class="instructions">\\s+', '<p>', bereich)
        bereich = sub('</div>', '</p>', bereich)
        bereich = sub('<br />\r\n<br />', '</p><p>', bereich)
        bereich = sub('<br>.<br>', '</p><p>', bereich)
        bereich = sub('<br>', ' ', bereich)
        bereich = sub('  ', ' ', bereich)
        bereich = sub('\t', '', bereich)
        bereich = transHTML(bereich)
        text = ''
        a = findall('<p.*?>(.*?)</p>', bereich.replace('\r', '').replace('\n', ''))
        for x in a:
            if x != '':
                text = text + x + '\n\n'

        text = sub('<br />', '\n', text)
        text = sub('<[^>]*>', '', text)
        text = sub('</p<<p<', '\n\n', text)
        text = sub('\n\\s+\n*', '\n\n', text)
        if self.xd == True:
            fill = '________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Kommentare einblenden'
        else:
            fill = '____________________________________________________________________________________________________________________________________\nChefkoch.de\n\n*Gelb = Kommentare einblenden'
        text = text + fill
        self['textpage'].setText(text)
        self.postviewready = True

    def getPic1(self, output):
        f = open(self.pic1, 'wb')
        f.write(output)
        f.close()
        self.showPic1(self.pic1)

    def showPic1(self, pic1):
        if self.xd == True:
            currPic = loadPic(pic1, 112, 75, 3, 0, 0, 0)
        else:
            currPic = loadPic(pic1, 135, 90, 3, 0, 0, 0)
        if currPic != None:
            self['pic1'].instance.setPixmap(currPic)
        return

    def getPic2(self, output):
        f = open(self.pic2, 'wb')
        f.write(output)
        f.close()
        self.showPic2(self.pic2)

    def showPic2(self, pic2):
        if self.xd == True:
            currPic = loadPic(pic2, 112, 75, 3, 0, 0, 0)
        else:
            currPic = loadPic(pic2, 135, 90, 3, 0, 0, 0)
        if currPic != None:
            self['pic2'].instance.setPixmap(currPic)
        return

    def getPic3(self, output):
        f = open(self.pic3, 'wb')
        f.write(output)
        f.close()
        self.showPic3(self.pic3)

    def showPic3(self, pic3):
        if self.xd == True:
            currPic = loadPic(pic3, 112, 75, 3, 0, 0, 0)
        else:
            currPic = loadPic(pic3, 135, 90, 3, 0, 0, 0)
        if currPic != None:
            self['pic3'].instance.setPixmap(currPic)
        return

    def getPic4(self, output):
        f = open(self.pic4, 'wb')
        f.write(output)
        f.close()
        self.showPic4(self.pic4)

    def showPic4(self, pic4):
        if self.xd == True:
            currPic = loadPic(pic4, 112, 75, 3, 0, 0, 0)
        else:
            currPic = loadPic(pic4, 135, 90, 3, 0, 0, 0)
        if currPic != None:
            self['pic4'].instance.setPixmap(currPic)
        return

    def getPic5(self, output):
        f = open(self.pic5, 'wb')
        f.write(output)
        f.close()
        self.showPic5(self.pic5)

    def showPic5(self, pic5):
        if self.xd == True:
            currPic = loadPic(pic5, 112, 75, 3, 0, 0, 0)
        else:
            currPic = loadPic(pic5, 135, 90, 3, 0, 0, 0)
        if currPic != None:
            self['pic5'].instance.setPixmap(currPic)
        return

    def getPic6(self, output):
        f = open(self.pic6, 'wb')
        f.write(output)
        f.close()
        self.showPic6(self.pic6)

    def showPic6(self, pic6):
        if self.xd == True:
            currPic = loadPic(pic6, 112, 75, 3, 0, 0, 0)
        else:
            currPic = loadPic(pic6, 135, 90, 3, 0, 0, 0)
        if currPic != None:
            self['pic6'].instance.setPixmap(currPic)
        return

    def getPicPost(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPicPost(self.picfile)

    def showPicPost(self, picpost):
        if self.xd == True:
            currPic = loadPic(picpost, 225, 150, 3, 0, 0, 0)
        else:
            currPic = loadPic(picpost, 300, 200, 3, 0, 0, 0)
        if currPic != None:
            self['picpost'].instance.setPixmap(currPic)
        return

    def showYellowButton(self, yellowbutton):
        currPic = loadPic(yellowbutton, 18, 18, 3, 1, 0, 1)
        if currPic != None:
            self['yellowbutton'].instance.setPixmap(currPic)
        return

    def showRedButton(self, redbutton):
        currPic = loadPic(redbutton, 18, 18, 3, 1, 0, 1)
        if currPic != None:
            self['redbutton'].instance.setPixmap(currPic)
        return

    def showRedButton2(self, redbutton):
        currPic = loadPic(redbutton, 18, 18, 3, 1, 0, 1)
        if currPic != None:
            self['redbutton2'].instance.setPixmap(currPic)
        return

    def showGreenButton(self, greenbutton):
        currPic = loadPic(greenbutton, 18, 18, 3, 1, 0, 1)
        if currPic != None:
            self['greenbutton'].instance.setPixmap(currPic)
        return

    def showGreenButton2(self, greenbutton):
        currPic = loadPic(greenbutton, 18, 18, 3, 1, 0, 1)
        if currPic != None:
            self['greenbutton2'].instance.setPixmap(currPic)
        return

    def showScore(self, score):
        if self.xd == True:
            currPic = loadPic(score, 157, 24, 3, 0, 0, 0)
        else:
            currPic = loadPic(score, 236, 36, 3, 0, 0, 0)
        if currPic != None:
            self['score'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadSearch(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadSearchError)

    def downloadSearchError(self, output):
        search = self.searchtext.replace('+', 'CUT')
        search = search + 'FIN'
        self.searchtext = sub('CUT.*?FIN', '', search)
        self.link = 'http://www.chefkoch.de/rs/s0/' + self.searchtext + '/Rezepte.html'
        self.makeChefkochTimer.callback.append(self.downloadSearch2(self.link, self.makeChefkoch))

    def downloadSearch2(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadSearch2Error)

    def downloadSearch2Error(self, output):
        self.makeChefkochTimer.callback.append(self.download(self.link, self.makeChefkoch))

    def showProgrammPage(self):
        self['label'].setText('Bouquet +- = Seite vor/zur\xfcck')
        if self.magazin == False:
            self['label2'].setText('= Suche')
            self['label3'].setText('')
            self['label4'].setText('%s' % self.seitenlabel)
            self['yellowbutton'].show()
        else:
            self['label2'].setText('')
            self['label3'].setText('= Rubrik zu Favoriten hinzuf\xfcgen')
            self['label4'].setText('')
            self['redbutton2'].show()
        self['label5'].setText('')
        self['label6'].setText('')
        self['redbutton'].hide()
        self['greenbutton'].hide()
        self['score'].hide()
        self['scoretext'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['picpost'].hide()
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
                try:
                    picurl1 = self.picurllist[0]
                    self.download(picurl1, self.getPic1)
                    self['pic1'].show()
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[1]
                    self.download(picurl2, self.getPic2)
                    self['pic2'].show()
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[2]
                    self.download(picurl3, self.getPic3)
                    self['pic3'].show()
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[3]
                    self.download(picurl4, self.getPic4)
                    self['pic4'].show()
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[4]
                    self.download(picurl5, self.getPic5)
                    self['pic5'].show()
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[5]
                    self.download(picurl6, self.getPic6)
                    self['pic6'].show()
                except IndexError:
                    self['pic6'].hide()

            elif c % 6 == 5:
                try:
                    picurl1 = self.picurllist[c + 1]
                    self.download(picurl1, self.getPic1)
                    self['pic1'].show()
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c + 2]
                    self.download(picurl2, self.getPic2)
                    self['pic2'].show()
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c + 3]
                    self.download(picurl3, self.getPic3)
                    self['pic3'].show()
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c + 4]
                    self.download(picurl4, self.getPic4)
                    self['pic4'].show()
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c + 5]
                    self.download(picurl5, self.getPic5)
                    self['pic5'].show()
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c + 6]
                    self.download(picurl6, self.getPic6)
                    self['pic6'].show()
                except IndexError:
                    self['pic6'].hide()

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
                try:
                    picurl1 = self.picurllist[l - d]
                    self.download(picurl1, self.getPic1)
                    self['pic1'].show()
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[l - d + 1]
                    self.download(picurl2, self.getPic2)
                    self['pic2'].show()
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[l - d + 2]
                    self.download(picurl3, self.getPic3)
                    self['pic3'].show()
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[l - d + 3]
                    self.download(picurl4, self.getPic4)
                    self['pic4'].show()
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[l - d + 4]
                    self.download(picurl5, self.getPic5)
                    self['pic5'].show()
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[l - d + 5]
                    self.download(picurl6, self.getPic6)
                    self['pic6'].show()
                except IndexError:
                    self['pic6'].hide()

            elif c % 6 == 0:
                try:
                    picurl1 = self.picurllist[c - 6]
                    self.download(picurl1, self.getPic1)
                    self['pic1'].show()
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c - 5]
                    self.download(picurl2, self.getPic2)
                    self['pic2'].show()
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c - 4]
                    self.download(picurl3, self.getPic3)
                    self['pic3'].show()
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c - 3]
                    self.download(picurl4, self.getPic4)
                    self['pic4'].show()
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c - 2]
                    self.download(picurl5, self.getPic5)
                    self['pic5'].show()
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c - 1]
                    self.download(picurl6, self.getPic6)
                    self['pic6'].show()
                except IndexError:
                    self['pic6'].hide()

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
                try:
                    picurl1 = self.picurllist[c + 6]
                    self.download(picurl1, self.getPic1)
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c + 7]
                    self.download(picurl2, self.getPic2)
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c + 8]
                    self.download(picurl3, self.getPic3)
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c + 9]
                    self.download(picurl4, self.getPic4)
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c + 10]
                    self.download(picurl5, self.getPic5)
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c + 11]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    self['pic6'].hide()

            elif d == 1:
                try:
                    picurl1 = self.picurllist[c + 5]
                    self.download(picurl1, self.getPic1)
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c + 6]
                    self.download(picurl2, self.getPic2)
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c + 7]
                    self.download(picurl3, self.getPic3)
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c + 8]
                    self.download(picurl4, self.getPic4)
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c + 9]
                    self.download(picurl5, self.getPic5)
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c + 10]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    self['pic6'].hide()

            elif d == 2:
                try:
                    picurl1 = self.picurllist[c + 4]
                    self.download(picurl1, self.getPic1)
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c + 5]
                    self.download(picurl2, self.getPic2)
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c + 6]
                    self.download(picurl3, self.getPic3)
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c + 7]
                    self.download(picurl4, self.getPic4)
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c + 8]
                    self.download(picurl5, self.getPic5)
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c + 9]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    self['pic6'].hide()

            elif d == 3:
                try:
                    picurl1 = self.picurllist[c + 3]
                    self.download(picurl1, self.getPic1)
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c + 4]
                    self.download(picurl2, self.getPic2)
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c + 5]
                    self.download(picurl3, self.getPic3)
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c + 6]
                    self.download(picurl4, self.getPic4)
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c + 7]
                    self.download(picurl5, self.getPic5)
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c + 8]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    self['pic6'].hide()

            elif d == 4:
                try:
                    picurl1 = self.picurllist[c + 2]
                    self.download(picurl1, self.getPic1)
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c + 3]
                    self.download(picurl2, self.getPic2)
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c + 4]
                    self.download(picurl3, self.getPic3)
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c + 5]
                    self.download(picurl4, self.getPic4)
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c + 6]
                    self.download(picurl5, self.getPic5)
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c + 7]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    self['pic6'].hide()

            elif d == 5:
                try:
                    picurl1 = self.picurllist[c + 1]
                    self.download(picurl1, self.getPic1)
                except IndexError:
                    self['pic1'].hide()

                try:
                    picurl2 = self.picurllist[c + 2]
                    self.download(picurl2, self.getPic2)
                except IndexError:
                    self['pic2'].hide()

                try:
                    picurl3 = self.picurllist[c + 3]
                    self.download(picurl3, self.getPic3)
                except IndexError:
                    self['pic3'].hide()

                try:
                    picurl4 = self.picurllist[c + 4]
                    self.download(picurl4, self.getPic4)
                except IndexError:
                    self['pic4'].hide()

                try:
                    picurl5 = self.picurllist[c + 5]
                    self.download(picurl5, self.getPic5)
                except IndexError:
                    self['pic5'].hide()

                try:
                    picurl6 = self.picurllist[c + 6]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    self['pic6'].hide()

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
            if d == 0:
                try:
                    picurl1 = self.picurllist[c - 6]
                    self.download(picurl1, self.getPic1)
                    picurl2 = self.picurllist[c - 5]
                    self.download(picurl2, self.getPic2)
                    picurl3 = self.picurllist[c - 4]
                    self.download(picurl3, self.getPic3)
                    picurl4 = self.picurllist[c - 3]
                    self.download(picurl4, self.getPic4)
                    picurl5 = self.picurllist[c - 2]
                    self.download(picurl5, self.getPic5)
                    picurl6 = self.picurllist[c - 1]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    pass

            elif d == 1:
                try:
                    picurl1 = self.picurllist[c - 7]
                    self.download(picurl1, self.getPic1)
                    picurl2 = self.picurllist[c - 6]
                    self.download(picurl2, self.getPic2)
                    picurl3 = self.picurllist[c - 5]
                    self.download(picurl3, self.getPic3)
                    picurl4 = self.picurllist[c - 4]
                    self.download(picurl4, self.getPic4)
                    picurl5 = self.picurllist[c - 3]
                    self.download(picurl5, self.getPic5)
                    picurl6 = self.picurllist[c - 2]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    pass

            elif d == 2:
                try:
                    picurl1 = self.picurllist[c - 8]
                    self.download(picurl1, self.getPic1)
                    picurl2 = self.picurllist[c - 7]
                    self.download(picurl2, self.getPic2)
                    picurl3 = self.picurllist[c - 6]
                    self.download(picurl3, self.getPic3)
                    picurl4 = self.picurllist[c - 5]
                    self.download(picurl4, self.getPic4)
                    picurl5 = self.picurllist[c - 4]
                    self.download(picurl5, self.getPic5)
                    picurl6 = self.picurllist[c - 3]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    pass

            elif d == 3:
                try:
                    picurl1 = self.picurllist[c - 9]
                    self.download(picurl1, self.getPic1)
                    picurl2 = self.picurllist[c - 8]
                    self.download(picurl2, self.getPic2)
                    picurl3 = self.picurllist[c - 7]
                    self.download(picurl3, self.getPic3)
                    picurl4 = self.picurllist[c - 6]
                    self.download(picurl4, self.getPic4)
                    picurl5 = self.picurllist[c - 5]
                    self.download(picurl5, self.getPic5)
                    picurl6 = self.picurllist[c - 4]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    pass

            elif d == 4:
                try:
                    picurl1 = self.picurllist[c - 10]
                    self.download(picurl1, self.getPic1)
                    picurl2 = self.picurllist[c - 9]
                    self.download(picurl2, self.getPic2)
                    picurl3 = self.picurllist[c - 8]
                    self.download(picurl3, self.getPic3)
                    picurl4 = self.picurllist[c - 7]
                    self.download(picurl4, self.getPic4)
                    picurl5 = self.picurllist[c - 6]
                    self.download(picurl5, self.getPic5)
                    picurl6 = self.picurllist[c - 5]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    pass

            elif d == 5:
                try:
                    picurl1 = self.picurllist[c - 11]
                    self.download(picurl1, self.getPic1)
                    picurl2 = self.picurllist[c - 10]
                    self.download(picurl2, self.getPic2)
                    picurl3 = self.picurllist[c - 9]
                    self.download(picurl3, self.getPic3)
                    picurl4 = self.picurllist[c - 8]
                    self.download(picurl4, self.getPic4)
                    picurl5 = self.picurllist[c - 7]
                    self.download(picurl5, self.getPic5)
                    picurl6 = self.picurllist[c - 6]
                    self.download(picurl6, self.getPic6)
                except IndexError:
                    pass

            self['pic1'].show()
            self['pic2'].show()
            self['pic3'].show()
            self['pic4'].show()
            self['pic5'].show()
            self['pic6'].show()
        else:
            self['textpage'].pageUp()

    def returnPicShow(self):
        pass

    def returnVideo(self):
        self.ready = True

    def infoScreen(self):
        self.session.open(infoScreenChefkoch, True)

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

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

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu':
            self.close()
        elif self.fav == True:
            self.close()
        elif self.current == 'postview' and self.zufall == True:
            self.close()
        elif self.current == 'postview' and self.zufall == False:
            self.postviewready = False
            self.setTitle('')
            self.setTitle(self.titel)
            self.showProgrammPage()


class getNumber(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="175,70" backgroundColor="#000000" flags="wfNoBorder" title=" ">\n\t\t\t\t<widget name="number" position="0,0" size="175,70" font="{font};40" halign="center" valign="center" transparent="1" zPosition="1"/>\n\t\t\t</screen>'

    def __init__(self, session, number, max):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(getNumber.skin, self.dict)
        Screen.__init__(self, session)
        self.field = str(number)
        self['number'] = Label(self.field)
        self.max = max
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
        self.Timer.start(2000, True)

    def keyNumber(self, number):
        self.Timer.start(2000, True)
        self.field = self.field + str(number)
        self['number'].setText(self.field)
        if len(self.field) >= self.max:
            self.keyOK()

    def keyOK(self):
        self.Timer.stop()
        self.close(int(self['number'].getText()))

    def quit(self):
        self.Timer.stop()
        self.close(0)


class rezepteList(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="620,460" title=" ">\n\t\t\t\t<ePixmap position="0,0" size="620,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/rezepte.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="list" position="10,50" size="600,400" scrollbarMode="showOnDemand" zPosition="1" />\n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="740,460" title=" ">\n\t\t\t\t<ePixmap position="0,0" size="740,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/rezepteHD.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="list" position="10,50" size="720,400" scrollbarMode="showOnDemand" zPosition="1" />\n\t\t\t</screen>'

    def __init__(self, session, rezepte, links, title):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        if config.plugins.chefkoch.plugin_size.value == 'full':
            self.listwidth = 720
            self.font = 0
            self.xd = False
            self.skin = applySkinVars(rezepteList.skinHD, self.dict)
        else:
            self.listwidth = 600
            self.font = 1
            self.xd = True
            self.skin = applySkinVars(rezepteList.skin, self.dict)
        self.session = session
        Screen.__init__(self, session)
        self.hideflag = True
        self.title = title.replace(' | Chefkoch.de Magazin', '')
        self.links = links
        self.list = rezepte
        self.listentries = []
        self['list'] = ItemList([])
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'HelpActions',
         'NumberActions'], {'ok': self.ok,
         'cancel': self.exit,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'red': self.infoScreen,
         'yellow': self.infoScreen,
         'green': self.infoScreen,
         'blue': self.hideScreen,
         '0': self.gotoEnd,
         'displayHelp': self.infoScreen}, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        idx = 0
        for x in self.list:
            idx += 1

        for i in range(idx):
            try:
                res = ['']
                res.append(MultiContentEntryText(pos=(0, 0), size=(self.listwidth, 25), font=self.font, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
                self.listentries.append(res)
            except IndexError:
                pass

        self['list'].l.setList(self.listentries)
        self['list'].l.setItemHeight(25)
        self.setTitle(self.title)

    def ok(self):
        index = self['list'].getSelectedIndex()
        try:
            link = self.links[index]
            link = 'http://www.chefkoch.de' + link
            self.download(link, self.makeRezept)
        except IndexError:
            pass

    def makeRezept(self, output):
        link = search('<a href="(.*?)" class="button-green photobox-recipelink">Zum Rezept</a>', output)
        if link is not None:
            link = link.group(1)
            self.session.openWithCallback(self.returnRezept, ChefkochView, link, False, True, False, False, False)
        return

    def down(self):
        self['list'].down()

    def up(self):
        self['list'].up()

    def gotoEnd(self):
        end = len(self.list) - 1
        self['list'].moveToIndex(end)

    def returnRezept(self):
        pass

    def download(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def infoScreen(self):
        self.session.open(infoScreenChefkoch, True)

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

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class ChefkochPicShow(Screen):
    skin = '\n\t\t\t<screen position="center,{position}" size="1012,516" title="Mehr Rezeptbilder - Chefkoch.de">\n\t\t\t\t<ePixmap position="0,0" size="1012,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/chefkoch.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="250,7" size="512,40" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="score" position="6,60" size="157,24" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="scoretext" position="10,90" size="216,50" font="{font};{fontsize}" halign="left" zPosition="1" />\n\t\t\t\t<widget name="picture" position="226,60" size="560,420" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="picindex" position="796,60" size="206,20" font="{font};{fontsize2}" halign="center" zPosition="1" />\n\t\t\t\t<widget name="pictext" position="10,480" size="992,40" font="{font};{fontsize2}" halign="center" valign="center" zPosition="1" />\n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,{position}" size="1240,640" title="Mehr Rezeptbilder - Chefkoch.de">\n\t\t\t\t<ePixmap position="0,0" size="1240,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/chefkochHD.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="364,10" size="512,44" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="score" position="3,70" size="236,36" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="scoretext" position="10,113" size="260,50" font="{font};{fontsize}" halign="left" zPosition="1" />\n\t\t\t\t<widget name="picture" position="270,70" size="700,525" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="picindex" position="980,70" size="250,22" font="{font};{fontsize2}" halign="center" zPosition="1" />\n\t\t\t\t<widget name="pictext" position="10,595" size="1220,48" font="{font};{fontsize2}" halign="center" valign="center" zPosition="1" />\n\t\t\t</screen>'

    def __init__(self, session, link, score, scoretext):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        if config.plugins.chefkoch.plugin_size.value == 'full':
            self.xd = False
            position = str(config.plugins.chefkoch.position.value)
            if config.plugins.chefkoch.font_size.value == 'large':
                fontsize = '22'
                fontsize2 = '20'
            else:
                fontsize = '20'
                fontsize2 = '18'
            self.dict = {'position': position,
             'font': font,
             'fontsize': fontsize,
             'fontsize2': fontsize2}
            self.skin = applySkinVars(ChefkochPicShow.skinHD, self.dict)
        else:
            self.xd = True
            deskWidth = getDesktop(0).size().width()
            if deskWidth >= 1280:
                position = 'center'
            else:
                position = str(config.plugins.chefkoch.position.value)
            if config.plugins.chefkoch.font_size.value == 'large':
                fontsize = '20'
                fontsize2 = '18'
            else:
                fontsize = '18'
                fontsize2 = '16'
            self.dict = {'position': position,
             'font': font,
             'fontsize': fontsize,
             'fontsize2': fontsize2}
            self.skin = applySkinVars(ChefkochPicShow.skin, self.dict)
        Screen.__init__(self, session)
        self.baseurl = 'http://www.chefkoch.de'
        self.picfile = '/tmp/chefkoch.jpg'
        self.hideflag = True
        self.pixlist = []
        self.picmax = 0
        self.count = 0
        self.score = score
        self.scoretext = scoretext
        self.slidetype = 'static'
        self['score'] = Pixmap()
        self['scoretext'] = Label('')
        self['scoretext'].hide()
        self['picture'] = Pixmap()
        self['picindex'] = Label('')
        self['pictext'] = Label('')
        self['label'] = Label('OK = Vollbild\n< > = Zur\xfcck / Vorw\xc3\xa4rts')
        self['NumberActions'] = NumberActionMap(['NumberActions',
         'OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.picup,
         'left': self.picdown,
         'up': self.picup,
         'down': self.picdown,
         'red': self.infoScreen,
         'yellow': self.infoScreen,
         'green': self.infoScreen,
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
         '9': self.gotoPic,
         'displayHelp': self.infoScreen}, -1)
        self.getInfoTimer = eTimer()
        self.getInfoTimer.callback.append(self.download(link, self.getPixPage))
        self.getInfoTimer.start(500, True)

    def getPixPage(self, output):
        output = output.decode('latin1').encode('utf-8')
        startpos = find(output, '<div id="slideshow">')
        endpos = find(output, '<div id="recipe-image-voting-box">')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        title = search('<title>(.*?)</title>', output)
        title = transHTML(title.group(1))
        self.setTitle(title)
        self['pictext'].setText('%s' % title)
        if fileExists(self.score):
            self.showScore(self.score)
            self['score'].show()
        self['scoretext'].setText(self.scoretext)
        self['scoretext'].show()
        if search('<a href="https://static.chefkoch-cdn.de/ck.de/rezepte/', bereich) is not None:
            self.slidetype = 'static'
            self.pixlist = re.findall('<a href="https://static.chefkoch-cdn.de/ck.de/rezepte/(.*?)" id="', bereich)
            picurl = 'https://static.chefkoch-cdn.de/ck.de/rezepte/' + self.pixlist[0]
        elif search('<a href="https://cdn.chefkoch.de/ck.de/rezepte/', bereich) is not None:
            self.slidetype = 'cdn'
            self.pixlist = re.findall('<a href="https://cdn.chefkoch.de/ck.de/rezepte/(.*?)" id="', bereich)
            picurl = 'https://cdn.chefkoch.de/ck.de/rezepte/' + self.pixlist[0]
        elif search('src="https://cdn.chefkoch.de/ck.de/rezepte/', bereich) is not None:
            self.slidetype = 'cdn'
            self.pixlist = re.findall('src="https://cdn.chefkoch.de/ck.de/rezepte/(.*?)"', bereich)
            picurl = 'https://cdn.chefkoch.de/ck.de/rezepte/' + self.pixlist[0]
        else:
            self.session.open(MessageBox, '\nKein Foto vorhanden', MessageBox.TYPE_INFO, close_on_any_key=True)
            return
        try:
            self.download(picurl, self.getPic)
        except IndexError:
            pass

        self.picmax = len(self.pixlist)
        try:
            picnumber = self.count + 1
            self['picindex'].setText('Bild %s von %s' % (picnumber, self.picmax))
        except IndexError:
            pass

        return

    def ok(self):
        self.session.openWithCallback(self.showPic(self.picfile), FullScreen)

    def picup(self):
        self.count += 1
        if self.count < self.picmax:
            try:
                if self.slidetype == 'static':
                    link = 'https://static.chefkoch-cdn.de/ck.de/rezepte/' + self.pixlist[self.count]
                else:
                    link = 'https://cdn.chefkoch.de/ck.de/rezepte/' + self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('Bild %s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = 0
            try:
                if self.slidetype == 'static':
                    link = 'https://static.chefkoch-cdn.de/ck.de/rezepte/' + self.pixlist[self.count]
                else:
                    link = 'https://cdn.chefkoch.de/ck.de/rezepte/' + self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('Bild %s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def picdown(self):
        self.count -= 1
        if self.count >= 0:
            try:
                if self.slidetype == 'static':
                    link = 'https://static.chefkoch-cdn.de/ck.de/rezepte/' + self.pixlist[self.count]
                else:
                    link = 'https://cdn.chefkoch.de/ck.de/rezepte/' + self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('Bild %s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        else:
            self.count = self.picmax - 1
            try:
                if self.slidetype == 'static':
                    link = 'https://static.chefkoch-cdn.de/ck.de/rezepte/' + self.pixlist[self.count]
                else:
                    link = 'https://cdn.chefkoch.de/ck.de/rezepte/' + self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('Bild %s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

    def gotoPic(self, number):
        self.session.openWithCallback(self.numberEntered, getNumber, number, 2)

    def numberEntered(self, number):
        if number is None or number == 0:
            pass
        else:
            if number > self.picmax:
                number = self.picmax
            self.count = number - 1
            try:
                if self.slidetype == 'static':
                    link = 'https://static.chefkoch-cdn.de/ck.de/rezepte/' + self.pixlist[self.count]
                else:
                    link = 'https://cdn.chefkoch.de/ck.de/rezepte/' + self.pixlist[self.count]
                self.download(link, self.getPic)
            except IndexError:
                pass

            try:
                picnumber = self.count + 1
                self['picindex'].setText('Bild %s von %s' % (picnumber, self.picmax))
            except IndexError:
                pass

        return

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.showPic(self.picfile)

    def showPic(self, picture):
        if self.xd == True:
            currPic = loadPic(picture, 560, 420, 3, 0, 0, 0)
        else:
            currPic = loadPic(picture, 700, 525, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def showScore(self, score):
        if self.xd == True:
            currPic = loadPic(score, 157, 24, 3, 0, 0, 0)
        else:
            currPic = loadPic(score, 236, 36, 3, 0, 0, 0)
        if currPic != None:
            self['score'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def infoScreen(self):
        self.session.open(infoScreenChefkoch, True)

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

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class FullScreen(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="1024,576" flags="wfNoBorder" title="  " >\n\t\t\t\t<eLabel position="0,0" size="1024,576" backgroundColor="#000000" zPosition="1" />\n\t\t\t\t<widget name="picture" position="0,0" size="1024,576" alphatest="blend" zPosition="2" />\n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="1280,720" flags="wfNoBorder" title="  " >\n\t\t\t\t<eLabel position="0,0" size="1280,720" backgroundColor="#000000" zPosition="1" />\n\t\t\t\t<widget name="picture" position="0,0" size="1280,720" alphatest="blend" zPosition="2" />\n\t\t\t</screen>'

    def __init__(self, session):
        deskWidth = getDesktop(0).size().width()
        if deskWidth >= 1280:
            self.skin = FullScreen.skinHD
            self.xd = False
        else:
            self.skin = FullScreen.skin
            self.xd = True
        Screen.__init__(self, session)
        self.picfile = '/tmp/chefkoch.jpg'
        self.hideflag = True
        self['picture'] = Pixmap()
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.exit,
         'cancel': self.exit,
         'red': self.infoScreen,
         'yellow': self.infoScreen,
         'green': self.infoScreen,
         'blue': self.hideScreen}, -1)
        self.onShown.append(self.showPic)

    def showPic(self):
        if self.xd == True:
            currPic = loadPic(self.picfile, 1024, 576, 3, 0, 0, 0)
        else:
            currPic = loadPic(self.picfile, 1280, 720, 3, 0, 0, 0)
        if currPic != None:
            self['picture'].instance.setPixmap(currPic)
        return

    def infoScreen(self):
        self.session.open(infoScreenChefkoch, True)

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

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class chefkochFav(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="520,490" title=" ">\n\t\t\t\t<ePixmap position="0,0" size="520,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/chefkoch.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="208,16" size="250,20" font="{font};16" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<ePixmap position="184,16" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/red.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="favmenu" position="10,60" size="500,420" scrollbarMode="showOnDemand" zPosition="1" />\n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="620,590" title=" ">\n\t\t\t\t<ePixmap position="0,0" size="620,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/chefkochHD.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="243,20" size="250,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<ePixmap position="219,20" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/red.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="favmenu" position="10,70" size="600,510" scrollbarMode="showOnDemand" zPosition="1" />\n\t\t\t</screen>'

    def __init__(self, session):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        if config.plugins.chefkoch.plugin_size.value == 'full':
            self.listwidth = 600
            self.font = -1
            self.xd = False
            self.skin = applySkinVars(chefkochFav.skinHD, self.dict)
        else:
            self.listwidth = 500
            self.font = 0
            self.xd = True
            self.skin = applySkinVars(chefkochFav.skin, self.dict)
        self.session = session
        Screen.__init__(self, session)
        self.hideflag = True
        self.count = 0
        self.favlist = []
        self.favlink = []
        self.faventries = []
        self['favmenu'] = ItemList([])
        self['label'] = Label('= Entferne Favorit')
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'NumberActions'], {'ok': self.ok,
         'cancel': self.exit,
         'down': self.down,
         'up': self.up,
         'red': self.red,
         'yellow': self.infoScreen,
         'green': self.infoScreen,
         'blue': self.hideScreen,
         '0': self.move2end,
         '1': self.move2first}, -1)
        self.makeFav()

    def makeFav(self):
        self.setTitle('Chefkoch:::Favoriten')
        self.favoriten = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/db/favoriten'
        if fileExists(self.favoriten):
            f = open(self.favoriten, 'r')
            for line in f:
                if ':::' in line:
                    self.count += 1
                    favline = line.split(':::')
                    id = self.count
                    titel = str(favline[0])
                    link = favline[1]
                    res = ['']
                    res.append(MultiContentEntryText(pos=(0, 0), size=(self.listwidth, 30), font=self.font, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=titel))
                    self.faventries.append(res)
                    self.favlist.append(titel)
                    self.favlink.append(link)

            f.close()
            self['favmenu'].l.setList(self.faventries)
            if self.xd == False:
                self['favmenu'].l.setItemHeight(30)
            else:
                self['favmenu'].l.setItemHeight(28)

    def ok(self):
        try:
            c = self.getIndex(self['favmenu'])
            titel = self.favlist[c]
            link = self.favlink[c]
            link = link.replace('\n', '')
            if search('Chefkoch TV: ', titel) is not None:
                self.session.open(ChefkochView, link, True, False, False, True, True)
            elif search('/magazin/', link) is not None:
                self.session.open(ChefkochView, link, True, False, False, True, False)
            else:
                self.session.open(ChefkochView, link, True, False, False, False, False)
        except IndexError:
            pass

        return

    def red(self):
        if len(self.favlist) > 0:
            try:
                c = self.getIndex(self['favmenu'])
                name = self.favlist[c]
            except IndexError:
                name = ''

            self.session.openWithCallback(self.red_return, MessageBox, "\nRezept '%s' aus den Favoriten entfernen?" % name, MessageBox.TYPE_YESNO)

    def red_return(self, answer):
        if answer is True:
            c = self.getIndex(self['favmenu'])
            try:
                link = self.favlink[c]
            except IndexError:
                link = 'NONE'

            data = ''
            f = open(self.favoriten, 'r')
            for line in f:
                if link not in line and line != '\n':
                    data = data + line

            f.close()
            fnew = open(self.favoriten + '.new', 'w')
            fnew.write(data)
            fnew.close()
            os.rename(self.favoriten + '.new', self.favoriten)
            self.favlist = []
            self.favlink = []
            self.faventries = []
            self.makeFav()

    def move2first(self):
        try:
            c = self.getIndex(self['favmenu'])
            fav = self.favlist[c] + ':::' + self.favlink[c]
            fnew = open(self.favoriten + '.new', 'w')
            fnew.write(fav)
            fnew.close()
            data = ''
            f = open(self.favoriten, 'r')
            for line in f:
                if fav not in line and line != '\n':
                    data = data + line

            f.close()
            fnew = open(self.favoriten + '.new', 'a')
            fnew.write(data)
            fnew.close()
            os.rename(self.favoriten + '.new', self.favoriten)
            self.favlist = []
            self.favlink = []
            self.faventries = []
            self.makeFav()
        except IndexError:
            pass

    def move2end(self):
        try:
            c = self.getIndex(self['favmenu'])
            fav = self.favlist[c] + ':::' + self.favlink[c]
            data = ''
            f = open(self.favoriten, 'r')
            for line in f:
                if fav not in line and line != '\n':
                    data = data + line

            f.close()
            fnew = open(self.favoriten + '.new', 'w')
            fnew.write(data)
            fnew.close()
            fnew = open(self.favoriten + '.new', 'a')
            fnew.write(fav)
            fnew.close()
            os.rename(self.favoriten + '.new', self.favoriten)
            self.favlist = []
            self.favlink = []
            self.faventries = []
            self.makeFav()
        except IndexError:
            pass

    def getIndex(self, list):
        return list.getSelectedIndex()

    def down(self):
        self['favmenu'].down()

    def up(self):
        self['favmenu'].up()

    def infoScreen(self):
        self.session.open(infoScreenChefkoch, True)

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

    def exit(self):
        if self.hideflag == False:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class DownloadVideo(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="550,180" title="Download Video..." >\n\t\t\t\t<ePixmap position="10,10" size="530,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/download.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="name" position="10,60" size="530,50" font="{font};20" halign="center" valign="center" transparent="1" zPosition="1" />\n\t\t\t\t<widget name="size" position="10,110" size="530,25" font="{font};20" halign="center" transparent="1" zPosition="1" />\n\t\t\t\t<widget name="slider" position="10,140" size="530,30" transparent="0" zPosition="2" />\n\t\t\t</screen>'

    def __init__(self, session, url, name):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(DownloadVideo.skin, self.dict)
        Screen.__init__(self, session)
        try:
            moviedir = config.movielist.videodirs.value[0]
        except IndexError:
            moviedir = '/media/hdd/'

        self.name = name
        self.url = url
        self.filename = moviedir + name + '.mp4'
        self.hideflag = True
        self.loading = True
        self.filesize = 0
        self.localsize = 0
        self.progress = 0
        self.slider = Slider(0, 100)
        self['name'] = Label('Chefkoch TV: %s' % self.filename)
        self['size'] = Label('')
        self['slider'] = self.slider
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'HelpActions'], {'ok': self.hideScreen,
         'cancel': self.exit,
         'red': self.infoScreen,
         'yellow': self.infoScreen,
         'green': self.infoScreen,
         'blue': self.hideScreen,
         'displayHelp': self.infoScreen}, -1)
        self.StatusTimer = eTimer()
        self.StatusTimer.callback.append(self.UpdateStatus)
        self.StatusTimer.start(500, True)
        self.updateTimer = eTimer()
        self.updateTimer.callback.append(self.refresh)
        self.update_interval = 3000
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        self.loading = True
        self.getFileSize()
        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.finished)
        self.container.execute("wget -c '%s' -O '%s'" % (self.url, self.filename))

    def getFileSize(self):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        request = Request(self.url, None, header)
        try:
            filesize = urlopen(request, timeout=20).info().get('Content-Length')
            filesize = float(filesize)
            self.filesize = filesize
        except URLError:
            pass

        return

    def UpdateStatus(self):
        if fileExists(self.filename, 'r'):
            localsize = path.getsize(self.filename)
            self.localsize = localsize
        else:
            self.localsize = 0
        if self.filesize > 0:
            self.progress = self.localsize / self.filesize * 100
        if int(self.progress) > 0:
            self['slider'].setValue(int(self.progress))
            self['size'].setText('%s MB von %s MB' % (int(self.localsize) / 1048576, int(self.filesize) / 1048576))
        elif self.localsize > 0 and self.filesize == 0:
            self['slider'].setValue(0)
            self['size'].setText('%s MB von ??? MB' % (int(self.localsize) / 1048576))
        elif self.filesize > 0 and self.localsize == 0:
            self['slider'].setValue(0)
            self['size'].setText('0 MB von %s MB' % (int(self.filesize) / 1048576))
        self.updateTimer.start(self.update_interval)

    def refresh(self):
        self.UpdateStatus()

    def finished(self, retval):
        self.loading = False
        del self.container.appClosed[:]
        del self.container
        self.loading = False
        self.setTitle('Download beendet!')
        self['slider'].setValue(100)
        self.updateTimer.stop()
        self.show()
        self.session.openWithCallback(self.playVideo, MessageBox, '\nDownload beendet. Soll das Video nun gestartet werden?', MessageBox.TYPE_YESNO)

    def playVideo(self, answer):
        if answer is True:
            sref = eServiceReference(4097, 0, self.filename)
            sref.setName(self.name)
            self.session.openWithCallback(self.exit, MoviePlayer, sref)
        else:
            self.close()

    def infoScreen(self):
        self.session.open(infoScreenChefkoch, True)

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

    def stopDownload(self, answer):
        if answer is True:
            try:
                del self.container.appClosed[:]
                del self.container
            except AttributeError:
                pass

            if fileExists(self.filename):
                os.remove(self.filename)
            self.close()

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.loading == True:
            self.session.openWithCallback(self.stopDownload, MessageBox, '\nDer Download ist noch nicht beendet.\nSoll der Download abgebrochen und das Video gel\xc3\xb6scht werden?', MessageBox.TYPE_YESNO)
        else:
            self.close()


class infoScreenChefkoch(Screen):
    skin = '\n\t\t\t\t<screen position="center,center" size="425,425" title=" " >\n\t\t\t\t\t<ePixmap position="0,0" size="425,425" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/info.png" zPosition="1"/>\n\t\t\t\t\t<widget name="label" position="0,72" size="425,350" font="{font};18" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="center" valign="center" transparent="1" zPosition="2" />\n\t\t\t\t</screen>'

    def __init__(self, session, check):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(infoScreenChefkoch.skin, self.dict)
        Screen.__init__(self, session)
        self.check = check
        self['label'] = Label('www.kashmir-plugins.de\n\nGef\xc3\xa4llt Ihnen das Plugin?\nM\xc3\xb6chten Sie etwas spenden?\nGehen Sie dazu bitte wie folgt vor:\n\n\n\n1. Melden Sie sich bei PayPal an\n2. Klicken Sie auf: Geld senden\n3. Geld an Freunde und Familie senden\n4. Adresse: paypal@kashmir-plugins.de\n5. Betrag: 5 Euro\n6. Weiter\n7. Geld senden\nDanke!')
        self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.close,
         'cancel': self.close}, -1)
        self.version = '1.5rc5'
        if self.check == True:
            self.setTitle('Chefkoch.de %s' % self.version)
            self.link = 'http://sites.google.com/site/kashmirplugins/home/chefkoch-de'
            self.makeVersionTimer = eTimer()
            self.makeVersionTimer.callback.append(self.download(self.link, self.checkVersion))
            self.makeVersionTimer.start(500, True)
        else:
            self.setTitle('PayPal Info')

    def checkVersion(self, output):
        self.pluginname = 'Chefkoch.de'
        version = search('<img alt="Version (.*?)"', output)
        if version is not None:
            version = version.group(1)
            if version != self.version:
                pluginsource = search('<a href="(.*?)\\?attredirects=0".*?<img alt="Version ', output)
                if pluginsource is not None:
                    self.pluginsource = pluginsource.group(1)
                    self.pluginfile = self.pluginsource.replace('https://sites.google.com/site/kashmirplugins/', '').replace('%5f', '_')
                    versioninfo = re.findall('<li><span style="color:rgb\\(100,118,135\\)">(.*?)</span></li>', output)
                    if len(versioninfo) > 0:
                        info = ''
                        idx = 0
                        for x in versioninfo:
                            idx += 1

                        for i in range(idx):
                            try:
                                info = info + ' - ' + versioninfo[i] + '\n'
                            except IndexError:
                                Info = ''

                        self.session.openWithCallback(self.downloadPlugin, MessageBox, '\nEine neue Plugin Version ist verf\xfcgbar:\n%s Version %s\n\n%s\nSoll die neue Version jetzt installiert werden?' % (self.pluginname, version, info), MessageBox.TYPE_YESNO)
                    else:
                        self.session.openWithCallback(self.downloadPlugin, MessageBox, '\nEine neue Plugin Version ist verf\xfcgbar:\n%s Version %s\n\nSoll die neue Version jetzt installiert werden?' % (self.pluginname, version), MessageBox.TYPE_YESNO)
            else:
                self.session.open(MessageBox, '\nwww.kashmir-plugins.de\n\nIhre %s Version %s ist aktuell.' % (self.pluginname, self.version), MessageBox.TYPE_INFO, close_on_any_key=True)
        return

    def downloadPlugin(self, answer):
        if answer is True:
            self.pluginfile = '/tmp/' + str(self.pluginfile)
            self.session.openWithCallback(self.close, DownloadUpdate, self.pluginsource, self.pluginfile, self.pluginname)

    def download(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass


class DownloadUpdate(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="550,190" title="Download Update..." >\n\t\t\t\t<ePixmap position="10,10" size="530,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/download.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="name" position="10,70" size="530,50" font="Regular;20" halign="center" valign="center" transparent="1" zPosition="1" />\n\t\t\t\t<widget name="size" position="10,120" size="530,25" font="Regular;20" halign="center" transparent="1" zPosition="1" />\n\t\t\t\t<widget name="slider" position="10,150" size="530,30" transparent="0" zPosition="2" />\n\t\t\t</screen>'

    def __init__(self, session, url, file, name):
        Screen.__init__(self, session)
        if config.plugins.chefkoch.fhd.value == 'yes':
            try:
                gMainDC.getInstance().setResolution(1920, 1080)
                desktop = getDesktop(0)
                desktop.resize(eSize(1920, 1080))
            except:
                import traceback
                traceback.print_exc()

        self.url = url
        self.file = file
        self.name = name
        self.hideflag = True
        self.install = False
        self.filesize = 0
        self.localsize = 0
        self.progress = 0
        self.slider = Slider(0, 100)
        self['name'] = Label('Downloading: %s' % self.file)
        self['size'] = Label('')
        self['slider'] = self.slider
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.hideScreen,
         'cancel': self.exit,
         'blue': self.hideScreen}, -1)
        self.statusTimer = eTimer()
        self.statusTimer.callback.append(self.UpdateStatus)
        self.statusTimer.start(500, True)
        self.updateTimer = eTimer()
        self.updateTimer.callback.append(self.refresh)
        self.update_interval = 3000
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        self.getFileSize()
        downloadPage(self.url, self.file).addCallback(self.installPlugin)

    def installPlugin(self, string):
        self.install = True
        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.finished)
        self.container.dataAvail.append(self.dataAvail)
        self.container.execute('opkg install %s' % self.file)

    def getFileSize(self):
        header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'en-us,en;q=0.5'}
        request = Request(self.url, None, header)
        try:
            filesize = urlopen(request, timeout=20).info().get('Content-Length')
            filesize = float(filesize)
            self.filesize = filesize
        except URLError:
            pass

        return

    def UpdateStatus(self):
        if fileExists(self.file):
            localsize = path.getsize(self.file)
            self.localsize = localsize
        else:
            self.localsize = 0
        if self.filesize > 0:
            self.progress = self.localsize / self.filesize * 100
        if int(self.progress) > 1:
            self['slider'].setValue(int(self.progress))
            self['size'].setText('%s KB von %s KB' % (int(self.localsize) / 1024, int(self.filesize) / 1024))
        elif self.localsize > 0 and self.filesize == 0:
            self['slider'].setValue(0)
            self['size'].setText('%s KB von ??? KB' % (int(self.localsize) / 1024))
        elif self.filesize > 0 and self.localsize == 0:
            self['slider'].setValue(0)
            self['size'].setText('0 KB von %s KB' % (int(self.filesize) / 1024))
        self.updateTimer.start(self.update_interval)

    def refresh(self):
        self.UpdateStatus()

    def dataAvail(self, data):
        if data is not None:
            self.session.open(MessageBox, '\n%s' % data, MessageBox.TYPE_INFO, close_on_any_key=True)
        return

    def finished(self, retval):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.install = False
        del self.container.appClosed[:]
        del self.container.dataAvail[:]
        del self.container
        self.statusTimer.stop()
        self.updateTimer.stop()
        if retval == 0:
            self.setTitle('Update finished!')
            text = self.name + ' Update finished!'
            self['name'].setText(text)
            self['slider'].setValue(100)
            self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas %s Plugin wurde erfolgreich installiert.\nBitte starten Sie Enigma neu.' % self.name, MessageBox.TYPE_YESNO)
        else:
            self.close()

    def restartGUI(self, answer):
        if answer is True:
            try:
                self.session.open(TryQuitMainloop, 3)
            except RuntimeError:
                self.close()

        else:
            self.close()

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

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.install == True:
            del self.container.appClosed[:]
            del self.container.dataAvail[:]
            del self.container
        self.setTitle('Update canceled!')
        self['slider'].setValue(0)
        self.statusTimer.stop()
        self.updateTimer.stop()
        if fileExists(self.file):
            os.remove(self.file)
        self.close()


class ItemList(MenuList):

    def __init__(self, items, enableWrapAround=True):
        MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
        if config.plugins.chefkoch.font.value == 'yes':
            self.l.setFont(-2, gFont('Sans', 24))
            if config.plugins.chefkoch.font_size.value == 'large':
                self.l.setFont(-1, gFont('Sans', 24))
                self.l.setFont(0, gFont('Sans', 22))
                self.l.setFont(1, gFont('Sans', 20))
                self.l.setFont(2, gFont('Sans', 18))
            else:
                self.l.setFont(-1, gFont('Sans', 22))
                self.l.setFont(0, gFont('Sans', 20))
                self.l.setFont(1, gFont('Sans', 18))
                self.l.setFont(2, gFont('Sans', 16))
        else:
            self.l.setFont(-2, gFont('Regular', 24))
            if config.plugins.chefkoch.font_size.value == 'large':
                self.l.setFont(-1, gFont('Regular', 24))
                self.l.setFont(0, gFont('Regular', 22))
                self.l.setFont(1, gFont('Regular', 20))
                self.l.setFont(2, gFont('Regular', 18))
            else:
                self.l.setFont(-1, gFont('Regular', 22))
                self.l.setFont(0, gFont('Regular', 20))
                self.l.setFont(1, gFont('Regular', 18))
                self.l.setFont(2, gFont('Regular', 16))


class ChefkochMain(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="290,520" title="Chefkoch.de">\n\t\t\t\t<ePixmap position="0,0" size="290,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/menu.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="34,5" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label2" position="34,27" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label3" position="186,5" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label4" position="186,27" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />\n\t\t\t\t<ePixmap position="10,5" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/green.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<ePixmap position="10,27" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/yellow.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<ePixmap position="262,5" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/red.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<ePixmap position="262,27" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/blue.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="mainmenu" position="10,60" size="270,270" scrollbarMode="showNever" zPosition="2" />\n\t\t\t\t<widget name="secondmenu" position="10,60" size="270,450" scrollbarMode="showNever" zPosition="2" />\n\t\t\t\t<widget name="thirdmenu" position="10,60" size="270,450" scrollbarMode="showNever" zPosition="2" />\n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="290,590" title="Chefkoch.de">\n\t\t\t\t<ePixmap position="0,0" size="290,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/menuHD.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="label" position="34,10" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label2" position="34,32" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label3" position="186,10" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />\n\t\t\t\t<widget name="label4" position="186,32" size="70,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />\n\t\t\t\t<ePixmap position="10,10" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/green.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<ePixmap position="10,32" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/yellow.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<ePixmap position="262,10" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/red.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<ePixmap position="262,32" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/blue.png" alphatest="blend" zPosition="2" />\n\t\t\t\t<widget name="mainmenu" position="10,70" size="270,270" scrollbarMode="showNever" zPosition="2" />\n\t\t\t\t<widget name="secondmenu" position="10,70" size="270,510" scrollbarMode="showNever" zPosition="2" />\n\t\t\t\t<widget name="thirdmenu" position="10,70" size="270,510" scrollbarMode="showNever" zPosition="2" />\n\t\t\t</screen>'

    def __init__(self, session):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        if config.plugins.chefkoch.plugin_size.value == 'full':
            self.skin = applySkinVars(ChefkochMain.skinHD, self.dict)
        else:
            self.skin = applySkinVars(ChefkochMain.skin, self.dict)
        self.session = session
        Screen.__init__(self, session)
        self.fhd = False
        if config.plugins.chefkoch.fhd.value == 'yes':
            if getDesktop(0).size().width() == 1920:
                self.fhd = True
                try:
                    gMainDC.getInstance().setResolution(1280, 720)
                    desktop = getDesktop(0)
                    desktop.resize(eSize(1280, 720))
                except:
                    import traceback
                    traceback.print_exc()

        self.baseurl = 'http://www.chefkoch.de/rezepte/kategorien/'
        self.localhtml = '/tmp/chefkoch.html'
        self.picfile = '/tmp/chefkoch.jpg'
        self.pic1 = '/tmp/chefkoch1.jpg'
        self.pic2 = '/tmp/chefkoch2.jpg'
        self.pic3 = '/tmp/chefkoch3.jpg'
        self.pic4 = '/tmp/chefkoch4.jpg'
        self.pic5 = '/tmp/chefkoch5.jpg'
        self.pic6 = '/tmp/chefkoch6.jpg'
        self.rezeptfile = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/db/rezept.html'
        self.mainseite = []
        self.secondseite = []
        self.mainmenulist = []
        self.mainmenulink = []
        self.secondmenulist = []
        self.secondmenulink = []
        self.thirdmenulist = []
        self.thirdmenulink = []
        self.actmenu = 'mainmenu'
        self.hideflag = True
        self['mainmenu'] = ItemList([])
        self['secondmenu'] = ItemList([])
        self['thirdmenu'] = ItemList([])
        self['label'] = Label('= Zufall')
        self['label2'] = Label('= Suche')
        self['label3'] = Label('Favorit = ')
        self['label4'] = Label('Hide = ')
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ColorActions',
         'ChannelSelectBaseActions',
         'MovieSelectionActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.zap,
         'prevBouquet': self.zap,
         'red': self.fav,
         'yellow': self.yellow,
         'green': self.zufall,
         'blue': self.hideScreen,
         'showEventInfo': self.infoScreen,
         'contextMenu': self.config,
         'displayHelp': self.infoScreen}, -1)
        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        if config.plugins.chefkoch.autoupdate.value == 'yes':
            self.version = '1.5rc5'
            self.link = 'http://sites.google.com/site/kashmirplugins/home/chefkoch-de'
            self.makeVersionTimer = eTimer()
            self.makeVersionTimer.callback.append(self.downloadVersion(self.link, self.checkVersion))
            self.makeVersionTimer.start(500, True)
        self.ChefTimer = eTimer()
        self.ChefTimer.callback.append(self.downloadFullPage(self.baseurl, self.makeMainMenu))
        self.ChefTimer.start(500, True)

    def ok(self):
        try:
            c = self.getIndex(self[self.actmenu])
        except IndexError:
            c = 0

        if self.actmenu == 'mainmenu':
            try:
                seite = self.mainseite[c]
                link = self.mainmenulink[c]
                if seite == 'Chefkoch Magazin':
                    self.session.openWithCallback(self.selectMainMenu, ChefkochView, link, False, False, False, True, False)
                elif seite == 'Chefkoch TV':
                    self.session.openWithCallback(self.selectMainMenu, ChefkochView, link, False, False, False, True, True)
                else:
                    self.makeSecondMenu(seite)
            except IndexError:
                pass

        elif self.actmenu == 'secondmenu':
            try:
                seite = self.secondseite[c]
                if seite == 'Afrika' or seite == 'Amerika' or seite == 'Asien' or seite == 'Europa' or seite == 'Methoden' or seite == 'Beilage' or seite == 'Hauptspeise' or seite == 'Salat' or seite == 'Suppen' or seite == 'Vorspeisen' or seite == 'Cocktail' or seite == 'Gesund und fettarm':
                    link = self.baseurl
                    self.makeThirdMenu(seite)
                elif seite == 'K\xc3\xb6stliche Vorspeisen' or seite == 'Raffinierte Hauptspeisen':
                    link = 'http://www.chefkoch.de/magazin/6,103,0/Chefkoch/'
                    self.downloadThirdTVMenu(link, seite)
                else:
                    link = self.secondmenulink[c]
                    self.session.openWithCallback(self.selectSecondMenu, ChefkochView, link, False, False, False, False, False)
            except IndexError:
                pass

        elif self.actmenu == 'thirdmenu':
            try:
                link = self.thirdmenulink[c]
                self.session.openWithCallback(self.selectThirdMenu, ChefkochView, link, False, False, False, False, False)
            except IndexError:
                pass

    def makeMainMenu(self, string):
        output = open(self.localhtml, 'r').read()
        startpos = output.find('>Rezeptkategorien</h1>')
        endpos = output.find('<!-- /content -->')
        bereich = output[startpos:endpos].decode('latin1').encode('utf-8')
        bereich = transHTML(bereich)
        name = re.findall('<h2 class="category-level-1">\n.*?<a href=".*?">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                link = self.baseurl
                res = ['']
                res.append(MultiContentEntryText(pos=(0, 1), size=(270, 30), font=-2, flags=RT_HALIGN_CENTER, text=name[i]))
                self.mainmenulist.append(res)
                self.mainmenulink.append(link)
                self.mainseite.append(name[i])
            except IndexError:
                pass

        res = ['']
        res.append(MultiContentEntryText(pos=(0, 1), size=(270, 30), font=-2, flags=RT_HALIGN_CENTER, text='Chefkoch Magazin'))
        self.mainmenulist.append(res)
        self.mainmenulink.append('http://www.chefkoch.de/magazin/')
        self.mainseite.append('Chefkoch Magazin')
        res = ['']
        res.append(MultiContentEntryText(pos=(0, 1), size=(270, 30), font=-2, flags=RT_HALIGN_CENTER, text='Chefkoch TV'))
        self.mainmenulist.append(res)
        self.mainmenulink.append('http://www.chefkoch.de/video/')
        self.mainseite.append('Chefkoch TV')
        self['mainmenu'].l.setList(self.mainmenulist)
        self['mainmenu'].l.setItemHeight(30)
        self.selectMainMenu()

    def makeSecondMenu(self, seite):
        output = open(self.localhtml, 'r').read()
        self.secondmenulist = []
        self.secondmenulink = []
        self.secondseite = []
        self.seite = seite
        if seite == 'Backen & S\xc3\xbcssspeisen':
            startpos = output.find('title="Backen &amp; S&uuml;&szlig;speisen Rezepte">Backen &amp; S&uuml;&szlig;speisen</a>')
            endpos = output.find('title="Getr&auml;nke Rezepte">Getr&auml;nke</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Getr\xc3\xa4nke':
            startpos = output.find('title="Getr&auml;nke Rezepte">Getr&auml;nke</a>')
            endpos = output.find('title="Men&uuml;art Rezepte">Men&uuml;art</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Men\xc3\xbcart':
            startpos = output.find('title="Men&uuml;art Rezepte">Men&uuml;art</a>')
            endpos = output.find('title="Regional Rezepte">Regional</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Regional':
            startpos = output.find('title="Regional Rezepte">Regional</a>')
            endpos = output.find('title="Saisonal Rezepte">Saisonal</a>')
            bereich = output[startpos:endpos]
            bereich = sub('">Mittlerer und Naher Osten</a>', '">Mittlerer Osten</a>', bereich)
            bereich = transHTML(bereich)
        elif seite == 'Saisonal':
            startpos = output.find('title="Saisonal Rezepte">Saisonal</a>')
            endpos = output.find('title="Spezielles Rezepte">Spezielles</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Spezielles':
            startpos = output.find('title="Spezielles Rezepte">Spezielles</a>')
            endpos = output.find('title="Zubereitungsarten Rezepte">Zubereitungsarten</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Zubereitungsarten':
            startpos = output.find('title="Zubereitungsarten Rezepte">Zubereitungsarten</a>')
            endpos = output.find('<!-- /content -->')
            bereich = output[startpos:endpos]
            bereich = sub('">Gew&uuml;rze/&Ouml;l/Essig/Pasten</a>', '">Gew&uuml;rze/&Ouml;l/Essig</a>', bereich)
            bereich = sub('">Snacks und kleine Gerichte</a>', '">Snacks</a>', bereich)
            bereich = transHTML(bereich)
        lnk = re.findall('<div class="category-level-2">\n.*?<a href="(.*?)"', bereich)
        name = re.findall('<div class="category-level-2">\n.*?<a href=".*?">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                link = 'http://www.chefkoch.de' + lnk[i]
                res = ['']
                res.append(MultiContentEntryText(pos=(0, 1), size=(270, 30), font=-2, flags=RT_HALIGN_CENTER, text=name[i]))
                self.secondmenulist.append(res)
                self.secondmenulink.append(link)
                self.secondseite.append(name[i])
            except IndexError:
                pass

        self['secondmenu'].l.setList(self.secondmenulist)
        self['secondmenu'].l.setItemHeight(30)
        self['secondmenu'].moveToIndex(0)
        self.setTitle(seite)
        self.selectSecondMenu()

    def makeThirdMenu(self, seite):
        output = open(self.localhtml, 'r').read()
        self.thirdmenulist = []
        self.thirdmenulink = []
        if seite == 'Afrika':
            startpos = output.find('title="Afrika Rezepte">Afrika</a>')
            endpos = output.find('title="Amerika Rezepte">Amerika</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Amerika':
            startpos = output.find('title="Amerika Rezepte">Amerika</a>')
            endpos = output.find('title="Asien Rezepte">Asien</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Asien':
            startpos = output.find('title="Asien Rezepte">Asien</a>')
            endpos = output.find('title="Australien Rezepte">Australien</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Europa':
            startpos = output.find('title="Europa Rezepte">Europa</a>')
            endpos = output.find('title="Karibik &amp; Exotik Rezepte">Karibik &amp; Exotik</a>')
            bereich = output[startpos:endpos]
            bereich = sub('">Gro&szlig;britannien &amp; Irland</a>', '">Gro&szlig;britannien</a>', bereich)
            bereich = transHTML(bereich)
        elif seite == 'Methoden':
            startpos = output.find('title="Methoden Rezepte">Methoden</a>')
            endpos = output.find('title="Pasta Rezepte">Pasta</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Beilage':
            startpos = output.find('title="Beilage Rezepte">Beilage</a>')
            endpos = output.find('title="Dessert Rezepte">Dessert</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Hauptspeise':
            startpos = output.find('title="Hauptspeise Rezepte">Hauptspeise</a>')
            endpos = output.find('title="Salat Rezepte">Salat</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Salat':
            startpos = output.find('title="Salat Rezepte">Salat</a>')
            endpos = output.find('title="Suppen Rezepte">Suppen</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Suppen':
            startpos = output.find('title="Suppen Rezepte">Suppen</a>')
            endpos = output.find('title="Vorspeisen Rezepte">Vorspeisen</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Vorspeisen':
            startpos = output.find('title="Vorspeisen Rezepte">Vorspeisen</a>')
            endpos = output.find('title="Regional Rezepte">Regional</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Cocktail':
            startpos = output.find('title="Cocktail Rezepte">Cocktail</a>')
            endpos = output.find('title="Kaffee, Tee &amp; Kakao Rezepte">Kaffee, Tee &amp; Kakao</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        elif seite == 'Gesund und fettarm':
            startpos = output.find('title="Gesund und fettarm Rezepte">Gesund und fettarm</a>')
            endpos = output.find('title="Kinder Rezepte">Kinder</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
        lnk = re.findall('<div class="category-level-3">\n.*?<a href="(.*?)"', bereich)
        name = re.findall('<div class="category-level-3">\n.*?title=".*?">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                link = 'http://www.chefkoch.de' + lnk[i]
                res = ['']
                res.append(MultiContentEntryText(pos=(0, 1), size=(270, 30), font=-2, flags=RT_HALIGN_CENTER, text=name[i]))
                self.thirdmenulist.append(res)
                self.thirdmenulink.append(link)
            except IndexError:
                pass

        self['thirdmenu'].l.setList(self.thirdmenulist)
        self['thirdmenu'].l.setItemHeight(30)
        self['thirdmenu'].moveToIndex(0)
        self.setTitle(seite)
        self.selectThirdMenu()

    def makeSecondTVMenu(self, output):
        self.secondmenulist = []
        self.secondmenulink = []
        self.secondseite = []
        startpos = output.find('<ul class="video-categories">')
        endpos = output.find('<div class="sidebar-teaser-link">')
        bereich = output[startpos:endpos]
        bereich = sub('Grillen f\xc3\xbcr Profis', 'Grillen', bereich)
        bereich = sub('Club of Cooks - Powered by chefkoch.de', 'Club of Cooks', bereich)
        bereich = transHTML(bereich)
        lnk = re.findall('<li><a href="(.*?)">', bereich)
        name = re.findall('<li><a href=".*?">(.*?)</a></li>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                link = 'http://www.chefkoch.de' + lnk[i]
                res = ['']
                res.append(MultiContentEntryText(pos=(0, 1), size=(270, 30), font=-2, flags=RT_HALIGN_CENTER, text=name[i]))
                self.secondmenulist.append(res)
                self.secondmenulink.append(link)
                self.secondseite.append(name[i])
            except IndexError:
                pass

        self['secondmenu'].l.setList(self.secondmenulist)
        self['secondmenu'].l.setItemHeight(30)
        self['secondmenu'].moveToIndex(0)
        self.seite = 'Chefkoch TV'
        self.setTitle(self.seite)
        self.selectSecondMenu()

    def makeThirdTVMenu(self, output, seite):
        self.thirdmenulist = []
        self.thirdmenulink = []
        if seite == 'K\xc3\xb6stliche Vorspeisen':
            startpos = output.find('<div class="sidebar-box">')
            endpos = output.find('<li class="level0">\n\t\t\t\t\t\t<a href="/magazin/6,287,0/Chefkoch/">Raffinierte Hauptspeisen</a>')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
            bereich = sub('<li class="level1">', '<div class="category-level-3">', bereich)
            bereich = sub('>Fisch</a>', 'title="">Fisch</a>', bereich)
            bereich = sub('>Fleisch</a>', 'title="">Fleisch</a>', bereich)
            bereich = sub('>Vegetarisch</a>', 'title="">Vegetarisch</a>', bereich)
        elif seite == 'Raffinierte Hauptspeisen':
            startpos = output.find('<li class="level0">\n\t\t\t\t\t\t<a href="/magazin/6,287,0/Chefkoch/">Raffinierte Hauptspeisen</a>')
            endpos = output.find('<!-- /sidebar-box -->')
            bereich = output[startpos:endpos]
            bereich = transHTML(bereich)
            bereich = sub('<li class="level1">', '<div class="category-level-3">', bereich)
            bereich = sub('>Fisch</a>', 'title="">Fisch</a>', bereich)
            bereich = sub('>Fleisch</a>', 'title="">Fleisch</a>', bereich)
            bereich = sub('>Vegetarisch</a>', 'title="">Vegetarisch</a>', bereich)
        lnk = re.findall('<div class="category-level-3">\n.*?<a href="(.*?)"', bereich)
        name = re.findall('<div class="category-level-3">\n.*?title=".*?">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                link = 'http://www.chefkoch.de' + lnk[i]
                res = ['']
                res.append(MultiContentEntryText(pos=(0, 1), size=(270, 30), font=-2, flags=RT_HALIGN_CENTER, text=name[i]))
                self.thirdmenulist.append(res)
                self.thirdmenulink.append(link)
            except IndexError:
                pass

        self['thirdmenu'].l.setList(self.thirdmenulist)
        self['thirdmenu'].l.setItemHeight(30)
        self['thirdmenu'].moveToIndex(0)
        self.setTitle(seite)
        self.selectThirdMenu()

    def selectMainMenu(self):
        self.actmenu = 'mainmenu'
        self['mainmenu'].show()
        self['secondmenu'].hide()
        self['thirdmenu'].hide()
        self['mainmenu'].selectionEnabled(1)
        self['secondmenu'].selectionEnabled(0)
        self['thirdmenu'].selectionEnabled(0)

    def selectSecondMenu(self):
        if len(self.secondmenulist) > 0:
            self.actmenu = 'secondmenu'
            self['mainmenu'].hide()
            self['secondmenu'].show()
            self['thirdmenu'].hide()
            self['mainmenu'].selectionEnabled(0)
            self['secondmenu'].selectionEnabled(1)
            self['thirdmenu'].selectionEnabled(0)

    def selectThirdMenu(self):
        if len(self.thirdmenulist) > 0:
            self.actmenu = 'thirdmenu'
            self['mainmenu'].hide()
            self['secondmenu'].hide()
            self['thirdmenu'].show()
            self['mainmenu'].selectionEnabled(0)
            self['secondmenu'].selectionEnabled(0)
            self['thirdmenu'].selectionEnabled(1)

    def up(self):
        self[self.actmenu].up()

    def down(self):
        self[self.actmenu].down()

    def leftUp(self):
        self[self.actmenu].pageUp()

    def rightDown(self):
        self[self.actmenu].pageDown()

    def checkVersion(self, output):
        self.pluginname = 'Chefkoch.de'
        version = search('<img alt="Version (.*?)"', output)
        if version is not None:
            version = version.group(1)
            if version != self.version:
                pluginsource = search('<a href="(.*?)\\?attredirects=0".*?<img alt="Version ', output)
                if pluginsource is not None:
                    self.pluginsource = pluginsource.group(1)
                    self.pluginfile = self.pluginsource.replace('https://sites.google.com/site/kashmirplugins/', '').replace('%5f', '_')
                    versioninfo = re.findall('<li><span style="color:rgb\\(100,118,135\\)">(.*?)</span></li>', output)
                    if len(versioninfo) > 0:
                        info = ''
                        idx = 0
                        for x in versioninfo:
                            idx += 1

                        for i in range(idx):
                            try:
                                info = info + ' - ' + versioninfo[i] + '\n'
                            except IndexError:
                                Info = ''

                        self.session.openWithCallback(self.downloadPlugin, MessageBox, '\nEine neue Plugin Version ist verf\xfcgbar:\n%s Version %s\n\n%s\nSoll die neue Version jetzt installiert werden?' % (self.pluginname, version, info), MessageBox.TYPE_YESNO)
                    else:
                        self.session.openWithCallback(self.downloadPlugin, MessageBox, '\nEine neue Plugin Version ist verf\xfcgbar:\n%s Version %s\n\nSoll die neue Version jetzt installiert werden?' % (self.pluginname, version), MessageBox.TYPE_YESNO)
            elif config.plugins.chefkoch.paypal.value == 'yes':
                import random
                number = random.randint(1, 4)
                if number == 1:
                    self.session.open(infoScreenChefkoch, False)
        return

    def downloadPlugin(self, answer):
        if answer is True:
            self.pluginfile = '/tmp/' + str(self.pluginfile)
            self.session.openWithCallback(self.close, DownloadUpdate, self.pluginsource, self.pluginfile, self.pluginname)

    def downloadVersion(self, link, name):
        getPage(link).addCallback(name).addErrback(self.downloadVersionError)

    def downloadVersionError(self, output):
        pass

    def downloadSecondTVMenu(self, link):
        getPage(link).addCallback(self.makeSecondTVMenu).addErrback(self.downloadError)

    def downloadThirdTVMenu(self, link, seite):
        getPage(link).addCallback(self.makeThirdTVMenu, seite).addErrback(self.downloadError)

    def downloadFullPage(self, link, name):
        downloadPage(link, self.localhtml).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self.session.open(MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar.', MessageBox.TYPE_INFO, close_on_any_key=True)

    def getIndex(self, list):
        return list.getSelectedIndex()

    def yellow(self):
        self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Chefkoch - Suche Rezepte:', text='')

    def searchReturn(self, search):
        if search and search != '':
            self.searchtext = search.replace(' ', '+')
            searchlink = 'http://www.chefkoch.de/rs/s0/' + self.searchtext + '/Rezepte.html'
            self.session.openWithCallback(self.selectMainMenu, ChefkochView, searchlink, False, False, True, False, False)

    def fav(self):
        self.session.open(chefkochFav)

    def zufall(self):
        link = 'http://www.chefkoch.de/rezepte/zufallsrezept/'
        self.session.openWithCallback(self.selectMainMenu, ChefkochView, link, False, True, False, False, False)

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def config(self):
        config.usage.on_movie_stop.value = self.movie_stop
        config.usage.on_movie_eof.value = self.movie_eof
        self.session.openWithCallback(self.exit, chefkochConfig)

    def infoScreen(self):
        self.session.open(infoScreenChefkoch, True)

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

    def exit(self):
        if self.hideflag == False:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.actmenu == 'mainmenu':
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
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
            if fileExists(self.picfile):
                os.remove(self.picfile)
            if fileExists(self.rezeptfile):
                os.remove(self.rezeptfile)
            if fileExists(self.localhtml):
                os.remove(self.localhtml)
            if self.fhd == True:
                try:
                    gMainDC.getInstance().setResolution(1920, 1080)
                    desktop = getDesktop(0)
                    desktop.resize(eSize(1920, 1080))
                except:
                    import traceback
                    traceback.print_exc()

            self.close()
        elif self.actmenu == 'secondmenu':
            self.setTitle('Chefkoch.de')
            self.selectMainMenu()
        elif self.actmenu == 'thirdmenu':
            self.setTitle(self.seite)
            self.selectSecondMenu()


class chefkochConfig(ConfigListScreen, Screen):
    skin = '\n\t\t\t<screen position="center,center" size="530,518" backgroundColor="#20000000" title="Chefkoch Setup">\n\t\t\t\t<ePixmap position="0,0" size="530,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/chefkoch.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<ePixmap position="9,59" size="512,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/setup/seperator.png" alphatest="off" zPosition="1" />\n\t\t\t\t<widget name="config" position="9,60" size="512,125" itemHeight="25" scrollbarMode="showOnDemand" zPosition="1" />\n\t\t\t\t<ePixmap position="9,186" size="512,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/setup/seperator.png" alphatest="off" zPosition="1" />\n\t\t\t\t<eLabel position="150,195" size="125,20" font="{font};18" halign="left" text="Speichern" transparent="1" zPosition="1" />\n\t\t\t\t<eLabel position="365,195" size="125,20" font="{font};18" halign="left" text="Abbrechen" transparent="1" zPosition="1" />\n\t\t\t\t<ePixmap position="125,196" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/green.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<ePixmap position="340,196" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/buttons/red.png" alphatest="blend" zPosition="1" />\n\t\t\t\t<widget name="plugin" position="9,225" size="512,288" alphatest="blend" zPosition="1" />\n\t\t\t</screen>'

    def __init__(self, session):
        if config.plugins.chefkoch.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(chefkochConfig.skin, self.dict)
        Screen.__init__(self, session)
        self.password = config.plugins.chefkoch.password.value
        self['plugin'] = Pixmap()
        list = []
        list.append(getConfigListEntry('Plugin Gr\xc3\xb6\xc3\x9fe:', config.plugins.chefkoch.plugin_size))
        list.append(getConfigListEntry('Plugin Position:', config.plugins.chefkoch.position))
        list.append(getConfigListEntry('Plugin Schriftgr\xc3\xb6\xc3\x9fe:', config.plugins.chefkoch.font_size))
        list.append(getConfigListEntry('Plugin Sans Serif Schrift:', config.plugins.chefkoch.font))
        list.append(getConfigListEntry('Auto Update Check:', config.plugins.chefkoch.autoupdate))
        list.append(getConfigListEntry('Versende Rezepte per E-mail:', config.plugins.chefkoch.mail))
        list.append(getConfigListEntry('E-mail Absender:', config.plugins.chefkoch.mailfrom))
        list.append(getConfigListEntry('E-mail Empf\xc3\xa4nger:', config.plugins.chefkoch.mailto))
        list.append(getConfigListEntry('E-mail Login:', config.plugins.chefkoch.login))
        list.append(getConfigListEntry('E-mail Passwort:', config.plugins.chefkoch.password))
        list.append(getConfigListEntry('E-mail Server:', config.plugins.chefkoch.server))
        list.append(getConfigListEntry('E-mail Server Port:', config.plugins.chefkoch.port))
        list.append(getConfigListEntry('E-mail Server SSL:', config.plugins.chefkoch.ssl))
        list.append(getConfigListEntry('Full HD Skin Support:', config.plugins.chefkoch.fhd))
        list.append(getConfigListEntry('PayPal Info:', config.plugins.chefkoch.paypal))
        ConfigListScreen.__init__(self, list, on_change=self.UpdateComponents)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.save,
         'cancel': self.cancel,
         'red': self.cancel,
         'green': self.save}, -1)
        self.onLayoutFinish.append(self.UpdateComponents)

    def UpdateComponents(self):
        png = '/usr/lib/enigma2/python/Plugins/Extensions/Chefkoch/pic/setup/' + config.plugins.chefkoch.plugin_size.value + '.png'
        if fileExists(png):
            PNG = loadPic(png, 512, 288, 3, 0, 0, 0)
            if PNG != None:
                self['plugin'].instance.setPixmap(PNG)
        current = self['config'].getCurrent()
        if current == getConfigListEntry('PayPal Info:', config.plugins.chefkoch.paypal):
            import time
            from Screens.InputBox import PinInput
            self.pin = int(time.strftime('%d%m'))
            self.session.openWithCallback(self.returnPin, PinInput, pinList=[self.pin], triesEntry=config.ParentalControl.retries.servicepin)
        return

    def returnPin(self, pin):
        if pin:
            config.plugins.chefkoch.paypal.value = 'no'
            config.plugins.chefkoch.paypal.save()
            configfile.save()
        else:
            config.plugins.chefkoch.paypal.value = 'yes'
            config.plugins.chefkoch.paypal.save()

    def save(self):
        config.plugins.chefkoch.plugin_size.save()
        config.plugins.chefkoch.font_size.save()
        config.plugins.chefkoch.font.save()
        config.plugins.chefkoch.autoupdate.save()
        config.plugins.chefkoch.paypal.save()
        config.plugins.chefkoch.mail.save()
        config.plugins.chefkoch.mailfrom.save()
        config.plugins.chefkoch.mailto.save()
        config.plugins.chefkoch.login.save()
        if config.plugins.chefkoch.password.value != self.password:
            password = b64encode(str(config.plugins.chefkoch.password.value))
            config.plugins.chefkoch.password.value = password
            config.plugins.chefkoch.password.save()
        config.plugins.chefkoch.server.save()
        config.plugins.chefkoch.port.save()
        config.plugins.chefkoch.ssl.save()
        config.plugins.chefkoch.fhd.save()
        configfile.save()
        self.exit()

    def cancel(self):
        for x in self['config'].list:
            x[1].cancel()

        self.exit()

    def exit(self):
        self.session.openWithCallback(self.close, ChefkochMain)


def main(session, **kwargs):
    session.open(ChefkochMain)


def Plugins(**kwargs):
    return [PluginDescriptor(name='Chefkoch.de', description='Chefkoch.de Rezepte', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main), PluginDescriptor(name='Chefkoch.de', description='Chefkoch.de Rezepte', where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]
