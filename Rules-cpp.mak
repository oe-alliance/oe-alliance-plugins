AM_CFLAGS = -Wall

AM_CPPFLAGS = \
	@PYTHON_CPPFLAGS@ \
	-include Python.h \
	-include enigma2-plugins-config.h

AM_CXXFLAGS = \
	-Wall \
	-fno-exceptions \
	@PTHREAD_CFLAGS@

PLUGIN_LIBTOOL_FLAGS = \
	-avoid-version \
	-module \
	-shared
