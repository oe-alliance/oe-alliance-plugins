from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.EpgList import EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER
import skin

from .SCInfo import scinfo, scthreads
from .stalkerclient import SUPPORT_MODULES, SCThread, stalker

from math import ceil as math_ceil
from time import localtime, strftime, time


def checkFuture(chid):
	service = scinfo.epgdb.getServiceFromFavList(chid)
	query = ['BDTn', (service, 0, -1, -1)]
	events = scinfo.epgdb.epgcache.lookupEvent(query)
	if events:
		last_stop = events[-1][0] + events[-1][1]
		return float(last_stop)
	return time()


def saveEvents(result):
	res = ("0", time())
	if result:
		data = result.get('data')
		for e in data:
			if isinstance(e, dict) and float(e.get('stop_timestamp')) > time():
				event = StalkerEvent(e)
				scinfo.epgdb.putEvent(event.dict())
		if len(data) > 0:
			res = (data[0].get('ch_id'), float(data[0].get('start_timestamp')))
	else:
		print("[StalkerClient] got no events.")
	return res


def updateFuture(result):
	chid, t = saveEvents(result)

	if result:
		max_page_items = 0
		after_items = 0
		cur_page = 1
		try:
			total_items = int(result.get('total_items'))
			max_page_items = int(result.get('max_page_items'))
			cur_page = result.get('cur_page') and int(result.get('cur_page')) or 1
			after_items = total_items - ((cur_page - 1) * max_page_items + int(result.get('selected_item')))
		except Exception as e:
			print("[StalkerClient]", e)
			cur_page = 1
			max_page_items = 0

		last_page = max_page_items and int(math_ceil(float(after_items) / float(max_page_items))) or 0
		last_page += 1

		for p in range(cur_page, last_page):
			result = stalker.getSimpleDataTable(str(chid), str(strftime('%Y-%m-%d', localtime(t))), str(p + 1))
			saveEvents(result)


def updateEvent(chid, future=False):
	t = future and checkFuture(chid) or time()
	# 1 week
	if not t > time() + 604800:
		return stalker.getSimpleDataTable(str(chid), str(strftime('%Y-%m-%d', localtime(t))), "0")


def updateEvents(future=False):
	if stalker.isAvailable(SUPPORT_MODULES['epg.simple']) and scinfo.epgdb.getFavouriteServiceList:
		favlist = scinfo.epgdb.getFavouriteServiceList()
		print("[StalkerClient] %d channels in favourites." % len(favlist))
		t = scthreads.getRunningThread()
		if t:
			for chid in favlist:
				t.addTask(updateFuture, updateEvent, chid, future)
			t.addTask(None, updateDone)


def updateDone(unused=None):
	print("[StalkerClient] Events updated.")


class StalkerClient_EventViewBase:
	def __init__(self, Event, Channel, callback=None):
		self.cbFunc = callback
		self.currentChannel = Channel
		self.event = Event
		self["epg_description"] = ScrollLabel()
		self["datetime"] = Label()
		self["channel"] = Label()
		self["duration"] = Label()
		self["key_red"] = Button("")
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		self["actions"] = ActionMap(["OkCancelActions", "EventViewActions"],
		{
			"cancel": self.close,
			"ok": self.close,
			"pageUp": self.pageUp,
			"pageDown": self.pageDown,
			"prevEvent": self.prevEvent,
			"nextEvent": self.nextEvent,
		}, -1)
		self.onLayoutFinish.append(self.onLayoutFinishCB)

	def onLayoutFinishCB(self):
		self.setService(self.currentChannel)
		self.setEvent(self.event)

	def prevEvent(self):
		if self.cbFunc is not None:
			self.cbFunc(self.setEvent, self.setService, -1)

	def nextEvent(self):
		if self.cbFunc is not None:
			self.cbFunc(self.setEvent, self.setService, +1)

	def setService(self, service):
		self.currentChannel = service
		name = self.currentChannel[1]
		if name is not None:
			self["channel"].setText(name)
		else:
			self["channel"].setText(_("unknown service"))

	def setEvent(self, event):
		self.event = event
		if event is None:
			return
		text = event.name
		desc = event.descr
		if desc:
			if text:
				text += '\n\n'
			text += desc

		self.setTitle(event.name)
		self["epg_description"].setText(text)

		t = localtime(float(event.time))
		self["datetime"].setText("%02d.%02d, %02d:%02d" % (t[2], t[1], t[3], t[4]))
		self["duration"].setText(_("%d min") % (int(event.duration) / 60))

	def pageUp(self):
		self["epg_description"].pageUp()

	def pageDown(self):
		self["epg_description"].pageDown()


