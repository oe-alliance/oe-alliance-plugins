Contents:

1) CustomLCN
2) CustomMix
3) Favourites
4) Simple favourites
5) Provider keys

---------------------------------------------------------------------------------------------- 

CustomLCN
---------

CustomLCN allows channels to be moved around within one single provider. CustomLCN is great 
for providers that don't transmit logical channel numbers or if you want to move channels 
around so they appear at different channel numbers. The CustomLCN list can be complete or 
partial. It doesn't have to be in any particular order but having it sequential will make 
it easier to avoid making errors.

Each time ABM runs it makes an example CustomLCN xml file for each provider that is scanned, 
e.g. 'EXAMPLE_hd_sat_freesat_CustomLCN.xml'. These files are archived in:
/usr/lib/enigma2/python/Plugins/SystemPlugins/AutoBouquetsMaker/custom
To make your own custom LCN file just delete 'EXAMPLE_' from the filename, 
i.e. hd_sat_freesat_CustomLCN.xml. Configurations in the provider xml file, such as channel swap, 
on-top, etc, are done after CustomLCN has been processed.

The following is how to edit the file. Just cut and paste the lines into the order you want. 
DO NOT add any channels into more than one place in the list.

Also don't forget to include the ABM custom folder in your backups otherwise your newly 
created file may be lost during image updates.

This is an example of the original 'EXAMPLE_" file:
<custom>
	<include>yes</include>
	<lcnlist>
		<configuration lcn="101" channelnumber="101" description="BBC One Lon"></configuration>
		<configuration lcn="102" channelnumber="102" description="BBC Two HD"></configuration>
		<configuration lcn="103" channelnumber="103" description="ITV"></configuration>
		<configuration lcn="104" channelnumber="104" description="Channel 4"></configuration>
		<configuration lcn="105" channelnumber="105" description="Channel 5"></configuration>
		<configuration lcn="106" channelnumber="106" description="BBC Three HD"></configuration>
		<configuration lcn="107" channelnumber="107" description="BBC Four HD"></configuration>
		<configuration lcn="108" channelnumber="108" description="BBC One HD"></configuration>
		<configuration lcn="109" channelnumber="109" description="BBC Two Eng"></configuration>
		<configuration lcn="110" channelnumber="110" description="BBC ALBA"></configuration>

This is how to swap channels.		
If you want to swap ITV (103) with BBC Three HD (106) cut and paste both lines.
<custom>
	<include>yes</include>
	<lcnlist>
		<configuration lcn="101" channelnumber="101" description="BBC One Lon"></configuration>
		<configuration lcn="102" channelnumber="102" description="BBC Two HD"></configuration>
		<configuration lcn="106" channelnumber="106" description="BBC Three HD"></configuration>
		<configuration lcn="104" channelnumber="104" description="Channel 4"></configuration>
		<configuration lcn="105" channelnumber="105" description="Channel 5"></configuration>
		<configuration lcn="103" channelnumber="103" description="ITV"></configuration>
		<configuration lcn="107" channelnumber="107" description="BBC Four HD"></configuration>
		<configuration lcn="108" channelnumber="108" description="BBC One HD"></configuration>
		<configuration lcn="109" channelnumber="109" description="BBC Two Eng"></configuration>
		<configuration lcn="110" channelnumber="110" description="BBC ALBA"></configuration>

Now change the lcn numbers. lcn numbers should be in order to avoid errors!!
<custom>
	<include>yes</include>
	<lcnlist>
		<configuration lcn="101" channelnumber="101" description="BBC One Lon"></configuration>
		<configuration lcn="102" channelnumber="102" description="BBC Two HD"></configuration>
		<configuration lcn="103" channelnumber="106" description="BBC Three HD"></configuration>
		<configuration lcn="104" channelnumber="104" description="Channel 4"></configuration>
		<configuration lcn="105" channelnumber="105" description="Channel 5"></configuration>
		<configuration lcn="106" channelnumber="103" description="ITV"></configuration>
		<configuration lcn="107" channelnumber="107" description="BBC Four HD"></configuration>
		<configuration lcn="108" channelnumber="108" description="BBC One HD"></configuration>
		<configuration lcn="109" channelnumber="109" description="BBC Two Eng"></configuration>
		<configuration lcn="110" channelnumber="110" description="BBC ALBA"></configuration>
		
