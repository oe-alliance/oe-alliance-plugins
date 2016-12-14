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
AC_PATH_PROG(MSGINIT, msginit, AC_MSG_ERROR(Could not find msginit))
AC_PATH_PROG(MSGMERGE, msgmerge, AC_MSG_ERROR(Could not find msgmerge))
AC_PATH_PROG(MSGUNIQ, msguniq, AC_MSG_ERROR(Could not find msguniq))
AC_PATH_PROG(XGETTEXT, xgettext, AC_MSG_ERROR(Could not find xgettext))

AM_PATH_PYTHON
AX_PYTHON_DEVEL
AX_PTHREAD

AC_ARG_WITH(arch,
	[  --with-arch=NAME box arch [[none,ah4,mipsel...]]],
	[ARCH="$withval"],[ARCH="mipsel"])
AC_SUBST(ARCH)
AC_DEFINE_UNQUOTED(ARCH,"$ARCH",[box arch])

AM_CONDITIONAL(SH4, test `echo "$ARCH" | cut -b 1-3` == "sh4")
AM_CONDITIONAL(MIPSEL, test `echo "$ARCH" | cut -b 1-6` == "mipsel")

AC_ARG_WITH(boxtype,
	[  --with-boxtype=NAME box type [[none,dm7025,dm800...]]],
	[BOXTYPE="$withval"],[BOXTYPE="dm800"])
AC_SUBST(BOXTYPE)
AC_DEFINE_UNQUOTED(BOXTYPE,"$BOXTYPE",[box type])

AM_CONDITIONAL(AZBOX, test `echo "$BOXTYPE" | cut -b 1-5` == "azbox")
AM_CONDITIONAL(CUBE, test `echo "$BOXTYPE" | cut -b 1-4` == "cube")
AM_CONDITIONAL(DAGS, test `echo "$BOXTYPE" | cut -b 1-4` == "dags")
AM_CONDITIONAL(DREAMBOX, test `echo "$BOXTYPE" | cut -b 1-2` == "dm")
AM_CONDITIONAL(VUPLUS, test `echo "$BOXTYPE" | cut -b 1-2` == "vu")
AM_CONDITIONAL(XTREND, test `echo "$BOXTYPE" | cut -b 1-2` == "et")
AM_CONDITIONAL(INI, test `echo "$BOXTYPE" | cut -b 1-3` == "ini")
AM_CONDITIONAL(GIGABLUE, test `echo "$BOXTYPE" | cut -b 1-2` == "gb")
AM_CONDITIONAL(ODIN, test `echo "$BOXTYPE" | cut -b 1-4` == "odin")
AM_CONDITIONAL(EBOX, test `echo "$BOXTYPE" | cut -b 1-4` == "ebox")
AM_CONDITIONAL(SPARK, test `echo "$BOXTYPE" | cut -b 1-5` == "spark")
AM_CONDITIONAL(WETEK, test `echo "$BOXTYPE" | cut -b 1-5` == "wetek")

