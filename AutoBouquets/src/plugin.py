# AutoBouquets E2 for satellite 28.2E
# stream bouquet downloader by LraiZer
# HOMEPAGE Forum - www.ukcvs.org
# version date - 21st August 2012

from Screens.Screen import Screen
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Button import Button
from Tools.Directories import fileExists
from Plugins.Plugin import PluginDescriptor

class MyShCom(Screen):
	skin = """
		<screen position="center,center" size="365,480" title="AutoBouquets E2 for 28.2E" >
			<widget name="key_red" position="24,5" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/> 
			<widget name="key_green" position="200,5" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/> 
			<widget name="key_yellow" position="25,440" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_blue" position="200,440" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<ePixmap name="red" position="25,5" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="200,5" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="24,440" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" /> 
			<ePixmap name="blue" position="200,440" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" /> 
			<widget name="myMenu" position="25,55" size="315,370" scrollbarMode="showOnDemand" />		
		</screen>""" 

	def __init__(self, session, args = 0):
		self.session = session

		list = []
		list.append(("Atherstone HD", "4101 13"))
		list.append(("Atherstone SD", "4097 13"))
		list.append(("Border England HD", "4101 0c"))
		list.append(("Border England SD", "4097 0c"))
		list.append(("Border Scotland HD", "4102 24"))
		list.append(("Border Scotland SD", "4098 24"))
		list.append(("Brighton HD", "4103 41"))
		list.append(("Brighton SD", "4099 41"))
		list.append(("Central Midlands HD", "4101 03"))
		list.append(("Central Midlands SD", "4097 03"))
		list.append(("Channel Isles HD", "4104 22"))
		list.append(("Channel Isles SD", "4100 22"))
		list.append(("East Midlands HD", "4101 14"))
		list.append(("East Midlands SD", "4097 14"))
		list.append(("Essex HD", "4101 02"))
		list.append(("Essex SD", "4097 02"))
		list.append(("Gloucester HD", "4101 18"))
		list.append(("Gloucester SD", "4097 18"))
		list.append(("Grampian HD", "4102 23"))
		list.append(("Grampian SD", "4098 23"))
		list.append(("Granada HD", "4101 07"))
		list.append(("Granada SD", "4097 07"))
		list.append(("Henley On Thames HD", "4103 46"))
		list.append(("Henley On Thames SD", "4099 46"))
		list.append(("HTV Wales HD", "4103 2b"))
		list.append(("HTV Wales SD", "4099 2b"))
		list.append(("HTV West HD", "4101 04"))
		list.append(("HTV West SD", "4097 04"))
		list.append(("HTV West / Thames Valley HD", "4103 3f"))
		list.append(("HTV West / Thames Valley SD", "4099 3f"))
		list.append(("Humber HD", "4101 1d"))
		list.append(("Humber SD", "4097 1d"))
		list.append(("London HD", "4101 01"))
		list.append(("London SD", "4097 01"))
		list.append(("London / Essex HD", "4101 12"))
		list.append(("London / Essex SD", "4097 12"))
		list.append(("London / Thames Valley HD", "4103 42"))
		list.append(("London / Thames Valley SD", "4099 42"))
		list.append(("London Kent HD", "4103 40"))
		list.append(("London Kent SD", "4099 40"))
		list.append(("Meridian East HD", "4101 0b"))
		list.append(("Meridian East SD", "4097 0b"))
		list.append(("Meridian North HD", "4103 44"))
		list.append(("Meridian North SD", "4099 44"))
		list.append(("Meridian South HD", "4101 05"))
		list.append(("Meridian South SD", "4097 05"))
		list.append(("Meridian South East HD", "4101 0a"))
		list.append(("Meridian South East SD", "4097 0a"))
		list.append(("Merseyside HD", "4103 2d"))
		list.append(("Merseyside SD", "4099 2d"))
		list.append(("Norfolk HD", "4101 15"))
		list.append(("Norfolk SD", "4097 15"))
		list.append(("North East Midlands HD", "4103 3e"))
		list.append(("North East Midlands SD", "4099 3e"))
		list.append(("North West Yorkshire HD", "4101 08"))
		list.append(("North West Yorkshire SD", "4097 08"))
		list.append(("North Yorkshire HD", "4101 1a"))
		list.append(("North Yorkshire SD", "4097 1a"))
		list.append(("Northern Ireland HD", "4104 21"))
		list.append(("Northern Ireland SD", "4100 21"))
		list.append(("Oxford HD", "4103 47"))
		list.append(("Oxford SD", "4099 47"))
		list.append(("Republic of Ireland HD", "4104 32"))
		list.append(("Republic of Ireland SD", "4100 32"))
		list.append(("Ridge Hill HD", "4103 29"))
		list.append(("Ridge Hill SD", "4099 29"))
		list.append(("Scarborough HD", "4103 3d"))
		list.append(("Scarborough SD", "4099 3d"))
		list.append(("Scottish East HD", "4102 25"))
		list.append(("Scottish East SD", "4098 25"))
		list.append(("Scottish West HD", "4102 26"))
		list.append(("Scottish West SD", "4098 26"))
		list.append(("Sheffield HD", "4103 3c"))
		list.append(("Sheffield SD", "4099 3c"))
		list.append(("South Lakeland HD", "4101 1c"))
		list.append(("South Lakeland SD", "4097 1c"))
		list.append(("South Yorkshire HD", "4103 48"))
		list.append(("South Yorkshire SD", "4099 48"))
		list.append(("Tees HD", "4103 45"))
		list.append(("Tees SD", "4099 45"))
		list.append(("Thames Valley HD", "4101 09"))
		list.append(("Thames Valley SD", "4097 09"))
		list.append(("Tring HD", "4101 1b"))
		list.append(("Tring SD", "4097 1b"))
		list.append(("Tyne HD", "4101 0d"))
		list.append(("Tyne SD", "4097 0d"))
		list.append(("West Anglia HD", "4101 19"))
		list.append(("West Anglia SD", "4097 19"))
		list.append(("West Dorset HD", "4103 43"))
		list.append(("West Dorset SD", "4099 43"))
		list.append(("Westcountry HD", "4101 06"))
		list.append(("Westcountry SD", "4097 06"))

		Screen.__init__(self, session)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Start"))
		self["key_yellow"] = Button(_("Help"))
		self["key_blue"] = Button(_("About"))

		self["myMenu"] = MenuList(list)

		self["myActionMap"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.go,
			"yellow": self.help,
			"blue": self.about,
			"cancel": self.cancel,
			"ok": self.go
		}, -1)

	def go(self):
		returnValue = self["myMenu"].l.getCurrentSelection()[1]
		print "\n[MyShCom] returnValue: " + returnValue + "\n"

		if returnValue is not None:
			self.shcom("/usr/lib/enigma2/python/Plugins/Extensions/AutoBouquets/autobouquets_e2.sh " + returnValue)

	def shcom(self, com):
		if fileExists("/usr/bin/dvbsnoop"):
			self.session.open(Console,_("start shell com: %s") % (com), ["%s" % com])
		else:
			self.session.open(MessageBox,"dvbsnoop not found!",MessageBox.TYPE_ERROR)
			print "\n[MyShCom] dvbsnoop failed!\n"

	def about(self):
		self.session.open(MessageBox,"AutoBouquets E2 for 28.2E\nVersion date - 21/08/2012\n\nLraiZer @ www.ukcvs.org",MessageBox.TYPE_INFO)

	def help(self):
		self.session.open(Console,_("Showing AutoBouquets readme.txt"),["cat /usr/lib/enigma2/python/Plugins/Extensions/AutoBouquets/%s" % _("readme.txt")])

	def cancel(self):
		print "\n[MyShCom] cancel\n"
		self.close(None)

###########################################################################

def main(session, **kwargs):
	print "\n[MyShCom] start\n"
	session.open(MyShCom)

###########################################################################

def Plugins(**kwargs):
	return PluginDescriptor(
	name="AutoBouquets E2",
	description="28.2e stream bouquet downloader",
	where = PluginDescriptor.WHERE_PLUGINMENU,
	icon="autobouquets.png",
	fnc=main)
