AC_INIT([enigma2-oe-alliance-plugins],[1.0])
AM_INIT_AUTOMAKE([dist-bzip2 foreign no-define tar-pax])
AC_CONFIG_HEADERS([enigma2-plugins-config.h])

# Silent rules are available since 1.11, but older versions
# are still in use. So don't use them unconditionally.
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

AC_USE_SYSTEM_EXTENSIONS
AC_SYS_LARGEFILE

AC_PROG_CC
AC_PROG_CXX
m4_ifdef([LT_INIT], [LT_INIT], [AC_PROG_LIBTOOL])
AC_CONFIG_MACRO_DIR([m4])

AC_CHECK_HEADERS([dbox/fp.h dbox/lcd-ks0713.h])

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))

AM_PATH_PYTHON
AX_PYTHON_DEVEL
AX_PTHREAD

TUXBOX_APPS_DVB

AC_ARG_WITH(boxtype,
	[  --with-boxtype=NAME box type [[none,dm7025,dm800...]]],
	[BOXTYPE="$withval"],[BOXTYPE="dm800"])
AC_SUBST(BOXTYPE)
AC_DEFINE_UNQUOTED(BOXTYPE,"$BOXTYPE",[box type])

AM_CONDITIONAL(DREAMBOX, test `echo "$BOXTYPE" | cut -b 1-2` == "dm")
AM_CONDITIONAL(VUPLUS, test `echo "$BOXTYPE" | cut -b 1-2` == "vu")
AM_CONDITIONAL(XTREND, test `echo "$BOXTYPE" | cut -b 1-2` == "et")
AM_CONDITIONAL(TECHNOMATE, test `echo "$BOXTYPE" | cut -b 1-2` == "tm")
AM_CONDITIONAL(GIGABLUE, test `echo "$BOXTYPE" | cut -b 1-2` == "gb")
AM_CONDITIONAL(ODIN, test `echo "$BOXTYPE" | cut -b 1-4` == "odin")
AM_CONDITIONAL(VENTON, test `echo "$BOXTYPE" | cut -b 1-6` == "venton")
AM_CONDITIONAL(VUUNO, test "$BOXTYPE" == vuuno)
AM_CONDITIONAL(VUULTIMO, test "$BOXTYPE" == vuultimo)
AM_CONDITIONAL(VUSOLO, test "$BOXTYPE" == vusolo)
AM_CONDITIONAL(VUDUO, test "$BOXTYPE" == vuduo)
AM_CONDITIONAL(ET5X00, test "$BOXTYPE" == et5x00)
AM_CONDITIONAL(ET6X00, test "$BOXTYPE" == et6x00)
AM_CONDITIONAL(ET9X00, test "$BOXTYPE" == et9x00)
AM_CONDITIONAL(ODINM9, test "$BOXTYPE" == odinm9)
AM_CONDITIONAL(TMTWIN, test "$BOXTYPE" == tmtwin)
AM_CONDITIONAL(GB800SOLO, test "$BOXTYPE" == gb800solo)
AM_CONDITIONAL(GB800SE, test "$BOXTYPE" == gb800se)
AM_CONDITIONAL(GB800UE, test "$BOXTYPE" == gb800ue)
AM_CONDITIONAL(GBQUAD, test "$BOXTYPE" == gbquad)
AM_CONDITIONAL(VENTONHDX, test "$BOXTYPE" == venton-hdx)

PKG_CHECK_MODULES(ENIGMA2, enigma2)
PKG_CHECK_MODULES(GSTREAMER, gstreamer-0.10 gstreamer-pbutils-0.10)
PKG_CHECK_MODULES(LIBCRYPTO, libcrypto)

AC_ARG_WITH(tpm,
	AS_HELP_STRING([--with-tpm], [enable plugins that require a TPM]),
	[with_tpm="$withval"],[with_tpm="no"])
if test "$with_tpm" = "yes"; then
	AC_DEFINE([HAVE_TPM],[1],[Define to 1 to enable plugins that require a TPM])
fi
AM_CONDITIONAL(TPM, test "$with_tpm" = "yes")

AC_ARG_WITH(debug,
	AS_HELP_STRING([--without-debug],[disable debugging code]),
	[with_debug="$withval"],[with_debug="yes"])
if test "$with_debug" = "yes"; then
	DEBUG_CFLAGS="-ggdb3"
	AC_DEFINE([DEBUG],[1],[Define to 1 to enable debugging code])
fi
AC_SUBST(DEBUG_CFLAGS)

AC_ARG_WITH(po,
	AS_HELP_STRING([--with-po],[enable updating of po files]),
	[with_po="$withval"],[with_po="no"])
if test "$with_po" = "yes"; then
	AC_PATH_PROG(MSGINIT, msginit)
	AC_PATH_PROG(MSGMERGE, msgmerge)
	AC_PATH_PROG(MSGUNIQ, msguniq)
	AC_PATH_PROG(XGETTEXT, xgettext)
	if test -z "$MSGINIT" -o -z "$MSGMERGE" -o -z "$MSGUNIQ" -o -z "$XGETTEXT"; then
		AC_MSG_ERROR([Could not find required gettext tools])
	fi
fi
AM_CONDITIONAL(UPDATE_PO, test "$with_po" = "yes")

AC_CONFIG_FILES([
Makefile

Blindscan/Makefile
Blindscan/src/Makefile
Blindscan/meta/Makefile
Blindscan/po/Makefile

DLNABrowser/Makefile
DLNABrowser/src/Makefile
DLNABrowser/meta/Makefile

DLNAServer/Makefile
DLNAServer/src/Makefile
DLNAServer/meta/Makefile

FirmwareUpgrade/Makefile
FirmwareUpgrade/src/Makefile
FirmwareUpgrade/meta/Makefile
FirmwareUpgrade/po/Makefile

FPGAUpgrade/Makefile
FPGAUpgrade/src/Makefile
FPGAUpgrade/meta/Makefile
FPGAUpgrade/po/Makefile

TmTwinFanControl/Makefile
TmTwinFanControl/src/Makefile
TmTwinFanControl/meta/Makefile
TmTwinFanControl/po/Makefile

StreamTV/Makefile
StreamTV/src/Makefile
StreamTV/meta/Makefile
StreamTV/icons/Makefile

VentonFancontrol/Makefile
VentonFancontrol/src/Makefile
VentonFancontrol/meta/Makefile
VentonFancontrol/po/Makefile

VFDGiga/Makefile
VFDGiga/src/Makefile
VFDGiga/po/Makefile

VuRemote/Makefile
VuRemote/src/Makefile
VuRemote/meta/Makefile
VuRemote/po/Makefile

VuDuoFanControl/Makefile
VuDuoFanControl/src/Makefile
VuDuoFanControl/meta/Makefile
VuDuoFanControl/po/Makefile

VuplusEvent/Makefile
VuplusEvent/src/Makefile
VuplusEvent/meta/Makefile
VuplusEvent/po/Makefile

VuUnoFanControl/Makefile
VuUnoFanControl/src/Makefile
VuUnoFanControl/meta/Makefile
VuUnoFanControl/po/Makefile

XtrendFancontrol/Makefile
XtrendFancontrol/src/Makefile
XtrendFancontrol/meta/Makefile
XtrendFancontrol/po/Makefile

XtrendRemote/Makefile
XtrendRemote/src/Makefile
XtrendRemote/meta/Makefile
XtrendRemote/po/Makefile
])
AC_OUTPUT