class StalkerClient_EventViewSimple(Screen, StalkerClient_EventViewBase):
	def __init__(self, session, Event, Channel, callback=None):
		Screen.__init__(self, session)
		self.skinName = ["StalkerClient_EventView", "EventView"]
		StalkerClient_EventViewBase.__init__(self, Event, Channel, callback)


class StalkerClient_EventViewEPGSelect(Screen, StalkerClient_EventViewBase):
	def __init__(self, session, Event, Channel, callback=None, singleEPGCB=None, multiEPGCB=None):
		Screen.__init__(self, session)
		self.skinName = ["StalkerClient_EventView", "EventView"]
		StalkerClient_EventViewBase.__init__(self, Event, Channel, callback)
		self.cbSingleEPG = singleEPGCB
		self.cbMultiEPG = multiEPGCB
		self["key_yellow"].setText(_("Single EPG"))
		self["key_blue"].setText(_("Multi EPG"))
		self["epgactions"] = ActionMap(["EventViewEPGActions"],
			{
				"openSingleServiceEPG": self.onKeyYellow,
				"openMultiServiceEPG": self.onKeyBlue,
			})

	def onKeyYellow(self):
		if self.cbSingleEPG is not None:
			self.cbSingleEPG()

	def onKeyBlue(self):
		if self.cbMultiEPG is not None:
			self.cbMultiEPG()


# 2 hours
DT_DURATION = 7200


