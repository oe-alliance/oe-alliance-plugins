#!/bin/sh
# AutoBouquets E2 28.2E by LraiZer for www.ukcvs.org - 21st August 2012

echo '
AutoBouquets E2 28.2E by LraiZer
################################
#   HOMEPAGE:  www.ukcvs.org   #
################################

version date - 21st August 2012

USAGE:
1) perform a scan on 28.2e to generate latest lamedb
2) zap to any active channel on satellite 28.2e
3) select AutoBouquets E2 plugin from plugin menu
4) select your local SD or HD area from the list
5) wait a few minutes while your bouquets are generated
6) Have fun with your new bouquets direct from the stream ;)
'

date
rm -f -r /tmp/*.tv
rm -f -r /tmp/*.radio
if [ ! -e /usr/bin/dvbsnoop ]; then
	echo "dvbsnoop not found!"
	exit 0
fi

if ! wget -q -O - http://127.0.0.1/web/about|grep -q 'onid>2<'; then
	echo "please zap to an ACTIVE 28.2E channel"
	exit 0
fi

echo `date` >/tmp/autobouquets.log

if [ ! "$2" = "" ]; then
	DATA="$1"
	REGION="$2"
else
	DATA="4101"
	REGION="07"
fi

if [ ! "$3" = "" ]; then
	HDFIRST="$3"
else
	HDFIRST="N"
fi

echo "getting data set $DATA, region set $REGION"
echo "reading Bouquet Association Table, please wait..."
{ sleep 5; [ ! -s /tmp/dvb.txt ] && killall -9 dvbsnoop; } &
dvbsnoop -nph -n 500 0x11 >/tmp/dvb.txt
if [ ! -s /tmp/dvb.txt ] || ! grep -q 'Original_network_ID: 2 ' /tmp/dvb.txt >/dev/null 2>&1; then
	echo "no data available, dvbsnoop timed out!"
	echo "please zap to an ACTIVE 28.2E channel"
	rm -f /tmp/autobouquets.log
	rm -f /tmp/dvb.txt
	exit 0
fi

echo "getting references for $DATA data sections"
grep -n "Bouquet_ID: $DATA" /tmp/dvb.txt | cut -d ":" -f1 >/tmp/sections_ref.txt

echo "reading section numbers..."
dvb=`sed 'q' /tmp/sections_ref.txt`
sec_num_first=`sed -n "$(($dvb+4)){p}" /tmp/dvb.txt | cut -d " " -f2`
sec_num_last=`sed -n "$(($dvb+5)){p}" /tmp/dvb.txt | cut -d " " -f2`
echo "first section is $sec_num_first, last section is $sec_num_last"

if [ $sec_num_first -eq 0 ]; then
	sec_num_cycle=$sec_num_last
else
	sec_num_cycle=$(($sec_num_first-1))
fi

while read ln; do
	dvb1=$(($ln+4))
	sec_num=`sed -n "${dvb1}{p}" /tmp/dvb.txt | cut -d " " -f2`
	sed -n "$(($dvb1-17)),/^CRC/p" /tmp/dvb.txt >>/tmp/sections.txt
	echo "`date` $DATA-$sec_num@$dvb1"
	[ $sec_num -eq $sec_num_cycle ] && break
done < /tmp/sections_ref.txt
rm -f /tmp/sections_ref.txt
rm -f /tmp/dvb.txt

echo "Bouquet_data: $DATA" >/tmp/data.txt
TS='    Transport_stream_ID'
OO='                 00'
sed -n '/\('"$TS\|$OO"'\)/p' /tmp/sections.txt >>/tmp/data.txt
rm -f /tmp/sections.txt

sed -i 's/\(.\{74\}\).*/\1/;s/^[ \t]*//;s/  / /g' /tmp/data.txt
rm -f /tmp/region.txt

