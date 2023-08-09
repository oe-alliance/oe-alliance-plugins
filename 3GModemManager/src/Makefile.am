installdir = $(libdir)/enigma2/python/Plugins/SystemPlugins/3GModemManager

SUBDIRS = script

install_PYTHON = *.py

install_DATA = *.png *.xml 3gcommand

install-data-hook:
	@chmod +x $(DESTDIR)$(installdir)/3gcommand