Removing channels.
Channel removal only applies to unsorted lists, i.e. non-LCN providers where the list has not been 
sorted in any way. To remove a channel, just delete the line. NOTE: When <include>is set to 'yes', 
all channels not configured in the custom xml will be added at the end of the main bouquet. This way 
also new services from the provider will be added at the end of the channel list. Any new channels 
will be shown in the ABM log.

Changing 'channel numbers'.
If you wants your own numbering, edit the lcn numbers. lcn numbers should be in order to avoid errors!!
<custom>
	<include>no</include>
	<lcnlist>
		<configuration lcn="1" channelnumber="101" description="BBC One Lon"></configuration>
		<configuration lcn="2" channelnumber="102" description="BBC Two HD"></configuration>
		<configuration lcn="3" channelnumber="103" description="ITV"></configuration>
		<configuration lcn="4" channelnumber="104" description="Channel 4"></configuration>
		<configuration lcn="5" channelnumber="105" description="Channel 5"></configuration>
		<configuration lcn="6" channelnumber="106" description="BBC Three HD"></configuration>
		<configuration lcn="7" channelnumber="107" description="BBC Four HD"></configuration>
		<configuration lcn="8" channelnumber="108" description="BBC One HD"></configuration>
		<configuration lcn="9" channelnumber="109" description="BBC Two Eng"></configuration>
		<configuration lcn="10" channelnumber="110" description="BBC ALBA"></configuration>

NOTE: Be aware of correct sections in the provider xml.
e.g.
	<sections>
		<section number="101">Entertainment</section>
		<section number="200">News and Sport</section>
		<section number="300">Movies</section>
		<section number="400">Lifestyle</section>
		<section number="500">Music</section>
		<section number="600">Children</section>
		<section number="650">Special Interest</section>
		<section number="800">Shopping</section>
		<section number="870">Adult</section>
		<section number="950">Regional</section>
	</sections>
	
Your lcn numbering should match sections. In this example you can add a custom section.
	<sections>
		<section number="1">Custom list</section>
		<section number="101">Entertainment</section>
		<section number="200">News and Sport</section>
		<section number="300">Movies</section>
		<section number="400">Lifestyle</section>
		<section number="500">Music</section>
		<section number="600">Children</section>
		<section number="650">Special Interest</section>
		<section number="800">Shopping</section>
		<section number="870">Adult</section>
		<section number="950">Regional</section>
	</sections>
	
---------------------------------------------------------------------------------------------- 

CustomMix
---------

CustomMiX allows tv channels from one provider to be added to the bouquets of another provider. 
This is great if you mainly use one provider but want to add a few channels from other providers 
but don't want to create a complete list for the other provider. All providers that you want to 
receive channels from must be included in every ABM scan but if you don't want complete bouquets 
from that provider just set all the bouquet creation options to no.

For each provider you wish to add channels to you need to add an xml configuration file. The xml
configuration files reside in /usr/lib/enigma2/python/Plugins/SystemPlugins/AutoBouquetsMaker/custom 
and filenames are made up as follows... "provider_key_CustomMix.xml", e.g. for Sky UK the filename 
would be "sat_282_sky_uk_CustomMix.xml". For other providers please consult the list of provider 
keys below.

This is an example xml configuration file for Sky UK. Filename as above. 

<custommix>
	<inserts>
		<insert provider="cable_uk_virgin" source="150" target="171"></insert> <!-- channel5 hd -->
		<insert provider="cable_uk_virgin" source="110" target="106"></insert> <!-- sky one hd -->
	</inserts>
	<deletes>
		<delete target="170"></delete> <!-- Sky 3D -->
	</deletes>
</custommix>

