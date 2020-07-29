# Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/IPTVImporter/plugin.py
from __future__ import absolute_import
from base64 import b64encode, b64decode
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup
import re, os, json
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
import urllib.request, urllib.error, urllib.parse
from Screens.ChannelSelection import service_types_tv
from enigma import eServiceCenter, eServiceReference, eDVBDB, getDesktop
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigPassword, ConfigYesNo, ConfigPosition, ConfigInteger, getConfigListEntry, ConfigBoolean, ConfigText, ConfigSelection, configfile, NoSave
from boxbranding import getImageDistro
from Components.Sources.StaticText import StaticText
from Components.PluginComponent import plugins
config.plugins.iptvimport = ConfigSubsection()
config.plugins.iptvimport.portal = ConfigText(default='http://XXX', fixed_size=False)
config.plugins.iptvimport.username = ConfigText(default='', fixed_size=False)
config.plugins.iptvimport.password = ConfigPassword(default='', fixed_size=False)
config.plugins.iptvimport.delbouquets = ConfigYesNo(default=False)
config.plugins.iptvimport.vod = ConfigSelection(default='vod', choices=[('none', _('none')), ('vod', 'IPTV VOD')])
config.plugins.iptvimport.skyde = ConfigSelection(default='sky', choices=[('sky', 'IPTV Sky DE'), ('deutsch', 'IPTV DE'), ('none', _('none'))])
config.plugins.iptvimport.deutsch = ConfigSelection(default='deutsch', choices=[('inter', 'IPTV Inter'), ('deutsch', 'IPTV DE'), ('none', _('none'))])
config.plugins.iptvimport.sportde = ConfigSelection(default='sport', choices=[('sport', 'IPTV Sport DE'), ('de', 'IPTV DE'), ('none', _('none'))])
config.plugins.iptvimport.buli = ConfigSelection(default='buli', choices=[('buli', 'IPTV Bundesliga'), ('sport', 'IPTV Sport DE'), ('none', _('none'))])
config.plugins.iptvimport.other = ConfigSelection(default='deutsch', choices=[('deutsch', 'IPTV DE'), ('extra', 'IPTV Suisse and Austria'), ('none', _('none'))])
config.plugins.iptvimport.xxx = ConfigSelection(default='none', choices=[('none', _('none')), ('xxx', 'IPTV XXX'), ('inter', 'IPTV Inter')])
config.plugins.iptvimport.italy = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('italy', 'IPTV Italy')])
config.plugins.iptvimport.france = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('france', 'IPTV France')])
config.plugins.iptvimport.uk = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('uk', 'IPTV UK')])
config.plugins.iptvimport.spain = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('spain', 'IPTV Spain')])
config.plugins.iptvimport.nl = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('nl', 'IPTV Netherland')])
config.plugins.iptvimport.pl = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('pl', 'IPTV Poland')])
config.plugins.iptvimport.yu = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('yu', 'IPTV Ex-Yu')])
config.plugins.iptvimport.ro = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('ro', 'IPTV Romania')])
config.plugins.iptvimport.us = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('us', 'IPTV US')])
config.plugins.iptvimport.arabic = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('arabic', 'IPTV Arabic')])
config.plugins.iptvimport.turk = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('turkey', 'IPTV Turkey')])
config.plugins.iptvimport.sweden = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('sweden', 'IPTV Sweden')])
config.plugins.iptvimport.finland = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('finland', 'IPTV Finland')])
config.plugins.iptvimport.portugal = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('portugal', 'IPTV Portugal')])
config.plugins.iptvimport.spain = ConfigSelection(default='none', choices=[('none', _('none')), ('inter', 'IPTV Inter'), ('spain', 'IPTV Spain')])
config.plugins.iptvimport.showinplugins = ConfigYesNo(default=False)
config.plugins.iptvimport.showinextensions = ConfigYesNo(default=False)
config.plugins.iptvimport.showinmenu = ConfigYesNo(default=True)