AM_CONDITIONAL(AZBOXHD, test "$BOXTYPE" == "azboxhd")
AM_CONDITIONAL(AZBOXME, test "$BOXTYPE" == "azboxme")
AM_CONDITIONAL(AZBOXMINIME, test "$BOXTYPE" == "azboxminime")
AM_CONDITIONAL(BLACKBOX7405, test "$BOXTYPE" == "blackbox7405")
AM_CONDITIONAL(CUBE, test "$BOXTYPE" == "cube")
AM_CONDITIONAL(DAGS1, test "$BOXTYPE" == "dags1")
AM_CONDITIONAL(DAGS2, test "$BOXTYPE" == "dags2")
AM_CONDITIONAL(DAGS3, test "$BOXTYPE" == "dags3")
AM_CONDITIONAL(DAGS4, test "$BOXTYPE" == "dags4")
AM_CONDITIONAL(DAGS5, test "$BOXTYPE" == "dags5")
AM_CONDITIONAL(DAGS6, test "$BOXTYPE" == "dags6")
AM_CONDITIONAL(DAGS7335, test "$BOXTYPE" == "dags7335")
AM_CONDITIONAL(DAGS7362, test "$BOXTYPE" == "dags7362")
AM_CONDITIONAL(DAGS73625, test "$BOXTYPE" == "dags73625")
AM_CONDITIONAL(DAGS7356, test "$BOXTYPE" == "dags7356")
AM_CONDITIONAL(DM500HD, test "$BOXTYPE" == "dm500hd")
AM_CONDITIONAL(DM500HDV2, test "$BOXTYPE" == "dm500hdv2")
AM_CONDITIONAL(DM800, test "$BOXTYPE" == "dm800")
AM_CONDITIONAL(DM800SE, test "$BOXTYPE" == "dm800se")
AM_CONDITIONAL(DM800SEV2, test "$BOXTYPE" == "dm800sev2")
AM_CONDITIONAL(DM7020HD, test "$BOXTYPE" == "dm7020hd")
AM_CONDITIONAL(DM7020HDV2, test "$BOXTYPE" == "dm7020hdv2")
AM_CONDITIONAL(DM8000, test "$BOXTYPE" == "dm8000")
AM_CONDITIONAL(E3HD, test "$BOXTYPE" == "e3hd")
AM_CONDITIONAL(EBOX5000, test "$BOXTYPE" == "ebox5000")
AM_CONDITIONAL(EBOX5100, test "$BOXTYPE" == "ebox5100")
AM_CONDITIONAL(EBOX7358, test "$BOXTYPE" == "ebox7358")
AM_CONDITIONAL(EBOXLUMI, test "$BOXTYPE" == "eboxlumi")
AM_CONDITIONAL(ET4X00, test "$BOXTYPE" == "et4x00")
AM_CONDITIONAL(ET5X00, test "$BOXTYPE" == "et5x00")
AM_CONDITIONAL(ET6X00, test "$BOXTYPE" == "et6x00")
AM_CONDITIONAL(ET9X00, test "$BOXTYPE" == "et9x00")
AM_CONDITIONAL(ET8000, test "$BOXTYPE" == "et8000")
AM_CONDITIONAL(ET10000, test "$BOXTYPE" == "et10000")
AM_CONDITIONAL(VG2000, test `echo "$BOXTYPE"` == "vg2000")
AM_CONDITIONAL(VG5000, test `echo "$BOXTYPE"` == "vg5000")
AM_CONDITIONAL(JJ7362, test `echo "$BOXTYPE"` == "jj7362")
AM_CONDITIONAL(EW7358, test `echo "$BOXTYPE"` == "ew7358")
AM_CONDITIONAL(EW7362, test `echo "$BOXTYPE"` == "ew7362")
AM_CONDITIONAL(EW7356, test `echo "$BOXTYPE"` == "ew7356")
AM_CONDITIONAL(FORMULER1, test "$BOXTYPE" == formuler1)
AM_CONDITIONAL(FORMULER3, test "$BOXTYPE" == formuler3)
AM_CONDITIONAL(FORMULER4, test "$BOXTYPE" == formuler4)
AM_CONDITIONAL(FORMULER4TURBO, test "$BOXTYPE" == formuler4turbo)
AM_CONDITIONAL(G100, test "$BOXTYPE" == "g100")
AM_CONDITIONAL(G101, test "$BOXTYPE" == "g101")
AM_CONDITIONAL(GB800SOLO, test "$BOXTYPE" == "gb800solo")
AM_CONDITIONAL(GB800SE, test "$BOXTYPE" == "gb800se")
AM_CONDITIONAL(GB800UE, test "$BOXTYPE" == "gb800ue")
AM_CONDITIONAL(GB800SEPLUS, test "$BOXTYPE" == "gb800seplus")
AM_CONDITIONAL(GB800UEPLUS, test "$BOXTYPE" == "gb800ueplus")
AM_CONDITIONAL(GBIPBOX, test "$BOXTYPE" == "gbipbox")
AM_CONDITIONAL(GBQUADPLUS, test "$BOXTYPE" == "gbquadplus")
AM_CONDITIONAL(GBQUAD, test "$BOXTYPE" == "gbquad")
AM_CONDITIONAL(GBULTRAUE, test "$BOXTYPE" == "gbultraue")
AM_CONDITIONAL(GBULTRAUEH, test "$BOXTYPE" == "gbultraueh")
AM_CONDITIONAL(GBX1, test "$BOXTYPE" == "gbx1")
AM_CONDITIONAL(GBX2, test "$BOXTYPE" == "gbx2")
AM_CONDITIONAL(GBX3, test "$BOXTYPE" == "gbx3")
AM_CONDITIONAL(GBX3H, test "$BOXTYPE" == "gbx3h")
AM_CONDITIONAL(GB7356, test "$BOXTYPE" == "gb7356")
AM_CONDITIONAL(GB7362, test "$BOXTYPE" == "gb7362")
AM_CONDITIONAL(GB73625, test "$BOXTYPE" == "gb73625")
AM_CONDITIONAL(GB7358, test "$BOXTYPE" == "gb7358")
AM_CONDITIONAL(GB7325, test "$BOXTYPE" == "gb7325")
AM_CONDITIONAL(INIHDE, test "$BOXTYPE" == "inihde")
AM_CONDITIONAL(INIHDE2, test `echo "$BOXTYPE" | cut -b 1-7` == inihde2)
AM_CONDITIONAL(INIHDP, test "$BOXTYPE" == "inihdp")
AM_CONDITIONAL(INIHDX, test "$BOXTYPE" == "inihdx")
AM_CONDITIONAL(IXUSSZERO, test "$BOXTYPE" == "ixusszero")
AM_CONDITIONAL(IXUSSONE, test "$BOXTYPE" == "ixussone")
AM_CONDITIONAL(HD2400, test "$BOXTYPE" == "hd2400")
AM_CONDITIONAL(HD1500, test "$BOXTYPE" == "hd1500")
AM_CONDITIONAL(HD1265, test "$BOXTYPE" == "hd1265")
AM_CONDITIONAL(HD1200, test "$BOXTYPE" == "hd1200")
AM_CONDITIONAL(HD1100, test "$BOXTYPE" == "hd1100")
AM_CONDITIONAL(HD500C, test "$BOXTYPE" == "hd500c")
AM_CONDITIONAL(HD530C, test "$BOXTYPE" == "hd530c")
AM_CONDITIONAL(PROTEK9900LX, test "$BOXTYPE" == "9900lx")
AM_CONDITIONAL(ODINM7, test "$BOXTYPE" == odinm7)
AM_CONDITIONAL(ODINM7S, test "$BOXTYPE" == odinm7s)
AM_CONDITIONAL(ODINM7C, test "$BOXTYPE" == odinm7c)
AM_CONDITIONAL(ODINM9, test "$BOXTYPE" == odinm9)
AM_CONDITIONAL(VP7358CI, test "$BOXTYPE" == "vp7358ci")
AM_CONDITIONAL(VUUNO, test "$BOXTYPE" == vuuno)
AM_CONDITIONAL(VUULTIMO, test "$BOXTYPE" == vuultimo)
AM_CONDITIONAL(VUSOLO, test "$BOXTYPE" == vusolo)
AM_CONDITIONAL(VUSOLOSE, test "$BOXTYPE" == vusolose)
AM_CONDITIONAL(VUDUO, test "$BOXTYPE" == vuduo)
AM_CONDITIONAL(VUSOLO2, test "$BOXTYPE" == vusolo2)
AM_CONDITIONAL(VUSOLO4K, test "$BOXTYPE" == vusolo4k)
AM_CONDITIONAL(VUUNO4K, test "$BOXTYPE" == vuuno4k)
AM_CONDITIONAL(VUULTIMO4K, test "$BOXTYPE" == vuultimo4k)
AM_CONDITIONAL(VUDUO2, test "$BOXTYPE" == vuduo2)
AM_CONDITIONAL(VUZERO, test "$BOXTYPE" == vuzero)
AM_CONDITIONAL(XP1000, test "$BOXTYPE" == xp1000)
AM_CONDITIONAL(S7220S, test `echo "$BOXTYPE"` == "7220s")
AM_CONDITIONAL(S7225S, test `echo "$BOXTYPE"` == "7225s")
AM_CONDITIONAL(S7300S, test `echo "$BOXTYPE"` == "7300s")
AM_CONDITIONAL(S7400S, test `echo "$BOXTYPE"` == "7400s")
AM_CONDITIONAL(SH1, test `echo "$BOXTYPE"` == "sh1")
AM_CONDITIONAL(H3, test `echo "$BOXTYPE"` == "h3")
AM_CONDITIONAL(H5, test `echo "$BOXTYPE"` == "h5")
AM_CONDITIONAL(LC, test `echo "$BOXTYPE"` == "lc")
AM_CONDITIONAL(TRIPLEX, test `echo "$BOXTYPE"` == "triplex")
AM_CONDITIONAL(SPARK, test `echo "$BOXTYPE" | cut -b 1-5` == spark)
AM_CONDITIONAL(XC7362, test "$BOXTYPE" == xc7362)
AM_CONDITIONAL(XC7358, test "$BOXTYPE" == xc7358)
AM_CONDITIONAL(XC7358CI, test "$BOXTYPE" == xc7358ci)
AM_CONDITIONAL(WETEKPLAY, test "$BOXTYPE" == wetekplay)
if test `echo "$BOXTYPE" | cut -b 1-2` == "dm"; then
	AC_DEFINE(DREAMBOX, 1, [Dreambox hardware])
