# -*- coding: utf-8 -*-
from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo
from .PiconsUpdaterView import PiconsUpdaterView
from . import _, getConfigSizeList, getConfigBackgroundList, DEFAULT_PICON_PATH

def main(session, **kwargs):
    config.plugins.PiconsUpdater = ConfigSubsection()
    config.plugins.PiconsUpdater.piconsPath = ConfigText(default=DEFAULT_PICON_PATH, fixed_size=False, visible_width=30)
    config.plugins.PiconsUpdater.piconsPath.lastValue = config.plugins.PiconsUpdater.piconsPath.getValue()
    config.plugins.PiconsUpdater.size = ConfigSelection(default='220x132', choices=getConfigSizeList())
    config.plugins.PiconsUpdater.background = ConfigSelection(default='', choices=getConfigBackgroundList())
    config.plugins.PiconsUpdater.mirror_effect = ConfigYesNo(default=False)
    session.open(PiconsUpdaterView)


def Plugins(**kwargs):
    pluginList = [PluginDescriptor(name='PiconsUpdater', description=_('Download Picons for your channellist (favourites)'), where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main, needsRestart=False)]
    return pluginList