class IPTVImporter(Screen, ConfigListScreen):
    if getDesktop(0).size().width() >= 1280:
        skin = '\n\t\t\t<screen name="IPTVImporter" position="center,center" size="1280,720" title="IPTVImporter v 0.9.9">\n\t\t\t\t<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />\n\t\t\t\t<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;24" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t\t\t<ePixmap pixmap="skin_default/buttons/green.png" position="150,0" size="140,40" alphatest="on" />\n\t\t\t\t<widget source="key_green" render="Label" position="150,0" zPosition="1" size="140,40" font="Regular;24" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget name="config" position="5,50" size="1260,680" zPosition="1" scrollbarMode="showOnDemand" />\n\t\t\t</screen>\n\t\t\t'
    else:
        skin = '\n\t\t\t<screen name="IPTVImporter" position="center,center" size="710,450" title="IPTVImporter v 0.9.9">\n\t\t\t\t<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />\n\t\t\t\t<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;24" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t\t\t<ePixmap pixmap="skin_default/buttons/green.png" position="150,0" size="140,40" alphatest="on" />\n\t\t\t\t<widget source="key_green" render="Label" position="150,0" zPosition="1" size="140,40" font="Regular;24" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget name="config" position="5,50" size="700,250" zPosition="1" scrollbarMode="showOnDemand" />\n\t\t\t</screen>'

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, self.session)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session)
        self.iptvimport = config.plugins.iptvimport
        self.list.append(getConfigListEntry(_('Portal'), config.plugins.iptvimport.portal))
        self.list.append(getConfigListEntry(_('User'), config.plugins.iptvimport.username))
        self.list.append(getConfigListEntry(_('Password'), config.plugins.iptvimport.password))
        self.list.append(getConfigListEntry(_('Delete IPTV Bouquets before Import'), config.plugins.iptvimport.delbouquets))
        self.list.append(getConfigListEntry(_('Import VOD in Bouquet'), config.plugins.iptvimport.vod))
        self.list.append(getConfigListEntry(_('Import Sky Germany Channels in Bouquet'), config.plugins.iptvimport.skyde))
        self.list.append(getConfigListEntry(_('Import Germany Channels in Bouquet'), config.plugins.iptvimport.deutsch))
        self.list.append(getConfigListEntry(_('Import German Sport Channels in Bouquet'), config.plugins.iptvimport.sportde))
        self.list.append(getConfigListEntry(_('Import Bundesliga Channels in Bouquet'), config.plugins.iptvimport.buli))
        self.list.append(getConfigListEntry(_('Import Suisse and Austria Channels in Bouquet'), config.plugins.iptvimport.other))
        self.list.append(getConfigListEntry(_('Import XXX Channels in Bouquet'), config.plugins.iptvimport.xxx))
        self.list.append(getConfigListEntry(_('Import Italian Channels in Bouquet'), config.plugins.iptvimport.italy))
        self.list.append(getConfigListEntry(_('Import France Channels in Bouquet'), config.plugins.iptvimport.france))
        self.list.append(getConfigListEntry(_('Import UK Channels in Bouquet'), config.plugins.iptvimport.uk))
        self.list.append(getConfigListEntry(_('Import Netherlands Channels in Bouquet'), config.plugins.iptvimport.nl))
        self.list.append(getConfigListEntry(_('Import Polish Channels in Bouquet'), config.plugins.iptvimport.pl))
        self.list.append(getConfigListEntry(_('Import Ex-Yu Channels in Bouquet'), config.plugins.iptvimport.yu))
        self.list.append(getConfigListEntry(_('Import Romania Channels in Bouquet'), config.plugins.iptvimport.ro))
        self.list.append(getConfigListEntry(_('Import US Channels in Bouquet'), config.plugins.iptvimport.us))
        self.list.append(getConfigListEntry(_('Import Arabic Channels in Bouquet'), config.plugins.iptvimport.arabic))
        self.list.append(getConfigListEntry(_('Import Turkey Channels in Bouquet'), config.plugins.iptvimport.turk))
        self.list.append(getConfigListEntry(_('Import Sweden Channels in Bouquet'), config.plugins.iptvimport.sweden))
        self.list.append(getConfigListEntry(_('Import Finland Channels in Bouquet'), config.plugins.iptvimport.finland))
        self.list.append(getConfigListEntry(_('Import Portugal Channels in Bouquet'), config.plugins.iptvimport.portugal))
        self.list.append(getConfigListEntry(_('Import Spain Channels in Bouquet'), config.plugins.iptvimport.spain))
        self.list.append(getConfigListEntry(_('Show IPTV Importer in Extensions'), config.plugins.iptvimport.showinextensions))
        self.list.append(getConfigListEntry(_('Show IPTV Importer in Menu'), config.plugins.iptvimport.showinmenu))
        self.list.append(getConfigListEntry(_('Show IPTV Importer in Plugins'), config.plugins.iptvimport.showinplugins))
        self['config'].list = self.list
        self['config'].l.setList(self.list)
        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Save'))
        self['actions'] = NumberActionMap(['SetupActions', 'ColorActions'], {'ok': self.ok,
         'back': self.cancel,
         'cancel': self.cancel,
         'red': self.cancel,
         'green': self.ok}, -2)

    def ok(self):
        config.plugins.iptvimport.save()
        self.close()

    def cancel(self):
        for x in self['config'].list:
            x[1].cancel()

        self.close()


