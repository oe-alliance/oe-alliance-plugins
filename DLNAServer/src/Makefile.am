installdir = $(pkglibdir)/python/Plugins/Extensions/DLNAServer

install_PYTHON = \
	dlnaserver \
	__init__.py \
	plugin.py

install-data-hook:
	@chmod +x $(DESTDIR)$(installdir)/dlnaserver

