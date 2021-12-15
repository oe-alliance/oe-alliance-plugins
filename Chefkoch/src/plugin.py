# -*- coding: utf-8 -*-
from base64 import b64encode, b64decode
from datetime import datetime
from json import loads
from operator import itemgetter
from os import linesep, rename, remove
from random import randrange
from re import match
from requests import get
from PIL import Image
from smtplib import SMTP, SMTP_SSL
from time import strftime
from twisted.web.client import getPage
from six import ensure_str, ensure_binary
from six.moves.email_mime_multipart import MIMEMultipart
from six.moves.email_mime_text import MIMEText
from six.moves.email_mime_image import MIMEImage
from enigma import addFont, eConsoleAppContainer, eListboxPythonMultiContent, eServiceReference, ePicLoad, eTimer, getDesktop, gFont, loadPNG, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigPassword, ConfigSelection, ConfigText, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean
from Components.ScrollLabel import ScrollLabel
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS

Release = 'V1.6'
config.plugins.chefkoch = ConfigSubsection()
Pluginpath = resolveFilename(SCOPE_PLUGINS) + 'Extensions/Chefkoch/'
deskWidth = getDesktop(0).size().width()
if deskWidth >= 1920:
    config.plugins.chefkoch.plugin_size = ConfigSelection(default='FHDclassic', choices=[(
        'FHDclassic', 'FullHD (1920x1080) klassisch'), ('FHDaltern', 'FullHD (1920x1080) alternativ'), ('HDclassic', 'HD (1280x720) klassisch')])
else:
    config.plugins.chefkoch.plugin_size = ConfigSelection(default='HDclassic', choices=[('HDclassic', 'HD (1280x720) klassisch')])
config.plugins.chefkoch.position = ConfigInteger(85, (0, 160))
config.plugins.chefkoch.font_size = ConfigSelection(default='large', choices=[('large', 'Groß'), ('normal', 'Normal')])
config.plugins.chefkoch.font = ConfigYesNo(default=True)
if config.plugins.chefkoch.font.value:
    addFont(Pluginpath + 'font/Sans.ttf', 'Sans', 100, False, 0)
config.plugins.chefkoch.maxrecipes = ConfigSelection(default='100', choices=['10', '20', '50', '100', '200', '500', '1000'])
config.plugins.chefkoch.maxcomments = ConfigSelection(default='100', choices=['10', '20', '50', '100', '200', '500'])
config.plugins.chefkoch.maxpictures = ConfigSelection(default='20', choices=['10', '20', '50', '100'])
config.plugins.chefkoch.mail = ConfigYesNo(default=False)
config.plugins.chefkoch.mailfrom = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.mailto = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.login = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.password = ConfigPassword(default='', fixed_size=False)
config.plugins.chefkoch.server = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.port = ConfigInteger(465, (0, 99999))
config.plugins.chefkoch.ssl = ConfigYesNo(default=True)
config.plugins.chefkoch.debuglog = ConfigYesNo(default=False)
config.plugins.chefkoch.logtofile = ConfigYesNo(default=False)


def applySkinVars(skin, dict):
    for key in dict.keys():
        skin = skin.replace('{' + key + '}', dict[key])
    return skin


picurlbase = 'https://img.chefkoch-cdn.de/rezepte'
apiuribase = 'https://api.chefkoch.de/v2'


def APIget(apiuri):
    f = get(apiuri)
    return(f.text, f.status_code)


def getAPIdata(apiuri):
    apiuri = apiuribase + apiuri
    content, resp = APIget(apiuri)
    if resp != 200:
        CKlog('request failure from', apiuri)
        CKlog('Serverrespose error#', resp)
    return(content, resp)


def CKlog(info, wert="", debug=False):
    if debug and not config.plugins.chefkoch.debuglog.value:
        return

    if config.plugins.chefkoch.logtofile.value:
        try:
            f = open('/home/root/logs/chefkoch.log', 'a')
            try:
                f.write(strftime('%H:%M:%S') + ' %s %s\r\n' % (str(info), str(wert)))
            finally:
                f.close()
        except IOError:
            print('[Chefkoch] Logging-Error')
    else:
        print('[Chefkoch] %s %s' % (str(info), str(wert)))


