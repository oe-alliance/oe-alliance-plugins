import dvbreader
import datetime
import time

from operator import itemgetter

TIMEOUT_SEC = 30

bouquets_list = []
namespace = 0x11a0000

def readBouquet(bouquet_id):
	print "[DvbScanner] Reading bouquet_id = 0x%x..." % bouquet_id

	fd = dvbreader.open("/dev/dvb/adapter0/demux0", 0xf01, 0x4a, 0xff, 0)
	if fd < 0:
		print "[DvbScanner] Cannot open the demuxer"
		return None

	bat_section_version = -1
	bat_sections_read = []
	bat_sections_count = 0
	bat_content = []

	timeout = datetime.datetime.now()
	timeout += datetime.timedelta(0, TIMEOUT_SEC)
	while True:
		if datetime.datetime.now() > timeout:
			print "[DvbScanner] Timed out"
			break

		section = dvbreader.read_bat(fd, 0x4a)
		if section is None:
			time.sleep(0.1)	# no data.. so we wait a bit
			continue

		if section["header"]["table_id"] == 0x4a:
			if section["header"]["bouquet_id"] != bouquet_id:
				continue

			if section["header"]["version_number"] != bat_section_version:
				bat_section_version = section["header"]["version_number"]
				bat_sections_read = []
				bat_content = []
				bat_sections_count = section["header"]["last_section_number"] + 1

			if section["header"]["section_number"] not in bat_sections_read:
				bat_sections_read.append(section["header"]["section_number"])
				bat_content += section["content"]

				if len(bat_sections_read) == bat_sections_count:
					break

	dvbreader.close(fd)
	
	bouquet_name = None
	for section in bat_content:
		if section["descriptor_tag"] == 0x47:
			bouquet_name = section["description"]
			break

	if bouquet_name is None:
		print "[DvbScanner] Canno get bouquet name for bouquet_id = 0x%x" % bouquet_id
		return
		
	for section in bat_content:
		if section["descriptor_tag"] == 0xd4:
			bouquet = {
				"name": bouquet_name + " - " + section["description"],
				"region": section["region_id"],
				"bouquet": bouquet_id,
				"namespace": namespace
			}
			bouquets_list.append(bouquet)

	print "[DvbScanner] Done"


#for bouquet_id in [0x100, 0x101]:
for bouquet_id in [0x100, 0x101, 0x102, 0x103, 0x110, 0x111, 0x112, 0x113, 0x118, 0x119, 0x11a, 0x11b]:
	readBouquet(bouquet_id)

bouquets_list = sorted(bouquets_list, key=itemgetter('name'))
for bouquet in bouquets_list:
	key = "freesat_%x_%x" % (bouquet["bouquet"], bouquet["region"])
	name = bouquet["name"].replace("&", "&amp;")
	print "<configuration key=\"%s\" bouquet=\"0x%x\" region=\"0x%x\" namespace=\"0x%x\">%s</configuration>" % (key, bouquet["bouquet"], bouquet["region"], bouquet["namespace"], name)