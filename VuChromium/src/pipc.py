from __future__ import absolute_import
import os
import threading
import time
import socket
import select
import struct
from . import cbcfg

_OPCODE = {}
_BUFSIZE = 4096

_SOCKETFILE = None


def SetHandler(opcode, handler):
    try:
        _OPCODE[opcode][1] = handler
    except:
        cbcfg.ERROR("Fail to set handler (unknown opcode): %s", opcode)
        return False
    return True


def GetHandler(opcode):
    for key, value in _OPCODE.items():
        if value[0] == opcode:
            cbcfg.DEBUG("recv socket: [%s]", key)
            return value[1]
    return None


class PServerHandlers:
    def __init__(self, opcode_list, szcbh):
        global _OPCODE

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
                cbcfg.DEBUG("add handler -> [%s]", opcodestr)
                SetHandler(opcodestr, fref)
                registreted_idx += 1
            except:
                pass
        cbcfg.DEBUG("%d handlers registreated.", registreted_idx)


class PServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mSock = None
        self.mFlag = False
        self.mTimeout = 5

    def open(self, timeout=5):
        addr = _SOCKETFILE
        self.mTimeout = timeout
        try:
            os.unlink(addr)
        except:
            if os.path.exists(addr):
                cbcfg.ERROR("Fail to remove %s.", addr)
                return False
        try:
            self.mSock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.mSock.settimeout(self.mTimeout)
            self.mSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.mSock.bind(addr)
        except Exception as err:
            cbcfg.ERROR("socket() fail : %s", err)
            return False
        return True

    def parse_header(self, data):
        hlen = struct.calcsize('ibi')
        packet = ""
        opcode, result, length = struct.unpack('ibi', data[:hlen])
        cbcfg.DEBUG("%s %s %d - %d", opcode, result, length, len(data))

        return [opcode, result, length, hlen]

    def assamble(self, opcode, result, packet):
        if packet is None:
            packet = ""
        header = struct.pack('ibi', opcode, (result and 1 or 0), len(packet))
        return header + packet

    def process(self, conn, addr):
        read_packet = conn.recv(12)
        read_header = self.parse_header(read_packet)

        opcode, result, length, hlen = read_header[0], read_header[1], read_header[2], read_header[3]
        recv_data = ""
        if length > 0:
            recv_data = conn.recv(length)

        result, send_packet = False, None
        try:
            result, send_packet = GetHandler(opcode)(result, recv_data)
        except Exception as err:
            cbcfg.ERROR(err)
        send_data = self.assamble(opcode, result, send_packet)
        conn.sendall(send_data)

    def run(self):
        if self.mSock is None:
            raise

        self.mFlag = True
        self.mSock.listen(1)
        cbcfg.DEBUG("PServerThread Start")
        while self.mFlag:
            readable, writable, errored = select.select([self.mSock], [], [], self.mTimeout)
            for s in readable:
                if s is self.mSock:
                    conn, addr = None, None
                    try:
                        conn, addr = self.mSock.accept()
                        self.process(conn, addr)
                    except Exception as err:
                        cbcfg.ERROR("PServerThread: %s", err)
                    finally:
                        if conn is not None:
                            conn.close()
        PServerThread.close()
        cbcfg.DEBUG("PServerThread Stop")

    @staticmethod
    def close(self=None):
        if _SOCKETFILE is not None and os.path.exists(_SOCKETFILE):
            os.unlink(_SOCKETFILE)

    def kill(self):
        self.mFlag = False
