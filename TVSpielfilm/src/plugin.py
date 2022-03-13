#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from Components.config import config, configfile, ConfigDirectory, ConfigInteger, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigText, getConfigListEntry, ConfigYesNo
from Tools.Directories import fileExists
from Plugins.Plugin import PluginDescriptor
from .ui import tvEvent, tvJetzt, tvMain, TVSlog
from .util import DESKTOP_WIDTH

config.plugins.tvspielfilm = ConfigSubsection()
if DESKTOP_WIDTH > 1280:
    config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='FHD', choices=[('FHD', 'FullHD (1920x1080)'), ('HD', 'HD (1280x720)')])
else:
    config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='HD', choices=[('HD', 'HD (1280x720)')])
config.plugins.tvspielfilm.position = ConfigInteger(40, (0, 160))
config.plugins.tvspielfilm.font_size = ConfigSelection(default='normal', choices=[('large', 'Groß'), ('normal', 'Normal'), ('small', 'Klein')])
config.plugins.tvspielfilm.meintvs = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.login = ConfigText(default='', fixed_size=False)
config.plugins.tvspielfilm.password = ConfigPassword(default='', fixed_size=False)
config.plugins.tvspielfilm.encrypt = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.picon = ConfigSelection(default='standard', choices=[('plugin', 'vom Plugin'), ('standard', 'Standard'), ('own', 'Eigener Ordner')])
config.plugins.tvspielfilm.piconfolder = ConfigDirectory(default='/usr/share/enigma2/picon/')
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
config.plugins.tvspielfilm.maxsearch = ConfigSelection(default='50', choices=[('20', '20'), ('50', '50'), ('100', '100'), ('150', '150'), ('200', '200')])
config.plugins.tvspielfilm.maxgenre = ConfigSelection(default='50', choices=[('20', '20'), ('50', '50'), ('100', '100'), ('150', '150'), ('200', '200')])
config.plugins.tvspielfilm.autotimer = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.ytresolution = ConfigSelection(default='best', choices=[('best', 'bestmöglich'), ('best[height<=?480]', 'max. 480p')])
config.plugins.tvspielfilm.debuglog = ConfigYesNo(default=False)
config.plugins.tvspielfilm.logtofile = ConfigYesNo(default=False)
HIDEFLAG = True
ALPHA = '/proc/stb/video/alpha' if fileExists('/proc/stb/video/alpha') else None
if not ALPHA:
    print('Alphachannel not found! Hide/show-function (=blue button) is disabled')
    TVSlog('Alphachannel not found! Hide/show-function (=blue button) is disabled')


def main(session, **kwargs):
    session.open(tvMain)


def mainjetzt(session, **kwargs):
    session.open(tvJetzt, 'https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html')


def mainprime(session, **kwargs):
    session.open(tvJetzt, 'https://www.tvspielfilm.de/tv-programm/sendungen/abends.html')


def mainevent(session, **kwargs):
    session.open(tvEvent)


def Plugins(**kwargs):
    return [PluginDescriptor(name='TV Spielfilm', description='TV Spielfilm', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='TVmain.png', fnc=main),
            PluginDescriptor(name='TV Spielfilm 20:15', description='TV Spielfilm Prime Time', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='TV2015.png', fnc=mainprime),
            PluginDescriptor(name='TV Spielfilm Jetzt', description='TV Spielfilm Jetzt im TV', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='TVjetzt.png', fnc=mainjetzt),
            PluginDescriptor(name='TV Spielfilm EventView', description='TV Spielfilm EventView', where=[PluginDescriptor.WHERE_EVENTINFO], icon='TVevent.png', fnc=mainevent)]
