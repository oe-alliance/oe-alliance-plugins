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

if HAVE_ARMV7A
SUBDIRS += armv7a
endif

if HAVE_CORTEXA9HF
SUBDIRS += cortexa9hf
endif

if HAVE_ARMV7AHF
SUBDIRS += armv7ahf
endif