class ChefkochView(Screen):
    skinHD = '''
        <screen position="center,{position}" size="1240,640" title="lade Daten, bitte warten...">
            <ePixmap position="0,0" size="1240,60" pixmap="{picpath}chefkochHD.png" alphatest="blend" zPosition="1" />
            <widget name="menu" position="10,75" size="1085,540" scrollbarMode="showNever" zPosition="1" />
            <widget name="vid0" position="1095,75" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid1" position="1095,165" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid2" position="1095,255" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid3" position="1095,345" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid4" position="1095,435" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid5" position="1095,525" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="pic0" position="1095,75" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic1" position="1095,165" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic2" position="1095,255" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic3" position="1095,345" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic4" position="1095,435" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic5" position="1095,525" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="postpic" position="450,70" size="280,210" zPosition="1" />
            <widget name="postvid" position="520,125" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="score" position="10,70" size="236,36" alphatest="blend" zPosition="1" />
            <widget name="scoretext" position="10,105" size="440,165" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="recipetext" position="765,70" size="470,210" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="textpage" position="10,280" size="1220,365" font="{font};{fontsize}" halign="left" zPosition="0" />
            <widget name="slider_textpage" position="1214,280" size="22,360" pixmap="{picpath}slider/slider_360.png" alphatest="blend" zPosition="1" />
            <widget name="label1" position="270,8" size="640,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget name="label2" position="740,8" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label3" position="740,31" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label4" position="120,0" size="350,60" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" valign="center" transparent="1" zPosition="2" />
            <widget name="label5" position="300,8" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label6" position="300,31" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label7" position="270,31" size="640,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget render="Label" source="global.CurrentTime" position="1125,0" size="105,30" font="{font};26" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
                <convert type="ClockToText">Format:%H:%M:%S</convert>
            </widget>
            <widget name="release" position="1125,28" size="105,30" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="2" />
            <widget name="greenbutton" position="132,10" size="18,18" pixmap="{picpath}buttons/greenHD.png" alphatest="blend" zPosition="2" />
            <widget name="greenbutton2" position="274,10" size="18,18" pixmap="{picpath}buttons/greenHD.png" alphatest="blend" zPosition="2" />
            <widget name="yellowbutton" position="132,32" size="18,18" pixmap="{picpath}buttons/yellowHD.png" alphatest="blend" zPosition="2" />
            <widget name="yellowbutton2" position="274,32" size="18,18" pixmap="{picpath}buttons/yellowHD.png" alphatest="blend" zPosition="2" />
            <widget name="redbutton" position="1100,10" size="18,18" pixmap="{picpath}buttons/redHD.png" alphatest="blend" zPosition="2" />
            <widget name="bluebutton" position="1100,32" size="18,18" pixmap="{picpath}buttons/blueHD.png" alphatest="blend" zPosition="2" />
        </screen>'''
    skinFHD = '''
        <screen position="center,{position}" size="1860,960" title="lade Daten, bitte warten...">
            <ePixmap position="0,0" size="1860,90" pixmap="{picpath}chefkochFHD.png" alphatest="blend" zPosition="1" />
            <widget name="menu" position="15,112" size="1627,810" scrollbarMode="showNever" zPosition="1" />
            <widget name="vid0" position="1642,112" size="202,135" pixmap="{picpath}videoiconFHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid1" position="1642,247" size="202,135" pixmap="{picpath}videoiconFHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid2" position="1642,382" size="202,135" pixmap="{picpath}videoiconFHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid3" position="1642,517" size="202,135" pixmap="{picpath}videoiconFHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid4" position="1642,652" size="202,135" pixmap="{picpath}videoiconFHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid5" position="1642,787" size="202,135" pixmap="{picpath}videoiconFHD.png" alphatest="blend" zPosition="1" />
            <widget name="pic0" position="1642,112" size="202,135" alphatest="blend" zPosition="1" />
            <widget name="pic1" position="1642,247" size="202,135" alphatest="blend" zPosition="1" />
            <widget name="pic2" position="1642,382" size="202,135" alphatest="blend" zPosition="1" />
            <widget name="pic3" position="1642,517" size="202,135" alphatest="blend" zPosition="1" />
            <widget name="pic4" position="1642,652" size="202,135" alphatest="blend" zPosition="1" />
            <widget name="pic5" position="1642,787" size="202,135" alphatest="blend" zPosition="1" />
            <widget name="postpic" position="675,105" size="420,315" zPosition="1" />
            <widget name="postvid" position="780,187" size="202,135" pixmap="{picpath}videoiconFHD.png" alphatest="blend" zPosition="1" />
            <widget name="score" position="15,105" size="354,54" alphatest="blend" zPosition="1" />
            <widget name="scoretext" position="15,157" size="660,247" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="recipetext" position="1147,105" size="705,315" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="textpage" position="15,423" size="1830,547" font="{font};{fontsize}" halign="left" zPosition="0" />
            <widget name="slider_textpage" position="1821,420" size="33,540" pixmap="{picpath}slider/slider_360.png" alphatest="blend" zPosition="1" />
            <widget name="label1" position="405,12" size="960,33" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget name="label2" position="1110,12" size="525,33" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label3" position="1110,46" size="525,33" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label4" position="180,0" size="525,90" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" valign="center" transparent="1" zPosition="2" />
            <widget name="label5" position="456,12" size="525,33" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label6" position="456,46" size="525,33" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label7" position="405,46" size="960,33" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget render="Label" source="global.CurrentTime" position="1687,0" size="157,45" font="{font};39" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
                <convert type="ClockToText">Format:%H:%M:%S</convert>
            </widget>
            <widget name="release" position="1687,42" size="157,45" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="2" />
            <widget name="greenbutton" position="198,15" size="27,27" pixmap="{picpath}buttons/greenFHD.png" alphatest="blend" zPosition="2" />
            <widget name="greenbutton2" position="420,15" size="27,27" pixmap="{picpath}buttons/greenFHD.png" alphatest="blend" zPosition="2" />
            <widget name="yellowbutton" position="198,48" size="27,27" pixmap="{picpath}buttons/yellowFHD.png" alphatest="blend" zPosition="2" />
            <widget name="yellowbutton2" position="420,48" size="27,27" pixmap="{picpath}buttons/yellowFHD.png" alphatest="blend" zPosition="2" />
            <widget name="redbutton" position="1650,15" size="27,27" pixmap="{picpath}buttons/redFHD.png" alphatest="blend" zPosition="2" />
            <widget name="bluebutton" position="1650,48" size="27,27" pixmap="{picpath}buttons/blueFHD.png" alphatest="blend" zPosition="2" />
        </screen>'''
    skinALT = '''
        <screen position="center,{position}" size="1240,980" title="lade Daten, bitte warten...">
            <ePixmap position="0,0" size="1240,60" pixmap="{picpath}chefkochHD.png" alphatest="blend" zPosition="1" />
            <widget name="menu" position="10,75" size="1085,900" scrollbarMode="showNever" zPosition="2" />
            <widget name="vid0" position="1095,75" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid1" position="1095,165" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid2" position="1095,255" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid3" position="1095,345" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid4" position="1095,435" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid5" position="1095,525" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid6" position="1095,615" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid7" position="1095,705" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid8" position="1095,795" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="vid9" position="1095,885" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="pic0" position="1095,75" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic1" position="1095,165" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic2" position="1095,255" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic3" position="1095,345" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic4" position="1095,435" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic5" position="1095,525" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic6" position="1095,615" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic7" position="1095,705" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic8" position="1095,795" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="pic9" position="1095,885" size="135,90" alphatest="blend" zPosition="1" />
            <widget name="postpic" position="450,70" size="280,210" zPosition="1" />
            <widget name="postvid" position="520,125" size="135,90" pixmap="{picpath}videoiconHD.png" alphatest="blend" zPosition="1" />
            <widget name="score" position="10,70" size="236,36" alphatest="blend" zPosition="1" />
            <widget name="scoretext" position="10,105" size="440,165" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="recipetext" position="765,70" size="470,210" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="textpage" position="10,280" size="1220,705" font="{font};{fontsize}" halign="left" zPosition="0" />
            <widget name="slider_textpage" position="1214,280" size="22,700" pixmap="{picpath}slider/slider_700.png" alphatest="blend" zPosition="1" />
            <widget name="label1" position="270,8" size="640,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget name="label2" position="740,8" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label3" position="740,31" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label4" position="120,0" size="350,60" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" valign="center" transparent="1" zPosition="2" />
            <widget name="label5" position="300,8" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label6" position="300,31" size="350,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label7" position="270,31" size="640,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget render="Label" source="global.CurrentTime" position="1125,0" size="105,30" font="{font};26" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
                <convert type="ClockToText">Format:%H:%M:%S</convert>
            </widget>
            <widget name="release" position="1125,28" size="105,30" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="2" />
            <widget name="greenbutton" position="132,10" size="18,18" pixmap="{picpath}buttons/greenHD.png" alphatest="blend" zPosition="2" />
            <widget name="greenbutton2" position="274,10" size="18,18" pixmap="{picpath}buttons/greenHD.png" alphatest="blend" zPosition="2" />
            <widget name="yellowbutton" position="132,32" size="18,18" pixmap="{picpath}buttons/yellowHD.png" alphatest="blend" zPosition="2" />
            <widget name="yellowbutton2" position="274,32" size="18,18" pixmap="{picpath}buttons/yellowHD.png" alphatest="blend" zPosition="2" />
            <widget name="redbutton" position="1100,10" size="18,18" pixmap="{picpath}buttons/redHD.png" alphatest="blend" zPosition="2" />
            <widget name="bluebutton" position="1100,32" size="18,18" pixmap="{picpath}buttons/blueHD.png" alphatest="blend" zPosition="2" />
        </screen>'''

    def __init__(self, session, query, titel, sort, fav, zufall):
        self.session = session
        self.query = query
        self.titel = titel
        self.sort = sort
        self.fav = fav
        self.zufall = zufall
        self.sortname = ['{keine}', 'Anzahl Bewertungen', 'Anzahl Sterne', 'mit Video', 'Datum']
        self.orgGRP = []
        self.picfile = '/tmp/chefkoch.jpg'
        font = 'Sans' if config.plugins.chefkoch.font.value else 'Regular'
        position = str(config.plugins.chefkoch.position.value)
        if config.plugins.chefkoch.font_size.value == 'large':
            self.fontlarge = True
            fontsize = '%d' % int(22 * scale)
        else:
            self.fontlarge = False
            fontsize = '%d' % int(20 * scale)
        self.dict = {'position': position, 'picpath': Pluginpath + 'pic/', 'font': font, 'fontsize': fontsize}
        if config.plugins.chefkoch.plugin_size.value == 'FHDclassic':
            self.skin = applySkinVars(ChefkochView.skinFHD, self.dict)
        elif config.plugins.chefkoch.plugin_size.value == 'FHDaltern':
            self.skin = applySkinVars(ChefkochView.skinALT, self.dict)
        else:
            self.skin = applySkinVars(ChefkochView.skinHD, self.dict)
        Screen.__init__(self, session)
        self.currItem = 0
        self.rezeptfile = '/tmp/Rezept.html'
        self.hideflag = True
        self.ready = False
        self.postviewready = False
        self.comment = False
        self.len = 0
        self.count = 0
        self.maxPage = 0
        self.current = 'menu'
        self.name = ''
        self.seitenlabel = ''
        self.chefvideo = ''
        self.kochentries = []
        self.kochId = []
        self.picurllist = []
        self.titellist = []
        self.videolist = []
        self.rezeptelist = []
        self.rezeptelinks = []
        for i in range(linesPerPage):
            self['pic%d' % i] = Pixmap()
            self['vid%d' % i] = Pixmap()
            self['pic%d' % i].hide
            self['vid%d' % i].hide()
        self['postpic'] = Pixmap()
        self['postvid'] = Pixmap()
        self['score'] = Pixmap()
        self['scoretext'] = Label('')
        self['scoretext'].hide()
        self['recipetext'] = Label('')
        self['recipetext'].hide()
        self['greenbutton'] = Pixmap()
        self['greenbutton2'] = Pixmap()
        self['redbutton'] = Pixmap()
        self['yellowbutton'] = Pixmap()
        self['yellowbutton2'] = Pixmap()
        self['bluebutton'] = Pixmap()
        self['textpage'] = ScrollLabel('')
        self['slider_textpage'] = Pixmap()
        self['slider_textpage'].hide()
        self['menu'] = ItemList([])
        self['greenbutton'].hide()
        self['greenbutton2'].hide()
        self['yellowbutton'].hide()
        self['yellowbutton2'].hide()
        self['redbutton'].hide()
        self['bluebutton'].hide()
        self['label1'] = Label('')
        self['label2'] = Label('')
        self['label3'] = Label('')
        self['label4'] = Label('')
        self['label5'] = Label('')
        self['label6'] = Label('')
        self['label7'] = Label('')
        self['release'] = Label(Release)
        self['helpactions'] = ActionMap(['HelpActions'], {'displayHelp': self.infoScreen}, -1)
        self['NumberActions'] = NumberActionMap(['NumberActions', 'OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'ButtonSetupActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'play': self.playVideo,
            'playpause': self.playVideo,
            'right': self.nextPage,
            'left': self.prevPage,
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
        }, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)  # warte bis __Init__ abgeschlossen ist
        self.postpicload = ePicLoad()
        self.prevpicload = []
        for i in range(linesPerPage):
            self.prevpicload.append(ePicLoad())

    def onLayoutFinished(self):
        self.postpicload.setPara((self['postpic'].instance.size().width(), self['postpic'].instance.size().height(), 1.0, 0, False, 1, "#00000000"))
        xres = self['pic0'].instance.size().width()
        yres = self['pic0'].instance.size().height()
        for i in range(linesPerPage):
            self.prevpicload[i].setPara((xres, yres, 1.0, 0, False, 1, "#00000000"))
        self.makeChefkochTimer = eTimer()
        if self.zufall:
            self.current = 'postview'
            self.getGRP()
            zufallsId = self.GRP[randrange(0, len(self.GRP))]['id']
            self.makeChefkochTimer.callback.append(self.makePostviewPage(zufallsId))
        elif self.fav:
            self.current = 'postview'
            self.makeChefkochTimer.callback.append(self.makePostviewPage(self.query))
        else:
            self.current = 'menu'
            self.makeChefkochTimer.callback.append(self.makeChefkoch)
        self.makeChefkochTimer.start(500, True)

    def makeChefkoch(self):  # erzeuge Rezeptliste
        for i in range(linesPerPage):
            self['pic%d' % i].hide()
            self['vid%d' % i].hide()
        self.getGRP()
        self.kochentries = []
        self.kochId = []
        self.picurllist = []
        self.titellist = []
        self.videolist = []
        self.pic = []
        for i in range(linesPerPage):
            self.pic.append('/tmp/chefkoch%d.jpg' % i)
        self['postvid'].hide()
        self['greenbutton'].hide()
        self['greenbutton2'].show()
        self['yellowbutton'].hide()
        self['yellowbutton2'].show()
        self['redbutton'].show()
        self['bluebutton'].show()
        self['label1'].setText('')
        self['label2'].setText('Rezept zu Favoriten hinzufügen =')
        self['label3'].setText('Ein-/Ausblenden =')
        self.seitenlabel = 'Rezept Nr. ' + str(self.currItem + 1) + '\nSeite ' + str(int(self.currItem // linesPerPage + 1)) + ' von ' + str(self.maxPage)
        self['label4'].setText(self.seitenlabel)
        self['label5'].setText('= Sortierung: %s' % self.sortname[self.sort])
        self['label6'].setText('= Suche')
        self.headline = str(len(self.GRP)) + ' "' + self.titel.replace(' Rezepte', '') + '" Rezepte ('
        self.headline += '1 Video)' if self.videocount == 1 else str(self.videocount) + ' Videos)'
        self.setTitle(str(self.headline))
        for i in range(len(self.GRP)):
            id = str(self.GRP[i]['id'])
            titel = self.GRP[i]['title']
            time = str(self.GRP[i]['preparationTime'])
            if self.GRP[i]['numVotes']:
                count = str(self.GRP[i]['numVotes'])
                score = str(round(self.GRP[i]['rating'] / 5, 1) * 5).replace('.', '_').replace('_0', '')
            else:
                count = 'keine'
                score = '0'
            if self.GRP[i]['previewImageId']:
                picurl = picurlbase + '/' + id + '/bilder/' + str(self.GRP[i]['previewImageId']) + '/crop-160x120/' + titel.replace(' ', '-') + '.jpg'
            else:
                picurl = 'http://img.chefkoch-cdn.de/img/default/layout/recipe-nopicture.jpg'
            text = self.GRP[i]['subtitle']
            if len(text) > 155:
                text = text[:155] + '...'
            self.kochId.append(id)
            self.picurllist.append(picurl)
            self.titellist.append(titel)
            self.videolist.append(self.GRP[i]['hasVideo'])
            res = [i]
            res.append(MultiContentEntryText(pos=(int(110 * scale), 0), size=(int(965 * scale), int(30 * scale)), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titel))  # TITLE
            png = Pluginpath + 'pic/logos/suche-score-%sHD.png' % score
            if fileExists(png):
                res.append(MultiContentEntryPixmapAlphaTest(pos=(int(12 * scale), int(33 * scale)), size=(int(72 * scale), int(14 * scale)), png=loadPNG(png)))  # SCORE
            res.append(MultiContentEntryText(pos=(0, int(52 * scale)), size=(int(95 * scale), int(25 * scale)), font=-
                       1, color=16777215, color_sel=16777215, flags=RT_HALIGN_CENTER, text='(' + count + ')'))  # COUNT
            res.append(MultiContentEntryText(pos=(int(111 * scale), int(30 * scale)), size=(int(965 * scale), int(60 * scale)),
                       font=-1, color=10857646, color_sel=13817818, flags=RT_HALIGN_LEFT | RT_WRAP, text=text))  # TEXT
            res.append(MultiContentEntryText(pos=(0, 0), size=(int(95 * scale), int(30 * scale)), font=-1, backcolor=12255304,
                       color=16777215, backcolor_sel=12255304, color_sel=16777215, flags=RT_HALIGN_CENTER, text=time))  # TIME
            self.kochentries.append(res)

        self.setPrevIcons(0)
        self.len = len(self.kochentries)
        self['menu'].l.setItemHeight(int(90 * scale))
        self['menu'].l.setList(self.kochentries)
        self['menu'].moveToIndex(0)
        self.ready = True

    def formatDatum(self, date):
        return str(datetime.strptime(date[:10], '%Y-%m-%d').strftime('%d.%m.%Y'))

    def formatDatumZeit(self, date):
        datum = datetime.strptime(date[:10], '%Y-%m-%d').strftime('%d.%m.%Y')
        zeit = datetime.strptime(date[11:19], '%H:%M:%S').strftime('%H:%M')
        return 'vom ' + str(datum) + ' um ' + str(zeit)

    def formatUsername(self, username, rank, trim):
        return 'Unbekannt' if "unknown" in username else (str(username) + ' (' + str(rank) + '*)')[:trim if trim > 0 else 100]

    def makePostviewPage(self, Id):  # erzeuge Rezept
        effort = ['keiner', 'simpel', 'normal', 'pfiffig']
        for i in range(linesPerPage):
            self['pic%d' % i].hide()
            self['vid%d' % i].hide()
        self.currId = Id
        self.KOM = []
        self.REZ = self.getREZ(self.currId)
        self.IMG = self.getIMG(self.currId)
        self.KOM = self.getKOM(self.currId)
        self.rezept = 'https://www.chefkoch.de/rezepte/'
        self['menu'].hide()
        self['greenbutton'].show()
        self['greenbutton2'].hide()
        self['yellowbutton'].hide()
        self['yellowbutton2'].hide()
        self['redbutton'].show()
        self['bluebutton'].show()
        self['label2'].setText('Rezept zu Favoriten hinzufügen =')
        self['label3'].setText('Ein-/Ausblenden =')
        self['label4'].setText('')
        self['label5'].setText('')
        self['label6'].setText('')
        self['textpage'].show()
        self.picCount = self.REZ['imageCount']
        self.setTitle(str(self.REZ['title']))
        if self.picCount == 0:
            self['label7'].setText('')
        elif self.picCount > 1:
            self['label7'].setText('OK = zeige %d Rezeptbilder' % (self.IMGlen))
        else:
            self['label7'].setText('OK = Vollbild')
        if self.REZ['rating']:
            score = str(round(self.REZ['rating']['rating'] / 5, 1) * 5).replace('.', '_').replace('_0', '')
            scoretext = str('%1.1f' % self.REZ['rating']['rating']) + ' (' + str(self.REZ['rating']['numVotes']) + ' Bewertungen)'
        else:
            score = '0'
            scoretext = '(ohne Bewertung)'
        preptime = self.REZ['preparationTime']
        cooktime = self.REZ['cookingTime']
        resttime = self.REZ['restingTime']
        totaltime = self.REZ['totalTime']
        if preptime != 0:
            scoretext += '\nArbeitszeit\t: ' + self.getTimeString(preptime)
        if cooktime != 0:
            scoretext += '\nKoch-/Backzeit\t: ' + self.getTimeString(cooktime)
        if resttime != 0:
            scoretext += '\nRuhezeit\t: ' + self.getTimeString(resttime)
        if totaltime != 0:
            scoretext += '\nGesamtzeit\t: ' + self.getTimeString(totaltime)
        pictype = 'FHD.png' if config.plugins.chefkoch.plugin_size.value == 'FHDclassic' else 'HD.png'
        scorepng = Pluginpath + 'pic/logos/score-' + score + pictype
        if fileExists(scorepng):
            self.showScore(scorepng)
            self['score'].show()
        self['scoretext'].setText(scoretext)
        self['scoretext'].show()
        recipetext = 'Rezept-Identnr.\t: ' + str(self.currId)
        recipetext += '\nAufwand\t: ' + effort[self.REZ['difficulty']]
        recipetext += '\nErstellername\t: ' + self.formatUsername(self.REZ['owner']['username'], self.REZ['owner']['rank'], 22)
        recipetext += '\nErstelldatum\t: ' + self.formatDatum(self.REZ['createdAt'])
        if self.REZ['nutrition']:
            kcalori = self.REZ['nutrition']['kCalories']
            if kcalori:
                kcalori = str(kcalori)
            else:
                kcalori = 'k.A.'
            protein = self.REZ['nutrition']['proteinContent']
            if protein:
                protein = str(protein) + ' g'
            else:
                protein = 'k.A.'
            fatcont = self.REZ['nutrition']['fatContent']
            if fatcont:
                fatcont = str(fatcont) + ' g'
            else:
                fatcont = 'k.A.'
            carbohyd = self.REZ['nutrition']['carbohydrateContent']
            if carbohyd:
                carbohyd = str(carbohyd) + ' g'
            else:
                carbohyd = 'k.A.'
            recipetext += '\n\n{0:13}{1:13}{2:14}{3}'.format('kcal', 'Eiweiß', 'Fett', 'Kohlenhydr.')
            recipetext += '\n{0:13}{1:13}{2:12}{3}'.format(kcalori, protein, fatcont, carbohyd)
        self['recipetext'].setText(str(recipetext))
        self['recipetext'].show()
        if self.REZ['hasImage']:
            picurl = picurlbase + '/' + self.currId + '/bilder/' + self.REZ['previewImageId'] + '/crop-960x720/' + self.titel + '.jpg'
        else:
            picurl = 'https://img.chefkoch-cdn.de/img/default/layout/recipe-nopicture.jpg'
        self.Pdownload(picurl, self.getPostPic)
        self.postpicload.PictureData.get().append(self.showPostPic)
        self['postpic'].show()
        self.makeRezept()
        self.postviewready = True

    def getREZ(self, id):  # hole den jeweiligen Rezeptdatensatz
        content, resp = getAPIdata('/recipes/' + id)
        if resp != 200:
            return resp
        result = loads(content)
        return result

    def getIMG(self, id):  # hole die jeweilige Rezeptbilderliste
        content, resp = getAPIdata('/recipes/' + id + '/images?&offset=0&limit=' + config.plugins.chefkoch.maxpictures.value)
        if resp != 200:
            return resp
        result = loads(content)
        self.IMGlen = int(config.plugins.chefkoch.maxpictures.value) if result['count'] > int(config.plugins.chefkoch.maxpictures.value) else result['count']
        dict = {}
        dict['count'] = self.IMGlen
        dict['results'] = result['results']
        return dict

    def getKOM(self, id):  # hole die jeweilige Rezeptkommentarliste
        if not self.KOM:
            content, resp = getAPIdata('/recipes/' + id + '/comments?&offset=0&limit=' + config.plugins.chefkoch.maxcomments.value)
            if resp != 200:
                return resp
            result = loads(content)
        else:
            result = self.KOM
        self.KOMlen = int(config.plugins.chefkoch.maxcomments.value) if result['count'] > int(config.plugins.chefkoch.maxcomments.value) else result['count']
        return result

    def getGRP(self):  # hole die gewünschte Rezeptgruppe (alle Rezepte oder nur Videos)
        if not self.orgGRP:
            limit = int(config.plugins.chefkoch.maxrecipes.value)
            videocount = 0
            for i in range(max((limit) // 100, 1)):
                content, resp = getAPIdata('/recipes?query=%s&offset=%d&limit=%d' % (self.query, i * 100, min(limit, 100)))
                if resp == 200:
                    result = loads(content)
                else:
                    return resp
                for j in range(len(result['results'])):
                    dict = {}
                    dict['id'] = result['results'][j]['recipe']['id']
                    dict['createdAt'] = result['results'][j]['recipe']['createdAt']
                    dict['preparationTime'] = result['results'][j]['recipe']['preparationTime']
                    if result['results'][j]['recipe']['rating'] != None:
                        dict['rating'] = result['results'][j]['recipe']['rating']['rating']
                        dict['numVotes'] = result['results'][j]['recipe']['rating']['numVotes']
                    else:
                        dict['rating'] = 0
                        dict['numVotes'] = False
                    if result['results'][j]['recipe']['hasImage']:
                        dict['previewImageId'] = result['results'][j]['recipe']['previewImageId']
                    else:
                        dict['previewImageId'] = False
                    dict['hasVideo'] = result['results'][j]['recipe']['hasVideo']
                    titel = str(result['results'][j]['recipe']['title'])
                    dict['title'] = titel
                    dict['subtitle'] = str(result['results'][j]['recipe']['subtitle'])
                    if result['results'][j]['recipe']['hasVideo']:
                        videocount += 1
                    self.orgGRP.append(dict)
            self.videocount = videocount
        if self.sort == 0:
            self.GRP = self.orgGRP
        elif self.sort == 1:
            self.GRP = sorted(self.orgGRP, key=itemgetter('numVotes'), reverse=True)
        elif self.sort == 2:
            self.GRP = sorted(self.orgGRP, key=itemgetter('rating'), reverse=True)
        elif self.sort == 3:
            self.GRP = sorted(self.orgGRP, key=itemgetter('hasVideo', 'numVotes'), reverse=True)
        elif self.sort == 4:
            self.GRP = sorted(self.orgGRP, key=itemgetter('createdAt'), reverse=True)
        self.maxPage = (len(self.GRP) - 1) // linesPerPage + 1

    def getTimeString(self, duration):
        days = duration // 1440
        hours = duration // 60
        minutes = duration % 60
        if days == 0:
            daytext = ''
            hourtext = 'ca. ' + str(hours) + ' h ' if hours != 0 else ''
            minutetext = str(minutes) + ' min' if minutes != 0 else ''
        else:
            daytext = str(days) + ' Tage' if days > 1 else '1 Tag'
            hourtext = ''
            minutetext = ''
        ausgabe = daytext + hourtext + minutetext
        return ausgabe

    def ok(self):
        if self.hideflag:
            if self.current == 'menu':
                self.selectPage()
            elif self.current == 'postview' and self.postviewready:
                if self.picCount == 1:
                    self.session.openWithCallback(self.showPostPic, FullScreen)
                if self.picCount > 1:
                    self.session.openWithCallback(self.returnPicShow, ChefkochPicShow, self.titel, self.REZ, self.IMG)

    def selectPage(self):
        if self.ready:
            self.current = 'postview'
            self.currItem = self['menu'].getSelectedIndex()
            self.makePostviewPage(self.kochId[self.currItem])

    def red(self):
        if self.ready or self.postviewready:
            if not self.zufall:
                self.currItem = self['menu'].getSelectedIndex()
                name = self.titellist[self.currItem]
            else:
                name = self.name
            self.session.openWithCallback(self.red_return, MessageBox, "\nRezept '%s' zu den Favoriten hinzufügen?" % name, MessageBox.TYPE_YESNO)

    def red_return(self, answer):
        if answer is True:
            favoriten = Pluginpath + 'db/favoriten'
            if not self.zufall:
                self.currItem = self['menu'].getSelectedIndex()
                data = self.titellist[self.currItem] + ':::' + self.kochId[self.currItem]
            else:
                data = self.name + ':::' + self.kochId[self.currItem]
            f = open(favoriten, 'a')
            f.write(data)
            f.write(linesep)
            f.close()
            self.session.open(chefkochFav)

    def green(self):
        if self.current == 'postview' and self.postviewready:
            if config.plugins.chefkoch.mail.value:
                mailto = config.plugins.chefkoch.mailto.value.split(",")
                mailto = [(i.strip(),) for i in mailto]
                self.session.openWithCallback(self.green_return, ChoiceBox, title='Rezept an folgende E-mail Adresse senden:', list=mailto)
            else:
                self.session.open(MessageBox, '\nDie E-mail Funktion ist nicht aktiviert. Aktivieren Sie die E-mail Funktion im Setup des Plugins.', MessageBox.TYPE_INFO, close_on_any_key=True)
        if self.current == 'menu':
            self.sort = self.sort + 1 if self.sort < len(self.sortname) - 1 else 0
            self.currItem = 0
            self.makeChefkoch()

    def green_return(self, answer):
        if answer:
            self.sendRezept(answer[0])

    def sendRezept(self, mailTo):
        effort = ['keine', 'simpel', 'normal', 'pfiffig']
        msgText = '\n'
        msgText = '<p>Linkadresse: <a href="' + self.rezept + self.currId + '">' + self.rezept + self.currId + '</a></p>'
        if self.REZ['rating']:
            score = str(round(self.REZ['rating']['rating'] / 5, 1) * 5).replace('.', '_').replace('_0', '')
            scoretext = str('%1.1f' % self.REZ['rating']['rating']) + ' (' + str(self.REZ['rating']['numVotes']) + ' Bewertungen)'
        else:
            score = '0'
            scoretext = '(ohne Bewertung)'
        preptime = self.REZ['preparationTime']
        cooktime = self.REZ['cookingTime']
        resttime = self.REZ['restingTime']
        totaltime = self.REZ['totalTime']
        if preptime != 0:
            scoretext += '\nArbeitszeit   : ' + self.getTimeString(preptime)
        if cooktime != 0:
            scoretext += '\nKoch-/Backzeit: ' + self.getTimeString(cooktime)
        if resttime != 0:
            scoretext += '\nRuhezeit      : ' + self.getTimeString(resttime)
        if totaltime != 0:
            scoretext += '\nGesamtzeit    : ' + self.getTimeString(totaltime)
        msgText += scoretext
#        pictype = 'FHD.png' if config.plugins.chefkoch.plugin_size.value == 'FHDclassic' else 'HD.png'
#        scorepng = Pluginpath + 'pic/logos/score-' + score + pictype
#        if fileExists(scorepng):
#           Hier kann man noch die Bewertungssternchen mit reinnehmen
        recipetext = '\n\nRezept-Identnr.: ' + str(self.currId)
        recipetext += '\nAufwand: ' + effort[self.REZ['difficulty']]
        recipetext += '\nErstellername: ' + self.formatUsername(self.REZ['owner']['username'], self.REZ['owner']['rank'], 22)
        recipetext += '\nErstelldatum: ' + self.formatDatum(self.REZ['createdAt'])
        if self.REZ['nutrition']:
            kcalori = self.REZ['nutrition']['kCalories']
            if kcalori:
                kcalori = str(kcalori)
            else:
                kcalori = 'k.A.'
            protein = self.REZ['nutrition']['proteinContent']
            if protein:
                protein = str(protein) + 'g'
            else:
                protein = 'k.A.'
            fatcont = self.REZ['nutrition']['fatContent']
            if fatcont:
                fatcont = str(fatcont) + 'g'
            else:
                fatcont = 'k.A.'
            carbohyd = self.REZ['nutrition']['carbohydrateContent']
            if carbohyd:
                carbohyd = str(carbohyd) + 'g'
            else:
                carbohyd = 'k.A.'
            recipetext += '\n\nkcal  Eiweiß  Fett  Kohlenhydr.'
            recipetext += '\n' + str(kcalori) + ' ' + str(protein) + ' ' + str(fatcont) + ' ' + str(carbohyd)
        msgText += recipetext + '\n\n'
        if self.REZ['subtitle']:
            msgText += 'BESCHREIBUNG: ' + self.REZ['subtitle'] + '\n\n'
        msgText += 'ZUTATEN\n'
        for i in range(len(self.REZ['ingredientGroups'])):
            for j in range(len(self.REZ['ingredientGroups'][i]['ingredients'])):
                if not (i == 0 and j == 0):
                    msgText += '; '
                if self.REZ['ingredientGroups'][i]['ingredients'][j]['amount'] != 0:
                    msgText += str(self.REZ['ingredientGroups'][i]['ingredients'][j]['amount']).replace('.0', '') + ' '
                    msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['unit'] + ' '
                msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['name']
                msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['usageInfo']
        msgText += '\n\nZUBEREITUNG\n' + self.REZ['instructions']
        msgText += '\n' + '_' * 30 + '\nChefkoch.de'
        Image.open('/tmp/chefkoch.jpg').resize((320, 240), Image.ANTIALIAS).save('/tmp/emailpic.jpg')

        mailFrom = ensure_str(config.plugins.chefkoch.mailfrom.value.encode('ascii', 'xmlcharrefreplace'))
        mailTo = ensure_str(mailTo.encode('ascii', 'xmlcharrefreplace'))
        mailLogin = ensure_str(config.plugins.chefkoch.login.value.encode('ascii', 'xmlcharrefreplace'))
        mailPassword = ensure_str(b64decode(config.plugins.chefkoch.password.value.encode('ascii', 'xmlcharrefreplace')))
        mailServer = ensure_str(config.plugins.chefkoch.server.value.encode('ascii', 'xmlcharrefreplace'))
        mailPort = config.plugins.chefkoch.port.value

        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = 'Chefkoch.de: %s' % self.titel
        msgRoot['From'] = mailFrom
        msgRoot['To'] = mailTo  # bei Bedarf ergänzbar: msgRoot['Cc'] =cc
        msgRoot.preamble = 'Multi-part message in MIME format.'
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        msgAlternative.attach(MIMEText(msgText, _subtype='plain', _charset='UTF-8'))
        msgHeader = '"' + self.titel + '" gesendet vom Plugin "Chefkoch.de"'
        msgText = ensure_str(msgText.replace('\n', '<br>').encode('ascii', 'xmlcharrefreplace'))
        msgAlternative.attach(MIMEText('<b>' + msgHeader + '</b><br><br><img src="cid:0"><br>' + msgText, 'html'))
        with open('/tmp/emailpic.jpg', 'rb') as img:
            msgImage = MIMEImage(img.read(), _subtype="jpeg")
        msgImage.add_header('Content-ID', '<0>')
        msgRoot.attach(msgImage)
        try:
            if config.plugins.chefkoch.ssl.value:
                server = SMTP_SSL(mailServer, mailPort)
            else:
                server = SMTP(mailServer, mailPort)
            server.login(mailLogin, mailPassword)
            server.sendmail(mailFrom, mailTo, msgRoot.as_string())
            server.quit()
            self.session.open(MessageBox, 'E-mail erfolgreich gesendet an: %s' % str(mailTo), MessageBox.TYPE_INFO, close_on_any_key=True)
        except Exception as e:
            self.session.open(MessageBox, 'E-mail kann nicht gesendet werden: %s' % str(e), MessageBox.TYPE_INFO, close_on_any_key=True)

    def nextPage(self):
        if self.current == 'menu':
            self.currItem = self['menu'].getSelectedIndex()
            offset = self.currItem % linesPerPage
            if self.currItem + linesPerPage > self.len - 1:
                if offset > (self.len - 1) % linesPerPage:
                    self.currItem = self.len - 1
                    self['menu'].moveToIndex(self.currItem)  # springe auf letzten Eintrag der letzten Seite
                    self.setPrevIcons(self.currItem - offset)
                else:
                    self.currItem = offset
                    self['menu'].moveToIndex(self.currItem)  # springe auf gleichen Offset der ersten Seite
                    self.setPrevIcons(0)
            else:
                self.currItem = self.currItem + linesPerPage
                self['menu'].pageDown()
                self.setPrevIcons(self.currItem - offset)
            self.seitenlabel = 'Rezept Nr. ' + str(self.currItem + 1) + '\nSeite ' + str(int(self.currItem // linesPerPage + 1)) + ' von ' + str(self.maxPage)
            self['label4'].setText(self.seitenlabel)
        else:
            self['textpage'].pageDown()

    def prevPage(self):
        if self.current == 'menu':
            self.currItem = self['menu'].getSelectedIndex()
            offset = self.currItem % linesPerPage
            lasttop = (self.len - 1) // linesPerPage * linesPerPage
            if self.currItem - linesPerPage < 0:
                if offset > (self.len - 1) % linesPerPage:
                    self.currItem = self.len - 1
                    self['menu'].moveToIndex(self.currItem)  # springe auf gleichen Offset der vorherigen Seite
                else:
                    self.currItem = lasttop + offset
                    self['menu'].moveToIndex(self.currItem)  # springe auf letzten Eintrag der letzten Seite
                self.setPrevIcons(lasttop)
            else:
                self.currItem = self.currItem - linesPerPage
                self['menu'].pageUp()
                self.setPrevIcons(self.currItem - offset)
            self.seitenlabel = 'Rezept Nr. ' + str(self.currItem + 1) + '\nSeite ' + str(int(self.currItem // linesPerPage + 1)) + ' von ' + str(self.maxPage)
            self['label4'].setText(self.seitenlabel)
        else:
            self['textpage'].pageUp()

    def down(self):
        if self.current == 'menu':
            self['menu'].down()
            self.currItem = self['menu'].getSelectedIndex()
            self.seitenlabel = 'Rezept Nr. ' + str(self.currItem + 1) + '\nSeite ' + str(int(self.currItem // linesPerPage + 1)) + ' von ' + str(self.maxPage)
            self['label4'].setText('%s' % self.seitenlabel)
            if self.currItem == self.len:  # neue Vorschaubilder der ersten Seite anzeigen
                self.setPrevIcons(0)
            if self.currItem % linesPerPage == 0:  # neue Vorschaubilder der nächsten Seite anzeigen
                self.setPrevIcons(self.currItem)
        else:
            self['textpage'].pageDown()

    def up(self):
        if self.current == 'menu':
            self['menu'].up()
            self.currItem = self['menu'].getSelectedIndex()
            self.seitenlabel = 'Rezept Nr. ' + str(self.currItem + 1) + '\nSeite ' + str(int(self.currItem // linesPerPage + 1)) + ' von ' + str(self.maxPage)
            self['label4'].setText('%s' % self.seitenlabel)
            if self.currItem == self.len - 1:  # neue Vorschaubilder der letzte Seite anzeigen
                d = self.len % linesPerPage if self.len % linesPerPage != 0 else linesPerPage
                self.setPrevIcons(self.len - d)
            if self.currItem % linesPerPage == linesPerPage - 1:  # neue Vorschaubilder der vorherige Seite anzeigen
                self.setPrevIcons(self.currItem // linesPerPage * linesPerPage)
        else:
            self['textpage'].pageUp()

    def gotoPage(self, number):
        if self.current != 'postview' and self.ready:
            self.session.openWithCallback(self.numberEntered, getNumber, number, 5)
        elif self.current == 'postview':
            if number == 0:
                self['textpage'].lastPage()
            elif number == 1:
                if self.comment:
                    self.makeKommentar()
                else:
                    self.makeRezept()

    def numberEntered(self, number):
        if number and number != 0:
            count = int(number)
            if count > self.maxPage:
                count = self.maxPage
                self.session.open(MessageBox, '\nNur %s Seiten verfügbar. Gehe zu Seite %s.' % (str(count), str(count)), MessageBox.TYPE_INFO, close_on_any_key=True)
            self.currItem = (count - 1) * linesPerPage
            self['menu'].moveToIndex(self.currItem)
            self.setPrevIcons(self.currItem)
            self.seitenlabel = 'Rezept Nr. ' + str(self.currItem + 1) + '\nSeite ' + str(int(self.currItem // linesPerPage + 1)) + ' von ' + str(self.maxPage)
            self['label4'].setText(self.seitenlabel)

    def setPrevIcons(self, toppos):
        for i in range(linesPerPage):
            if len(self.picurllist) > toppos + i:
                self.prevpicload[i].PictureData.get().append(self.showPrevPic)
                self.Idownload(i, self.picurllist[toppos + i], self.getPrevPic)
                self['pic%d' % i].show()
                if self.videolist[toppos + i]:
                    self['vid%d' % i].show()
                else:
                    self['vid%d' % i].hide()
            else:
                self['pic%d' % i].hide()
                self['vid%d' % i].hide()

    def yellow(self):
        if self.current == 'menu':
            self.currItem = self['menu'].getSelectedIndex()
            self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Chefkoch - Suche Rezepte:', text='')
        elif self.current == 'postview' and self.postviewready:
            if self.KOMlen > 0:
                if self.comment:
                    self.comment = False
                    self.makeRezept()
                else:
                    self.comment = True
                    self.makeKommentar()

    def searchReturn(self, search):
        if search and search != '':
            self.session.open(ChefkochView, search, 'mit "' + search + '" gefundene Rezepte', 0, False, False)

    def makeKommentar(self):
        self.postviewready = False
        self['label1'].setText('1/0 = Erster/Letzer Kommentar')
        self.seitenlabel = '        = Rezept per E-mail senden\n'
        self.seitenlabel += '        = Rezeptbeschreibung einblenden'
        self['label4'].setText(self.seitenlabel)
        self['textpage'].setText('')
        text = ''
        for i in range(self.KOMlen):
            text += '\nKommentar %s/%s' % (i + 1, self.KOMlen) + ' von '
            text += self.formatUsername(self.KOM['results'][i]['owner']['username'], self.KOM['results'][i]['owner']['rank'], 0)
            text += ' ' + self.formatDatumZeit(self.KOM['results'][i]['createdAt']) + ' Uhr\n'
            text += self.KOM['results'][i]['text']
            if config.plugins.chefkoch.plugin_size.value == 'FHDclassic':
                if config.plugins.chefkoch.font.value:
                    repeat = 128 if self.fontlarge else 148
                else:
                    repeat = 128 if self.fontlarge else 136
            else:
                if config.plugins.chefkoch.font.value:
                    repeat = 132 if self.fontlarge else 148
                else:
                    repeat = 132
            text += '\n' + '_' * repeat
        text += '\nChefkoch.de'
        self['textpage'].setText(str(text))
        self.postviewready = True

    def makeRezept(self):  # bereite die eigentliche Rezeptseite vor
        self.postviewready = False
        self.seitenlabel = '        = Rezept per E-mail senden\n'
        if self.KOMlen > 0:
            self['yellowbutton'].show()
            self.seitenlabel += '        = ' + str(self.KOMlen) + ' Kommentare einblenden'
        else:
            self['yellowbutton'].hide()
        self['label4'].setText(self.seitenlabel)
        self['textpage'].setText('')
        if self.REZ['hasVideo']:
            self['postvid'].show()
            self['label1'].setText('PLAY = Video abspielen')
        else:
            self['postvid'].hide()
            self['label1'].setText('')
        text = ''
        if self.REZ['subtitle']:
            text += 'BESCHREIBUNG: ' + self.REZ['subtitle'] + '\n\n'
        text += 'ZUTATEN\n'
        for i in range(len(self.REZ['ingredientGroups'])):
            for j in range(len(self.REZ['ingredientGroups'][i]['ingredients'])):
                if not (i == 0 and j == 0):
                    text += '; '
                if self.REZ['ingredientGroups'][i]['ingredients'][j]['amount'] != 0:
                    text += str(self.REZ['ingredientGroups'][i]['ingredients'][j]['amount']).replace('.0', '') + ' '
                    text += self.REZ['ingredientGroups'][i]['ingredients'][j]['unit'] + ' '
                text += self.REZ['ingredientGroups'][i]['ingredients'][j]['name']
                text += self.REZ['ingredientGroups'][i]['ingredients'][j]['usageInfo']
        text += '\n\nZUBEREITUNG\n' + self.REZ['instructions']
        if config.plugins.chefkoch.plugin_size.value == 'FHDclassic':
            if config.plugins.chefkoch.font.value:
                repeat = 128 if self.fontlarge else 148
            else:
                repeat = 128 if self.fontlarge else 136
        else:
            if config.plugins.chefkoch.font.value:
                repeat = 132 if self.fontlarge else 148
            else:
                repeat = 132
        text += '\n' + '_' * repeat + '\nChefkoch.de'
        self['textpage'].setText(str(text))
        self.postviewready = True

    def getPrevPic(self, picdata, i):
        f = open(self.pic[i], 'wb')
        f.write(picdata)
        f.close()
        self.prevpicload[i].startDecode(self.pic[i])

    def showPrevPic(self, picInfo=None):
        if picInfo:
            i = int(match('/tmp/chefkoch(\d.*).jpg', picInfo).groups()[0])
        ptr = self.prevpicload[i].getData()
        if ptr != None:
            self['pic%d' % i].instance.setPixmap(ptr.__deref__())

    def getPostPic(self, picdata):
        f = open(self.picfile, 'wb')
        f.write(picdata)
        f.close()
        self.postpicload.startDecode(self.picfile)

    def showPostPic(self, picInfo=None):
        ptr = self.postpicload.getData()
        if ptr != None:
            self['postpic'].instance.setPixmap(ptr.__deref__())

    def showScore(self, scorepng):
        currPic = loadPNG(scorepng)
        if currPic != None:
            self['score'].instance.setPixmap(currPic)

    def Idownload(self, i, link, name):  # PrevPic-Download
        link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20'))
        getPage(link).addCallback(name, i).addErrback(self.IdownloadError)

    def IdownloadError(self, output):
        CKlog('Idownloaderror:', output)
        pass

    def Pdownload(self, link, name):  # Pic-Download
        link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20'))
        getPage(link).addCallback(name).addErrback(self.PdownloadError)

    def PdownloadError(self, output):
        CKlog('PdownloadError:', output)
        pass

    def showProgrammPage(self):  # zeige Rezeptliste
        self.current = 'menu'
        self['greenbutton'].hide()
        self['greenbutton2'].show()
        self['yellowbutton'].hide()
        self['yellowbutton2'].show()
        self['redbutton'].show()
        self['bluebutton'].show()
        self['label1'].setText('')
        self['label2'].setText('Rezept zu Favoriten hinzufügen =')
        self['label3'].setText('Ein / Ausblenden =')
        self.seitenlabel = 'Rezept Nr. ' + str(self.currItem + 1) + '\nSeite ' + str(int(self.currItem // linesPerPage + 1)) + ' von ' + str(self.maxPage)
        self['label4'].setText(self.seitenlabel)
        self['label5'].setText('= Sortierung: %s' % self.sortname[self.sort])
        self['label6'].setText('= Suche')
        self['label7'].setText('')
        self['score'].hide()
        self['scoretext'].hide()
        self['recipetext'].hide()
        self['textpage'].hide()
        self['slider_textpage'].hide()
        self['postpic'].hide()
        self['menu'].show()
        self.currItem = self['menu'].getSelectedIndex()
        self.setPrevIcons(self.currItem - self.currItem % linesPerPage)

    def returnPicShow(self):
        pass

    def returnVideo(self):
        self.ready = True

    def infoScreen(self):
        pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def hideScreen(self):
        if self.hideflag:
            self.hideflag = False
            for i in range(40, 0, -1):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()
        else:
            self.hideflag = True
            for i in range(1, 41):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()

    def exit(self):
        if not self.hideflag:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        if self.current == 'menu':
            self.close()
        elif self.fav:
            self.close()
        elif self.current == 'postview' and self.zufall:
            self.close()
        elif self.current == 'postview' and not self.zufall:
            self.postviewready = False
            self.setTitle(str(self.headline))
            self.showProgrammPage()

    def playVideo(self):
        if self.current == 'menu':
            self.REZ = self.getREZ(self.kochId[self.currItem])
        if self.REZ['recipeVideoId']:
            content, resp = getAPIdata('/videos/' + self.REZ['recipeVideoId'])
            if resp != 200:
                return resp
            result = loads(content)
            sref = eServiceReference(4097, 0, str(result['video_brightcove_url']))
            description = result['video_description']
            if len(result['video_title'] + ' - ' + description) < 30:
                sref.setName(str(result['video_title'] + ' - ' + result['video_description']))
            else:
                sref.setName(str(result['video_title']))
            self.session.openWithCallback(self.returnVideo, MoviePlayer, sref)


class getNumber(Screen):
    skin = '''
        <screen position="center,{position}" size="275,70" backgroundColor="#000000" flags="wfNoBorder" title="">
            <widget name="number" position="0,0" size="175,70" font="{font};40" halign="center" valign="center" transparent="1" zPosition="1"/>
        </screen>'''

    def __init__(self, session, number, max):
        position = str(config.plugins.chefkoch.position.value)
        font = 'Sans' if config.plugins.chefkoch.font.value else 'Regular'
        self.dict = {'position': position, 'font': font}
        self.skin = applySkinVars(getNumber.skin, self.dict)
        Screen.__init__(self, session)
        self.field = str(number)
        self['number'] = Label(self.field)
        self.max = max
        self['actions'] = NumberActionMap(['NumberActions', 'OkCancelActions'], {
            'cancel': self.quit,
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
            '0': self.keyNumber
        }, -2)
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


class ChefkochPicShow(Screen):
    skinHD = '''
        <screen position="center,{position}" size="1240,640" title="">
            <ePixmap position="0,0" size="1240,60" pixmap="{picpath}chefkochHD.png" alphatest="blend" zPosition="1" />
            <widget name="label" position="364,10" size="512,44" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget name="score" position="3,70" size="236,36" alphatest="blend" zPosition="1" />
            <widget name="scoretext" position="10,113" size="260,50" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="picture" position="270,70" size="720,540" alphatest="blend" zPosition="1" />
            <widget name="picindex" position="1000,70" size="250,50" font="{font};{fontsize2}" halign="left" zPosition="1" />
            <widget name="pictext" position="10,595" size="1220,48" font="{font};{fontsize2}" halign="center" valign="center" zPosition="1" />
        </screen>'''
    skinFHD = '''
        <screen position="center,{position}" size="1860,960" title="">
            <ePixmap position="0,0" size="1860,90" pixmap="{picpath}chefkochFHD.png" alphatest="blend" zPosition="1" />
            <widget name="label" position="546,15" size="768,66" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
            <widget name="score" position="15,105" size="354,54" alphatest="blend" zPosition="1" />
            <widget name="scoretext" position="15,169" size="390,240" font="{font};{fontsize}" halign="left" zPosition="1" />
            <widget name="picture" position="405,105" size="1080,810" alphatest="blend" zPosition="1" />
            <widget name="picindex" position="1500,105" size="375,75" font="{font};{fontsize2}" halign="left" zPosition="1" />
            <widget name="pictext" position="15,892" size="1830,72" font="{font};{fontsize2}" halign="center" valign="center" zPosition="1" />
        </screen>'''

    def __init__(self, session, titel, recipe, images):
        self.REZ = recipe
        self.IMG = images
        self.titel = titel
        self.currId = str(recipe['id'])
        font = 'Sans' if config.plugins.chefkoch.font.value else 'Regular'
        position = str(config.plugins.chefkoch.position.value)
        fontoffset = 2 if config.plugins.chefkoch.font_size.value == 'large' else 0
        if 'FHD' in config.plugins.chefkoch.plugin_size.value:
            fontsize = '%d' % int((20 + fontoffset) * 1.5)
            fontsize2 = '%d' % int((18 + fontoffset) * 1.5)
        else:
            fontsize = '%d' % int(18 + fontoffset)
            fontsize2 = '%d' % int(16 + fontoffset)
        self.dict = {'position': position, 'picpath': Pluginpath + 'pic/', 'font': font, 'fontsize': fontsize, 'fontsize2': fontsize2}
        if 'FHD' in config.plugins.chefkoch.plugin_size.value:
            self.skin = applySkinVars(ChefkochPicShow.skinFHD, self.dict)
        else:
            self.skin = applySkinVars(ChefkochPicShow.skinHD, self.dict)
        Screen.__init__(self, session)
        self.setTitle(titel)
        self.picfile = '/tmp/chefkoch.jpg'
        self.hideflag = True
        self.pixlist = []
        self.picmax = 0
        self.count = 0
        self['score'] = Pixmap()
        self['scoretext'] = Label('')
        self['scoretext'].hide()
        self['picture'] = Pixmap()
        self['picindex'] = Label('')
        self['pictext'] = Label('')
        self['label'] = Label('OK = Vollbild\n< > = Zurück / Vorwärts')
        self['NumberActions'] = NumberActionMap(['NumberActions', 'OkCancelActions', 'DirectionActions', 'ColorActions', 'HelpActions'], {
            'ok': self.ok,
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
            'displayHelp': self.infoScreen
        }, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.showPic)

    def onLayoutFinished(self):
        self.picload.setPara((self['picture'].instance.size().width(), self['picture'].instance.size().height(), 1.0, 1, False, 1, "#00000000"))
        self.getInfoTimer = eTimer()
        self.getInfoTimer.callback.append(self.getPixPage())
        self.getInfoTimer.start(500, True)

    def formatUsername(self, username, rank, trim):
        return 'Unbekannt' if "unknown" in username else (str(username) + ' (' + str(rank) + '*)')[:trim if trim > 0 else 100]

    def getPixPage(self):
        self.count = 0
        self.setTitle(str(self.titel))
        if self.REZ['subtitle']:
            self['pictext'].setText('BESCHREIBUNG: ' + str(self.REZ['subtitle']))
        if self.REZ['rating'] != None:
            score = str(round(self.REZ['rating']['rating'] / 5, 1) * 5).replace('.', '_').replace('_0', '')
            scoretext = str(self.REZ['rating']['rating']) + ' (' + str(self.REZ['rating']['numVotes']) + ' Bewertungen)'
        else:
            score = '0'
            scoretext = '(ohne Bewertung)'
        pictype = 'FHD.png' if 'FHD' in config.plugins.chefkoch.plugin_size.value else 'HD.png'
        scorepng = Pluginpath + 'pic/logos/score-' + score + pictype
        if fileExists(scorepng):
            self.showScore(scorepng)
            self['score'].show()
        self['scoretext'].setText(scoretext)
        self['scoretext'].show()
        if self.IMG['count'] > 0:
            for i in range(len(self.IMG['results'])):
                self.pixlist.append(self.IMG['results'][i]['id'])
            picurl = picurlbase + '/' + self.currId + '/bilder/' + self.REZ['previewImageId'] + '/crop-960x720/' + self.titel + '.jpg'
            self.Wdownload(picurl, self.getPic)
            self.picmax = len(self.pixlist) - 1
            username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
            self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)
        else:
            self.session.open(MessageBox, '\nKein Foto vorhanden', MessageBox.TYPE_INFO, close_on_any_key=True)

    def ok(self):
        self.session.openWithCallback(self.showPic(self.picfile), FullScreen)

    def picup(self):
        self.count += 1 if self.count < self.picmax else - self.count
        picurl = picurlbase + '/' + self.currId + '/bilder/' + str(self.IMG['results'][self.count]['id']) + '/crop-960x720/' + self.titel + '.jpg'
        self.Wdownload(picurl, self.getPic)
        username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
        self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)

    def picdown(self):
        self.count -= 1 if self.count > 0 else - self.picmax
        picurl = picurlbase + '/' + self.currId + '/bilder/' + str(self.IMG['results'][self.count]['id']) + '/crop-960x720/' + self.titel + '.jpg'
        self.Wdownload(picurl, self.getPic)
        username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
        self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)

    def gotoPic(self, number):
        self.session.openWithCallback(self.numberEntered, getNumber, number, 2)

    def numberEntered(self, number):
        if number > self.picmax:
            number = self.picmax
        self.count = number - 1
        picurl = picuribase + '/' + self.currId + '/bilder/' + str(self.IMG['results'][self.count]['id']) + '/crop-960x720/' + self.titel + '.jpg'
        self.pixlist[self.count]
        self.Wdownload(picurl, self.getPic)
        username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
        self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)

    def getPic(self, output):
        f = open(self.picfile, 'wb')
        f.write(output)
        f.close()
        self.picload.startDecode(self.picfile)

    def showPic(self, picInfo=None):
        ptr = self.picload.getData()
        if ptr != None:
            self['picture'].instance.setPixmap(ptr.__deref__())

    def showScore(self, scorepng):
        currPic = loadPNG(scorepng)
        if currPic != None:
            self['score'].instance.setPixmap(currPic)

    def Wdownload(self, link, name):
        link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20'))
        getPage(link).addCallback(name).addErrback(self.WdownloadError)

    def WdownloadError(self, output):
        CKlog('Wdownloaderror:', output)
        pass

    def infoScreen(self):
        pass

    def hideScreen(self):
        if self.hideflag:
            self.hideflag = False
            for i in range(40, 0, -1):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()
        else:
            self.hideflag = True
            for i in range(1, 41):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()

    def exit(self):
        if not self.hideflag:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class FullScreen(Screen):
    skinHD = '''
        <screen position="center,center" size="1280,720" flags="wfNoBorder" title="" >
            <eLabel position="center,center" size="960,720" backgroundColor="#000000" zPosition="1" />
            <widget name="picture" position="center,center" size="960,720" alphatest="blend" zPosition="2" />
        </screen>'''
    skinFHD = '''
        <screen position="center,center" size="1920,1080" flags="wfNoBorder" title="" >
            <eLabel position="center,center" size="1440,1080" backgroundColor="#000000" zPosition="1" />
            <widget name="picture" position="center,center" size="1440,1080" alphatest="blend" zPosition="2" />
        </screen>'''

    def __init__(self, session):
        if 'FHD' in config.plugins.chefkoch.plugin_size.value:
            self.skin = FullScreen.skinFHD
        else:
            self.skin = FullScreen.skinHD
        Screen.__init__(self, session)
        self.picfile = '/tmp/chefkoch.jpg'
        self.hideflag = True
        self['picture'] = Pixmap()
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {
            'ok': self.exit,
            'cancel': self.exit,
            'red': self.infoScreen,
            'yellow': self.infoScreen,
            'green': self.infoScreen,
            'blue': self.hideScreen
        }, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.showPic)

    def onLayoutFinished(self):
        self.picload.setPara((self['picture'].instance.size().width(), self['picture'].instance.size().height(), 1.0, 1, False, 1, "#00000000"))
        self.picload.startDecode(self.picfile)

    def showPic(self, picInfo=None):
        ptr = self.picload.getData()
        if ptr != None:
            self['picture'].instance.setPixmap(ptr.__deref__())

    def infoScreen(self):
        pass

    def hideScreen(self):
        if self.hideflag:
            self.hideflag = False
            for i in range(40, 0, -1):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()
        else:
            self.hideflag = True
            for i in range(1, 41):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()

    def exit(self):
        if not self.hideflag:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()


class chefkochFav(Screen):
    skinHD = '''
        <screen position="center,{position}" size="1240,590" title="">
            <ePixmap position="0,0" size="1240,60" pixmap="{picpath}chefkochHD.png" alphatest="blend" zPosition="1" />
            <widget name="label" position="243,20" size="250,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <ePixmap position="219,20" size="18,18" pixmap="{picpath}buttons/redHD.png" alphatest="blend" zPosition="2" />
            <widget name="favmenu" position="10,70" size="1200,510" scrollbarMode="showOnDemand" zPosition="1" />
        </screen>'''
    skinFHD = '''
        <screen position="center,{position}" size="1860,885" title="">
            <ePixmap position="0,0" size="1860,90" pixmap="{picpath}chefkochFHD.png" alphatest="blend" zPosition="1" />
            <widget name="label" position="364,30" size="375,33" font="{font};27" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <ePixmap position="328,30" size="27,27" pixmap="{picpath}buttons/redFHD.png" alphatest="blend" zPosition="2" />
            <widget name="favmenu" position="15,105" size="1800,765" scrollbarMode="showOnDemand" zPosition="1" />
        </screen>'''
    skinALT = '''
        <screen position="center,{position}" size="1240,980" title="">
            <ePixmap position="0,0" size="1240,60" pixmap="{picpath}chefkochHD.png" alphatest="blend" zPosition="1" />
            <widget name="label" position="243,20" size="250,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <ePixmap position="219,20" size="18,18" pixmap="{picpath}buttons/redHD.png" alphatest="blend" zPosition="2" />
            <widget name="favmenu" position="10,70" size="1200,800" scrollbarMode="showOnDemand" zPosition="1" />
        </screen>'''

    def __init__(self, session):
        position = str(config.plugins.chefkoch.position.value)
        font = 'Sans' if config.plugins.chefkoch.font.value else 'Regular'
        self.dict = {'position': position, 'picpath': Pluginpath + 'pic/', 'font': font}
        self.font = 0
        if config.plugins.chefkoch.plugin_size.value == 'FHDclassic':
            self.font = -1
            self.skin = applySkinVars(chefkochFav.skinFHD, self.dict)
        elif config.plugins.chefkoch.plugin_size.value == 'FHDaltern':
            self.skin = applySkinVars(chefkochFav.skinALT, self.dict)
        else:
            self.skin = applySkinVars(chefkochFav.skinHD, self.dict)
        self.session = session
        Screen.__init__(self, session)
        self.hideflag = True
        self.count = 0
        self.favlist = []
        self.favId = []
        self.faventries = []
        self['favmenu'] = ItemList([])
        self['label'] = Label('= Entferne Favorit')
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'down': self.down,
            'up': self.up,
            'red': self.red,
            'yellow': self.infoScreen,
            'green': self.infoScreen,
            'blue': self.hideScreen,
            '0': self.move2end,
            '1': self.move2first
        }, -1)
        self.makeFav()

    def makeFav(self):
        self.setTitle('Chefkoch:::Favoriten')
        self.favoriten = Pluginpath + 'db/favoriten'
        if fileExists(self.favoriten):
            f = open(self.favoriten, 'r')
            for line in f:
                if ':::' in line:
                    self.count += 1
                    favline = line.split(':::')
                    titel = str(favline[0])
                    Id = favline[1].replace('\n', '')
                    res = ['']
                    res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * scale), int(30 * scale)), font=self.font,
                               color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=titel))
                    self.faventries.append(res)
                    self.favlist.append(titel)
                    self.favId.append(Id)
            f.close()
            self['favmenu'].l.setList(self.faventries)
            self['favmenu'].l.setItemHeight(int(30 * scale))

    def ok(self):
        self.currItem = self.getIndex(self['favmenu'])
        if len(self.favlist) > 0:
            titel = self.favlist[self.currItem]
            Id = self.favId[self.currItem]
            self.session.open(ChefkochView, Id, titel, 1, True, False)

    def red(self):
        if len(self.favlist) > 0:
            try:
                self.currItem = self.getIndex(self['favmenu'])
                name = self.favlist[self.currItem]
            except IndexError:
                name = ''
            self.session.openWithCallback(self.red_return, MessageBox, "\nRezept '%s' aus den Favoriten entfernen?" % name, MessageBox.TYPE_YESNO)

    def red_return(self, answer):
        if answer is True:
            self.currItem = self.getIndex(self['favmenu'])
            try:
                link = self.favId[self.currItem]
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
            rename(self.favoriten + '.new', self.favoriten)
            self.favlist = []
            self.favId = []
            self.faventries = []
            self.makeFav()

    def move2first(self):
        try:
            self.currItem = self.getIndex(self['favmenu'])
            fav = self.favlist[self.currItem] + ':::' + self.favId[self.currItem]
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
            rename(self.favoriten + '.new', self.favoriten)
            self.favlist = []
            self.favId = []
            self.faventries = []
            self.makeFav()
        except IndexError:
            pass

    def move2end(self):
        try:
            self.currItem = self.getIndex(self['favmenu'])
            fav = self.favlist[self.currItem] + ':::' + self.favId[self.currItem]
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
            rename(self.favoriten + '.new', self.favoriten)
            self.favlist = []
            self.favId = []
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
        pass

    def hideScreen(self):
        if self.hideflag:
            self.hideflag = False
            for i in range(40, 0, -1):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()
        else:
            self.hideflag = True
            for i in range(1, 41):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()

    def exit(self):
        if not self.hideflag:
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        self.close()

    def onLayoutFinished(self):
        self.loading = True
        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.finished)
        self.container.execute("wget -c '%s' -O '%s'" % (self.url, self.filename))

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
            self['size'].setText('%s MB von %s MB' %
                                 (int(self.localsize) / 1048576, int(self.filesize) / 1048576))
        elif self.localsize > 0 and self.filesize == 0:
            self['slider'].setValue(0)
            self['size'].setText('%s MB von ??? MB' % (int(self.localsize) / 1048576))
        elif self.filesize > 0 and self.localsize == 0:
            self['slider'].setValue(0)
            self['size'].setText('0 MB von %s MB' % (int(self.filesize) / 1048576))
        self.updateTimer.start(self.update_interval)

    def refresh(self):
        self.UpdateStatus()

    def playVideo(self, answer):
        if answer is True:
            sref = eServiceReference(4097, 0, self.filename)
            sref.setName(self.name)
            self.session.openWithCallback(self.exit, MoviePlayer, sref)
        else:
            self.close()

    def infoScreen(self):
        pass

    def exit(self):
        if not self.hideflag:
            self.hideflag = True
            f = open('/proc/stb/video/alpha', 'w')
            f.write('%i' % config.av.osd_alpha.value)
            f.close()
        else:
            self.close()


class ItemList(MenuList):
    def __init__(self, items, enableWrapAround=True):
        MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
        fontname = 'Sans' if config.plugins.chefkoch.font.value else 'Regular'
        fontoffset = 2 if config.plugins.chefkoch.font_size.value == 'large' else 0
        self.l.setFont(-2, gFont(fontname, int(24 * scale)))
        self.l.setFont(-1, gFont(fontname, int((22 + fontoffset) * scale)))
        self.l.setFont(0, gFont(fontname, int((20 + fontoffset) * scale)))
        self.l.setFont(1, gFont(fontname, int((18 + fontoffset) * scale)))
        self.l.setFont(2, gFont(fontname, int((16 + fontoffset) * scale)))


class ChefkochMain(Screen):
    skinHD = '''
        <screen position="center,{position}" size="590,625" title="Chefkoch.de">
            <ePixmap position="0,0" size="590,60" pixmap="{picpath}menuHD.png" alphatest="blend" zPosition="1" />
            <widget name="label1" position="34,10" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label2" position="34,32" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label3" position="416,10" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label4" position="416,32" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="release" position="350,45" size="105,20" font="{font};14" foregroundColor="#00000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <ePixmap position="10,10" size="18,18" pixmap="{picpath}buttons/greenHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="10,32" size="18,18" pixmap="{picpath}buttons/yellowHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="562,10" size="18,18" pixmap="{picpath}buttons/redHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="562,32" size="18,18" pixmap="{picpath}buttons/blueHD.png" alphatest="blend" zPosition="2" />
            <widget name="mainmenu" position="10,70" size="570,540" scrollbarMode="showNever" zPosition="2" />
            <widget name="secondmenu" position="10,70" size="570,540" scrollbarMode="showNever" zPosition="2" />
            <widget name="thirdmenu" position="10,70" size="570,540" scrollbarMode="showNever" zPosition="2" />
        </screen>'''
    skinFHD = '''
        <screen position="center,{position}" size="885,980" title="Chefkoch.de">
            <ePixmap position="0,0" size="885,90" pixmap="{picpath}menuFHD.png" alphatest="blend" zPosition="1" />
            <widget name="label1" position="51,13" size="210,30" font="{font};24" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label2" position="51,46" size="210,30" font="{font};24" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label3" position="624,13" size="210,30" font="{font};24" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label4" position="624,46" size="210,30" font="{font};24" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="release" position="525,67" size="158,30" font="{font};21" foregroundColor="#00000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <ePixmap position="15,15" size="24,24" pixmap="{picpath}buttons/greenFHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="15,48" size="24,24" pixmap="{picpath}buttons/yellowFHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="843,15" size="24,24" pixmap="{picpath}buttons/redFHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="843,48" size="24,24" pixmap="{picpath}buttons/blueFHD.png" alphatest="blend" zPosition="2" />
            <widget name="mainmenu" position="15,105" size="855,860" scrollbarMode="showNever" zPosition="2" />
            <widget name="secondmenu" position="15,105" size="855,860" scrollbarMode="showNever" zPosition="2" />
            <widget name="thirdmenu" position="15,105" size="855,860" scrollbarMode="showNever" zPosition="2" />
        </screen>'''
    skinALT = '''
        <screen position="center,{position}" size="590,980" title="Chefkoch.de">
            <ePixmap position="0,0" size="590,60" pixmap="{picpath}menuHD.png" alphatest="blend" zPosition="1" />
            <widget name="label1" position="34,10" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label2" position="34,32" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label3" position="416,10" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="label4" position="416,32" size="140,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
            <widget name="release" position="350,45" size="105,20" font="{font};14" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <ePixmap position="10,10" size="18,18" pixmap="{picpath}buttons/greenHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="10,32" size="18,18" pixmap="{picpath}buttons/yellowHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="562,10" size="18,18" pixmap="{picpath}buttons/redHD.png" alphatest="blend" zPosition="2" />
            <ePixmap position="562,32" size="18,18" pixmap="{picpath}buttons/blueHD.png" alphatest="blend" zPosition="2" />
            <widget name="mainmenu" position="10,70" size="570,900" scrollbarMode="showNever" zPosition="2" />
            <widget name="secondmenu" position="10,70" size="570,900" scrollbarMode="showNever" zPosition="2" />
            <widget name="thirdmenu" position="10,70" size="570,900" scrollbarMode="showNever" zPosition="2" />
        </screen>'''

    def __init__(self, session):
        global scale
        global linesPerPage
        self.session = session
        font = 'Sans' if config.plugins.chefkoch.font.value else 'Regular'
        position = str(config.plugins.chefkoch.position.value)
        self.dict = {'position': position, 'picpath': Pluginpath + 'pic/', 'font': font}
        scale = 1.0
        linesPerPage = 6
        if config.plugins.chefkoch.plugin_size.value == 'FHDclassic':
            self.skin = applySkinVars(ChefkochMain.skinFHD, self.dict)
            scale = 1.5
        elif config.plugins.chefkoch.plugin_size.value == 'FHDaltern':
            linesPerPage = 10
            self.skin = applySkinVars(ChefkochMain.skinALT, self.dict)
        else:
            self.skin = applySkinVars(ChefkochMain.skinHD, self.dict)
        Screen.__init__(self, session)
        self.picfile = '/tmp/chefkoch.jpg'
        self.rezeptfile = '/tmp/Rezept.html'
        self.actmenu = 'mainmenu'
        self.hideflag = True
        self['mainmenu'] = ItemList([])
        self['secondmenu'] = ItemList([])
        self['thirdmenu'] = ItemList([])
        self['label1'] = Label('= Zufall')
        self['label2'] = Label('= Suche')
        self['label3'] = Label('Favorit =')
        self['label4'] = Label('Ausblenden =')
        self['release'] = Label(Release)
        self['helpactions'] = ActionMap(['HelpActions'], {'displayHelp': self.infoScreen}, -1)
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'MovieSelectionActions'], {
            'ok': self.ok,
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
            'contextMenu': self.config
        }, -1)
        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        self.ChefTimer = eTimer()
        self.makeMainMenu()
        self.ChefTimer.start(500, True)

    def ok(self):
        self.currItem = self.getIndex(self[self.actmenu])
        if self.actmenu == 'mainmenu':
            mainId = self.mainId[self.currItem]
            if mainId == '998':  # Id für CK-Video Hauptmenü (= Secondmenu)
                self.CKvideo = True
                self.currKAT = self.getVKAT()
                self.makeSecondMenu(mainId)
            elif mainId == '996': # Id für CK-Magazin Hauptmenü (= Secondmenu)
                self.CKvideo = False
                self.currKAT = self.getMKAT()
                self.makeSecondMenu(mainId)
            else:
                self.CKvideo = False
                self.currKAT = self.getNKAT()
                if list(filter(lambda i: i['parentId'] == mainId, self.currKAT)):
                    self.makeSecondMenu(mainId)
                else:
                    sort = 4 if mainId == '999' else 1  # Datumsortierung für "Das perfekte Dinner"
                    self.session.openWithCallback(self.selectMainMenu, ChefkochView, self.mainmenuquery[self.currItem], self.mainmenutitle[self.currItem], sort, False, False)

        elif self.actmenu == 'secondmenu':
            secondId = self.secondId[self.currItem]
            if list(filter(lambda i: i['parentId'] == secondId, self.currKAT)):
                self.makeThirdMenu(secondId)
            else:
                sort = 3 if self.CKvideo else 1  # Videosortierung für "Chefkoch Video"
                self.session.openWithCallback(self.selectSecondMenu, ChefkochView, self.secondmenuquery[self.currItem], self.secondmenutitle[self.currItem], sort, False, False)

        elif self.actmenu == 'thirdmenu':
            sort = 3 if self.CKvideo else 1  # Videosortierung für "Chefkoch Video"
            self.session.openWithCallback(self.selectThirdMenu, ChefkochView, self.thirdmenuquery[self.currItem], self.thirdmenutitle[self.currItem], sort, False, False)

    def makeMainMenu(self):
        self.NKAT = [] # Normalkategorien
        self.VKAT = [] # Videokategorien
        self.MKAT = [] # Magazinkategorien
        self.mainmenulist = []
        self.mainmenuquery = []
        self.mainmenutitle = []
        self.mainId = []
        self.currKAT = self.getNKAT()
        for i in range(len(self.currKAT)):
            res = ['']
            if self.currKAT[i]['level'] == 1:
                res.append(MultiContentEntryText(pos=(0, 1), size=(int(570 * scale), int(30 * scale)), font=-2, flags=RT_HALIGN_CENTER, text=str(self.currKAT[i]['descriptionText'])))
                self.mainmenulist.append(res)
                self.mainmenuquery.append(self.currKAT[i]['descriptionText'])
                self.mainmenutitle.append(self.currKAT[i]['descriptionText'])
                self.mainId.append(self.currKAT[i]['id'])
        self['mainmenu'].l.setList(self.mainmenulist)
        self['mainmenu'].l.setItemHeight(int(30 * scale))
        self['mainmenu'].l.setFont(-2, gFont('Sans', int(24 * scale)))
        self.selectMainMenu()

    def makeSecondMenu(self, parentId):
        self.secondmenulist = []
        self.secondmenuquery = []
        self.secondmenutitle = []
        self.secondId = []
        self.parentId = parentId
        for i in range(len(self.currKAT)):
            res = ['']
            if self.currKAT[i]['level'] == 2 and self.currKAT[i]['parentId'] == parentId:
                res.append(MultiContentEntryText(pos=(0, 1), size=(int(570 * scale), int(30 * scale)), font=-2, flags=RT_HALIGN_CENTER, text=str(self.currKAT[i]['descriptionText'])))
                self.secondmenulist.append(res)
                self.secondmenuquery.append(self.currKAT[i]['descriptionText'])
                self.secondmenutitle.append(self.currKAT[i]['descriptionText'])
                self.secondId.append(self.currKAT[i]['id'])
        self['secondmenu'].l.setList(self.secondmenulist)
        self['secondmenu'].l.setItemHeight(int(30 * scale))
        self['secondmenu'].l.setFont(-2, gFont('Sans', int(24 * scale)))
        self['secondmenu'].moveToIndex(0)
        for i in range(len(self.currKAT)):
            if self.currKAT[i]['id'] == parentId:
                break
        self.setTitle(str(self.currKAT[i]['title']))
        self.selectSecondMenu()

    def makeThirdMenu(self, parentId):
        self.thirdmenulist = []
        self.thirdmenuquery = []
        self.thirdmenutitle = []
        for i in range(len(self.currKAT)):
            res = ['']
            if self.currKAT[i]['level'] == 3 and self.currKAT[i]['parentId'] == parentId:
                res.append(MultiContentEntryText(pos=(0, 1), size=(int(570 * scale), int(30 * scale)), font=-2, flags=RT_HALIGN_CENTER, text=str(self.currKAT[i]['descriptionText'])))
                self.thirdmenulist.append(res)
                self.thirdmenuquery.append(self.currKAT[i]['descriptionText'])
                self.thirdmenutitle.append(self.currKAT[i]['descriptionText'])
        self['thirdmenu'].l.setList(self.thirdmenulist)
        self['thirdmenu'].l.setItemHeight(int(30 * scale))
        self['thirdmenu'].l.setFont(-2, gFont('Sans', int(24 * scale)))
        self['thirdmenu'].moveToIndex(0)
        for i in range(len(self.currKAT)):
            if self.currKAT[i]['id'] == parentId:
                break
        self.setTitle(str(self.currKAT[i]['title']))
        self.selectThirdMenu()

    def makeVKATdb(self):  # hole alle verfügbaren Videokategorien
        content, resp = getAPIdata('/videos?&offset=0&limit=10000')
        if resp != 200:
            return resp
        result = loads(content)
        VKAT = []
        f = open(Pluginpath + 'db/VKATdb', 'a')
        for i in range(len(result)):
            data = result[i]['video_format']
            if data != 'unknown':
                id = ''.join(x for x in data if x.isdigit())
                if id not in VKAT:
                    VKAT.append(id)
                    f.write(data + '|' + data + '\n')
        f.close()

    def getNKAT(self):  # erzeuge die normale Kategorie
        if not self.NKAT:
            content, resp = getAPIdata('/recipes/categories')
            if resp != 200:
                return resp
            self.NKAT = loads(content)
            self.NKAT.append({'id': '996', 'title': 'Chefkoch Magazin', 'parentId': None, 'level': 1, 'descriptionText': 'Chefkoch Magazin', 'linkName': 'https://www.chefkoch.de/magazin/'})
            self.NKAT.append({'id': '998', 'title': 'Chefkoch Videos', 'parentId': None, 'level': 1, 'descriptionText': 'Chefkoch Videos', 'linkName': 'video.html'})
            self.NKAT.append({'id': '999', 'title': 'Perfekte Dinner', 'parentId': None, 'level': 1, 'descriptionText': 'Das perfekte Dinner Rezepte', 'linkName': 'das-perfekte-dinner.html'})
        return self.NKAT

    def getVKAT(self):  # erzeuge die Videokategorie
        if not self.VKAT:
            for i in range(len(self.NKAT)):
                if self.NKAT[i]['level'] == 1:
                    self.VKAT.append(self.NKAT[i])
            if not fileExists(Pluginpath + 'db/VKATdb'):
                self.makeVKATdb()  # wird nur bei fehlender VKATdb erzeugt (= Notfall)
            i = 1000  # erzeuge eigene Video-IDs über 1000
            f = open(Pluginpath + 'db/VKATdb', 'r')
            for data in f:
                dict = {}
                dict['id'] = str(i)
                dict['title'] = data.split('|')[1].replace('\n', '')
                if data.split('|')[0].startswith('drupal'):
                    dict['parentId'] = '998'  # Id für CK-Video Hauptmenü (= Secondmenu)
                    dict['level'] = 2
                else:
                    dict['parentId'] = '997'  # Id für CK-Video Untermenü (= Thirdmenu)
                    dict['level'] = 3
                dict['descriptionText'] = data.split('|')[1].replace('\n', '')
                dict['linkName'] = data.split('|')[0]
                self.VKAT.append(dict)
                i += 1
            f.close()
            self.VKAT.append({'id': '997', 'title': 'weitere Videos', 'parentId': '998', 'level': 2, 'descriptionText': '>>> weitere Chefkoch Videos <<<', 'linkName': ''})
        return self.VKAT

    def getMKAT(self):  # erzeuge die Magazinkategorie
        if not self.MKAT:
            content, resp = getAPIdata('/magazine/categories')
            if resp != 200:
                return resp
            result = loads(content)
            offset = 2000  # erzeuge eigene Magazin-IDs über 2000
            for i in range(len(result)):
                dict = {}
                if result[i]['parent'] == '34' and result[i]['published']: # Id 34 ist die Root von CK-Magazin
                    dict['id'] = str(int(result[i]['id']) + offset)
                    dict['title'] = result[i]['name']
                    dict['parentId'] = '996'  # Id für CK-Magazin Hauptmenü (= Secondmenu)
                    dict['level'] = 2
                    dict['descriptionText'] = result[i]['name']
                    dict['linkName'] = result[i]['url']
                    self.MKAT.append(dict)
            MKATlen = len(self.MKAT)
            for i in range(len(result)):
                for j in range(MKATlen):
                    dict = {}
                    parentId = result[i]['parent']
                    if parentId:
                        if int(parentId) + offset == int(self.MKAT[j]['id']):
                            dict['id'] = str(int(result[i]['id']) + offset)
                            dict['title'] = result[i]['name']
                            dict['parentId'] = str(int(parentId) + offset)
                            dict['level'] = 3
                            dict['descriptionText'] = result[i]['name']
                            dict['linkName'] = result[i]['url']
                            self.MKAT.append(dict)
                            break
            self.MKAT.reverse()
        return self.MKAT

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

    def getIndex(self, list):
        return list.getSelectedIndex()

    def yellow(self):
        self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Chefkoch - Suche Rezepte:', text='')

    def searchReturn(self, search):
        if search and search != '':
            self.session.open(ChefkochView, search, 'mit "' + search + '" gefundene Rezepte', 0, False, False)

    def fav(self):
        self.session.open(chefkochFav)

    def zufall(self):
        self.session.openWithCallback(self.selectMainMenu, ChefkochView, 'recipe-of-today', 'Zufallsrezept', 1, False, True)

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def config(self):
        config.usage.on_movie_stop.value = self.movie_stop
        config.usage.on_movie_eof.value = self.movie_eof
        self.session.openWithCallback(self.exit, chefkochConfig)

    def infoScreen(self):
        pass

    def hideScreen(self):
        if self.hideflag:
            self.hideflag = False
            for i in range(40, 0, -1):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
                f.close()
        else:
            self.hideflag = True
            for i in range(1, 41):
                f = open('/proc/stb/video/alpha', 'w')
                f.write('%i' % (config.av.osd_alpha.value * i / 40))
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
            for i in range(linesPerPage):
                pic = '/tmp/chefkoch%d.jpg' % i
                if fileExists(pic):
                    remove(pic)
            if fileExists(self.picfile):
                remove(self.picfile)
            if fileExists(self.rezeptfile):
                remove(self.rezeptfile)
            self.close()
        elif self.actmenu == 'secondmenu':
            self.CurrKAT = self.getNKAT()
            self.setTitle('Chefkoch.de')
            self.selectMainMenu()
        elif self.actmenu == 'thirdmenu':
            for i in range(len(self.currKAT)):
                if self.currKAT[i]['id'] == self.parentId:
                    break
            self.setTitle(str(self.currKAT[i]['title']))
            self.selectSecondMenu()


class chefkochConfig(ConfigListScreen, Screen):
    skin = '''
        <screen position="center,center" size="530,518" backgroundColor="#20000000" title="Chefkoch Setup">
            <ePixmap position="0,0" size="530,50" pixmap="{picpath}chefkoch.png" alphatest="blend" zPosition="1" />
            <ePixmap position="9,59" size="512,1" pixmap="{picpath}setup/seperator.png" alphatest="off" zPosition="1" />
            <widget name="config" position="9,60" size="512,125" itemHeight="25" scrollbarMode="showOnDemand" zPosition="1" />
            <ePixmap position="9,186" size="512,1" pixmap="{picpath}setup/seperator.png" alphatest="off" zPosition="1" />
            <eLabel position="60,195" size="135,20" font="{font};18" halign="left" text="TEXT = Tastatur" transparent="1" zPosition="1" />
            <eLabel position="250,195" size="125,20" font="{font};18" halign="left" text="Speichern" transparent="1" zPosition="1" />
            <eLabel position="395,195" size="125,20" font="{font};18" halign="left" text="Abbrechen" transparent="1" zPosition="1" />
            <ePixmap position="225,196" size="18,18" pixmap="{picpath}buttons/greenHD.png" alphatest="blend" zPosition="1" />
            <ePixmap position="370,196" size="18,18" pixmap="{picpath}buttons/redHD.png" alphatest="blend" zPosition="1" />
            <widget name="plugin" position="9,225" size="512,288" alphatest="blend" zPosition="1" />
            <widget source="VKeyIcon" text="" render="Label" position="0,0" size="0,0" conditional="VKeyIcon">
                <convert type="ConditionalShowHide" />
            </widget>
        </screen>'''

    def __init__(self, session):
        font = 'Sans' if config.plugins.chefkoch.font.value else 'Regular'
        self.dict = {'picpath': Pluginpath + 'pic/', 'font': font}
        self.skin = applySkinVars(chefkochConfig.skin, self.dict)
        Screen.__init__(self, session)
        self['VKeyIcon'] = Boolean(False)
        self.password = config.plugins.chefkoch.password.value
        self['plugin'] = Pixmap()
        list = []
        list.append(getConfigListEntry('Plugin Größe:', config.plugins.chefkoch.plugin_size, _("Plugins Größe"))
        list.append(getConfigListEntry('Plugin Position:', config.plugins.chefkoch.position, _("Plugins Position"))
        list.append(getConfigListEntry('Plugin Schriftgröße:', config.plugins.chefkoch.font_size, _("Schriftgröße"))
        list.append(getConfigListEntry('Plugin Sans Serif Schrift:', config.plugins.chefkoch.font, _("Plugin Sans Serif Schrift"))
        list.append(getConfigListEntry('Maximale Anzahl Rezepte:', config.plugins.chefkoch.maxrecipes, _("Maximale Anzahl Rezepte"))
        list.append(getConfigListEntry('Maximale Anzahl Kommentare:', config.plugins.chefkoch.maxcomments, _("Maximale Anzahl Kommentare"))
        list.append(getConfigListEntry('Maximale Anzahl Rezeptbilder:', config.plugins.chefkoch.maxpictures, _("Maximale Anzahl Rezeptbilder"))
        list.append(getConfigListEntry('Versende Rezepte per E-mail:', config.plugins.chefkoch.mail, _("Versende Rezepte per E-mail"))
        list.append(getConfigListEntry('E-mail Absender:', config.plugins.chefkoch.mailfrom, _("E-mail Absender"))
        list.append(getConfigListEntry('E-mail Empfänger:', config.plugins.chefkoch.mailto, _("E-mail Empfänger"))
        list.append(getConfigListEntry('E-mail Login:', config.plugins.chefkoch.login, _("E-mail Login"))
        list.append(getConfigListEntry('E-mail Passwort:', config.plugins.chefkoch.password, _("E-mail Passwort"))
        list.append(getConfigListEntry('E-mail Server:', config.plugins.chefkoch.server, _("E-mail Server"))
        list.append(getConfigListEntry('E-mail Server Port:', config.plugins.chefkoch.port, _("E-mail Server Port"))
        list.append(getConfigListEntry('E-mail Server SSL:', config.plugins.chefkoch.ssl, _("E-mail Server SSL"))
        list.append(getConfigListEntry('DebugLog', config.plugins.chefkoch.debuglog, _("Debug Logging aktivieren"))
        list.append(getConfigListEntry('Log in Datei', config.plugins.chefkoch.logtofile, _("Log in Datei '/home/root/logs'"))

        self['actions']=ActionMap(['OkCancelActions', 'ColorActions'], {
            'cancel': self.keyCancel,
            'red': self.keyCancel,
            'green': self.keySave
        }, -2)
        ConfigListScreen.__init__(self, list, on_change=self.UpdateComponents)
        self.onLayoutFinish.append(self.UpdateComponents)

    def UpdateComponents(self):
        png=Pluginpath + 'pic/setup/' + config.plugins.chefkoch.plugin_size.value + '.png'
        if fileExists(png):
            PNG=loadPNG(png)
            if PNG != None:
                self['plugin'].instance.setPixmap(PNG)
        current=self['config'].getCurrent()

    def keySave(self):
        if config.plugins.chefkoch.password.value != self.password:
            password=b64encode(config.plugins.chefkoch.password.value.encode('utf-8'))
            config.plugins.chefkoch.password.value=password
        current=self['config'].getCurrent()
        self.saveAll()
        self.exit()

    def keyCancel(self):
        for x in self['config'].list:
            x[1].cancel()
        self.exit()

    def exit(self):
        self.session.openWithCallback(self.close, ChefkochMain)


def main(session, **kwargs):
    session.open(ChefkochMain)


def Plugins(**kwargs):
    return [PluginDescriptor(name='Chefkoch.de', description='Chefkoch.de Rezepte', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main), PluginDescriptor(name='Chefkoch.de', description='Chefkoch.de Rezepte', where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]
