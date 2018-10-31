TerrestrialScan plugin
----------------------

The TerrestrialScan plugin, is designed to compliment ABM. It draws heavily on ideas 
from and lessons learned during the development of ABM.

ABM is designed to scan a single transponder and create bouquets based on the data carried 
on that single transponder. Scanning only one transponder is extremely rapid, but unfortunately 
the data is often incomplete or just plain wrong. T2 transponders have missing frequencies 
and repeaters have wrong frequencies. We have tried to patch the data where possible but 
we have had to rely on users submitting the data and due to this not all areas work 100% 
correctly. There are other problems too such as some providers spreading their data across 
several transponders so the single (fast) transponder approach is not available.

The TerrestrialScan plugin attempts to get around the above problems by doing an exhaustive 
search of all possible frequencies in the 8 MHz European band plan. This takes much longer 
but the advantage is that the plugin confirms the channels it saves are really present on 
each transponder. 

The plugin also checks the signal strength of each transponder and when it finds duplicated 
transponders it only saves the one that has the strongest signal. This avoids users having 
a list of duplicated channels, or worse still, scanning in the weaker transponder while the  
stronger one is completely missing.

The plugin allows the user to select one single "original network ID" so services from 
multiple providers can be avoided.

There is also an option to create one terrestrial bouquet containing all the terrestrial 
services. This bouquet will only be created when "Logical Channel Number" data (LCN) is 
available. When first created this bouquet will be at the top but you can move it down 
using the tools built into enigma and it will stay where you put it during subsequent scans, 
but may be moved by other processes that also write to the bouquet index such as ABM. The 
created bouquet contains padding so the channel numbering remains correct, and at the end 
of the channel list there is more padding so that the numbering in the subsequent bouquets 
remains correct. To remove the bouquet, if necessary, use the tools built in to enigma.

Currently, TV and radio channels are mixed based on LCN, in the same bouquet.

