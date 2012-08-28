installdir = $(libdir)/enigma2/python/Plugins/SystemPlugins/3GModemManager

SUBDIRS = script

install_PYTHON = \
	__init__.py \
	plugin.py \
	apnlist.xml \
	3gcommand 

install-data-hook:
	@chmod +x $(DESTDIR)$(installdir)/3gcommand

