# Based on ReachView code from Egor Fedorov (egor.fedorov@emlid.com)
# Updated for Python 3.6.8 on a Raspberry  Pi
# source: https://gist.github.com/castis/0b7a162995d0b465ba9c84728e60ec01#file-bluetoothctl-py
# Updated for enigma2 by jbleyel

# If you are interested in using ReachView code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of ReachView.

# ReachView is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ReachView is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ReachView.  If not, see <http://www.gnu.org/licenses/>.

from pexpect import EOF, TIMEOUT, spawnu
from re import compile
from subprocess import check_output, CalledProcessError
from time import sleep
from os import kill
import threading


class Bluetoothctl:
    """A wrapper for bluetoothctl utility."""

    def __init__(self):
        check_output("rfkill unblock bluetooth", shell=True)
        self.process = None
        self.isReady = False
        self.isScanning = False
        self._start_thread()
        #self.max_attempts = 5
        #self.attempts = 0

    def _start_thread(self):
        thread = threading.Thread(target=self._start_bluetoothctl)
        thread.daemon = True
        thread.start()

    def kill_existing_bluetoothctl(self):
        try:
            output = check_output("pgrep bluetoothctl", shell=True).decode().strip()
            for pid in output.splitlines():
                print(f"Killing leftover bluetoothctl process {pid}")
                kill(int(pid), 9)
        except CalledProcessError:
            # pgrep returns non-zero if no process found, which is fine
            pass

    def _start_bluetoothctl(self):
        #while not self.isReady and self.attempts < self.max_attempts:
        while not self.isReady:
            print(f"Trying to start bluetoothctl...")
            self.kill_existing_bluetoothctl()
            try:
                self.process = spawnu("bluetoothctl", echo=False)
                self.process.expect("Agent registered", timeout=10)
                self.isReady = True
                print(f"bluetoothctl is ready.")
            except Exception as e:
                print(f"bluetoothctl start failed: {e}")
                sleep(2)
            #self.attempts += 1

    def send(self, command, pause=0):
        self.process.send(f"{command}\n")
        sleep(pause)
        if self.process.expect(["#", EOF, TIMEOUT]):
            raise Exception(f"bluetoothctl failed after {command}")

    def get_output(self, *args, **kwargs):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        self.send(*args, **kwargs)
        return self.process.before.split("\r\n")

    def start_scan(self):
        """Start bluetooth scanning process."""
        try:
            self.send("scan on")
            self.isScanning = True
        except Exception as e:
            print(e)

    def stop_scan(self):
        """Start bluetooth scanning process."""
        try:
            self.send("scan off")
            self.isScanning = False
        except Exception as e:
            print(e)

    def scan(self, timeout=5):
        """Start and stop bluetooth scanning process."""
        self.start_scan()
        sleep(timeout)
        self.stop_scan()

    def make_discoverable(self):
        """Make device discoverable."""
        try:
            self.send("discoverable on")
        except Exception as e:
            print(e)

    def parse_device_info(self, info_string):
        """Parse a string corresponding to a device."""
        device = {}
        block_list = ["[\x1b[0;", "removed"]
        if not any(keyword in info_string for keyword in block_list):
            try:
                device_position = info_string.index("Device")
            except ValueError:
                pass
            else:
                if device_position > -1:
                    attribute_list = info_string[device_position:].split(" ", 2)
                    if len(attribute_list) == 3:
                        device = {
                            "mac_address": attribute_list[1],
                            "name": attribute_list[2]
                        }

        return device

    def get_available_devices(self):
        """Return a list of tuples of paired and discoverable devices."""
        available_devices = []
        try:
            out = self.get_output("devices")
        except Exception as e:
            print(e)
        else:
            for line in out:
                device = self.parse_device_info(line)
                if device:
                    available_devices.append(device)
        return available_devices

    def get_paired_devices(self):
        """Return a list of tuples of paired devices."""
        paired_devices = []
        try:
            out = self.get_output("paired-devices")
        except Exception as e:
            print(e)
        else:
            for line in out:
                device = self.parse_device_info(line)
                if device:
                    paired_devices.append(device)

        return paired_devices

    def get_discoverable_devices(self):
        """Filter paired devices out of available."""
        available = self.get_available_devices()
        paired = self.get_paired_devices()

        return [d for d in available if d not in paired]

    def get_device_info(self, mac_address):
        """Get device info by mac address."""
        try:
            out = self.get_output(f"info {mac_address}")
        except Exception as e:
            print(e)
            return False
        else:
            return out

    def pair(self, mac_address):
        """Try to pair with a device by mac address."""
        if mac_address in [x['mac_address'] for x in self.get_paired_devices()]:
            return True
        self.passkey = None
        try:
            self.send(f"pair {mac_address}", 4)
        except Exception as e:
            print(e)
            return False
        else:
            res = self.process.expect(["Failed to pair", "Pairing successful", "Passkey: ", "PIN code: ", "Request authorization", EOF])
            if res == 1:
                return True
            elif res == 4:
                self.send("yes")
                sleep(2)
                if mac_address in [x['mac_address'] for x in self.get_paired_devices()]:
                    return True
                res = self.process.expect(["Request confirmation", EOF])
                return res == 0
            elif res in [2, 3]:
                ansi_escape = compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
                self.passkey = ansi_escape.sub('', str(self.process.buffer))
                return False
            else:
                print(f"Failed to pair. Res = {res}")
                return False

    def trust(self, mac_address):
        """Trust the device with the given MAC address"""
        try:
            self.get_output(f"trust {mac_address}")
        except Exception as e:
            print(e)
            return False
        else:
            res = self.process.expect(
                [".*not available\r\n", "trust succe", EOF]
            )
            return res == 1

    def remove(self, mac_address):
        """Remove paired device by mac address, return success of the operation."""
        try:
            self.send(f"remove {mac_address}", 3)
        except Exception as e:
            print(e)
            return False
        else:
            res = self.process.expect(
                ["not available", "Device has been removed", EOF]
            )
            return res == 1

    def connect(self, mac_address):
        """Try to connect to a device by mac address."""
        try:
            self.send(f"connect {mac_address}", 2)
        except Exception as e:
            print(e)
            return False
        else:
            res = self.process.expect(
                ["Failed to connect", "Connection successful", EOF]
            )
            return res == 1

    def disconnect(self, mac_address):
        """Try to disconnect to a device by mac address."""
        try:
            self.send(f"disconnect {mac_address}", 2)
        except Exception as e:
            print(e)
            return False
        else:
            res = self.process.expect(
                ["Failed to disconnect", "Successful disconnected", EOF]
            )
            return res == 1

    def agent_noinputnooutput(self):
        """Start agent"""
        try:
            self.send("agent NoInputNoOutput")
        except Exception as e:
            print(e)

    def agent_off(self):
        """Stop agent"""
        try:
            self.send("agent off")
        except Exception as e:
            print(e)

    def default_agent(self):
        """Start default agent"""
        try:
            self.send("default-agent")
        except Exception as e:
            print(e)

    def pairable_on(self):
        """Enable Pairable"""
        try:
            self.send("pairable on")
        except Exception as e:
            print(e)

    def pairable_off(self):
        """Disbale Pairable"""
        try:
            self.send("pairable off")
        except Exception as e:
            print(e)


iBluetoothctl = Bluetoothctl()
