import os

class L4Lelement:
	List = {}
	Refresh = False
	MAX_W = [0, 0, 0]
	MAX_H = [0, 0, 0]
	Screen = ''
	LCD = ''
	Hold = False

	def __init__(self):
		self.session = None

	def add(self, element, para):
		print 'Add', element, para
		if '%' in para.get('Align', ''):
			para['Align'] = ('0000' + para['Align'].replace('%', '00'))[-4:]
		if para.get('Value', None) is not None:
			para['Value'] = min(max(int(para['Value']), 0), 100)
		L4Lelement.List[element] = para

	def delete(self, element):
		print 'Del', element
		if L4Lelement.List.get(element, None) is not None:
			del L4Lelement.List[element]

	def show(self):
		print L4Lelement.List

	def get(self, element = None):
		if element == None:
			return L4Lelement.List
		else:
			return L4Lelement.List.get(element, {})

	def web(self, EX):
		exec "self.add('%s)" % EX.replace(',', "',", 1)

	def getResolution(self, LCD):
		if LCD < 1 or LCD > 3:
			return (0, 0)
		return (L4Lelement.MAX_W[LCD - 1], L4Lelement.MAX_H[LCD - 1])

	def setResolution(self, LCD, MW, MH):
		L4Lelement.MAX_W[LCD - 1] = MW
		L4Lelement.MAX_H[LCD - 1] = MH

	def resetRefresh(self):
		L4Lelement.Refresh = False

	def setRefresh(self):
		L4Lelement.Refresh = True

	def getRefresh(self):
		return L4Lelement.Refresh

	def getHold(self):
		return L4Lelement.Hold

	def setHold(self, H):
		L4Lelement.Hold = H

	def getScreen(self):
		return L4Lelement.Screen

	def setScreen(self, S, Lcd = '', Hold = False):
		L4Lelement.Screen = str(S)
		L4Lelement.LCD = Lcd
		L4Lelement.Hold = Hold
		L4Lelement.Refresh = True

	def getLcd(self):
		return L4Lelement.LCD


def L4LVtest(VV):
	L4Linfo = '/%s/lib/opkg/info/enigma2-plugin-extensions-lcd4linux.control'
	O = ''
	if os.path.exists(L4Linfo % 'var'):
		O = 'var'
	elif os.path.exists(L4Linfo % 'usr'):
		O = 'usr'
	if O != '':
		try:
			f = open(L4Linfo % O)
			B = f.readline()
			O = f.readline().strip().split()[1].startswith(VV[1:])
			f.close()
		except:
			pass

	return O