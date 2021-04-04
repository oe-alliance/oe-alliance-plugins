# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from enigma import fbClass, eRCInput
import os
import threading
import time
import socket
import select
import struct
from . import vbcfg

_OPCODE  = {}
_BUFSIZE = 4096

def SetHandler(opcode, handler):
	try:
		_OPCODE[opcode][1] = handler
	except:
		vbcfg.ERR("Fail to set handler (unknown opcode): %s" % opcode)
		return False
	return True

def GetHandler(opcode):
	for key, value in _OPCODE.items():
		if value[0] == opcode:
			vbcfg.DEBUG("recv socket: [%s]" % key)
			return value[1]
	return None

def GetOpcode(opcode):
	try:
		return _OPCODE[opcode][0]
	except:
		return -1

class VBController:
	@staticmethod
	def assamble(opcodestr, data):
		opcode = _OPCODE[opcodestr][0]
		header = struct.pack('i', opcode)
		return header + data

	@staticmethod
	def command(opcodestr, data=""):
		cmd_fd = None
		vbcfg.DEBUG("send ipc: [%s]" % opcodestr)
		try:
			send_data = VBController.assamble(opcodestr, data)
			if not os.path.exists(vbcfg.CONTROLFILE):
				raise Exception("no found controller file.")
			cmd_fd = os.open(vbcfg.CONTROLFILE, os.O_WRONLY)
			if cmd_fd is None:
				raise Exception("fail to open controller file.")
			os.write(cmd_fd, send_data)
		except Exception as err:
			vbcfg.ERR("VBHController: %s" % err)
			vbcfg.setPosition(vbcfg.g_position)
			fbClass.getInstance().unlock()
			eRCInput.getInstance().unlock()
			return False
		finally:
			if cmd_fd is not None:
				os.close(cmd_fd)
		return True

class VBServerThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.mSock = None
		self.mFlag = False
		self.mTimeout = 5

	def open(self, timeout=5):
		addr = vbcfg.SOCKETFILE
		self.mTimeout = timeout

		try:
			os.unlink(addr)
		except:
			if os.path.exists(addr):
				return False
		try:
			self.mSock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			self.mSock.settimeout(self.mTimeout)
			self.mSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.mSock.bind(addr)
		except:
			return False
		return True

	def parse(self, data):
		hlen = struct.calcsize('ibi')
		packet = ""
		opcode, result, length = struct.unpack('ibi', data[:hlen])
		#vbcfg.DEBUG("%s %s %d" % (opcode, result, length))
		if length > 0:
			packet = data[hlen:hlen+length]
		return [opcode, result, packet]

	def assamble(self, opcode, result, packet):
		if packet is None:
			packet = ""
		header = struct.pack('ibi', opcode, (result and 1 or 0), len(packet))
		return header + bytes(packet, 'utf-8',errors='ignore')

	def process(self, conn, addr):
		read_data = conn.recv(_BUFSIZE)
		request = self.parse(read_data)
		opcode, result, read_packet = request[0], request[1], request[2]
		result, send_packet = False, None
		try:
			result, send_packet = GetHandler(opcode)(result, read_packet)
		except Exception as ErrMsg:
			vbcfg.ERR(ErrMsg)
		send_data = self.assamble(opcode, result, send_packet)
		conn.sendall(send_data)

	def run(self):
		if self.mSock is None:
			raise

		self.mFlag = True
		self.mSock.listen(1)
		while self.mFlag:
			readable, writable, errored = select.select([self.mSock], [], [], self.mTimeout)
			for s in readable:
				if s is self.mSock:
					conn, addr = None, None
					try:
						conn, addr = self.mSock.accept()
						self.process(conn, addr)
					except Exception as err:
						vbcfg.ERR("VBSServerThread: %s" % err)
					finally:
						if conn is not None:
							conn.close()

	def kill(self):
		self.mFlag = False

class VBHandlers:
	def __init__(self, opcode_list, szcbh):
		opcode = 0
		for opcode_str in opcode_list:
			if opcode_str is None and len(opcode_str) == 0:
				continue
			_OPCODE[opcode_str] = [opcode, None]
			opcode = opcode + 1

		registreted_idx = 0
		for fname in dir(self):
			try:
				if not fname.startswith(szcbh):
					continue
				fref = getattr(self, fname)
				if fref is None:
					continue
				opcodestr = fname[len(szcbh):]
				vbcfg.DEBUG("registrated at %s" % opcodestr)
				SetHandler(opcodestr, fref)
				registreted_idx += 1
			except:
				pass
		vbcfg.DEBUG("%d registreated" % registreted_idx)