full_line="false"
while read ln; do
	case "$ln" in
		"Transport_stream_ID"*)
			if [ $full_line = "true" ] ; then
				echo "$TSID$SID" >>/tmp/region.txt
			fi
			TSID=`echo "$ln"|sed 's/.*x\(.*\)).*/\1/'`
			SID=""
		;;
		"0000"*)
			if [ $full_line = "true" ] ; then
				echo "$TSID$SID" >>/tmp/region.txt
			fi
			SID="`echo "$ln"|sed 's/^.....\(.*\)/\1/'`"
			full_line="true"
		;;
		"00"*)
			SID="$SID`echo "$ln"|sed 's/^.....\(.*\)/\1/'`"
			if [ ${#ln} -eq 53 ]; then
				full_line="true"
			else
				full_line="false"
				echo "$TSID$SID" >>/tmp/region.txt
			fi
		;;
	esac
done < /tmp/data.txt
rm -f /tmp/data.txt

grep '^........'"$REGION" /tmp/region.txt >/tmp/area.txt
grep '^.....ff' /tmp/region.txt >>/tmp/area.txt
rm -f /tmp/region.txt

echo '
Processing Services, please wait...
'
while read ln; do
	count=1
	number=7
	services=$((${#ln} / 27 ))
	while [ $count -le $services ]; do
		echo "$ln" | sed 's/^\(.\{4\}\).\{'$number'\}\(..\).\(..\).\(..\).\(..\).\(..\).\(..\).\(..\).*/\7\8 \5\6 #SERVICE 1:0:\4:\2\3:\1/' >>/tmp/services_unsorted.txt
		number=$(($number+27))
		count=$(($count+1))
	done
done < /tmp/area.txt
rm -f /tmp/area.txt

#temp hack to manually add none regional irish
if [ ! "$REGION" = "21" -a ! "$REGION" = "32" ]; then
	#423 Setanta Ireland
	echo '01a7 0e11 #SERVICE 1:0:01:c7a7:096c' >>/tmp/services_unsorted.txt
	#424 Setanta Sports1
	echo '01a8 11c7 #SERVICE 1:0:01:c7a8:096c' >>/tmp/services_unsorted.txt
fi

cat /tmp/services_unsorted.txt|sort >/tmp/services.txt
rm -f /tmp/services_unsorted.txt

bouquet="1"
bouquetname(){
bouquet=$(($bouquet+1)); bq=$1
echo "writing... userbouquet.ukcvs$bq.tv < $2"
echo -e "#NAME 28.2E -- $2 --\n#SERVICE 1:64:1:0:0:0:0:0:0:0:\n#DESCRIPTION $2" >>/tmp/userbouquet.ukcvs$bq.tv
echo -e "#SERVICE 1:64:$bouquet:0:0:0:0:0:0:0:\n#DESCRIPTION $2" >>/tmp/userbouquet.ukcvs_bq.tv
echo -e "#NAME 28.2E -- High Definition --\n#SERVICE 1:64:1:0:0:0:0:0:0:0:\n#DESCRIPTION $2" >>/tmp/userbouquet.ukcvs_hd.tv
echo '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.ukcvs'$bq'.tv" ORDER BY bouquet' >>/tmp/bouquets.tv
}

bouquetmarker(){
	case "$1" in
		"101")
			bouquetname "01" "Entertainment"
		;;
		"240")
			bouquetname "02" "Lifestyle and Culture"
		;;
		"301")
			bouquetname "03" "Movies"
		;;
		"350")
			bouquetname "04" "Music"
		;;
		"401")
			bouquetname "05" "Sports"
		;;
		"501")
			bouquetname "06" "News"
		;;
		"520")
			bouquetname "07" "Documentaries"
		;;
		"580")
			bouquetname "08" "Religious"
		;;
		"601")
			bouquetname "09" "Kids"
		;;
		"640")
			bouquetname "0a" "Shopping"
		;;
		"700")
			bouquetname "0b" "Sky Box Office"
		;;
		"780")
			bouquetname "0c" "International"
		;;
		"861")
			bouquetname "0d" "Gaming and Dating"
		;;
		"881")
			bouquetname "0e" "Specialist"
		;;
		"889")
			bouquetname "0f" "Bonus channels"
		;;
		"899")
			bouquetname "10" "Sky Information"
		;;
		"900")
			bouquetname "11" "Adult"
		;;
		"950")
			bouquetname "12" "Other"
		;;
		"65535")
			case "$2" in
				"1391")
					bouquetname "13" "Sky Sports Interactive"
				;;
				"2143")
					bouquetname "14" "BBC Interactive"
				;;
			esac
		;;
	esac
}

placeholder(){
cnt=$3
while [ $cnt -lt $1 ]; do
	cnt=$(($cnt+1))
echo -e '#SERVICE 1:320:1:0:0:0:0:0:0:0:\n#DESCRIPTION  ' >>/tmp/userbouquet.ukcvs_bq.tv
if [ $HDFIRST = "Y" ]; then
	echo -e '#SERVICE 1:320:1:0:0:0:0:0:0:0:\n#DESCRIPTION  ' >>/tmp/userbouquet.ukcvs$bq.tv
fi
bouquetmarker "$cnt" "$2"
done
}

