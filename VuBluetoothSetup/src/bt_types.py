from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

BT_EVENT_DEVICE_ADDED 				= 0
BT_EVENT_SCAN_END 					= 1
BT_EVENT_CONNECTED 					= 2
BT_EVENT_DISCONNECTED 				= 3
BT_EVENT_PAIRING_SUCCESS 			= 4
BT_EVENT_PAIRING_FAIL 				= 5
BT_EVENT_PAIRING_TIMEOUT 			= 6
BT_EVENT_PAIRING_WRONG_PIN 			= 7
BT_EVENT_PAIRING_PASSCODE_REQUIRED 	= 8
BT_EVENT_CONNECT_TIMEOUT 			= 9
BT_EVENT_REQUEST_AUDIO_CONNECT		= 10
BT_EVENT_READ_BATTERY_LEVEL			= 11
BT_EVENT_LINK_DOWN = 12
BT_EVENT_NEW_VOICE = 13
BT_EVENT_BT_CONNECTED = 14
BT_EVENT_BT_DISCONNECTED = 15
BT_EVENT_BT_VOICE_START = 16
BT_EVENT_BT_VOICE_STOP	= 17
BT_EVENT_BT_NO_VOICE	= 18

g_event_description = {}
g_event_description[BT_EVENT_DEVICE_ADDED] = "A New Device has been discovered"
g_event_description[BT_EVENT_SCAN_END] = "Discovery finish"
g_event_description[BT_EVENT_CONNECTED] = "Connected"
g_event_description[BT_EVENT_DISCONNECTED] = "Disconnected"
g_event_description[BT_EVENT_PAIRING_SUCCESS] = "Pairing success!"
g_event_description[BT_EVENT_PAIRING_FAIL] = "Pairing failed!"
g_event_description[BT_EVENT_PAIRING_TIMEOUT] = "Pairing Timeout!"
g_event_description[BT_EVENT_PAIRING_WRONG_PIN] = "Pairing wrong pin!"
g_event_description[BT_EVENT_PAIRING_PASSCODE_REQUIRED] = "Pairing passcode required!"
g_event_description[BT_EVENT_CONNECT_TIMEOUT] = "connection timeout!"
g_event_description[BT_EVENT_REQUEST_AUDIO_CONNECT] = "Auto audio connect."
g_event_description[BT_EVENT_READ_BATTERY_LEVEL] = "Battery level"
g_event_description[BT_EVENT_LINK_DOWN] = "Link down"
g_event_description[BT_EVENT_NEW_VOICE] = "new voice"
g_event_description[BT_EVENT_BT_CONNECTED] = "BT dongle is inserted!"
g_event_description[BT_EVENT_BT_DISCONNECTED] = "BT dongle is removed!"

def getEventDesc(event):
	if event in list(g_event_description.keys()):
		return g_event_description[event]
	return "Unknown event"

BT_PROFILE_VU_RC = 1
BT_PROFILE_HID_UNKNOWN = 2
BT_PROFILE_KEYBOARD = 3
BT_PROFILE_MOUSE = 4
BT_PROFILE_HEADPHONE = 6
BT_PROFILE_SPEAKER = 7
BT_PROFILE_GATT_UNKNOWN = 8
BT_PROFILE_GATT_HID = 9

BT_BATTERY_LEVEL_OTA_TH = 60
BT_BATTERY_LEVEL_LOW = 45 + 3

OTA_APP_VERSION = 2
OTA_FILE_APP_VERSION = 7

BT_FIRMWARE_FILEPATH = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/BluetoothSetup/vu_rcu_firmware.bin")

def isAudioProfile(profile):
	return profile in (BT_PROFILE_HEADPHONE, BT_PROFILE_SPEAKER)

BT_VUPLUS_RCU_NAME = "VUPLUS-BLE-RCU"
BT_VOICE_PATH = "/tmp/voice.wav"

btkeyboard = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/BluetoothSetup/bt_keyboard.png"))
btaudio = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/BluetoothSetup/bt_audio.png")) 	
btrc = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/BluetoothSetup/bt_rc.png"))
bticon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/BluetoothSetup/bt_misc.png"))

def getIcon(profile):
	global btkeyboard, btaudio, btrc, bticon
	if profile == BT_PROFILE_VU_RC :
		return btrc
	elif profile in (BT_PROFILE_HID_UNKNOWN, BT_PROFILE_KEYBOARD, BT_PROFILE_MOUSE, BT_PROFILE_GATT_HID):
		return btkeyboard
	elif profile in (BT_PROFILE_HEADPHONE, BT_PROFILE_SPEAKER):
		return btaudio
	else:
		return bticon

