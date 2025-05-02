from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo
from .PiconsUpdaterView import PiconsUpdaterView
from . import getConfigSizeList, getConfigBackgroundList, DEFAULT_PICON_PATH, ALTERN_PICON_PATH, _  # for localized messages


def getConfigPathList():
	ChoicePath = []
	for path in ALTERN_PICON_PATH:
		if len(path) == 2:
			ChoicePath.append(path)
		else:
			ChoicePath.append((path, _(path)))

	return ChoicePath


def main(session, **kwargs):
	config.plugins.PiconsUpdater = ConfigSubsection()
	config.plugins.PiconsUpdater.source = ConfigSelection(
		default=0,
		choices=[
			(0, "Default"),
			(1, "Lululla")
		]
	)
	config.plugins.PiconsUpdater.piconsPath = ConfigSelection(default=DEFAULT_PICON_PATH, choices=getConfigPathList())
	config.plugins.PiconsUpdater.piconsPath.lastValue = config.plugins.PiconsUpdater.piconsPath.getValue()
	config.plugins.PiconsUpdater.size = ConfigSelection(default='220x132', choices=getConfigSizeList())
	config.plugins.PiconsUpdater.background = ConfigSelection(default='', choices=getConfigBackgroundList())
	config.plugins.PiconsUpdater.mirror_effect = ConfigYesNo(default=False)
	config.plugins.PiconsUpdater.exclude_iptv = ConfigYesNo(default=True)
	config.plugins.PiconsUpdater.exclude_radio = ConfigYesNo(default=True)
	config.plugins.PiconsUpdater.rescanIntoTmp = ConfigYesNo(default=False)
	# config.plugins.PiconsUpdater.getfiltername = ConfigYesNo(default=False)
	config.plugins.PiconsUpdater.clearpicons = ConfigYesNo(default=False)
	session.open(PiconsUpdaterView)


def Plugins(**kwargs):
	pluginList = [PluginDescriptor(name='PiconsUpdater', description=_('Download Picons for your channellist (favourites)'), where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main, needsRestart=False)]
	return pluginList
