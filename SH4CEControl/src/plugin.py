from Plugins.Plugin import PluginDescriptor
from Components.Scanner import scanDevice
from Screens.InfoBar import InfoBar
import Screens.Standby

import time
from threading import Thread 
import sys 
import os 

global_session = None
global_thread = None
global_shutdown = False

class CEControlThread(Thread): 
	def __init__ (self): 
		Thread.__init__(self) 

	def clear(self):
		open("/proc/stb/cec/state_activesource").read()[:-1]
		open("/proc/stb/cec/state_cecaddress").read()[:-1]
		open("/proc/stb/cec/state_standby").read()[:-1]
		
	def run(self): 
		global global_session
		global global_shutdown
		
		# Hello world, live long and prosper
		open("/proc/stb/cec/onetouchplay", "w").write("0")
		self.clear()
		while global_shutdown is False:
			time.sleep(0.5)
			try:
				events = open("/proc/stb/cec/event_poll").readline()
				
				isDiscovery    = ord(events[0]) - ord('0')
				isActiveSource = ord(events[1]) - ord('0')
				isStandby      = ord(events[2]) - ord('0')
				
				if isDiscovery != 0 or isActiveSource != 0 or isStandby != 0:
					print "[CEControl] event: ", events
				
				if isActiveSource > 0:
					try:
						activesource = open("/proc/stb/cec/state_activesource").readline()
						cecaddress = open("/proc/stb/cec/state_cecaddress").readline()
						if activesource == cecaddress:
							if Screens.Standby.inStandby:
								print "[CEControl] wakeup"
								Screens.Standby.inStandby.Power()
							else:
								# We are not the active source, if we were in pause mode, continue
								print "[CEControl] continue playback"
								if global_session is not None and global_session.nav is not None:
									service = global_session.nav.getCurrentService()
									if service is not None:
										pauseable = service.pause()
										if pauseable is not None:
											pauseable.unpause()
						
						else:
							# we lost focus, pause if current playback in progress
							print "[CEControl] pause playback"
							if global_session is not None and global_session.nav is not None:
								service = global_session.nav.getCurrentService()
								if service is not None:
									pauseable = service.pause()
									if pauseable is not None:
										pauseable.pause()
					except IOError:
						continue
				
				if isStandby > 0:
					try:
						standby = open("/proc/stb/cec/state_standby").readline()
						# we were told to goto standby
						print "[CEControl] entering standby"
						global_session.open(Screens.Standby.Standby)
					except IOError:
						continue
			
			except IOError:
				continue
				
		# We are shutting down, notify tv to shut down as well
		# 0 = TV
		# f = ALL DEVICES
		try:
			activesource = open("/proc/stb/cec/state_activesource").readline()
			cecaddress = open("/proc/stb/cec/state_cecaddress").readline()
			if activesource == cecaddress:
				# We are the active source so lets shut down
				open("/proc/stb/cec/systemstandby", "w").write("0")
		except IOError:
			print "IOError:"
		


def sessionstart(reason, session):
	global global_session
	global global_shutdown
	global global_thread
	
	global_session = session

def autostart(reason, **kwargs):
	global global_session
	global global_shutdown
	global global_thread
	if reason == 0: #starting
		print "[CEControl] starting"
		global_thread = CEControlThread() 
		global_thread.start() 
	elif reason == 1: #shutingdown #TODO: How to detect restart ?
		print "[CEControl] shutting down"
		global_shutdown = True
		if global_thread is not None:
			global_thread.join()
		
		global_session = None

def Plugins(**kwargs):
	return [
		#PluginDescriptor(name="CEControl", description=_("HDMI CEC"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = sessionstart),
 		PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart)
		]

