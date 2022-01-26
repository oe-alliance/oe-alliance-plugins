##############################################################################
#	(c)2021 by Oberhesse (oh20@gmx.de)
#	Creative Commons CC BY-NC-SA 3.0 License
#	Check the file "LICENSE" for more informations
##############################################################################

def umlautS(s):
	repAou = [('_ae', '\xc3\xa4'), ('_oe', '\xc3\xb6'), ('_ue', '\xc3\xbc'), ('_Ae', '\xc3\x84'), ('_Oe', '\xc3\x96'), ('_Ue', '\xc3\x9c'), ('_ss', '\xc3\x9f')]
	for ch in repAou:
		s = s.replace(ch[0], ch[1])
	return s


def _(s): return umlautS(s)
