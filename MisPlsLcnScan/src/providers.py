# for localized messages
from . import _

PROVIDERS = {
	"fransat_5W": {
		"name": _("Fransat MIS 5W"),
		"orb_pos": 3550,
		"onids": (0x20FA,),
		"overrides": {"1:20fa:110": 3}},
	"italiasat_5W": {
		"name": _("Italia MIS 5W"),
		"orb_pos": 3550,
		"onids": (0x013E, 0xC8, 0x1D, 0x217C, 0x0110),
		"priority": ("4000:13e:d49", "4000:13e:d4a", "4000:13e:d53")}, }
