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
AM_CONDITIONAL(IQON, test `echo "$BOXTYPE" | cut -b 1-4` == "iqon")
AM_CONDITIONAL(GIGABLUE, test `echo "$BOXTYPE" | cut -b 1-2` == "gb")
AM_CONDITIONAL(ODIN, test `echo "$BOXTYPE" | cut -b 1-4` == "odin")
AM_CONDITIONAL(VENTON, test `echo "$BOXTYPE" | cut -b 1-6` == "venton")
AM_CONDITIONAL(VUUNO, test "$BOXTYPE" == vuuno)
AM_CONDITIONAL(VUULTIMO, test "$BOXTYPE" == vuultimo)
AM_CONDITIONAL(VUSOLO, test "$BOXTYPE" == vusolo)
AM_CONDITIONAL(VUDUO2, test "$BOXTYPE" == vuduo2)
AM_CONDITIONAL(VUSOLO2, test "$BOXTYPE" == vusolo2)
AM_CONDITIONAL(VUDUO, test "$BOXTYPE" == vuduo)
AM_CONDITIONAL(ET4X00, test "$BOXTYPE" == et4x00)
AM_CONDITIONAL(ET5X00, test "$BOXTYPE" == et5x00)
AM_CONDITIONAL(ET6X00, test "$BOXTYPE" == et6x00)
AM_CONDITIONAL(ET9X00, test "$BOXTYPE" == et9x00)
AM_CONDITIONAL(ODINM7, test "$BOXTYPE" == odinm7)
AM_CONDITIONAL(ODINM9, test "$BOXTYPE" == odinm9)
AM_CONDITIONAL(TMTWIN, test "$BOXTYPE" == tmtwin)
AM_CONDITIONAL(TM2T, test "$BOXTYPE" == tm2t)
AM_CONDITIONAL(TMSINGLE, test "$BOXTYPE" == tmsingle)
AM_CONDITIONAL(IQONIOS100HD, test "$BOXTYPE" == iqonios100hd)
AM_CONDITIONAL(IQONIOS200HD, test "$BOXTYPE" == iqonios200hd)
AM_CONDITIONAL(IQONIOS300HD, test "$BOXTYPE" == iqonios300hd)
AM_CONDITIONAL(GB800SOLO, test "$BOXTYPE" == gb800solo)
AM_CONDITIONAL(GB800SE, test "$BOXTYPE" == gb800se)
AM_CONDITIONAL(GB800UE, test "$BOXTYPE" == gb800ue)
AM_CONDITIONAL(GBQUAD, test "$BOXTYPE" == gbquad)
AM_CONDITIONAL(IXUSSONE, test "$BOXTYPE" == ixussone)
AM_CONDITIONAL(VENTONHDX, test "$BOXTYPE" == ventonhdx)
AM_CONDITIONAL(VENTONHDE, test "$BOXTYPE" == ventonhde)
AM_CONDITIONAL(XP1000, test "$BOXTYPE" == xp1000)
if test `echo "$BOXTYPE" | cut -b 1-2` == "dm"; then
	AC_DEFINE(DREAMBOX, 1, [Dreambox hardware])
fi

AM_CONDITIONAL(HAVE_TEMPFANCONTROL, test "$BOXTYPE" == dm8000 -o "$BOXTYPE" == dm800se -o "$BOXTYPE" == dm500hd -o "$BOXTYPE" == vuuno -o "$BOXTYPE" == vuultimo -o "$BOXTYPE" == vusolo2 -o "$BOXTYPE" == vuduo2 -o "$BOXTYPE" == tmsingle -o "$BOXTYPE" == tmtwin -o "$BOXTYPE" == tm2t -o "$BOXTYPE" == iqonios100hd -o "$BOXTYPE" == iqonios200hd -o "$BOXTYPE" == iqonios300hd)

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

3GModemManager/Makefile
3GModemManager/src/Makefile
3GModemManager/src/script/Makefile
3GModemManager/meta/Makefile

AutoBouquetsMaker/Makefile
AutoBouquetsMaker/images/Makefile
AutoBouquetsMaker/lib/Makefile
AutoBouquetsMaker/meta/Makefile
AutoBouquetsMaker/po/Makefile
AutoBouquetsMaker/providers/Makefile
AutoBouquetsMaker/src/Makefile
AutoBouquetsMaker/src/scanner/Makefile

Blindscan/Makefile
Blindscan/src/Makefile
Blindscan/meta/Makefile
Blindscan/po/Makefile

DLNABrowser/Makefile
DLNABrowser/src/Makefile
DLNABrowser/icons/Makefile
DLNABrowser/meta/Makefile

DLNAServer/Makefile
DLNAServer/src/Makefile
DLNAServer/meta/Makefile

FirmwareUpgrade/Makefile
FirmwareUpgrade/src/Makefile
FirmwareUpgrade/meta/Makefile
FirmwareUpgrade/po/Makefile

Fempa/Makefile
Fempa/meta/Makefile
Fempa/src/Makefile

FPGAUpgrade/Makefile
FPGAUpgrade/src/Makefile
FPGAUpgrade/meta/Makefile
FPGAUpgrade/po/Makefile

GigaBlueVFDControl/Makefile
GigaBlueVFDControl/src/Makefile
GigaBlueVFDControl/meta/Makefile
GigaBlueVFDControl/po/Makefile

HbbTV/Makefile
HbbTV/src/Makefile
HbbTV/meta/Makefile
HbbTV/po/Makefile

OdinM7VFDControl/Makefile
OdinM7VFDControl/src/Makefile
OdinM7VFDControl/meta/Makefile
OdinM7VFDControl/po/Makefile

MICOMUpgrade/Makefile
MICOMUpgrade/src/Makefile
MICOMUpgrade/src/bin/Makefile
MICOMUpgrade/meta/Makefile
MICOMUpgrade/po/Makefile
MICOMUpgrade/buttons/Makefile

OnDemand/Makefile
OnDemand/src/Makefile
OnDemand/src/icons/Makefile
OnDemand/meta/Makefile
OnDemand/po/Makefile

TempFanControl/Makefile
TempFanControl/src/Makefile
TempFanControl/meta/Makefile
TempFanControl/po/Makefile

TransCodingSetup/Makefile
TransCodingSetup/src/Makefile
TransCodingSetup/meta/Makefile
TransCodingSetup/po/Makefile

TunerServer/Makefile
TunerServer/src/Makefile
TunerServer/meta/Makefile
TunerServer/po/Makefile

OpenUitzendingGemist/Makefile
OpenUitzendingGemist/src/Makefile
OpenUitzendingGemist/meta/Makefile
OpenUitzendingGemist/po/Makefile

StreamTV/Makefile
StreamTV/src/Makefile
StreamTV/meta/Makefile
StreamTV/icons/Makefile

VentonFancontrol/Makefile
VentonFancontrol/src/Makefile
VentonFancontrol/meta/Makefile
VentonFancontrol/po/Makefile

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

WebBrowser/Makefile
WebBrowser/src/Makefile
WebBrowser/meta/Makefile
WebBrowser/keymap/Makefile
WebBrowser/icons/Makefile
WebBrowser/po/Makefile

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
