AC_INIT(plugins,0.0.1)
AM_INIT_AUTOMAKE(plugins,0.0.1)

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))

AM_PATH_PYTHON
AC_PYTHON_DEVEL

AC_PROG_CXX

CPPFLAGS="$CPPFLAGS $PYTHON_CPPFLAGS"
LDFLAGS="$LDFLAGS $PYTHON_LDFLAGS"

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

AC_CONFIG_FILES([
Makefile
src/Makefile
src/Extensions/Makefile
src/Extensions/VuplusEvent/Makefile
src/Extensions/VuplusEvent/meta/Makefile
src/SystemPlugins/Makefile
src/SystemPlugins/Blindscan/Makefile
src/SystemPlugins/Blindscan/meta/Makefile
src/SystemPlugins/FirmwareUpgrade/Makefile
src/SystemPlugins/FirmwareUpgrade/meta/Makefile
src/SystemPlugins/FPGAUpgrade/Makefile
src/SystemPlugins/FPGAUpgrade/meta/Makefile
src/SystemPlugins/TmTwinFanControl/Makefile
src/SystemPlugins/TmTwinFanControl/meta/Makefile
src/SystemPlugins/RemoteControlCode/Makefile
src/SystemPlugins/RemoteControlCode/meta/Makefile
src/SystemPlugins/SABnzbdSetup/Makefile
src/SystemPlugins/VFDGiga/Makefile
src/SystemPlugins/VuDuoFanControl/Makefile
src/SystemPlugins/VuDuoFanControl/meta/Makefile
src/SystemPlugins/VuUnoFanControl/Makefile
src/SystemPlugins/VuUnoFanControl/meta/Makefile
src/SystemPlugins/XtrendFancontrol/Makefile
src/SystemPlugins/XtrendFancontrol/meta/Makefile
po/Makefile
])
AC_OUTPUT
