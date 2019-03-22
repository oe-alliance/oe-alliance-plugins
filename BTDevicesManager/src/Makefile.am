installdir = $(libdir)/enigma2/python/Plugins/Extensions/BTDevicesManager

install_PYTHON = \
	__init__.py \
	bluetoothctl.py \
	plugin.py

install_DATA = plugin.png BTAudioConnect

install-data-hook:
	@chmod +x $(DESTDIR)$(installdir)/BTAudioConnect
