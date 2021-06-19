#!/bin/sh

APPROOT=/usr/bin
APPNAME=browser
SOCKET=/tmp/.browser.support
INDEX=$2

case $1 in
	"start")
		export MOZ_PLUGIN_PATH=/usr/lib/mozilla/plugins
		exec ${APPROOT}/${APPNAME} --enable-spatial-navigation=true --enable-page-cache=false --enable-caret-browsing=false --enable-default-context-menu=false --enable-offline-web-application-cache=false --enable-html5-database=true --enable-html5-local-storage=true --enable-developer-extras=true ${INDEX} > /dev/null 2>&1 &
		;;
	"stop")
		killall -9 ${APPNAME}
		if [ -f ${SOCKET} ]; then
			rm -f ${SOCKET}
		fi
		;;
	"check")
		echo `ps | grep ${APPNAME} | grep -v 'grep' | wc -l`
		;;
	"restart")
		killall -2 ${APPNAME}
		if [ -f ${SOCKET} ]; then
			rm -f ${SOCKET}
		fi
		export MOZ_PLUGIN_PATH=/usr/lib/mozilla/plugins
		exec ${APPROOT}/${APPNAME} --enable-spatial-navigation=true --enable-page-cache=false --enable-caret-browsing=false --enable-default-context-menu=false --enable-offline-web-application-cache=false --enable-html5-database=true --enable-html5-local-storage=true --enable-developer-extras=true ${INDEX} > /dev/null 2>&1 &
		;;
esac

exit 1
