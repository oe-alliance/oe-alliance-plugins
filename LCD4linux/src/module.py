import os

class L4Lelement:
	List = {}

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