fi

AM_CONDITIONAL(HAVE_TEMPFANCONTROL, test "$BOXTYPE" == dm8000 -o "$BOXTYPE" == dm800se -o "$BOXTYPE" == dm800sev2 -o "$BOXTYPE" == dm500hd -o "$BOXTYPE" == vuuno -o "$BOXTYPE" == vuultimo -o "$BOXTYPE" == vusolo2 -o "$BOXTYPE" == vuduo2 -o "$BOXTYPE" == dags1 -o "$BOXTYPE" == dags2 -o "$BOXTYPE" == dags3 -o "$BOXTYPE" == dags4 -o "$BOXTYPE" == dags5 -o "$BOXTYPE" == dags7335 -o "$BOXTYPE" == dags7362 -o "$BOXTYPE" == dags73625 -o "$BOXTYPE" == dags7356 -o "$BOXTYPE" == triplex)

AM_CONDITIONAL(HAVE_ARMV7A, test "$BOXTYPE" == cube)
AM_CONDITIONAL(HAVE_ARMV7AHF, test "$BOXTYPE" == hd51  -o "$BOXTYPE" == hd52 -o "$BOXTYPE" == vusolo4k -o "$BOXTYPE" == vuuno4k -o "$BOXTYPE" == vuultimo4k -o "$BOXTYPE" == dm900 -o "$BOXTYPE" == sf4008)
AM_CONDITIONAL(HAVE_CORTEXA9HF, test "$BOXTYPE" == wetekplay -o "$BOXTYPE" == wetekplayplus)