class StalkerClient_EPGSelection(Screen):
	def __init__(self, session, Channel, type=EPG_TYPE_SINGLE):
		Screen.__init__(self, session)
		self.session = session

		self["key_red"] = Button("")
		self["key_green"] = Button("")
		self["Service"] = ServiceEvent()
		self["Event"] = Event()

		self.m_type = type
		if self.m_type is EPG_TYPE_SINGLE:
			self.skinName = "EPGSelection"
			self["key_yellow"] = Button("")
			self["key_blue"] = Button("")
		else:
			self.skinName = "EPGSelectionMulti"
			self["key_yellow"] = Button(_("Prev"))
			self["key_blue"] = Button(_("Next"))
			self["now_button"] = Pixmap()
			self["next_button"] = Pixmap()
			self["more_button"] = Pixmap()
			self["now_button_sel"] = Pixmap()
			self["next_button_sel"] = Pixmap()
			self["more_button_sel"] = Pixmap()
			self["now_text"] = Label()
			self["next_text"] = Label()
			self["more_text"] = Label()
			self["date"] = Label()

			self.m_max_page_items = 0
			self.m_last_page = 0

			self.m_next_step = 0
			self.m_fromts = time() + (self.m_next_step * DT_DURATION)

		self["actions"] = ActionMap(["OkCancelActions", "WizardActions", "EPGSelectActions"],
		{
			"cancel": self.close,
			"ok": self.onKeyOK,
			"up": self.onKeyUp,
			"down": self.onKeyDown,
			"left": self.onKeyLeft,
			"right": self.onKeyRight,
			"yellow": self.onKeyYellow,
			"blue": self.onKeyBlue,
		}, -1)

		self.scepgList = StalkerEPGList(self.m_type)
		self["list"] = self.scepgList
		self.scepgList.onSelectionChanged.append(self.onSelectionChanged)

		self.m_channel = Channel

		self.thread = SCThread('stalkerclientepg')
		scthreads.pushThread(self.thread)

		self.onLayoutFinish.append(self.onLayoutFinishCB)
		self.onClose.append(self.onCloseCB)

	def onLayoutFinishCB(self):
		if self.m_type is EPG_TYPE_SINGLE:
			self.showSimpleDataTable()
		else:
			self.showDataTable(self.m_fromts, self.m_channel[0])

	def onCloseCB(self):
		self.onClose.remove(self.onCloseCB)

		t = scthreads.popThread()
		if t:
			t.kill()
			t.join()

	def onSelectionChanged(self):
		if self.m_type == EPG_TYPE_MULTI:
			if self.m_next_step > 1:
				self.applyButtonState(3)
			elif self.m_next_step > 0:
				self.applyButtonState(2)
			else:
				self.applyButtonState(1)
			days = [_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun")]
			datestr = ""
			cur = self.scepgList.getCurrent()
			if cur and len(cur.epglist) > 0:
				event = cur.epglist[0]
				if event is not None:
					now = time()
					beg = event.time
					nowTime = localtime(now)
					begTime = localtime(float(beg))
					if nowTime[2] != begTime[2]:
						datestr = '%s %d.%d.' % (days[begTime[6]], begTime[2], begTime[1])
					else:
						datestr = '%s %d.%d.' % (_("Today"), begTime[2], begTime[1])
			self["date"].setText(datestr)

	def eventViewCallback(self, setEvent, setService, val):
		if self.m_type is EPG_TYPE_SINGLE:
			l = self["list"]
			old = l.getCurrent()
			if val == -1:
				self.onKeyUp()
			elif val == +1:
				self.onKeyDown()
			cur = l.getCurrent()
			setService(self.m_channel)
			setEvent(cur)

	def showSimpleDataTable(self):
		def updateEvent(result):
			if result:
				data = result.get('data')
				for event in data:
					if isinstance(event, dict) and float(event.get('stop_timestamp')) > time():
						e = StalkerEvent(event)
						self.scepgList.addItem(e)
						e.saveEvent(e.dict())
				self.scepgList.updateList(self.scepgList.getSelectedIndex())
			else:
				print("[StalkerClient] got no event.")

		def showSimpleDataTableCB(result):
			if result:
				self.scepgList.clear()
				updateEvent(result)

				max_page_items = 0
				after_items = 0
				try:
					total_items = int(result.get('total_items'))
					max_page_items = int(result.get('max_page_items'))
					cur_page = int(result.get('cur_page'))
					after_items = total_items - ((cur_page - 1) * max_page_items + int(result.get('selected_item')))
				except Exception as e:
					print("[StalkerClient]", e)
					cur_page = 1
					max_page_items = 0

				last_page = max_page_items and int(math_ceil(float(after_items) / float(max_page_items))) or 0
				last_page += 1

				for p in range(cur_page, last_page):
					self.thread.addTask(updateEvent, stalker.getSimpleDataTable, self.m_channel[0], str(strftime('%Y-%m-%d', today)), str(p + 1))

				# after PM 3:00
				if int(today[3]) > 15:
					tomorrow = localtime(time() + 60 * 60 * 24)
					self.thread.addTask(updateEvent, stalker.getSimpleDataTable, self.m_channel[0], str(strftime('%Y-%m-%d', tomorrow)), "0")

		today = localtime(time())
		if stalker.isAvailable(SUPPORT_MODULES['epg.simple']):
			self.thread.addTask(showSimpleDataTableCB, stalker.getSimpleDataTable, self.m_channel[0], str(strftime('%Y-%m-%d', today)), "0")

	def showDataTable(self, from_ts, ch_id, page="0", index=0):
		def showDataTableCB(result):
			if result:
				total_items = int(result.get('total_items'))
				self.m_max_page_items = int(result.get('max_page_items'))
				self.m_last_page = self.m_max_page_items and int(math_ceil(float(total_items) / float(self.m_max_page_items))) or 0

				cur_page = result.get('cur_page') and int(result.get('cur_page')) or self.scepgList.getPage()
				selected_item = result.get('selected_item') and int(result.get('selected_item')) - 1 or index

				self.scepgList.clear(cur_page, self.m_last_page)
				if cur_page is -1:
					print("[StalkerClient] got no event.")
					return

				data = result.get('data')
				for events in data:
					d = StalkerServiceEvent(events)
					self.scepgList.addItem(d)
				self.scepgList.updateList(selected_item)
			else:
				print("[StalkerClient] got no event.")

		if stalker.isAvailable(SUPPORT_MODULES['epg']):
			self.thread.addTask(showDataTableCB, stalker.getDataTable, from_ts, from_ts + DT_DURATION, "0", str(ch_id), str(page))

	def onKeyLeft(self):
		idx = self.scepgList.getSelectedIndex()
		cur = self.scepgList.getCurrent()
		self.scepgList.leftPage()
		if self.m_type is EPG_TYPE_MULTI and int(self.m_last_page) > 1:
			chid = cur and cur.ch_id or ""
			self.showDataTable(self.m_fromts, chid, self.scepgList.getPage(), idx)

	def onKeyRight(self):
		idx = self.scepgList.getSelectedIndex()
		cur = self.scepgList.getCurrent()
		self.scepgList.rightPage()
		if self.m_type is EPG_TYPE_MULTI and int(self.m_last_page) > 1:
			chid = cur and cur.ch_id or ""
			self.showDataTable(self.m_fromts, chid, self.scepgList.getPage(), idx)

	def onKeyUp(self):
		cur = self.scepgList.getCurrent()
		self.scepgList.upPage()
		if self.m_type is EPG_TYPE_MULTI and self.scepgList.getRefresh():
			chid = cur and cur.ch_id or ""
			self.showDataTable(self.m_fromts, chid, self.scepgList.getPage(), self.m_max_page_items)

	def onKeyDown(self):
		cur = self.scepgList.getCurrent()
		self.scepgList.downPage()
		if self.m_type is EPG_TYPE_MULTI and self.scepgList.getRefresh():
			chid = cur and cur.ch_id or ""
			self.showDataTable(self.m_fromts, chid, self.scepgList.getPage(), 0)

	def onKeyYellow(self):
		idx = self.scepgList.getSelectedIndex()
		cur = self.scepgList.getCurrent()
		if self.m_type is EPG_TYPE_MULTI and self.m_next_step > 0:
			self.m_next_step -= 1
			self.m_fromts = time() + (self.m_next_step * DT_DURATION)
			chid = cur and cur.ch_id or ""
			self.showDataTable(self.m_fromts, chid, self.scepgList.getPage(), idx)

	def onKeyBlue(self):
		idx = self.scepgList.getSelectedIndex()
		cur = self.scepgList.getCurrent()
		if self.m_type is EPG_TYPE_MULTI:
			self.m_next_step += 1
			self.m_fromts = time() + (self.m_next_step * DT_DURATION)
			chid = cur and cur.ch_id or ""
			self.showDataTable(self.m_fromts, chid, self.scepgList.getPage(), idx)

	def onKeyOK(self):
		if self.scepgList.hasItems():
			if self.m_type is EPG_TYPE_SINGLE:
				self.session.openWithCallback(self.EventViewCB, StalkerClient_EventViewSimple, self.scepgList.getCurrent(), self.m_channel, self.eventViewCallback)
			else:
				cur = self.scepgList.getCurrent()
				if cur and len(cur.epglist) > 0:
					self.session.openWithCallback(self.EventViewCB, StalkerClient_EventViewSimple, cur.epglist[0], (cur.ch_id, cur.ch_name))

	def EventViewCB(self):
		self.thread.clearTask()

	def applyButtonState(self, state):
		if state == 0:
			self["now_button"].hide()
			self["now_button_sel"].hide()
			self["next_button"].hide()
			self["next_button_sel"].hide()
			self["more_button"].hide()
			self["more_button_sel"].hide()
			self["now_text"].hide()
			self["next_text"].hide()
			self["more_text"].hide()
			self["key_red"].setText("")
		else:
			if state == 1:
				self["now_button_sel"].show()
				self["now_button"].hide()
			else:
				self["now_button"].show()
				self["now_button_sel"].hide()

			if state == 2:
				self["next_button_sel"].show()
				self["next_button"].hide()
			else:
				self["next_button"].show()
				self["next_button_sel"].hide()

			if state == 3:
				self["more_button_sel"].show()
				self["more_button"].hide()
			else:
				self["more_button"].show()
				self["more_button_sel"].hide()


class StalkerEvent(object):
	def __init__(self, event):
		self.m_id = event.get('id')
		self.m_name = event.get('name')
		self.m_descr = event.get('descr')
		self.m_start_timestamp = event.get('start_timestamp')
		self.m_stop_timestamp = event.get('stop_timestamp')
		self.m_duration = event.get('duration')
		self.m_ch_id = event.get('ch_id')

	def dict(self):
		event = {}
		event["id"] = self.m_id
		event["name"] = self.m_name
		event["descr"] = self.m_descr
		event["start_timestamp"] = self.m_start_timestamp
		event["stop_timestamp"] = self.m_stop_timestamp
		event["duration"] = self.m_duration
		event["ch_id"] = self.m_ch_id
		return event

	def getName(self):
		return self.m_name

	def getDescr(self):
		return self.m_descr

	def getStartTime(self):
		return self.m_start_timestamp

	def getStopTime(self):
		return self.m_stop_timestamp

	def getDuration(self):
		return self.m_duration

	def getChId(self):
		return self.m_ch_id

	name = property(getName)
	descr = property(getDescr)
	time = property(getStartTime)
	time_to = property(getStopTime)
	duration = property(getDuration)
	ch_id = property(getChId)

	def __str__(self):
		t = localtime(float(self.m_start_timestamp))
		return "[StalkerClient] Event [%s] %s" % (strftime('%Y-%m-%d %H:%M', t), self.m_name)

	def saveEvent(self, event):
		if int(self.m_ch_id) in scinfo.epgdb.getFavouriteServiceList():
			scinfo.epgdb.putEvent(event)


class StalkerServiceEvent(object):
	def __init__(self, data):
		self.m_chid = data.get('ch_id')
		self.m_chname = data.get('name')
		self.m_epglist = []

		events = data.get('epg')
		for e in events:
			d = StalkerEvent(e)
			self.m_epglist.append(d)
			d.saveEvent(d.dict())

	def dict(self):
		event = {}
		event["ch_id"] = self.m_chid
		event["ch_name"] = self.m_chname
		event["epglist"] = self.m_epglist
		return data

	def getSerivceId(self):
		return self.m_chid

	def getSerivceName(self):
		return self.m_chname

	def getEventList(self):
		return self.m_epglist

	ch_id = property(getSerivceId)
	ch_name = property(getSerivceName)
	epglist = property(getEventList)

	def __str__(self):
		return "[StalkerClient] %2d Events [%s]" % (len(self.m_epglist), self.m_chname)


def StalkerEPGComponent(entry, size, type):
	width = size.width()
	height = size.height()
	res = [entry]

	if type is EPG_TYPE_SINGLE:
		days = (_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun"))
		t = localtime(float(entry.time))

		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width / 20 * 2 - 10, height, 0, RT_HALIGN_RIGHT, days[t[6]]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width / 20 * 2, 0, width / 20 * 5 - 15, height, 0, RT_HALIGN_RIGHT, "%02d.%02d, %02d:%02d" % (t[2], t[1], t[3], t[4])))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width / 20 * 7, 0, width / 20 * 13, height, 0, RT_HALIGN_LEFT, entry.name))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width / 10 * 3 - 10, height, 0, RT_HALIGN_LEFT, entry.ch_name))

		epglist = entry.epglist
		if len(epglist) > 0:
			begin_time = float(epglist[0].time)
			end_time = float(epglist[0].time_to)
			name = epglist[0].name

			if begin_time is not None:
				now_time = time()
				if begin_time > now_time:
					begin = localtime(begin_time)
					end = localtime(end_time)
					res.append((eListboxPythonMultiContent.TYPE_TEXT, width / 10 * 3, 0, width / 10 * 2 - 10, height, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER, "%02d.%02d - %02d.%02d" % (begin[3], begin[4], end[3], end[4])))
				else:
					percent = (now_time - begin_time) * 100 / (end_time - begin_time)
					res.append((eListboxPythonMultiContent.TYPE_PROGRESS, width / 10 * 3, 4, width / 10 * 2 - 10, height - 8, percent))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, width / 10 * 3 + width / 10 * 2, 0, width / 10 * 5, height, 0, RT_HALIGN_LEFT, name))

	return res


