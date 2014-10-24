ABM is making an example file for each provider which is scanned by ABM, e.g. 'EXAMPLE_hd_sat_freesat_CustomLCN.xml'.
Making your own custom LCN file just delete the 'EXAMPLE_' is the name of the file (hd_sat_freesat_CustomLCN.xml). 
This file will overwrite the ordering of channels ABM is doing normally in the MAIN bouquet.

How to change the file.
Just cut and past the line into the order you wants.
DO NOT use channels more then 1 time in the list!!

Don't forget to add the custom folder into the backup files.

example original:
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

*Swap channels.*		
If you want to swap ITV (103) with BBC Three HD (106) cut and past both lines.
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
Now change the lcn numbers. lcn numbers must be in order!!
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
		
*Remove channels.*
Removing channels, just delete the line.
NOTE: When <include>is set to 'yes', all channels not configured in the custom xml will be added at the end of the main bouquet.
This way also new services (channels) of the provider are added at the end of the main bouquet.

*Changing 'channel numbers'.*
If you wants your own numbering, edit the lcn numbers. lcn numbers must be in order!!
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
