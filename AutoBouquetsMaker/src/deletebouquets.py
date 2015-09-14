# -*- coding: utf-8 -*-
# for localized messages
from . import _

from enigma import eDVBDB
from Screens.MessageBox import MessageBox
from scanner.bouquetsreader import BouquetsReader
from scanner.bouquetswriter import BouquetsWriter

class AutoBouquetsMaker_DeleteBouquets():

	ABM_BOUQUET_PREFIX = "userbouquet.abm."

	def __init__(self, res):
		path = "/etc/enigma2"
		if res:
			bouquets = BouquetsReader().getBouquetsList(path)
			currentBouquets = {}
			currentBouquets["tv"] = []
			currentBouquets["radio"] = []
			bouquetsToKeep = {}
			bouquetsToKeep["tv"] = []
			bouquetsToKeep["radio"] = []
			for bouquet_type in ["tv", "radio"]:
				for bouquet in bouquets[bouquet_type]:
					 currentBouquets[bouquet_type].append(bouquet["filename"])
					 if bouquet["filename"][:len(self.ABM_BOUQUET_PREFIX)] != self.ABM_BOUQUET_PREFIX:
					 	bouquetsToKeep[bouquet_type].append(bouquet["filename"])
			BouquetsWriter().buildBouquetsIndex(path, [], None, bouquetsToKeep, currentBouquets, None, None)
			eDVBDB.getInstance().reloadServicelist()
			eDVBDB.getInstance().reloadBouquets()
			
class AutoBouquetsMaker_DeleteMsg(MessageBox):
	def __init__(self, session):
		MessageBox.__init__(self, session, _("Are you sure you want to remove all bouquets created by ABM?"), MessageBox.TYPE_YESNO, default=False)
		self.skinName = "MessageBox"
	
		
