SUBDIRS = data meteo wetter renderer

installdir = $(libdir)/enigma2/python/Plugins/Extensions/LCD4linux

install_PYTHON = *.py

install_SCRIPTS = FritzCallUserAction.sh
install_DATA = plugin.png History.txt

if SH4
    subdir1 = sh4
endif

if MIPSEL
    subdir2 = mips
endif

if HAVE_ARMV7A
    subdir3 = armv7a
endif

if HAVE_CORTEXA9HF
    subdir4 = cortexa9hf
endif

if HAVE_ARMV7AHF
    subdir5 = armv7ahf
endif

if HAVE_AARCH64
    subdir6 = aarch64
endif

if DINOBOT
    subdir7 = dinobot
endif

if HAVE_LCD4LINUX_SUBDIR
    SUBDIRS += $(subdir1)
    SUBDIRS += $(subdir2)
    SUBDIRS += $(subdir3)
    SUBDIRS += $(subdir4)
    SUBDIRS += $(subdir5)
    SUBDIRS += $(subdir6)
    SUBDIRS += $(subdir7)
endif