The "insert" lines are what do the work but all the tags must be present. The "insert" line has 3 
attributes, "provider", "source", and "target". "provider" is the key of provider from which the 
channel is being imported. See below for a list of provider keys. "source" is the channel number 
being imported. And "target" is the slot in the Sky UK bouquet into which that channel will be 
inserted. Each channel that is to be moved requires an "insert" line.

"Delete" lines allow you to remove individual channels from the provider you are customising. Just 
set "target" to the number of the channel you want to remove and it will disappear on the next scan.


---------------------------------------------------------------------------------------------- 

Favourites
----------

Favourites allows the creation of a complete favourites list that will preceed all other ABM bouquets. 
Please note, favourites lists are static. ABM will keep your favourites list up to date if there are 
changes to service references and transponder parameters but obviously it is not going to be updated 
if new channels start broadcasting, so any new channels you want in the list must be added manually.

Channels selected for the favourites list can come from any providers that are being scanned, and these 
providers must be scanned on every ABM run. The filename of the configuration file is:
/usr/lib/enigma2/python/Plugins/SystemPlugins/AutoBouquetsMaker/custom/favourites.xml

Here is an example favourites.xml file.

<favourites>
	<name>My List</name>
	<sections>
		<section number="100">Entertainment</section>
		<section number="200">Movies</section>
		<section number="300">Music</section>
		<section number="400">Sports</section>
		<section number="500">News</section>
		<section number="600">Documentaries</section>
		<section number="700">Kids</section>
		<section number="800">Other</section>
	</sections>
	<inserts>
		<insert provider="sat_282_sky_uk" source="105" target="105"></insert> <!-- channel5 hd -->
		<insert provider="sat_282_sky_uk" source="106" target="206"></insert> <!-- sky one hd -->
	</inserts>
	<bouquets>
		<main>1</main> <!-- 0 or 1 -->
		<sections>1</sections> <!-- 0 or 1 -->
	</bouquets>
</favourites>

"name" is the prefix of you favourites bouquets if you have "prefix" enabled in the ABM menu. "sections" 
is used for writing the section markers to your bouquets. You must have at least one section, and only 
channels with a greater channel number than the first section number will be added to your favourites 
bouquets. The "insert" lines have 3 attributes, "provider", "source", and "target". "provider" is the 
key of provider from which the channel is being imported. See below for a list of provider keys. "source" 
is the channel number being imported. And "target" is the slot in the favourites into which that channel 
will be inserted. Each channel that is to be moved requires an "insert" line. 
"main" has a value of 0 or 1. "0" means no main bouquet will be created and "1" that one will. Same for 
"sections". If "bouquets" -> "sections" is enabled the favourites list will be divided up into sections 
bouquets as per the section numbers above. All tags in the above example a necessary to get this working.


----------------------------------------------------------------------------------------------

Simple favourites
-----------------

You may just want to add a short favourites list to the beginning of one single provider. This is possible 
where the provider's channel numbering does not start at 1 and there is a group of empty slots that could 
be used. For example Sky UK's channel numbering starts at 101, so there are 100 unused slots that could be 
used for favourites. 

To do this create a copy of the provider's file and rename it. Provider's files are stored in:
/usr/lib/enigma2/python/Plugins/SystemPlugins/AutoBouquetsMaker/providers
For example, if you want to do this with Sky UK open the file: sat_282_sky_uk.xml and rename it to something 
like sat_282_my_sky_uk.xml. 

Inside the file change the provider name...

So:
<name>Sky UK</name>

will become [...] or whatever name you choose:
<name>My Sky</name>

The add a new first section at the top of the sections, so sections changes from this:
	<section number="101">Entertainment</section>
	<section number="301">Movies</section>
	<section number="350">Music</section>
	<section number="401">Sports</section>
	
to this:
	<section number="1">My Favourites</section>
	<section number="101">Entertainment</section>
	<section number="301">Movies</section>
	<section number="350">Music</section>
	<section number="401">Sports</section>
	