def setup(session, **kwargs):
    session.open(IPTVImporter)


def main(session, **kwargs):
    if config.plugins.iptvimport.delbouquets.value:
        os.system('rm /etc/enigma2/userbouquet.iptv_*.tv')
        print ('delete old IPTV Bouquets')
        f = file('/etc/enigma2/bouquets.tv', 'r+')
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if 'iptv' not in line:
                f.write(line)

        f.truncate()
        eDVBDB.getInstance().reloadBouquets()
    mapping = json.loads(open('/usr/lib/enigma2/python/Plugins/Extensions/IPTVImporter/mapping.json', 'r').read())
    password = config.plugins.iptvimport.password.value
    username = config.plugins.iptvimport.username.value
    portal = config.plugins.iptvimport.portal.value
    url = 'portal=%s/get.php?username=%s&password=%s&type=dreambox&output=mpegts' % (portal, username, password)
    url = url.replace('portal=', '')
    print (url)
    req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30'})
    try:
        channellist = urllib2.urlopen(req).read().split('\n')
        bouquets = {}
        ref = ''
        channelname = ''
        ctype = 0
        link = ''
        AddPopup(_('Import successful!'), type=MessageBox.TYPE_INFO, timeout=10)
    except:
        AddPopup(_('Connection failed! Aborted!'), type=MessageBox.TYPE_ERROR, timeout=10)
        return []

    for line in channellist:
        if line.startswith('#SERVICE'):
            if line.replace('#SERVICE ', '').startswith('4097'):
                ctype = 1
            else:
                ctype = 0
            ref = line.replace('#SERVICE ', '').split('http')[0]
            link = 'http' + line.replace('#SERVICE ', '').split('http')[1]
        elif line.startswith('#DESCRIPTION'):
            bouquet = ''
            channelname = line.replace('#DESCRIPTION ', '')
            if ctype == 1:
                if config.plugins.iptvimport.vod.value == 'vod':
                    bouquet = 'IPTV VOD'
                if config.plugins.iptvimport.vod.value == 'none':
                    pass
            else:
                bouquet = getBoquet(channelname.strip())
            if bouquet != '' and bouquet is not None:
                channelname = channelname.replace('DE: ', '').replace('UK:', '').replace('AT:', '').replace('CH:', '').replace('VIP DE:', '').replace('VIP ', '').replace('XXX:', '').replace(' (Nur bei Live Spiele) ', '').replace('(Nur bei Live Spiele)', '').replace('DE Sport FHD:', '').replace('DE Sport:', '').replace('DE-Sky:', '').replace('(Freitag/Montag Spiele)', '').replace('SW:', '').strip()
                if bouquet not in bouquets:
                    bouquets[bouquet] = []
                if bouquet == 'IPTV DE' or bouquet == 'IPTV XXX' or bouquet == 'IPTV Sport DE' or bouquet == 'IPTV Bundesliga' or bouquet == 'IPTV Sky DE' or bouquet == 'IPTV Suisse and Austria' or bouquet == 'IPTV Sweden' or bouquet == 'IPTV Finland' or bouquet == 'IPTV Portugal' or bouquet == 'IPTV Spain' or bouquet == 'IPTV Inter' or bouquet == 'IPTV Italy' or bouquet == 'IPTV France' or bouquet == 'IPTV UK' or bouquet == 'IPTV Espana' or bouquet == 'IPTV Netherland' or bouquet == 'IPTV Poland' or bouquet == 'IPTV US' or bouquet == 'IPTV Ex-Yu' or bouquet == 'IPTV Romania' or bouquet == 'IPTV Turkey' or bouquet == 'IPTV Arabic':
                    ref = getref(mapping[bouquet], channelname, ref)
                bouquets[bouquet].append((channelname.strip(), ref.strip(), link.strip()))

    tvbouquets = getTVBouquets()
    for b in bouquets.iterkeys():
        print (b)
        bname = ''
        bref = ''
        bouqname = b.replace(' ', '_').lower() + '__tv'
        for bouquet in tvbouquets:
            if bouquet[1] == b:
                bref = bouquet[0]

        if bref == '':
            serviceHandler = eServiceCenter.getInstance()
            mutableBouquetList = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet')).startEdit()
            chstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.%s.tv" ORDER BY bouquet' % bouqname
            new_bouquet_ref = eServiceReference(chstr)
            if not mutableBouquetList.addService(new_bouquet_ref):
                mutableBouquetList.flushChanges()
                eDVBDB.getInstance().reloadBouquets()
                mutableBouquet = serviceHandler.list(new_bouquet_ref).startEdit()
                if mutableBouquet:
                    mutableBouquet.setListName(b)
                    mutableBouquet.flushChanges()
            eDVBDB.getInstance().reloadBouquets()

    for b in bouquets.iterkeys():
        tvbouquets = getTVBouquets()
        bname = ''
        bref = ''
        bouqname = b.replace(' ', '_').lower() + '__tv'
        for bouquet in tvbouquets:
            if bouquet[1] == b:
                bref = bouquet[0]

        serviceHandler = eServiceCenter.getInstance()
        bouquetlist = getServiceList(str(bref))
        mutableBouquet = serviceHandler.list(eServiceReference(bref)).startEdit()
        for serviceref, servicename in bouquetlist:
            mutableBouquet.removeService(eServiceReference(serviceref))

        mutableBouquet.flushChanges()
        for ch in bouquets[b]:
            try:
                print ('Adding %s with Ref: %s and Link: %s') % ch
                channelref = str(ch[1]) + str(ch[2])
                newchannel = eServiceReference(channelref)
                newchannel.setName(str(ch[0]))
                mutableBouquet = serviceHandler.list(eServiceReference(bref)).startEdit()
                mutableBouquet.addService(newchannel)
                mutableBouquet.flushChanges()
            except Exception:
                pass

    return None