echo "#NAME 28.2E ---- UK Bouquets ----
#SERVICE 1:64:1:0:0:0:0:0:0:0:
#DESCRIPTION 28.2E -- UK Bouquets --
#SERVICE 1:0:1:11a3:7dc:2:11a0000:0:0:0:
#DESCRIPTION Created By AutoBouquets E2
#SERVICE 1:0:1:11a3:7dc:2:11a0000:0:0:0:
#DESCRIPTION Coding and Scripts by LraiZer
#SERVICE 1:0:1:11a3:7dc:2:11a0000:0:0:0:
#DESCRIPTION Developed by www.ukcvs.org
#SERVICE 1:0:1:11a3:7dc:2:11a0000:0:0:0:
#DESCRIPTION Created On `date`
#SERVICE 1:0:1:11a3:7dc:2:11a0000:0:0:0:
#DESCRIPTION Plugin Version date - 21st August 2012" >/tmp/userbouquet.ukcvs_bq.tv

bq="00"
echo -e '#NAME UKCVS - Bouquets (TV)\n#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.ukcvs00.tv" ORDER BY bouquet' >/tmp/bouquets.tv

echo 'writing... userbouquet.ukcvs00.tv < 28.2E UK Bouquets'

count=0
while read ln; do
	count=$(($count+1))
	tmpa=`echo $ln | cut -d ":" -f1 | sed 's/^.\{10\}\(.*\)/\1/'`
	tmpb=`echo $ln | cut -d ":" -f2`
	tmpc=`echo $ln | cut -d ":" -f3`
	sid=`echo $ln | cut -d ":" -f4`
	tsid=`echo $ln | cut -d ":" -f5`
	case $tmpc in
		0*) tmpc=${tmpc:1} ;;
		*) ;;
		esac
	case $sid in
		0*) sid=${sid:1} ;;
		*) ;;
		esac
	case $tsid in
		0*) tsid=${tsid:1} ;;
		*) ;;
		esac
	position=$(printf "%d\n" 0x`echo "$ln"|sed 's/^\(.\{4\}\).*/\1/'`)
	epg=$(printf "%d\n" 0x`echo "$ln"|sed 's/^.\{5\}\(.\{4\}\).*/\1/'`)
# 	channel=`echo "$ln" | sed 's/^.\{10\}\(.*\)/\1/'`
	channel=`echo "${tmpa}:${tmpb}:${tmpc}:${sid}:${tsid}"`

	echo "$channel #EPG $epg #POSITION $position" >>/tmp/autobouquets.log
	case "$tsid" in
		"7db")
			namespace=":0:11a2e8a:0:0:0:"
		;;
		"7e3")
			namespace=":2:11a2f26:0:0:0:"
		;;
		*)
			namespace=":2:11a0000:0:0:0:"
		;;
	esac
	if [ $position -lt 1000 ]; then
		if [ $count -eq $position ]; then
			bouquetmarker "$position" "$epg"
		else
			placeholder "$position" "$epg" "$count"
			count=$position
		fi
		echo "$channel$namespace" >>/tmp/userbouquet.ukcvs_bq.tv
		echo "$channel$namespace" >>/tmp/userbouquet.ukcvs$bq.tv
		if [ $tmpc -eq 19 -o $tmpc -eq 87 ]; then
			echo "$channel$namespace" >>/tmp/userbouquet.ukcvs_hd.tv
		fi
		if [ $position -eq 498 ]; then
			echo "#DESCRIPTION Primetime" >>/tmp/userbouquet.ukcvs_bq.tv
			echo "#DESCRIPTION Primetime" >>/tmp/userbouquet.ukcvs$bq.tv
		fi
		if [ $position -gt 699 -a $position -lt 780 ]; then
			if [ $position -lt 752 -o $position -gt 753 ]; then
				echo "#DESCRIPTION SBO $position" >>/tmp/userbouquet.ukcvs_bq.tv
				echo "#DESCRIPTION SBO $position" >>/tmp/userbouquet.ukcvs$bq.tv
			fi
		fi
	else
		bouquetmarker "$position" "$epg"
		if [ $epg -gt 1470 -a $epg -lt 1480 ]; then
			echo "$channel$namespace" >>/tmp/userbouquet.ukcvs_bq.tv
			echo "#DESCRIPTION Sky Sports Interactive $epg" >>/tmp/userbouquet.ukcvs_bq.tv
			echo "$channel$namespace" >>/tmp/userbouquet.ukcvs$bq.tv
			echo "#DESCRIPTION Sky Sports Interactive $epg" >>/tmp/userbouquet.ukcvs$bq.tv
		fi
		if [ $epg -gt 2142 -a $epg -lt 2148 ]; then
			echo "$channel$namespace" >>/tmp/userbouquet.ukcvs_bq.tv
			echo "#DESCRIPTION BBCi $epg" >>/tmp/userbouquet.ukcvs_bq.tv
			echo "$channel$namespace" >>/tmp/userbouquet.ukcvs$bq.tv
			echo "#DESCRIPTION BBCi $epg" >>/tmp/userbouquet.ukcvs$bq.tv
		fi
		if [ $tmpc -eq 19 -o $tmpc -eq 87 ]; then
			echo "$channel$namespace" >>/tmp/userbouquet.ukcvs_hd.tv
		fi
	fi