class StalkerEPGList(MenuList):
	def __init__(self, type, enableWrapAround=False):
		self.type = type
		self.list = []
		MenuList.__init__(self, [], enableWrapAround, eListboxPythonMultiContent)
		font = skin.fonts.get("EPGList0", ("Regular", 22))
		self.l.setFont(0, gFont(font[0], font[1]))
		font = skin.fonts.get("EPGList1", ("Regular", 16))
		self.l.setFont(1, gFont(font[0], font[1]))

		self.page_current = -1
		self.page_last = -1
		self.item_last = -1
		self.item_refresh = False

	def clear(self, current=-1, last=-1):
		del self.list[:]
		self.l.setList(self.list)
		self.page_current = current
		self.page_last = last
		self.item_last = -1
		self.item_refresh = False

	def addItem(self, item):
		self.list.append(StalkerEPGComponent(item, self.l.getItemSize(), self.type))
		self.item_last += 1

	def leftPage(self):
		if self.page_last < 0 or int(self.page_last) is 1:
			self.pageUp()
		else:
			self.page_current = int(self.page_current) - 1 if (int(self.page_current) > 1) else self.page_last

	def rightPage(self):
		if self.page_last < 0 or int(self.page_last) is 1:
			self.pageDown()
		else:
			self.page_current = int(self.page_current) + 1 if (int(self.page_current) < int(self.page_last)) else 1

	def upPage(self):
		if self.getSelectedIndex() > 0:
			self.up()
		else:
			if self.page_last < 0:
				self.moveToIndex(self.item_last)
			else:
				self.item_refresh = True if not int(self.page_last) is 1 else False
				self.leftPage()

	def downPage(self):
		if self.getSelectedIndex() < self.item_last:
			self.down()
		else:
			if self.page_last < 0:
				self.moveToIndex(0)
			else:
				self.item_refresh = True if not int(self.page_last) is 1 else False
				self.rightPage()

	def updateList(self, index=0):
		self.l.setList(self.list)
		i = index if int(index) < int(self.item_last) else self.item_last
		self.moveToIndex(int(i))

	def getRefresh(self):
		return self.item_refresh

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	def getPage(self):
		return self.page_current

	def hasItems(self):
		return True if len(self.list) > 0 else False
