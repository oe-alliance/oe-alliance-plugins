# -*- coding: utf-8 -*-
#
#	(c)2022 by Oberhesse (contact through www.vuplus-support.org)
#	Creative Commons CC BY-NC-SA 3.0 License
#

def correctedFileName (s):  #remove forbidden characters
	return s.replace('>','').replace('<','').replace('|','').replace(':','').replace('*','').replace('=','').replace('\\','').replace('/','').replace('?','')
	
def VTiName ( serviceName ):
	return correctedFileName( serviceName.replace('\xc2\x86', '').replace('\xc2\x87', '').replace('/', '_') + '.png' )
	
def interoperableName ( serviceName ):
	import re
	for ch in [ ('ä','ae'), ('ö','oe'),  ('ü','ue'), ('Ä','Ae'), ('Ö','Oe'),  ('Ü','Ue'),  ('ß', 'ss' ), ( '*', 'star' ), ( '+', 'plus' ) , ( '&', 'and' ) ]:
		serviceName = serviceName.replace( ch[0], ch[1] )
	return re.sub( '[^a-z0-9]', '', serviceName.lower() )
	
def fallBackName (serviceName):
	res, ok = serviceName, True
	for x in 'hd,uhd,austria,oesterreich,österreich,deutschland,nord,sued,süd'.split(','): 
		if res.lower().endswith(' '+x):  
			res = res[ :-(len(x)+1) ]
	for x in 'WDR,NDR,BR Fernsehen,SR,SWR,MDR,RTL,SAT.1,RBB,rbb,VOX,ORF2,ORF1,BBC,CNN'.split(','):
		if res.startswith(x+' '):
			for chSub in 'gold,emotion,ii,2,zwei'.split(','):
				if res.lower().find( ' '+chSub )>=0:  ok = False
			if ok: res = x
	if res == serviceName: res = ''
	return res
	
def reducedName ( byName):
	fb = fallBackName(byName.upper())
	if fb:
		byName = fb
	return interoperableName(byName)

def getInteroperableNames ( serviceName, vtiMode=1):
	try:
		res = []
		comp = fb = fbComp = ''  #example Nick/MTV+ HD
		if vtiMode:  
			serviceNameVTi = VTiName ( serviceName )  #Nick_MTV+ HD
		else: 
			serviceNameVTi = serviceName   #Nick/MTV+ HD
			
		corr = correctedFileName(serviceName )   #NickMTV+ HD
		if (corr!= serviceName): 
			res.append(corr)
			serviceName = corr
			
		comp = interoperableName( serviceName)   #nickmtvplushd
		if comp and (comp != serviceName):  
			res.append( comp )
			
		fb = fallBackName( serviceNameVTi )   #Nick_MTV+
		if fb and (fb != serviceNameVTi):  
			res.append( fb )
			
		if serviceNameVTi != serviceName:    
			fb = fallBackName( serviceName )  #NickMTV+
			if fb and (fb != serviceName):  
				res.append( fb )
			
		fb2 = interoperableName( fb )  #nickmtvplus
		if fb2 and (fb2 != fb):  
			res.append( fb2 )
	except:
		pass
	return res		# [ 'Nick_MTV+ HD', 'NickMTV+ HD', 'nickmtvplushd', 'Nick_MTV+', 'NickMTV+', 'nickmtvplus' ]
	



	
