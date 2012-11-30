# for localized messages
from . import _

from Components.ActionMap import ActionMap
from Components.Sensors import sensors
from Components.Sources.Sensor import SensorSource
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry

from Screens.Screen import Screen

from Plugins.Plugin import PluginDescriptor
from Components.FanControl import fancontrol

class ManualFancontrol(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="570,420" title="FanControl settings" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />


			<widget source="red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			
			<widget name="config" position="10,50" size="550,120" scrollbarMode="showOnDemand" />
			
			<widget source="SensorTempText0" render="Label" position="10,150" zPosition="1" size="90,40" font="Regular;20" halign="left" valign="top" backgroundColor="#9f1313" transparent="1" />
			<widget source="SensorTemp0" render="Label" position="100,150" zPosition="1" size="100,20" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>

			<widget source="SensorFanText0" render="Label" position="290,150" zPosition="1" size="90,40" font="Regular;20" halign="left" valign="top" backgroundColor="#9f1313" transparent="1" />
			<widget source="SensorFan0" render="Label" position="380,150" zPosition="1" size="150,20" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Fan Control"))
		
		templist = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
		tempcount = len(templist)
		fanlist = sensors.getSensorsList(sensors.TYPE_FAN_RPM)
		fancount = len(fanlist)
		
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		for count in range(8):
			if count < tempcount:
				id = templist[count]
				self["SensorTempText%d" % count] = StaticText(sensors.getSensorName(id))		
				self["SensorTemp%d" % count] = SensorSource(sensorid = id)
			else:
				self["SensorTempText%d" % count] = StaticText("")
				self["SensorTemp%d" % count] = SensorSource()
				
			if count < fancount:
				id = fanlist[count]
				self["SensorFanText%d" % count] = StaticText(sensors.getSensorName(id))		
				self["SensorFan%d" % count] = SensorSource(sensorid = id)
			else:
				self["SensorFanText%d" % count] = StaticText("")
				self["SensorFan%d" % count] = SensorSource()
		
		self.list = []
		for count in range(fancontrol.getFanCount()):
			self.list.append(getConfigListEntry(_("Fan %d Voltage") % (count + 1), fancontrol.getConfig(count).vlt))
			self.list.append(getConfigListEntry(_("Fan %d PWM") % (count + 1), fancontrol.getConfig(count).pwm))
			self.list.append(getConfigListEntry(_("Standby Fan %d Voltage") % (count + 1), fancontrol.getConfig(count).vlt_standby))
			self.list.append(getConfigListEntry(_("Standby Fan %d PWM") % (count + 1), fancontrol.getConfig(count).pwm_standby))
		
		ConfigListScreen.__init__(self, self.list, session = self.session)
		#self["config"].list = self.list
		#self["config"].setList(self.list)
		self["config"].l.setSeperation(300)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"ok": self.save,
			"cancel": self.revert,
			"red": self.revert,
			"green": self.save
		}, -1)

	def save(self):
		for count in range(fancontrol.getFanCount()):
			fancontrol.getConfig(count).vlt.save()
			fancontrol.getConfig(count).pwm.save()
			fancontrol.getConfig(count).vlt_standby.save()
			fancontrol.getConfig(count).pwm_standby.save()
		self.close()

	def revert(self):
		for count in range(fancontrol.getFanCount()):
			fancontrol.getConfig(count).vlt.load()
			fancontrol.getConfig(count).pwm.load()
			fancontrol.getConfig(count).vlt_standby.load()
			fancontrol.getConfig(count).pwm_standby.load()
		self.close()

def main(session, **kwargs):
	session.open(ManualFancontrol)

def startMenu(menuid):
	if menuid != "system":
		return []
	return [(_("Fan control"), main, "ManualFancontrol", 80)]

def Plugins(**kwargs):
	return PluginDescriptor(name = "Fan control", description = _("Temperature and Fan control"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc = startMenu)

