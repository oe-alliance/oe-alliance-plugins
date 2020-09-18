from Components.NimManager import nimmanager
from enigma import eDVBFrontendParametersSatellite

class TransponderFiltering:
	def getKnownTransponders(self, pos):
		tlist = []
		list = nimmanager.getTransponders(pos)
		for x in list:
			if x[0] == 0:
				parm = eDVBFrontendParametersSatellite()
				parm.frequency = x[1]
				parm.symbol_rate = x[2]
				parm.polarisation = x[3]
				parm.fec = x[4]
				parm.inversion = x[7]
				parm.orbital_position = pos
				parm.system = x[5]
				parm.modulation = x[6]
				parm.rolloff = x[8]
				parm.pilot = x[9]
				if len(x) > 12:
					parm.is_id = x[10]
					parm.pls_mode = x[11]
					parm.pls_code = x[12]
					if hasattr(parm, "t2mi_plp_id") and len(x) > 13:
						parm.t2mi_plp_id = x[13]
						if hasattr(parm, "t2mi_pid") and len(x) > 14:
							parm.t2mi_pid = x[14]
				tlist.append(parm)
		return tlist

	def syncWithKnownTransponders(self, tplist, knowntp):
		tolerance = 5
		multiplier = 1000
		x = 0
		for t in tplist:
			found = False
			for k in knowntp:
				if hasattr(t, "t2mi_plp_id"):
					t2mi_check = t.t2mi_plp_id == eDVBFrontendParametersSatellite.No_T2MI_PLP_Id or t.t2mi_plp_id == k.t2mi_plp_id
				else:
					t2mi_check = True # skip check
				if (t.polarisation % 2) == (k.polarisation % 2) and \
					abs(t.frequency - k.frequency) < (tolerance*multiplier) and \
					abs(t.symbol_rate - k.symbol_rate) < (tolerance*multiplier) and \
					t.is_id == k.is_id and t.pls_code == k.pls_code and t.pls_mode == k.pls_mode and \
					t2mi_check:
					tplist[x] = k
					found = True
					break
			if not found:
				self.tweakSR(t)
			x += 1
		return tplist

	def removeDuplicateTransponders(self, tplist):
		new_tplist = []
		tolerance = 5
		multiplier = 1000
		for i in range(len(tplist)):
			t = tplist[i]
			found = False
			for k in tplist[i+1:]:
				if hasattr(t, "t2mi_plp_id"):
					t2mi_check = t.t2mi_plp_id == eDVBFrontendParametersSatellite.No_T2MI_PLP_Id or t.t2mi_plp_id == k.t2mi_plp_id
				else:
					t2mi_check = True # skip check
				if (t.polarisation % 2) == (k.polarisation % 2) and \
					abs(t.frequency - k.frequency) < (tolerance*multiplier) and \
					abs(t.symbol_rate - k.symbol_rate) < (tolerance*multiplier) and \
					t.is_id == k.is_id and t.pls_code == k.pls_code and t.pls_mode == k.pls_mode and \
					t2mi_check:
					found = True
					break
			if not found:
				new_tplist.append(t)
		return new_tplist

	def removeKnownTransponders(self, tplist, knowntp):
		new_tplist = []
		tolerance = 5
		multiplier = 1000
		for t in tplist:
			isnt_known = True
			for k in knowntp:
				if hasattr(t, "t2mi_plp_id"):
					t2mi_check = t.t2mi_plp_id == eDVBFrontendParametersSatellite.No_T2MI_PLP_Id or t.t2mi_plp_id == k.t2mi_plp_id
				else:
					t2mi_check = True # skip check
				if (t.polarisation % 2) == (k.polarisation % 2) and \
					abs(t.frequency - k.frequency) < (tolerance*multiplier) and \
					abs(t.symbol_rate - k.symbol_rate) < (tolerance*multiplier) and \
					t.is_id == k.is_id and t.pls_code == k.pls_code and t.pls_mode == k.pls_mode and \
					t2mi_check:
					isnt_known = False
					break
			if isnt_known:
				self.tweakSR(t)
				new_tplist.append(t)
		return new_tplist

	def tweakSR(self, t):
		pull_sr_max = 4 
		lowest_sr_to_adjust = 4996
		multiplier = 1000
		# Cosmetic: tweak symbol rates to nearest multiple of 100 if this is closer than "pull_sr_max" away and t.symbol_rate > lowest_sr_to_adjust
		if t.symbol_rate > (lowest_sr_to_adjust*multiplier) and abs(t.symbol_rate - int(round(t.symbol_rate, -5))) <= (pull_sr_max*multiplier):
			t.symbol_rate = int(round(t.symbol_rate, -5))

	def filterOffAdjacentSatellites(self, tplist, pos, degrees):
		neighbours = []
		tenths_of_degrees = degrees * 10
		for sat in nimmanager.satList:
			if sat[0] != pos and self.positionDiff(pos, sat[0]) <= tenths_of_degrees:
				neighbours.append(sat[0])
		
		for neighbour in neighbours:
			tplist = self.removeKnownTransponders(tplist, self.getKnownTransponders(neighbour))
		return tplist

	def positionDiff(self, pos1, pos2):
		diff = pos1 - pos2
		return min(abs(diff % 3600), 3600 - abs(diff % 3600))