Lastly you need to add the channels you want to include in your simple favourites list. Lets say 
you want to add the following channels, BBC1 HD (141), BBC2 HD (102), ITV1 HD (178), C4 HD (227) 
and C5 (105), and you want to put those channels into positions 1, 2, 3, 4, and 5 in your simple 
favourites list. Make a Python dictionary as follows:
my_favourites = {141:1, 102:2, 178:3, 227:4, 105:5} # LCN of channel to add followed by position.

Now that has to be added to <servicehacks> with a little bit of code to make it work, as follows:

Here is the code:

#################################################################################################
# add some channels to a favourites bouquet
x = 0
my_favourites = {141:1, 102:2, 178:3, 227:4, 105:5} # LCN of channel to add followed by position.
for n in service["numbers"]:
	if n in my_favourites:
		x = n
		break
if x:
	service["numbers"].append(my_favourites[x])
#################################################################################################
	
This is what it looks like added to <servicehacks>:


#################################################################################################
	<servicehacks>
<![CDATA[
# add some channels to a favourites bouquet
x = 0
my_favourites = {141:1, 102:2, 178:3, 227:4, 105:5} # LCN of channel to add followed by position.
for n in service["numbers"]:
	if n in my_favourites:
		x = n
		break
if x:
	service["numbers"].append(my_favourites[x])
]]>
	</servicehacks>
#################################################################################################
	

If there is already code in <servicehacks> add this code at the end of the <servicehacks> section 
after all other code, and just before the "]]>".

That's it. Just save the file and then select "My Sky" from the ABM providers list and run a scan.

---------------------------------------------------------------------------------------------- 

Provider keys
-------------

Provider name: Caiway (NL)
Provider key: cable_nl_caiway

Provider name: Delta (NL)
Provider key: cable_nl_delta

Provider name: Harderwijk (NL)
Provider key: cable_nl_harderwijk

Provider name: KabelNoord (NL)
Provider key: cable_nl_kabelnoord

Provider name: Kabeltex (NL)
Provider key: cable_nl_kabeltex

Provider name: Pijnacker (NL)
Provider key: cable_nl_pijnacker

Provider name: SKV (NL)
Provider key: cable_nl_skv

Provider name: UPC (NL)
Provider key: cable_nl_upc

Provider name: Ziggo (NL)
Provider key: cable_nl_ziggo

Provider name: Virgin (UK)
Provider key: cable_uk_virgin

Provider name: Sky Italia
Provider key: sat_130_sky_italy

Provider name: Tivusat
Provider key: sat_130_tivusat

Provider name: AustriaSat
Provider key: sat_192_austriasat

Provider name: Canal Digitaal HD
Provider key: sat_192_canaldigitaal_hd

Provider name: Canal Digitaal SD
Provider key: sat_192_canaldigitaal_sd

Provider name: Canal+ Esp
Provider key: sat_192_canal_plus_esp

Provider name: Sky Deutschland
Provider key: sat_192_sky_deutschland

Provider name: TéléSAT
Provider key: sat_192_telesat

Provider name: TNTSat
Provider key: sat_192_tntsat

Provider name: TV Vlaanderen
Provider key: sat_192_tvvlaanderen

Provider name: AustriaSat
Provider key: sat_235_austriasat

Provider name: Canal Digitaal HD
Provider key: sat_235_canaldigitaal_hd

Provider name: Canal Digitaal SD
Provider key: sat_235_canaldigitaal_sd

Provider name: Skylink Czech Republic
Provider key: sat_235_skylink_czech_republic

Provider name: Skylink Slovak Republic
Provider key: sat_235_skylink_slovak_republic

Provider name: TeleSAT
Provider key: sat_235_telesat

Provider name: TV Vlaanderen
Provider key: sat_235_tvvlaanderen

Provider name: FreeSat (UK)
Provider key: sat_282_freesat

Provider name: Sky ROI
Provider key: sat_282_sky_irl

Provider name: Sky UK
Provider key: sat_282_sky_uk

Provider name: FranSat
Provider key: sat_3550_fransat

Provider name: Turksat
Provider key: sat_420_turksat

Provider name: FreeView (UK)
Provider key: terrestrial_uk_freeview

