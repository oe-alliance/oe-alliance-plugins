====================================================
AutoBouquets E2 for satellite 28.2E 
Version date - 21st August 2012
Coding by LraiZer @ www.ukcvs.org
====================================================

Plugin Usage
----------------
first perform a scan on 28.2e satellite so that you
have the latest lamedb service file for 28.2 East.

next zap to an active channel on 28.2e so that we can
get dvbsnoop to read the bouquet data from the stream.

now its time to select AutoBouquets E2 Plugin from the
plugins menu and choose your nearest localized region.

generated bouquets are prepended to any existing
bouquets so your current bouquets are not overwritten.

sit back and watch for a few minutes as your regional
bouquets are read and generated direct from the stream.


Tips
----------------
if you want 1, 2, 3 button presses for BBC1, BBC2, ITV1.
simply remove your "28.2E ---- UK Bouquets ---" bouquet.
this will remove the official epg numbering and set your
Entertainment bouquet channels to starting with 1, 2, 3.

the Plugin does not re-create any bouquets that have been
previously removed by the user. if for example you remove
the adult bouquet, it will remain removed the next time
you run the plugin and so remain child friendly updatable.

changing the order of the bouquets also remains static and
does not get re-ordered on subsequent runs. if you want to
revert to the first run setup again. then you would be
required to remove all the generated bouquets from the list.


Prerequisites
----------------
dvbsnoop binary is required in /usr/bin/ folder.
frontend GUI should work on systems using Enigma2,
backend script should work on most linux systems.

script requires all the common busybox functions:
grep, sed, cat, printf, wget, echo, mv, rm, date.
also math support in kernel for arithmetic $((1+1))
all these should be standard in your linux image.


Manual Installation - AutoBouquets_E2.rar (archive)
---------------
1) make sure you have dvbsnoop in your /usr/bin/

2) place files onto engima2 box in relevant folders.
   make autobouquets_e2.sh executable (chmod 755)

3) restart Enigma2 to reload AutoBouquets E2 plugin

HOW TO: install required dvbsnoop on openpli image?
telnet to your box and type the following command:

opkg update && opkg install dvbsnoop 


Version infos
---------------
10-08-2012
 first version released to public for testing, this
 is totaly untested, so backup your files first! :)

13-08-2012
 current bouquets are no longer overwritten. if not
 detected as already present in user bouquets, they
 are written to front to preserve official numbering.
 various other code fixes and imporvements also done.

19-08-2012
 new GUI with help button for onbox readme.txt viewing.
 error checks added to stop box lockup on none active.
 added special handling of the sbo channels namespace.
 other file and error checking and various code fixes.

21-08-2012
 added checks to make sure we only process 28.2E sat.
 also .ipk installer for mipsel with dvbsnoop depend.
 
======================================================
  www.ukcvs.org thanks you for using AutoBouquets E2
  thanks to PaphosAL for plugin icon.   HAVE FUN!
======================================================