def getref(mapping, channelname, ref):
    print (channelname)
    print (ref)
    if str(channelname) in mapping:
        return mapping[str(channelname)]
    else:
        return ref


def getBoquet(channelname):
    if config.plugins.iptvimport.xxx.value == 'xxx':
        if channelname.startswith('XXX: '):
            return 'IPTV XXX'
    if config.plugins.iptvimport.xxx.value == 'inter':
        if channelname.startswith('XXX: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.xxx.value == 'none':
        pass
    if config.plugins.iptvimport.buli.value == 'buli':
        if channelname.startswith('DE Sport: ') and ' Bundesliga ' in channelname:
            return 'IPTV Bundesliga'
        if channelname.startswith('VIP DE: ') and ' Bundesliga ' in channelname:
            return 'IPTV Bundesliga'
        if channelname.startswith('DE: ') and ' Bundesliga ' in channelname:
            return 'IPTV Bundesliga'
        if channelname.startswith('DE Sport FHD:') and ' Bundesliga ' in channelname:
            return 'IPTV Bundesliga'
    if config.plugins.iptvimport.buli.value == 'sport':
        if channelname.startswith('DE Sport:') and 'Bundesliga' in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('DE: ') and 'Bundesliga' in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('VIP DE: ') and 'Bundesliga' in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('DE Sport FHD:') and 'Bundesliga' in channelname:
            return 'IPTV Sport DE'
    if config.plugins.iptvimport.buli.value == 'none':
        pass
    if config.plugins.iptvimport.sportde.value == 'sport':
        if channelname.startswith('DE: ') and 'DAZN' in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('DE: ') and 'Telekom' in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('DE: ') and 'Sport' in channelname and 'Bundesliga' not in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('VIP DE: ') and 'Sport' in channelname and 'Bundesliga' not in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('DE Sport FHD: ') and 'Bundesliga' not in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('DE: ') and 'Eurosport' in channelname:
            return 'IPTV Sport DE'
        if channelname.startswith('DE Sport: '):
            return 'IPTV Sport DE'
    if config.plugins.iptvimport.sportde.value == 'de':
        if channelname.startswith('DE: ') and 'DAZN' in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE: ') and 'Telekom' in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE: ') and 'Eurosport' in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE: ') and 'Sport' in channelname and 'Bundesliga' not in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE Sport FHD: ') and 'Bundesliga' not in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE: ') or channelname.startswith('VIP DE:  '):
            return 'IPTV DE'
    if config.plugins.iptvimport.sportde.value == 'none':
        pass
    if config.plugins.iptvimport.skyde.value == 'sky':
        if channelname.startswith('DE: ') and 'Sky ' in channelname and 'Bundesliga' not in channelname and 'BundesLiga' not in channelname and ' Sports ' not in channelname and ' Sport ' not in channelname:
            return 'IPTV Sky DE'
        if channelname.startswith('VIP DE: ') and 'Sky ' in channelname and 'Bundesliga' not in channelname and 'BundesLiga' not in channelname and ' Sports ' not in channelname and ' Sport ' not in channelname:
            return 'IPTV Sky DE'
        if channelname.startswith('VIP DE: ') and 'Film Club ' in channelname and 'Bundesliga' not in channelname and 'BundesLiga' not in channelname and ' Sports ' not in channelname and ' Sport ' not in channelname:
            return 'IPTV Sky DE'
        if channelname.startswith('DE: ') and 'SKY ' in channelname and 'Bundesliga' not in channelname and 'BundesLiga' not in channelname and ' Sports ' not in channelname and ' Sport ' not in channelname:
            return 'IPTV Sky DE'
        if channelname.startswith('VIP DE: ') and 'SKY ' in channelname and 'Bundesliga' not in channelname and 'BundesLiga' not in channelname and ' Sports ' not in channelname and ' Sport ' not in channelname:
            return 'IPTV Sky DE'
    if config.plugins.iptvimport.skyde.value == 'deutsch':
        if channelname.startswith('DE: ') and 'Sky' in channelname and 'Bundesliga' not in channelname and 'BundesLiga' not in channelname and ' Sports ' not in channelname and ' Sport ' not in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE: ') and 'SKY' in channelname and 'Bundesliga' not in channelname and 'BundesLiga' not in channelname and ' Sports ' not in channelname and ' Sport ' not in channelname:
            return 'IPTV DE'
    if config.plugins.iptvimport.skyde.value == 'none':
        pass
    if config.plugins.iptvimport.deutsch.value == 'deutsch':
        if channelname.startswith('DE: ') and ' Sky ' not in channelname and ' SRF ' not in channelname and ' ORF ' not in channelname and ' SKY ' not in channelname and 'Bundesliga' not in channelname and ' Sport ' not in channelname and ' Eurosport ' not in channelname:
            return 'IPTV DE'
    if config.plugins.iptvimport.deutsch.value == 'inter':
        if channelname.startswith('DE: ') and ' Sky ' not in channelname and ' SRF ' not in channelname and ' ORF ' not in channelname and ' SKY ' not in channelname and 'Bundesliga' not in channelname and ' Sport ' not in channelname and ' Eurosport ' not in channelname:
            return 'IPTV Inter'
    if config.plugins.iptvimport.deutsch.value == 'none':
        pass
    if config.plugins.iptvimport.other.value == 'deutsch':
        if channelname.startswith('SW: ') or 'Austria' in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE: ') and ' SRF ' in channelname:
            return 'IPTV DE'
        if channelname.startswith('DE: ') and ' ORF ' in channelname:
            return 'IPTV DE'
    if config.plugins.iptvimport.other.value == 'extra':
        if channelname.startswith('SW: ') or 'Austria' in channelname:
            return 'IPTV Suisse and Austria'
        if channelname.startswith('AT: '):
            return 'IPTV Suisse and Austria'
        if channelname.startswith('CH: '):
            return 'IPTV Suisse and Austria'
        if channelname.startswith('VIP CH: '):
            return 'IPTV Suisse and Austria'
        if channelname.startswith('VIP AT: '):
            return 'IPTV Suisse and Austria'
        if channelname.startswith('DE: ') and ' SRF ' in channelname:
            return 'IPTV Suisse and Austria'
        if channelname.startswith('DE: ') and ' ORF ' in channelname:
            return 'IPTV Suisse and Austria'
    if config.plugins.iptvimport.other.value == 'none':
        pass
    if config.plugins.iptvimport.italy.value == 'italy':
        if channelname.startswith('IT: '):
            return 'IPTV Italy'
    if config.plugins.iptvimport.italy.value == 'inter':
        if channelname.startswith('IT: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.italy.value == 'none':
        pass
    if config.plugins.iptvimport.france.value == 'france':
        if channelname.startswith('FR: '):
            return 'IPTV France'
    if config.plugins.iptvimport.france.value == 'inter':
        if channelname.startswith('FR: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.france.value == 'none':
        pass
    if config.plugins.iptvimport.uk.value == 'uk':
        if channelname.startswith('UK: '):
            return 'IPTV UK'
    if config.plugins.iptvimport.uk.value == 'inter':
        if channelname.startswith('UK: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.uk.value == 'none':
        pass
    if config.plugins.iptvimport.spain.value == 'spain':
        if channelname.startswith('ES: '):
            return 'IPTV Espana'
    if config.plugins.iptvimport.spain.value == 'inter':
        if channelname.startswith('ES: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.spain.value == 'none':
        pass
    if config.plugins.iptvimport.nl.value == 'nl':
        if channelname.startswith('NL: '):
            return 'IPTV Netherland'
    if config.plugins.iptvimport.nl.value == 'inter':
        if channelname.startswith('NL: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.nl.value == 'none':
        pass
    if config.plugins.iptvimport.pl.value == 'pl':
        if channelname.startswith('PL: '):
            return 'IPTV Poland'
    if config.plugins.iptvimport.pl.value == 'inter':
        if channelname.startswith('PL: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.pl.value == 'none':
        pass
    if config.plugins.iptvimport.yu.value == 'yu':
        if channelname.startswith('Ex-Yu: '):
            return 'IPTV Ex-Yu'
    if config.plugins.iptvimport.yu.value == 'inter':
        if channelname.startswith('Ex-Yu: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.yu.value == 'none':
        pass
    if config.plugins.iptvimport.ro.value == 'ro':
        if channelname.startswith('RO: '):
            return 'IPTV Romania'
    if config.plugins.iptvimport.ro.value == 'inter':
        if channelname.startswith('RO: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.ro.value == 'none':
        pass
    if config.plugins.iptvimport.us.value == 'us':
        if channelname.startswith('US: '):
            return 'IPTV US'
        if channelname.startswith('USA: '):
            return 'IPTV US'
    if config.plugins.iptvimport.us.value == 'inter':
        if channelname.startswith('US: '):
            return 'IPTV Inter'
        if channelname.startswith('USA: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.us.value == 'none':
        pass
    if config.plugins.iptvimport.arabic.value == 'arabic':
        if channelname.startswith('AR: '):
            return 'IPTV Arabic'
    if config.plugins.iptvimport.arabic.value == 'inter':
        if channelname.startswith('AR: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.arabic.value == 'none':
        pass
    if config.plugins.iptvimport.turk.value == 'turkey':
        if channelname.startswith('TR: '):
            return 'IPTV Turkey'
    if config.plugins.iptvimport.turk.value == 'inter':
        if channelname.startswith('TR: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.turk.value == 'none':
        pass
    if config.plugins.iptvimport.sweden.value == 'sweden':
        if channelname.startswith('SWE: '):
            return 'IPTV Sweden'
    if config.plugins.iptvimport.sweden.value == 'inter':
        if channelname.startswith('SWE: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.sweden.value == 'none':
        pass
    if config.plugins.iptvimport.finland.value == 'finland':
        if channelname.startswith('FIN: '):
            return 'IPTV Finland'
    if config.plugins.iptvimport.finland.value == 'inter':
        if channelname.startswith('FIN: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.finland.value == 'none':
        pass
    if config.plugins.iptvimport.portugal.value == 'portugal':
        if channelname.startswith('PT: '):
            return 'IPTV Portugal'
    if config.plugins.iptvimport.portugal.value == 'inter':
        if channelname.startswith('PT: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.portugal.value == 'none':
        pass
    if config.plugins.iptvimport.spain.value == 'spain':
        if channelname.startswith('ES: '):
            return 'IPTV Spain'
    if config.plugins.iptvimport.spain.value == 'inter':
        if channelname.startswith('ES: '):
            return 'IPTV Inter'
    if config.plugins.iptvimport.spain.value == 'none':
        pass


def getServiceList(ref):
    root = eServiceReference(str(ref))
    serviceHandler = eServiceCenter.getInstance()
    return serviceHandler.list(root).getContent('SN', True)


def getTVBouquets():
    return getServiceList(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')


def startMenu(menuid):
    if menuid == 'scan':
        return [(_('IPTV Import'),
          main,
          'startimport',
          70)]
    else:
        return []


extlist = PluginDescriptor(name='IPTV Import', description='IPTV Import', where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
menulist = PluginDescriptor(name='IPTV Import', description='IPTV Import', where=PluginDescriptor.WHERE_MENU, fnc=startMenu)
if getDesktop(0).size().width() <= 1280:
    pluginlist = PluginDescriptor(name='IPTV Import', description='IPTV Import', where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main)
else:
    pluginlist = PluginDescriptor(name='IPTV Import', description='IPTV Import', where=PluginDescriptor.WHERE_PLUGINMENU, icon='pluginfhd.png', fnc=main)

def Plugins(**kwargs):
    result = [PluginDescriptor(name='IPTV Import Edit', description='IPTV Import Edit', where=PluginDescriptor.WHERE_PLUGINMENU, icon='edit.png', fnc=setup)]
    if config.plugins.iptvimport.showinextensions.value:
        result.append(extlist)
    if config.plugins.iptvimport.showinplugins.value:
        result.append(pluginlist)
    if config.plugins.iptvimport.showinmenu.value:
        result.append(menulist)
    return result