done < /tmp/services.txt

echo "writing... userbouquet.ukcvs15.tv < High Definition"
if [ $HDFIRST = "Y" ]; then
	echo '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet' >>/tmp/bouquets.tv
	cp /tmp/userbouquet.ukcvs_hd.tv /tmp/userbouquet.ukcvs15.tv
	count=`echo "$(cat /tmp/userbouquet.ukcvs_hd.tv | grep ' 1:0:' | wc -l)"`
	while [ "$count" -lt "100" ]
	do
	echo -e '#SERVICE 1:320:1:0:0:0:0:0:0:0:\n#DESCRIPTION  ' >>/tmp/userbouquet.ukcvs_hd.tv
	count=$(($count + 1))
	done
	cp /tmp/userbouquet.ukcvs_hd.tv /tmp/userbouquet.ukcvs00.tv
else
	echo -e '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.ukcvs15.tv" ORDER BY bouquet\n#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet' >>/tmp/bouquets.tv
	cp /tmp/userbouquet.ukcvs_hd.tv /tmp/userbouquet.ukcvs15.tv
	cat /tmp/userbouquet.ukcvs_bq.tv|sed '14,22d' >/tmp/userbouquet.ukcvs00.tv
fi

echo "writing... userbouquet.ukcvs00.radio < 28.2E UK Radio"
echo "#NAME 28.2E -- UK RADIO --
#SERVICE 1:64:1:0:0:0:0:0:0:0:
#DESCRIPTION 28.2E -- Radio --" >/tmp/userbouquet.ukcvs00.radio
grep '^......... #SERVICE 1:0:02:' /tmp/services.txt | sed 's/^.\{10\}\(.*\)/\1'"$namespace"'/' >>/tmp/userbouquet.ukcvs00.radio
echo '#NAME UKCVS - Bouquets (RADIO)
#SERVICE 1:7:2:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.ukcvs00.radio" ORDER BY bouquet
#SERVICE 1:7:2:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.radio" ORDER BY bouquet' >/tmp/bouquets.radio
rm -f /tmp/services.txt

if [ -e /etc/enigma2/bouquets.tv ]; then
	if grep -q 'userbouquet.ukcvs' /etc/enigma2/bouquets.tv >/dev/null 2>&1; then
		rm -f /tmp/bouquets.tv
		rm -f /tmp/bouquets.radio
	else
		sed -i '$d' /tmp/bouquets.tv
		sed -i '$d' /tmp/bouquets.radio
		cat /etc/enigma2/bouquets.tv|sed '1d' >>/tmp/bouquets.tv
		cat /etc/enigma2/bouquets.radio|sed '1d' >>/tmp/bouquets.radio
	fi
fi

mv /tmp/*.tv /etc/enigma2/
mv /tmp/*.radio /etc/enigma2/

echo `date` >>/tmp/autobouquets.log
mv /tmp/autobouquets.log /usr/lib/enigma2/python/Plugins/Extensions/AutoBouquets/

echo '
Updating Bouquets, Please Wait...'
wget -q -O - http://127.0.0.1/web/servicelistreload?mode=0 >/dev/null

echo '
######################################################
# BOUQUET PROCESSING NOW COMPLETE! press EXIT button #
# www.ukcvs.org thanks you for using AutoBouquets E2 #
# HAVE FUN!                                          #
######################################################
'
date
