from __future__ import print_function
from enigma import eTimer

class BluetoothState:
	STATE_NONE = 0
	STATE_CONNECTING = 1
	STATE_DISCONNECTING = 2
	STATE_SCANNING = 3
	STATE_PAIRING = 4
	STATE_ENABLING = 6

	def __init__(self):
		self.btstate = self.STATE_NONE
		self.stateChangedCB = None

	def getState(self):
		return self.btstate

	def setState(self, state):
		self.btstate = state
		if self.stateChangedCB:
			self.stateChangedCB()

	def checkState(self, state):
		return self.btstate == state

	def registerStateChangeCB(self, _callback):
		self.stateChangedCB = _callback

	def isIdle(self):
		return self.checkState(self.STATE_NONE)

	def isConnecting(self):
		return self.checkState(self.STATE_CONNECTING)

	def isDisconnecting(self):
		return self.checkState(self.STATE_DISCONNECTING)

	def isScanning(self):
		return self.checkState(self.STATE_SCANNING)

	def isPairing(self):
		return self.checkState(self.STATE_PAIRING)

	def setIdle(self):
		self.setState(self.STATE_NONE)

	def setConnecting(self):
		self.setState(self.STATE_CONNECTING)

	def setDisconnecting(self):
		self.setState(self.STATE_DISCONNECTING)

	def setScanning(self):
		self.setState(self.STATE_SCANNING)

	def setPairing(self):
		self.setState(self.STATE_PAIRING)

class BluetoothTask(BluetoothState):
	TASK_CONNECT = 0
	TASK_DISCONNECT = 1
	TASK_WAIT_DISCONNECT = 2
	TASK_START_SCAN = 3
	TASK_START_PAIRING = 4
	TASK_CALL_FUNC = 5
	TASK_EXIT = 6

	def __init__(self):
		BluetoothState.__init__(self)
		self.tasks = []
		self.curTask = None
		self.doNextTmer = eTimer()
		self.doNextTmer.callback.append(self.doNext)
		self.doNextInterval = 100 # ms

	def updateState(self, taskType):
		if taskType == self.TASK_CONNECT:
			self.setConnecting()
		elif taskType == self.TASK_DISCONNECT:
			self.setDisconnecting()
		elif taskType == self.TASK_WAIT_DISCONNECT:
			self.setDisconnecting()
		elif taskType == self.TASK_START_SCAN:
			self.setScanning()
		elif taskType == self.TASK_START_PAIRING:
			self.setPairing()
		else:
			pass

	def addTask(self, taskType, callFunc, mac, args, eventCB):
		task = {"taskType": taskType, "callFunc": callFunc, "mac": mac, "args": args, "eventCB": eventCB}
		#print("==> addTask : ")
		#self.printTask(task)

		if self.isTaskEmpty():
			self.doTask(task)
		else:
			self.tasks.append(task)

	def doTask(self, task):
		#print("==> doTask : ")
		#self.printTask(task)

		callFunc = task["callFunc"]
		args = task["args"]
		eventCB = task["eventCB"]
		taskType = task["taskType"]

		if callFunc is None:
			return

		res = False
		if self.isIdle():
			if args:
				res = callFunc(args)
			else:
				res = callFunc()

		# return False
		if res is False:
			self.curTask = None
			self.doNext()

		# do not have to wait for event
		elif not eventCB:
			self.curTask = None
			self.doNext()

		# set state and wait for event
		else:
			# set state
			self.curTask = task
			self.updateState(taskType)

	def handleEvent(self, event, name, data):
		#print "==> handleEvent event : ", event
		#print "==> handleEvent name : ", name
		#print "==> handleEvent data : ", data
		#print("==> handleEvent self.curTask : ")
		#self.printTask(self.curTask)

		if self.curTask is None:
			return

		args = self.curTask["args"]
		mac = self.curTask["mac"]
		eventCB = self.curTask["eventCB"]

		if event in eventCB:
			if not args or data and (data["bd_addr"] == mac):
				eventCB = eventCB[event]
				if eventCB:
					eventCB(event, args)

				self.curTask = None
				self.setIdle()

				self.doNextTmer.start(self.doNextInterval, True)

	def doNext(self):
		#print("==> doNext self.tasks :")
		#for t in self.tasks:
		#	self.printTask(t)
		#print("==> doNext self.curTask :")
		#self.printTask(self.curTask)

		if self.curTask:
			return

		if self.tasks:
			task = self.tasks.pop(0)
			self.doTask(task)

	def findTask(self, taskType):
		for task in self.tasks:
			if task["taskType"] == taskType:
				return task

		return None

	def removeTask(self, taskType):
		while True:
			task = self.findTask(taskType)
			if task:
				self.tasks.remove(task)
			else:
				break

	def removeAll(self):
		self.tasks = []

	def isTaskEmpty(self):
		return (self.curTask is None) and (not self.tasks)

	def printTask(self, task):
		if task is None:
			return

		taskDesc = {
			self.TASK_CONNECT: "TASK_CONNECT",
			self.TASK_DISCONNECT: "TASK_DISCONNECT",
			self.TASK_WAIT_DISCONNECT: "TASK_WAIT_DISCONNECT",
			self.TASK_START_SCAN: "TASK_START_SCAN",
			self.TASK_START_PAIRING: "TASK_START_PAIRING",
			self.TASK_CALL_FUNC: "TASK_CALL_FUNC",
			self.TASK_EXIT: "TASK_EXIT"
		}

		print("		taskType : ", taskDesc[task["taskType"]])
		print("		callFunc : ", task["callFunc"])
		print("		mac : ", task["mac"])
		print("		args : ", task["args"])
		print("		eventCB : ", task["eventCB"])
