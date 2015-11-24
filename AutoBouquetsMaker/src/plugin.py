# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Components.NimManager import nimmanager

from menu import AutoBouquetsMaker_Menu
from scanner.main import AutoBouquetsMakerautostart, AutoBouquetsMaker

from Components.config import config, configfile, ConfigSubsection, ConfigYesNo, ConfigSelection, ConfigText, ConfigNumber, NoSave, ConfigClock, getConfigListEntry
config.autobouquetsmaker = ConfigSubsection()
config.autobouquetsmaker.level = ConfigSelection(default = "simple", choices = [("simple", _("simple")), ("expert", _("expert"))])
config.autobouquetsmaker.providers = ConfigText("", False)
config.autobouquetsmaker.bouquetsorder = ConfigText("", False)
config.autobouquetsmaker.schedule = ConfigYesNo(default = False)
config.autobouquetsmaker.scheduletime = ConfigClock(default = 0) # 1:00
config.autobouquetsmaker.repeattype = ConfigSelection(default = "daily", choices = [("daily", _("Daily")), ("weekly", _("Weekly")), ("monthly", _("30 Days"))])
config.autobouquetsmaker.retry = ConfigNumber(default = 30)
config.autobouquetsmaker.retrycount = NoSave(ConfigNumber(default = 0))
config.autobouquetsmaker.nextscheduletime = NoSave(ConfigNumber(default = 0))
config.autobouquetsmaker.lastlog = ConfigText(default=' ', fixed_size=False)
config.autobouquetsmaker.keepallbouquets = ConfigYesNo(default = True)
config.autobouquetsmaker.keepbouquets = ConfigText("", False)
config.autobouquetsmaker.hidesections = ConfigText("", False)
config.autobouquetsmaker.addprefix = ConfigYesNo(default = False)
config.autobouquetsmaker.extensions = ConfigYesNo(default = False)
config.autobouquetsmaker.placement = ConfigSelection(default = "top", choices = [("top", _("Top")), ("bottom", _("Bottom"))])
config.autobouquetsmaker.skipservices = ConfigYesNo(default = True)
config.autobouquetsmaker.showextraservices = ConfigYesNo(default = False)
config.autobouquetsmaker.extra_debug = ConfigYesNo(default = False)
config.autobouquetsmaker.FTA_only = ConfigText("", False)

def main(session, **kwargs):
	session.open(AutoBouquetsMaker_Menu)

def startscan(session, **kwargs):
	session.open(AutoBouquetsMaker)

def AutoBouquetsMakerSetup(menuid, **kwargs):
	if menuid == "scan":
		return [(_("AutoBouquetsMaker"), main, "autobouquetsmakermaker", 10)]
	else:
		return []

def Plugins(**kwargs):
	plist = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=AutoBouquetsMakerautostart)]
	plist.append(PluginDescriptor(name=_("AutoBouquetsMaker"), description="Scan and create bouquets.", where = PluginDescriptor.WHERE_MENU, fnc=AutoBouquetsMakerSetup))
	if config.autobouquetsmaker.extensions.getValue():
		plist.append(PluginDescriptor(name=_("AutoBouquetsMaker Scanner"), description="Scan and create bouquets.", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=startscan))
	return plist