AC_CONFIG_FILES([
Makefile

3GModemManager/Makefile
3GModemManager/src/Makefile
3GModemManager/src/script/Makefile
3GModemManager/po/Makefile
3GModemManager/meta/Makefile

AudioEffect/Makefile
AudioEffect/src/Makefile
AudioEffect/meta/Makefile
AudioEffect/po/Makefile

AnimationSetup/Makefile
AnimationSetup/src/Makefile
AnimationSetup/po/Makefile
AnimationSetup/meta/Makefile

Blindscan/Makefile
Blindscan/src/Makefile
Blindscan/meta/Makefile
Blindscan/po/Makefile

BTDevicesManager/Makefile
BTDevicesManager/src/Makefile
BTDevicesManager/meta/Makefile
BTDevicesManager/po/Makefile

DLNABrowser/Makefile
DLNABrowser/src/Makefile
DLNABrowser/icons/Makefile
DLNABrowser/po/Makefile
DLNABrowser/meta/Makefile

DLNAServer/Makefile
DLNAServer/src/Makefile
DLNAServer/po/Makefile
DLNAServer/meta/Makefile

DMBlindscan/Makefile
DMBlindscan/src/Makefile
DMBlindscan/meta/Makefile
DMBlindscan/po/Makefile

FirmwareUpgrade/Makefile
FirmwareUpgrade/src/Makefile
FirmwareUpgrade/meta/Makefile
FirmwareUpgrade/po/Makefile

Fempa/Makefile
Fempa/meta/Makefile
Fempa/src/Makefile
Fempa/po/Makefile

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

INIVFDControl/Makefile
INIVFDControl/src/Makefile
INIVFDControl/meta/Makefile
INIVFDControl/po/Makefile

EWVFDControl/Makefile
EWVFDControl/src/Makefile
EWVFDControl/meta/Makefile
EWVFDControl/po/Makefile

F3LEDControl/Makefile
F3LEDControl/src/Makefile
F3LEDControl/meta/Makefile
F3LEDControl/po/Makefile

VPLEDControl/Makefile
VPLEDControl/src/Makefile
VPLEDControl/meta/Makefile
VPLEDControl/po/Makefile

LCD4linux/Makefile
LCD4linux/src/Makefile
LCD4linux/src/data/Makefile
LCD4linux/src/data/Clock1/Makefile
LCD4linux/src/data/Clock2/Makefile
LCD4linux/src/data/Clock3/Makefile
LCD4linux/src/data/Clock4/Makefile
LCD4linux/src/data/Clock5/Makefile
LCD4linux/src/data/Clock6/Makefile
LCD4linux/src/meteo/Makefile
LCD4linux/src/renderer/Makefile
LCD4linux/src/wetter/Makefile
LCD4linux/src/armv7a/Makefile
LCD4linux/src/armv7ahf/Makefile
LCD4linux/src/cortexa9hf/Makefile
LCD4linux/src/mips/Makefile
LCD4linux/src/sh4/Makefile
LCD4linux/meta/Makefile
LCD4linux/po/Makefile

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

MultiTransCodingSetup/Makefile
MultiTransCodingSetup/src/Makefile
MultiTransCodingSetup/meta/Makefile
MultiTransCodingSetup/po/Makefile

OnDemand/Makefile
OnDemand/src/Makefile
OnDemand/src/icons/Makefile
OnDemand/meta/Makefile
OnDemand/po/Makefile

RemoteChannelStreamConverter/Makefile
RemoteChannelStreamConverter/src/Makefile
RemoteChannelStreamConverter/po/Makefile

SH4BoosterControl/Makefile
SH4BoosterControl/src/Makefile
SH4BoosterControl/meta/Makefile
SH4BoosterControl/po/Makefile

SH4OSDAdjustment/Makefile
SH4OSDAdjustment/src/Makefile
SH4OSDAdjustment/meta/Makefile
SH4OSDAdjustment/po/Makefile

TempFanControl/Makefile
TempFanControl/src/Makefile
TempFanControl/meta/Makefile
TempFanControl/po/Makefile

TerrestrialScan/Makefile
TerrestrialScan/images/Makefile
TerrestrialScan/meta/Makefile
TerrestrialScan/po/Makefile
TerrestrialScan/src/Makefile

TransCodingSetup/Makefile
TransCodingSetup/src/Makefile
TransCodingSetup/meta/Makefile
TransCodingSetup/po/Makefile

TunerServer/Makefile
TunerServer/src/Makefile
TunerServer/meta/Makefile
TunerServer/po/Makefile

ReZap/Makefile
ReZap/src/Makefile
ReZap/meta/Makefile

RCUSelect/Makefile
RCUSelect/src/Makefile
RCUSelect/conf/Makefile
RCUSelect/po/Makefile
RCUSelect/meta/Makefile

SatipClient/Makefile
SatipClient/src/Makefile
SatipClient/po/Makefile
SatipClient/meta/Makefile

SF8VFDControl/Makefile
SF8VFDControl/src/Makefile
SF8VFDControl/meta/Makefile
SF8VFDControl/po/Makefile

StreamTV/Makefile
StreamTV/src/Makefile
StreamTV/meta/Makefile
StreamTV/po/Makefile
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

WebBrowser/Makefile
WebBrowser/src/Makefile
WebBrowser/meta/Makefile
WebBrowser/keymap/Makefile
WebBrowser/icons/Makefile
WebBrowser/po/Makefile

WirelessAccessPoint/Makefile
WirelessAccessPoint/src/Makefile
WirelessAccessPoint/meta/Makefile
WirelessAccessPoint/po/Makefile

XtrendFancontrol/Makefile
XtrendFancontrol/src/Makefile
XtrendFancontrol/meta/Makefile
XtrendFancontrol/po/Makefile

XtrendRemote/Makefile
XtrendRemote/src/Makefile
XtrendRemote/meta/Makefile
XtrendRemote/po/Makefile

SparkVFDControl/Makefile
SparkVFDControl/src/Makefile
SparkVFDControl/meta/Makefile
SparkVFDControl/po/Makefile

SparkUnionTunerType/Makefile
SparkUnionTunerType/src/Makefile
SparkUnionTunerType/po/Makefile
SparkUnionTunerType/meta/Makefile

])
AC_OUTPUT
