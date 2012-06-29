installdir = $(libdir)/enigma2/python/Plugins/SystemPlugins

SUBDIRS = SABnzbdSetup

if XTREND
SUBDIRS += XtrendFancontrol Blindscan
endif

if ODIN
SUBDIRS += XtrendFancontrol Blindscan
endif

if VUUNO
SUBDIRS += VuUnoFanControl FPGAUpgrade Blindscan RemoteControlCode
endif

if VUULTIMO
SUBDIRS += VuUnoFanControl FirmwareUpgrade Blindscan RemoteControlCode
endif

if VUDUO
SUBDIRS += VuDuoFanControl
endif

if TMTWIN
SUBDIRS += TmTwinFanControl
endif

if GIGABLUE
SUBDIRS += VFDGiga
endif
