#!/bin/bash

GCC=/home/skaman/oe-alliance/build-enviroment/builds/opensif/odinm9/tmp/sysroots/i686-linux/usr/bin/mips32el-oe-linux/mipsel-oe-linux-gcc 
PYTHON_INC_PATH=/home/skaman/oe-alliance/build-enviroment/builds/opensif/odinm9/tmp/sysroots/odinm9/usr/include/python2.7/

FTP_USER=root
FTP_PASSWORD=nopass
FTP_HOST=172.16.1.119

$GCC dvbreader.c -shared -fPIC -o dvbreader.so -I$PYTHON_INC_PATH

ncftpput -m -u $FTP_USER -p $FTP_PASSWORD $FTP_HOST /home/root/scanner dvbreader.so
