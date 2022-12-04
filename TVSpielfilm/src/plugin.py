#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from glob import glob
from os.path import isfile

from Components.config import config, ConfigDirectory, ConfigInteger, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigText, ConfigYesNo
from Plugins.Plugin import PluginDescriptor
from .ui import TVSmakeServiceFile, TVSProgrammView, TVSJetztView, TVSEvent, TVSMain, TVSlog, SERVICEFILE
from .util import DESKTOP_WIDTH, PLUGINPATH, PICONPATH

config.plugins.tvspielfilm = ConfigSubsection()
if DESKTOP_WIDTH > 1280:
	config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='FHD', choices=[('FHD', 'FullHD (1920x1080)'), ('HD', 'HD (1280x720)')])
else:
	config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='HD', choices=[('HD', 'HD (1280x720)')])
config.plugins.tvspielfilm.position = ConfigInteger(40, (0, 160))
config.plugins.tvspielfilm.font = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
if config.plugins.tvspielfilm.font.value == 'yes':
    from enigma import addFont
    try:
        addFont(PLUGINPATH + 'font/Roboto-Regular.ttf', 'Regular', 100, False)
    except Exception as ex:
        addFont(PLUGINPATH + 'font/Roboto-Regular.ttf', 'Regular', 100, False, 0)
config.plugins.tvspielfilm.font_size = ConfigSelection(default='normal', choices=[('large', 'Groß'), ('normal', 'Normal'), ('small', 'Klein')])
config.plugins.tvspielfilm.meintvs = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.login = ConfigText(default='', fixed_size=False)
config.plugins.tvspielfilm.password = ConfigPassword(default='', fixed_size=False)
config.plugins.tvspielfilm.encrypt = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.picon = ConfigSelection(default='standard', choices=[('plugin', 'vom Plugin'), ('standard', 'Standard'), ('own', 'Eigener Ordner')])
config.plugins.tvspielfilm.piconfolder = ConfigDirectory(default=PICONPATH)
fullpaths = glob(PLUGINPATH + 'pics/FHD/selectors/selector_*.png') if config.plugins.tvspielfilm.plugin_size == 'FHD' else glob(PLUGINPATH + 'pics/HD/selectors/selector_*.png')
selectors = list(set([i[i.rfind('_') + 1:].replace('.png', '') if '_' in i else None for i in fullpaths]))
config.plugins.tvspielfilm.selectorcolor = ConfigSelection(default='Standard', choices=selectors)
config.plugins.tvspielfilm.tipps = ConfigSelection(default='yes', choices=[('no', 'Gruene Taste im Startmenue'), ('yes', 'Beim Start des Plugins'), ('false', 'Deaktiviert')])
config.plugins.tvspielfilm.primetime = ConfigSelection(default='primetime', choices=[('primetime', 'Primetime'), ('now', 'Aktuelle Zeit')])
config.plugins.tvspielfilm.eventview = ConfigSelection(default='list', choices=[('list', 'Programmliste'), ('info', 'Sendungsinfo')])
config.plugins.tvspielfilm.genreinfo = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
config.plugins.tvspielfilm.zapexit = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.maxsearch = ConfigSelection(default='2', choices=[('1', '1'), ('2', '2'), ('5', '5'), ('10', '10'), ('20', '20')])
config.plugins.tvspielfilm.maxgenre = ConfigSelection(default='2', choices=[('1', '1'), ('2', '2'), ('5', '5'), ('10', '10'), ('20', '20')])
config.plugins.tvspielfilm.autotimer = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.ytresolution = ConfigSelection(default='best', choices=[('best', 'bestmöglich'), ('best[height<=?480]', 'max. 480p')])
config.plugins.tvspielfilm.debuglog = ConfigYesNo(default=False)
config.plugins.tvspielfilm.logtofile = ConfigYesNo(default=False)
HIDEFLAG = True
ERRORMSG = 'Keine Bouquets gefunden! Zwecks Bouquetimport starte zuerst das TVS-Hauptplugin.'
ALPHA = '/proc/stb/video/alpha' if isfile('/proc/stb/video/alpha') else None
if not ALPHA:
	print('Alphachannel not found! Hide/show-function (=blue button) is disabled')
	TVSlog('Alphachannel not found! Hide/show-function (=blue button) is disabled')


def checkService(session, screen, link=None):
	def callback():
		if link:
			if link == "MAIN":
				session.open(TVSEvent)
			else:
				session.open(screen, link)
		else:
			session.open(screen)

	if isfile(SERVICEFILE):
		callback()
	else:
		session.openWithCallback(callback, TVSmakeServiceFile)


def main(session, **kwargs):
	checkService(session, TVSMain)


def mainjetzt(session, **kwargs):
	checkService(session, TVSJetztView, 'https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html')


def mainprime(session, **kwargs):
	checkService(session, TVSJetztView, 'https://www.tvspielfilm.de/tv-programm/sendungen/abends.html')


def mainlate(session, **kwargs):
	checkService(session, TVSJetztView, 'https://www.tvspielfilm.de/tv-programm/sendungen/fernsehprogramm-nachts.html')


def mainevent(session, **kwargs):
	checkService(session, TVSProgrammView, "MAIN")


def Plugins(**kwargs):
	return [PluginDescriptor(name='TV Spielfilm', description='TV Spielfilm', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TVmain.png', fnc=main),
			PluginDescriptor(name='TV Spielfilm 20:15', description='TV Spielfilm Prime Time', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TV2015.png', fnc=mainprime),
			PluginDescriptor(name='TV Spielfilm 22:00', description='TV Spielfilm LateNight', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TVlate.png', fnc=mainlate),
			PluginDescriptor(name='TV Spielfilm Jetzt', description='TV Spielfilm Jetzt im TV', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TVjetzt.png', fnc=mainjetzt),
			PluginDescriptor(name='TV Spielfilm EventView', description='TV Spielfilm EventView', where=[PluginDescriptor.WHERE_EVENTINFO], icon='./pics/FHD/logos/TVevent.png', fnc=mainevent)]
