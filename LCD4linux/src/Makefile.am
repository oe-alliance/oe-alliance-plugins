SUBDIRS = data meteo wetter renderer

installdir = $(libdir)/enigma2/python/Plugins/Extensions/LCD4linux

install_PYTHON = *.py

install_SCRIPTS = FritzCallUserAction.sh
install_DATA = plugin.png History.txt

if SH4
SUBDIRS += sh4
endif

if MIPSEL
SUBDIRS += mips
endif

if CUBE
SUBDIRS += cube
endif

if WETEKPLAY
SUBDIRS += wetek
endif

if VUSOLO4K
SUBDIRS += solo4k
endif