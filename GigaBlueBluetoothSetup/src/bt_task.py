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
		###print("setIdle")
		self.setState(self.STATE_NONE)

	def setConnecting(self):
		###print("setConnecting")
		self.setState(self.STATE_CONNECTING)

	def setDisconnecting(self):
		###print("setDisconnecting")
		self.setState(self.STATE_DISCONNECTING)

	def setScanning(self):
		###print("setScanning")
		self.setState(self.STATE_SCANNING)

	def setPairing(self):
		###print("setScanning")
		self.setState(self.STATE_PAIRING)


class BluetoothTask(BluetoothState):
	TASK_CONNECT = 0
	TASK_DISCONNECT = 1
	TASK_WAIT_DISCONNECT = 2
	TASK_START_SCAN = 3
	TASK_START_PAIRING = 4
	TASK_CALL_FUNC = 5
	TASK_CHECK_STATUS = 6
	TASK_EXIT = 7

	def __init__(self):
		BluetoothState.__init__(self)
		self.tasks = []
		self.curTask = None
		self.doNextTmer = eTimer()
		self.doNextTmer.callback.append(self.doNext)
		self.doNextInterval = 100  # ms

		self.tasks1 = []
		self.curTask1 = None
		self.doNextTmer1 = eTimer()
		self.doNextTmer1.callback.append(self.doNext1)
		self.doNextInterval1 = 100  # ms

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

	def addTask1(self, taskType, callFunc, mac, args, eventCB):
		task = {"taskType": taskType, "callFunc": callFunc, "mac": mac, "args": args, "eventCB": eventCB}
		#print("==> addTask1 : ")
		#self.printTask(task)
		#print("taskType :", task["taskType"])
		#print("callFunc :", task["callFunc"])
		#print("mac :", task["mac"])
		#print("args :", task["args"])
		#print("eventCB:", task["eventCB"])

		if self.isTaskEmpty1():
			self.doTask1(task)
		else:
			self.tasks1.append(task)

	def doTask1(self, task):
		#print("==> doTask1 : ")
		#self.printTask(task)

		callFunc = task["callFunc"]
		args = task["args"]
		eventCB = task["eventCB"]
		taskType = task["taskType"]

		if callFunc is None:
			return

		res = False
		res = callFunc()

		# return False
		if res is False:
			#print("doTask1 : break")
			self.curTask1 = None
			self.doNext1()

		# set state and wait for event
		else:
			# set state
			#print("doTask1 : continue")
			self.tasks1.append(task)
			self.curTask1 = None
			self.doNextTmer1.start(self.doNextInterval1, True)

	def doNext1(self):
		#print("==> doNext1 self.tasks :")
		#for t in self.tasks1:
		#	self.printTask(t)
		#print("==> doNext1 self.curTask :")
		#self.printTask(self.curTask1)

		if self.curTask1:
			return

		if self.tasks1:
			task = self.tasks1.pop(0)
			self.doTask1(task)

	def findTask1(self, taskType):
		for task in self.tasks1:
			if task["taskType"] == taskType:
				return task

		return None

	def removeTask1(self, taskType):
		while True:
			task = self.findTask1(taskType)
			if task:
				self.tasks1.remove(task)
			else:
				break

	def removeAll1(self):
		self.tasks1 = []

	def isTaskEmpty1(self):
		return (self.curTask1 is None) and (not self.tasks1)

	def addTask(self, taskType, callFunc, mac, args, eventCB):
		task = {"taskType": taskType, "callFunc": callFunc, "mac": mac, "args": args, "eventCB": eventCB}
		#print("==> addTask : ")
		#self.printTask(task)
		#print("taskType :", task["taskType"])
		#print("callFunc :", task["callFunc"])
		#print("mac :", task["mac"])
		#print("args :", task["args"])
		#print("eventCB:", task["eventCB"])

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
			#print("doTask : False")
			self.curTask = None
			self.doNext()

		# do not have to wait for event
		elif not eventCB:
			#print("doTask : not eventCB")
			self.curTask = None
			self.doNext()

		# set state and wait for event
		else:
			# set state
			#print("doTask : other status")
			self.curTask = task
			self.updateState(taskType)

	def handleEvent(self, event, name, data):
#		print("==> handleEvent event : ", event)
#		print("==> handleEvent name : ", name)
#		print("==> handleEvent data : ", data)
#		print("==> handleEvent self.curTask : ")
#		self.printTask(self.curTask)

		if self.curTask is None:
			return

		args = self.curTask["args"]
		mac = self.curTask["mac"]
		eventCB = self.curTask["eventCB"]

		if event in eventCB:
			if not args or data and (data["bd_addr"] == mac):
				eventCB = eventCB[event]

				self.curTask = None
				self.setIdle()

				if eventCB:
					eventCB(event, args)

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
			self.TASK_CHECK_STATUS: "TASK_CHECK_STATUS",
			self.TASK_EXIT: "TASK_EXIT"
		}

		print("		taskType : ", taskDesc[task["taskType"]])
		print("		callFunc : ", task["callFunc"])
		print("		mac : ", task["mac"])
		print("		args : ", task["args"])
		print("		eventCB : ", task["eventCB"])
