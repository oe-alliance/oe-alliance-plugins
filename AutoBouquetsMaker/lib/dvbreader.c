#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/ioctl.h>

#include <linux/dvb/frontend.h>
#include <linux/dvb/dmx.h>

#include <Python.h>

PyObject *ss_open(PyObject *self, PyObject *args) {
	int fd, pid;
	const char *demuxer;
	char filter, mask, frontend;
	struct dmx_sct_filter_params sfilter;
	dmx_source_t ssource = DMX_SOURCE_FRONT0;
	
	if (!PyArg_ParseTuple(args, "sibbb", &demuxer, &pid, &filter, &mask, &frontend))
		return Py_BuildValue("i", -1);
	
	memset(&sfilter, 0, sizeof(sfilter));
	sfilter.pid = pid & 0xffff;
	sfilter.filter.filter[0] = filter & 0xff;
	sfilter.filter.mask[0] = mask & 0xff;
	sfilter.timeout = 0;
	sfilter.flags = DMX_IMMEDIATE_START | DMX_CHECK_CRC;
	
	ssource = DMX_SOURCE_FRONT0 + frontend;

	if ((fd = open(demuxer, O_RDWR | O_NONBLOCK)) < 0) {
		printf("Cannot open demuxer '%s'", demuxer);
		return Py_BuildValue("i", -1);
	}

	if (ioctl(fd, DMX_SET_SOURCE, &ssource) == -1) {
		printf("ioctl DMX_SET_SOURCE failed");
		close(fd);
		return Py_BuildValue("i", -1);
	}

	if (ioctl(fd, DMX_SET_FILTER, &sfilter) == -1) {
		printf("ioctl DMX_SET_FILTER failed");
		close(fd);
		return Py_BuildValue("i", -1);
	}
	
	return Py_BuildValue("i", fd);
}

PyObject *ss_close(PyObject *self, PyObject *args) {
	int fd;
	if (PyArg_ParseTuple(args, "i", &fd))
		close(fd);

	return Py_None;
}

PyObject *ss_parse_bat(unsigned char *data, int length) {
	PyObject* list = PyList_New(0);
	
	int bouquet_id = (data[3] << 8) | data[4];
	int bouquet_descriptors_length = ((data[8] & 0x0f) << 8) | data[9];
	int transport_stream_loop_length = ((data[bouquet_descriptors_length + 10] & 0x0f) << 8) | data[bouquet_descriptors_length + 11];
	int offset1 = 10;
	int ret = 0;
	
	while (bouquet_descriptors_length > 0)
	{
		unsigned char descriptor_tag = data[offset1];
		unsigned char descriptor_length = data[offset1 + 1];
		int offset2 = offset1 + 2;
		
		if (descriptor_tag == 0xd4)
		{
			char lang[4];
			char description[256];
			memset(lang, '\0', 4);
			memset(description, '\0', 256);
			
			int region_id = (data[offset1 + 2] << 8) | data[offset1 + 3];
			memcpy(lang, data + offset1 + 4, 3);
			unsigned char description_size = data[offset1 + 7];
			if (description_size == 255)
				description_size--;
			memcpy(description, data + offset1 + 8, description_size);
				
			PyObject *item = Py_BuildValue("{s:i,s:i,s:s,s:s}",
						"descriptor_tag", descriptor_tag,
						"region_id", region_id,
						"language", lang,
						"description", description);
						
			PyList_Append(list, item);
			Py_DECREF(item);
		}
		else if (descriptor_tag == 0x47) // Bouquet name descriptor
		{
			char description[descriptor_length + 1];
			memset(description, '\0', descriptor_length + 1);
			memcpy(description, data + offset1 + 2, descriptor_length);
			char *description_ptr = description;
			if (strlen(description) == 0)
				strcpy(description, "Unknown");
			else if (description[0] == 0x05)
				description_ptr++;
			
			PyObject *item = Py_BuildValue("{s:i,s:i,s:s}",
						"descriptor_tag", descriptor_tag,
						"bouquet_id", bouquet_id,
						"description", description_ptr);
						
			PyList_Append(list, item);
			Py_DECREF(item);
		}
		else if (descriptor_tag == 0x83)	// LCN descriptor (Fransat, 5W)
		{
			int size = descriptor_length;
			while (size > 0)
			{
				int original_network_id = (data[offset2] << 8) | data[offset2 + 1];
				int transport_stream_id = (data[offset2 + 2] << 8) | data[offset2 + 3];
				int service_id = (data[offset2 + 4] << 8) | data[offset2 + 5];
				int logical_channel_number = (data[offset2 + 6] << 4) | (data[offset2 + 7] >> 4);

				PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
						"bouquet_id", bouquet_id,
						"original_network_id", original_network_id,
						"transport_stream_id", transport_stream_id,
						"service_id", service_id,
						"logical_channel_number", logical_channel_number,
						"descriptor_tag", descriptor_tag);
							
				PyList_Append(list, item);
				Py_DECREF(item);
				
				offset2 += 8;
				size -= 8;
			}
		}
		else  // unknown descriptors
		{
			char description[2 * descriptor_length + 5];
			memset(description, '\0', 2 * descriptor_length + 5);
			int length = descriptor_length + 2;
			int i = 0, j = 0;
			while (length > 0)
			{
				int decimalNumber = data[offset2 + i - 2];
				int quotient, n=0, temp;
				char hextemp[3] = {'0','0','\0'};
				quotient = decimalNumber;
				while(quotient!=0) 
				{
					temp = quotient % 16;
					if (temp < 10)
						temp = temp + 48; 
					else
						temp = temp + 55;
					hextemp[n]= temp;
					n += 1;
					quotient = quotient / 16;
				}
				//swap result
				description[j] = hextemp[1];
				j += 1;
				description[j] = hextemp[0];
				j += 1;
				i += 1;
				length -= 1;
			}
			if (strlen(description) == 0)
				strcpy(description, "Empty");
		
			PyObject *item = Py_BuildValue("{s:i,s:i,s:s}",
						"descriptor_tag", descriptor_tag,
						"descriptor_length", descriptor_length,
						"hexcontent", description);
						
			PyList_Append(list, item);
			Py_DECREF(item);
		}
		
		offset1 += (descriptor_length + 2);
		bouquet_descriptors_length -= (descriptor_length + 2);
	}
	
	offset1 += 2;
	
	while (transport_stream_loop_length > 0)
	{
		int transport_stream_id = (data[offset1] << 8) | data[offset1 + 1];
		int original_network_id = (data[offset1 + 2] << 8) | data[offset1 + 3];
		int transport_descriptor_length = ((data[offset1 + 4] & 0x0f) << 8) | data[offset1 + 5];
		int offset2 = offset1 + 6;

		offset1 += (transport_descriptor_length + 6);
		transport_stream_loop_length -= (transport_descriptor_length + 6);

		while (transport_descriptor_length > 0)
		{
			unsigned char descriptor_tag = data[offset2];
			unsigned char descriptor_length = data[offset2 + 1];
			int offset3 = offset2 + 2;

			offset2 += (descriptor_length + 2);
			transport_descriptor_length -= (descriptor_length + 2);

			if (descriptor_tag == 0xb1) // User defined Sky
			{
				unsigned char region_id;
				region_id = data[offset3 + 1];
				
				offset3 += 2;
				descriptor_length -= 2;
				while (descriptor_length > 0)
				{
					int i;
					int found = 0;
					unsigned short int channel_id;
					unsigned short int sky_id;
					unsigned short int service_id;
					unsigned char service_type;
					
					channel_id = (data[offset3 + 3] << 8) | data[offset3 + 4];
					sky_id = ( data[offset3 + 5] << 8 ) | data[offset3 + 6];
					service_id = (data[offset3] << 8) | data[offset3 + 1];
					service_type = data[offset3 + 2];
					
					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
							"descriptor_tag", descriptor_tag,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id, "number", sky_id,
							"service_type", service_type, "region_id", region_id,
							"channel_id", channel_id);
							
					PyList_Append(list, item);
					Py_DECREF(item);
					
					offset3 += 9;
					descriptor_length -= 9;
				}
			}
			else if (descriptor_tag == 0x41) // Service list descriptor 
			{
				while (descriptor_length > 0)
				{
					unsigned short int service_id;
					unsigned char service_type;
					service_id = (data[offset3] << 8) | data[offset3 + 1];
					service_type = data[offset3 + 2];
					
					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i}",
							"descriptor_tag", descriptor_tag,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id, "service_type", service_type);
							
					PyList_Append(list, item);
					Py_DECREF(item);
					
					descriptor_length -= 3;
				}
			}
			else if (descriptor_tag == 0x81)	// LCN descriptor (UPC, 0.8W)
			{
				while (descriptor_length > 0)
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int logical_channel_number = (data[offset3 + 2] << 8) | data[offset3 + 3];

					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
							"bouquet_id", bouquet_id,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"logical_channel_number", logical_channel_number,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
					
					offset3 += 4;
					descriptor_length -= 4;
				}
			}
			else if (descriptor_tag == 0x83)	// LCN descriptor (NC+, 13E)
			{
				while (descriptor_length > 0)
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int visible_service_flag = (data[offset3 + 2] >> 7) & 0x01;
					int logical_channel_number = ((data[offset3 + 2] & 0x03) << 8) | data[offset3 + 3];

					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
							"bouquet_id", bouquet_id,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"visible_service_flag", visible_service_flag,
							"logical_channel_number", logical_channel_number,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
					
					offset3 += 4;
					descriptor_length -= 4;
				}
			}
			else if (descriptor_tag == 0x86)	// LCN descriptor (DIGI 0.8W)
			{
				while (descriptor_length > 0)
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int logical_channel_number = (data[offset3 + 2] << 8) | data[offset3 + 3];

					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
							"bouquet_id", bouquet_id,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"logical_channel_number", logical_channel_number,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
					
					offset3 += 4;
					descriptor_length -= 4;
				}
			}
			else if (descriptor_tag == 0x93)	// LCN descriptor (NOVA, 13E)
			{
				while (descriptor_length > 0)
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int logical_channel_number = (data[offset3 + 2] << 8) | data[offset3 + 3];

					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
							"bouquet_id", bouquet_id,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"logical_channel_number", logical_channel_number,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
					
					offset3 += 4;
					descriptor_length -= 4;
				}
			}
			else if (descriptor_tag == 0xd3) // User defined
			{
				while (descriptor_length > 0)
				{
					unsigned short int service_id;
					unsigned char size;

					service_id = (data[offset3] << 8) | data[offset3 + 1];
					size = data[offset3 + 4];

					offset3 += 5;
					descriptor_length -= 5;
					while (size > 0)
					{
						unsigned short int region_id;
						unsigned short int channel_number;
						channel_number = ((data[offset3] << 8) | data[offset3 + 1]) & 0x0fff;
						region_id = (data[offset3 + 2] << 8) | data[offset3 + 3];

						PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
								"descriptor_tag", descriptor_tag,
								"transport_stream_id", transport_stream_id,
								"original_network_id", original_network_id,
								"service_id", service_id, "number", channel_number,
								"region_id", region_id);

						PyList_Append(list, item);
						Py_DECREF(item);

						offset3 += 4;
						size -= 4;
						descriptor_length -= 4;
					}
				}
			}
			else if (descriptor_tag == 0xe2) // LCN descriptor (Viasat, 4.8E)
			{
				while (descriptor_length > 0)
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int logical_channel_number = ((data[offset3 + 2] & 0x03) << 8) | data[offset3 + 3];
					
					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
							"descriptor_tag", descriptor_tag,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"bouquet_id", bouquet_id,
							"service_id", service_id,
							"logical_channel_number", logical_channel_number);
							
					PyList_Append(list, item);
					Py_DECREF(item);
					
					offset3 += 4;
					descriptor_length -= 4;
				}
			}
			else  // unknown descriptors
			{
				char description[2 * descriptor_length + 5];
				memset(description, '\0', 2 * descriptor_length + 5);
				int length = descriptor_length + 2;
				int i = 0, j = 0;
				while (length > 0)
				{
					int decimalNumber = data[offset3 + i - 2];
					int quotient, n=0, temp;
					char hextemp[3] = {'0','0','\0'};
					quotient = decimalNumber;
					while(quotient!=0) 
					{
						temp = quotient % 16;
						if (temp < 10)
							temp = temp + 48; 
						else
							temp = temp + 55;
						hextemp[n]= temp;
						n += 1;
						quotient = quotient / 16;
					}
					description[j] = hextemp[1];
					j += 1;
					description[j] = hextemp[0];
					j += 1;
					i += 1;
					length -= 1;
				}
				if (strlen(description) == 0)
					strcpy(description, "Empty");
			
				PyObject *item = Py_BuildValue("{s:i,s:i,s:s}",
							"descriptor_tag", descriptor_tag,
							"descriptor_length", descriptor_length,
							"hexcontent", description);
						
				PyList_Append(list, item);
				Py_DECREF(item);
			}
		}
	}

	return list;
}

PyObject *ss_parse_nit(unsigned char *data, int length) {
	PyObject* list = PyList_New(0);
	
	int network_descriptors_length = ((data[8] & 0x0f) << 8) | data[9];
	int transport_stream_loop_length = ((data[network_descriptors_length + 10] & 0x0f) << 8) | data[network_descriptors_length + 11];
	int offset1 = network_descriptors_length + 12;
	int ret = 0;

	while (transport_stream_loop_length > 0)
	{
		int transport_stream_id = (data[offset1] << 8) | data[offset1 + 1];
		int original_network_id = (data[offset1 + 2] << 8) | data[offset1 + 3];
		int transport_descriptor_length = ((data[offset1 + 4] & 0x0f) << 8) | data[offset1 + 5];
		int offset2 = offset1 + 6;

		offset1 += (transport_descriptor_length + 6);
		transport_stream_loop_length -= (transport_descriptor_length + 6);

		while (transport_descriptor_length > 0)
		{
			unsigned char descriptor_tag = data[offset2];
			unsigned char descriptor_length = data[offset2 + 1];

			if (descriptor_tag == 0x43)	// Satellite delivery system descriptor
			{
				int frequency = (data[offset2 + 2] >> 4) * 10000000;
				frequency += (data[offset2 + 2] & 0x0f) * 1000000;
				frequency += (data[offset2 + 3] >> 4) * 100000;
				frequency += (data[offset2 + 3] & 0x0f) * 10000;
				frequency += (data[offset2 + 4] >> 4) * 1000;
				frequency += (data[offset2 + 4] & 0x0f) * 100;
				frequency += (data[offset2 + 5] >> 4) * 10;
				frequency += data[offset2 + 5] & 0x0f;
				
				int orbital_position = (data[offset2 + 6] << 8) | data[offset2 + 7];
				int west_east_flag = (data[offset2 + 8] >> 7) & 0x01;
				int polarization = (data[offset2 + 8] >> 5) & 0x03;
				int roll_off = (data[offset2 + 8] >> 3) & 0x03;
				int modulation_system = (data[offset2 + 8] >> 2) & 0x01;
				int modulation_type = data[offset2 + 8] & 0x03;

				int symbol_rate = (data[offset2 + 9] >> 4) * 1000000;
				symbol_rate += (data[offset2 + 9] & 0xf) * 100000;
				symbol_rate += (data[offset2 + 10] >> 4) * 10000;
				symbol_rate += (data[offset2 + 10] & 0xf) * 1000;
				symbol_rate += (data[offset2 + 11] >> 4) * 100;
				symbol_rate += (data[offset2 + 11] & 0xf) * 10;
				symbol_rate += data[offset2 + 11] >> 4;
				
				int fec_inner = data[offset2 + 12] & 0xf;

				PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
						"transport_stream_id", transport_stream_id,
						"original_network_id", original_network_id,
						"frequency", frequency,
						"orbital_position", orbital_position,
						"west_east_flag", west_east_flag,
						"polarization", polarization,
						"roll_off", roll_off,
						"modulation_system", modulation_system,
						"modulation_type", modulation_type,
						"symbol_rate", symbol_rate,
						"fec_inner", fec_inner,
						"descriptor_tag", descriptor_tag);
						
				PyList_Append(list, item);
				Py_DECREF(item);
			}
			else if (descriptor_tag == 0x44)	// Cable delivery system descriptor
			{		
				int frequency = (data[offset2 + 2] >> 4) * 10000000;
				frequency += (data[offset2 + 2] & 0x0f) * 1000000;
				frequency += (data[offset2 + 3] >> 4) * 100000;
				frequency += (data[offset2 + 3] & 0x0f) * 10000;
				frequency += (data[offset2 + 4] >> 4) * 1000;
				frequency += (data[offset2 + 4] & 0x0f) * 100;
				frequency += (data[offset2 + 5] >> 4) * 10;
				frequency += data[offset2 + 5] & 0x0f;
				
				int fec_outer = data[offset2 + 7] & 0xf;
				int modulation_type = data[offset2 + 8];

				int symbol_rate = (data[offset2 + 9] >> 4) * 1000000;
				symbol_rate += (data[offset2 + 9] & 0xf) * 100000;
				symbol_rate += (data[offset2 + 10] >> 4) * 10000;
				symbol_rate += (data[offset2 + 10] & 0xf) * 1000;
				symbol_rate += (data[offset2 + 11] >> 4) * 100;
				symbol_rate += (data[offset2 + 11] & 0xf) * 10;
				symbol_rate += data[offset2 + 12] >> 4;
				
				int fec_inner = data[offset2 + 12] & 0xf;

				PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
						"transport_stream_id", transport_stream_id,
						"original_network_id", original_network_id,
						"frequency", frequency,
						"fec_outer", fec_outer,
						"modulation_type", modulation_type,
						"symbol_rate", symbol_rate,
						"fec_inner", fec_inner,
						"descriptor_tag", descriptor_tag);
						
				PyList_Append(list, item);
				Py_DECREF(item);
			}
			else if (descriptor_tag == 0x5A)	// Terrestrial delivery system descriptor
			{
				int frequency = ((data[offset2 + 2] << 24) | (data[offset2 + 3] << 16) | (data[offset2 + 4] << 8) | (data[offset2 + 5]));
				
				int bandwidth = (data[offset2 + 6] >> 5 & 0x07);
				int priority = (data[offset2 + 6] >> 4 & 0x01);
				int time_slicing = (data[offset2 + 6] >> 3 & 0x01);
				int mpe_fec = (data[offset2 + 6] >> 2 & 0x01);
				
				int modulation = (data[offset2 + 7] >> 6 & 0x03);
				int hierarchy = (data[offset2 + 7] >> 3 & 0x07);
				int code_rate_hp = (data[offset2 + 7] & 0x07);
				
				int code_rate_lp = (data[offset2 + 8] >> 5 & 0x07);
				int guard_interval = (data[offset2 + 8] >> 3 & 0x03);
				int transmission_mode = (data[offset2 + 8] >> 1 & 0x03);
				int other_frequency_flag = (data[offset2 + 8] & 0x01);
				
				PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
						"transport_stream_id", transport_stream_id,
						"original_network_id", original_network_id,
						"frequency", frequency,
						"bandwidth", bandwidth,
						"priority", priority,
						"time_slicing", time_slicing,
						"mpe_fec", mpe_fec,
						"modulation", modulation,
						"hierarchy", hierarchy,
						"code_rate_hp", code_rate_hp,
						"code_rate_lp", code_rate_lp,
						"guard_interval", guard_interval,
						"transmission_mode", transmission_mode,
						"other_frequency_flag", other_frequency_flag,
						"descriptor_tag", descriptor_tag);
						
				PyList_Append(list, item);
				Py_DECREF(item);
			}
			else if (descriptor_tag == 0x7f)	// DVB-T2 delivery system descriptor when descriptor_tag_extension == 4
			{
				unsigned char descriptor_tag_extension = data[offset2 + 2];
				if (descriptor_tag_extension == 0x04)
				{
					int system = 1;
					int inversion = 0;
					int plp_id = data[offset2 + 3];
					int T2_system_id = (data[offset2 + 4] << 8) | data[offset2 + 5];
					
					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:s,s:i,s:i,s:i}",
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"plp_id", plp_id,
							"T2_system_id", T2_system_id,
							"delivery_system_type", "DVB-T2",
							"system", system,
							"inversion", inversion,
							"descriptor_tag", descriptor_tag);
						
					PyList_Append(list, item);
					Py_DECREF(item);
				}
			
			}
			else if (descriptor_tag == 0x41)	// Service list descriptor
			{
				int offset3 = offset2 + 2;
				while (offset3 < (offset2 + descriptor_length + 2))
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int service_type = data[offset3 + 2];

					offset3 += 3;
					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i}",
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"service_type", service_type,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
				}
			}
			else if (descriptor_tag == 0x83)	// LCN descriptor
			{
				int offset3 = offset2 + 2;
				while (offset3 < (offset2 + descriptor_length + 2))
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int visible_service_flag = (data[offset3 + 2] >> 7) & 0x01;
					int logical_channel_number = ((data[offset3 + 2] & 0x03) << 8) | data[offset3 + 3];

					offset3 += 4;
					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"visible_service_flag", visible_service_flag,
							"logical_channel_number", logical_channel_number,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
				}
			}
			else if (descriptor_tag == 0x87)	// LCN V2 descriptor (Canal Digital Nordic 0.8W)
			{
				int offset3 = offset2 + 2;
				int channel_list_id = data[offset3];
				int channel_list_name_length = data[offset3 + 1];

				char channel_list_name[channel_list_name_length + 1];
				memset(channel_list_name, '\0', channel_list_name_length + 1);
				memcpy(channel_list_name, data + offset3 + 2, channel_list_name_length);
				char *channel_list_name_ptr = channel_list_name;
					
				char country_code[3];
				memset(country_code, '\0', 3);
				memcpy(country_code, data + offset3 + 2 + channel_list_name_length, 3);
				char *country_code_ptr = country_code;
				
				int descriptor_length_2 = offset3 + 2 + channel_list_name_length + 3;
				int offset4 = offset3 + 2 + channel_list_name_length + 3 + 1;
				
				while (offset4 < (offset3 + descriptor_length_2 + 2))
				{
					int service_id = (data[offset4] << 8) | data[offset4 + 1];
					int visible_service_flag = (data[offset4 + 2] >> 7) & 0x01;
					int logical_channel_number = ((data[offset4 + 2] & 0x03) << 8) | data[offset4 + 3];

					offset4 += 4;
					PyObject *item = Py_BuildValue("{s:i,s:s,s:s,s:i,s:i,s:i,s:i,s:i,s:i}",
							"channel_list_id", channel_list_id,
							"channel_list_name", channel_list_name_ptr,
							"country_code", country_code_ptr,
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"visible_service_flag", visible_service_flag,
							"logical_channel_number", logical_channel_number,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
				}
			}
			else if (descriptor_tag == 0x88)	// HD simulcast LCN descriptor
			{
				int offset3 = offset2 + 2;
				while (offset3 < (offset2 + descriptor_length + 2))
				{
					int service_id = (data[offset3] << 8) | data[offset3 + 1];
					int visible_service_flag = (data[offset3 + 2] >> 7) & 0x01;
					int hd_logical_channel_number = ((data[offset3 + 2] & 0x03) << 8) | data[offset3 + 3];

					offset3 += 4;
					PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i}",
							"transport_stream_id", transport_stream_id,
							"original_network_id", original_network_id,
							"service_id", service_id,
							"visible_service_flag", visible_service_flag,
							"logical_channel_number", hd_logical_channel_number,
							"descriptor_tag", descriptor_tag);
							
					PyList_Append(list, item);
					Py_DECREF(item);
				}
			}
			
			offset2 += (descriptor_length + 2);
			transport_descriptor_length -= (descriptor_length + 2);
		}
	}

	return list;
}

PyObject *ss_parse_sdt(unsigned char *data, int length) {
	PyObject* list = PyList_New(0);
	
	int transport_stream_id = (data[3] << 8) | data[4];
	int original_network_id = (data[8] << 8) | data[9];
	int offset = 11;
	length -= 11;
	
	while (length >= 5)
	{
		int service_id = (data[offset] << 8) | data[offset + 1];
		int free_ca = (data[offset + 3] >> 4) & 0x01;
		int descriptors_loop_length = ((data[offset + 3] & 0x0f) << 8) | data[offset + 4];
		char service_name[256];
		char provider_name[256];
		int service_type = 0;
		int lcn_id = 0;
		int bouquets_id = 0;
		int service_group_id = 0;
		memset(service_name, '\0', 256);
		memset(provider_name, '\0', 256);
		
		length -= 5;
		offset += 5;
		
		int offset2 = offset;

		length -= descriptors_loop_length;
		offset += descriptors_loop_length;

		while (descriptors_loop_length >= 2)
		{
			int tag = data[offset2];
			int size = data[offset2 + 1];
			
			if (tag == 0x48)	// Service descriptor
			{
				service_type = data[offset2 + 2];
				int service_provider_name_length = data[offset2 + 3];
				if (service_provider_name_length == 255)
					service_provider_name_length--;
					
				int service_name_length = data[offset2 + 4 + service_provider_name_length];
				if (service_name_length == 255)
					service_name_length--;
					
				memset(service_name, '\0', 256);
				memcpy(provider_name, data + offset2 + 4, service_provider_name_length);
				memcpy(service_name, data + offset2 + 5 + service_provider_name_length, service_name_length);
			}
			if (tag == 0xc0)	// sky/Virgin user defined descriptor????
			{
				//memset(service_name, '\0', 256);
				//memcpy(service_name, data + offset2 + 2, size);
				lcn_id = ((data[offset2 + 2] & 0x03) << 8) | data[offset2 + 3];
				int name_length = data[offset2 + 4];
				//service name is taken from descriptor 48
				bouquets_id = data[offset2 + 5 + name_length];
				service_group_id = data[offset2 + 6 + name_length];
			}
			if (tag == 0xca)	//User defined. Virgin LCN and Bouquets id
			{
				lcn_id = ((data[offset2 + 2] & 0x03) << 8) | data[offset2 + 3];
				int name_length = data[offset2 + 4];
				//service name is taken from descriptor 48
				bouquets_id = data[offset2 + 5 + name_length];
				service_group_id = data[offset2 + 6 + name_length];
			}
			descriptors_loop_length -= (size + 2);
			offset2 += (size + 2);
		}

		char *provider_name_ptr = provider_name;
		if (strlen(provider_name) == 0)
			strcpy(provider_name, "Unknown");
		else if (provider_name[0] == 0x05)
				provider_name_ptr++;

		char *service_name_ptr = service_name;
		if (strlen(service_name) == 0)
			strcpy(service_name, "Unknown");
		else if (service_name[0] == 0x05)
				service_name_ptr++;
		
		PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:s,s:s,s:i,s:i,s:i}",
					"transport_stream_id", transport_stream_id,
					"original_network_id", original_network_id,
					"service_id", service_id,
					"service_type", service_type,
					"free_ca", free_ca,
					"service_name", service_name_ptr,
					"provider_name", provider_name_ptr,
					"logical_channel_number", lcn_id,
					"bouquets_id", bouquets_id,
					"service_group_id", service_group_id);
		PyList_Append(list, item);
		Py_DECREF(item);
	}
	
	return list;
}

PyObject *ss_parse_fastscan(unsigned char *data, int length) {
	PyObject* list = PyList_New(0);
	
	int offset = 8;
	length -= 8;
	
	while (length >= 5)
	{
		char service_name[256];
		char provider_name[256];
		int service_type = 0;
		memset(service_name, '\0', 256);
		memset(provider_name, '\0', 256);
		
		int original_network_id = (data[offset] << 8) | data[offset + 1];
		int transport_stream_id = (data[offset + 2] << 8) | data[offset + 3];
		int service_id = (data[offset + 4] << 8) | data[offset + 5];
		int descriptors_loop_length = ((data[offset + 16] & 0x0f) << 8) | data[offset + 17];
		
		length -= 18;
		offset += 18;
		
		int offset2 = offset;

		length -= descriptors_loop_length;
		offset += descriptors_loop_length;
		
		while (descriptors_loop_length >= 2)
		{
			int tag = data[offset2];
			int size = data[offset2 + 1];
			
			if (tag == 0x48)	// Service descriptor
			{
				service_type = data[offset2 + 2];
				int service_provider_name_length = data[offset2 + 3];
				if (service_provider_name_length == 255)
					service_provider_name_length--;
					
				int service_name_length = data[offset2 + 4 + service_provider_name_length];
				if (service_name_length == 255)
					service_name_length--;
					
				memcpy(provider_name, data + offset2 + 4, service_provider_name_length);
				memcpy(service_name, data + offset2 + 5 + service_provider_name_length, service_name_length);
			}
			
			descriptors_loop_length -= (size + 2);
			offset2 += (size + 2);
		}
		
		char *provider_name_ptr = provider_name;
		if (strlen(provider_name) == 0)
			strcpy(provider_name, "Unknown");
		else if (provider_name[0] == 0x05)
				provider_name_ptr++;

		char *service_name_ptr = service_name;
		if (strlen(service_name) == 0)
			strcpy(service_name, "Unknown");
		else if (service_name[0] == 0x05)
				service_name_ptr++;
		
		PyObject *item = Py_BuildValue("{s:i,s:i,s:i,s:i,s:s,s:s}",
					"transport_stream_id", transport_stream_id,
					"original_network_id", original_network_id,
					"service_id", service_id,
					"service_type", service_type,
					"service_name", service_name_ptr,
					"provider_name", provider_name_ptr);
					
		PyList_Append(list, item);
		Py_DECREF(item);
	}
	
	return list;
}

PyObject *ss_parse_header(unsigned char *data, int length, const char *variable_key_name) //NIT and BAT
{
	int table_id = data[0];
	int variable_id = (data[3] << 8) | data[4];
	int version_number = (data[5] >> 1) & 0x1f;
	int current_next_indicator = data[5] & 0x01;
	int section_number = data[6];
	int last_section_number = data[7];
	int network_descriptors_length = ((data[8] & 0x0f) << 8) | data[9];
	int original_network_id = (data[network_descriptors_length + 5] << 8) | data[network_descriptors_length + 6];
	
	return Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
		"table_id", table_id, variable_key_name, variable_id,
		"version_number", version_number, "current_next_indicator", current_next_indicator,
		"section_number", section_number, "last_section_number", last_section_number,
		"original_network_id", original_network_id);
}

PyObject *ss_parse_header_2(unsigned char *data, int length, const char *variable_key_name) //SDT and Fastscan
{
	int table_id = data[0];
	int variable_id = (data[3] << 8) | data[4];
	int version_number = (data[5] >> 1) & 0x1f;
	int current_next_indicator = data[5] & 0x01;
	int section_number = data[6];
	int last_section_number = data[7];
	int original_network_id = (data[8] << 8) | data[9];
	
	return Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
		"table_id", table_id, variable_key_name, variable_id,
		"version_number", version_number, "current_next_indicator", current_next_indicator,
		"section_number", section_number, "last_section_number", last_section_number,
		"original_network_id", original_network_id);
}

PyObject *ss_parse_table(unsigned char *data, int length) {
	PyObject* list = PyList_New(0);
	int i = 0;
	while (length > 0)
	{
		int value = data[i];
		PyObject *item = Py_BuildValue("i", value);
		PyList_Append(list, item);
		Py_DECREF(item);
		i += 1;
		length -= 1;
	}
	return list;
}

PyObject *ss_read_ts(PyObject *self, PyObject *args) {
	PyObject *content = NULL, *header = NULL, *buffer1 = NULL;
	unsigned char buffer[4096], table_id_current, table_id_other;
	int fd;
	
	if (!PyArg_ParseTuple(args, "ibb", &fd, &table_id_current, &table_id_other))
		return Py_None;
	
	int size = read(fd, buffer, sizeof(buffer));
	if (size < 3)
		return Py_None;
		
	if (buffer[0] != table_id_current && buffer[0] != table_id_other)
		return Py_None;
		
	int section_length = ((buffer[1] & 0x0f) << 8) | buffer[2];
	
	if (size != section_length + 3)
		return Py_None;
		
	content = ss_parse_table(buffer, section_length);

	PyObject *ret = Py_BuildValue("O", content);
	Py_DECREF(content);
	return ret;
}

PyObject *ss_read_bat(PyObject *self, PyObject *args) {
	PyObject *content = NULL, *header = NULL;
	unsigned char buffer[4096], table_id;
	int fd;
	
	if (!PyArg_ParseTuple(args, "ib", &fd, &table_id))
		return Py_None;
	
	int size = read(fd, buffer, sizeof(buffer));
	if (size < 3)
		return Py_None;
		
	if (buffer[0] != table_id)
		return Py_None;
		
	int section_length = ((buffer[1] & 0x0f) << 8) | buffer[2];
	
	if (size != section_length + 3)
		return Py_None;

	header = ss_parse_header(buffer, section_length, "bouquet_id");
	content = ss_parse_bat(buffer, section_length);
	
	if (!header || !content)
		return Py_None;
		
	PyObject *ret = Py_BuildValue("{s:O,s:O}", "header", header, "content", content);
	Py_DECREF(header);
	Py_DECREF(content);
	return ret;
}

PyObject *ss_read_sdt(PyObject *self, PyObject *args) {
	PyObject *content = NULL, *header = NULL;
	unsigned char buffer[4096], table_id_current, table_id_other;
	int fd;
	
	if (!PyArg_ParseTuple(args, "ibb", &fd, &table_id_current, &table_id_other))
		return Py_None;
	
	int size = read(fd, buffer, sizeof(buffer));
	if (size < 3)
		return Py_None;
		
	if (buffer[0] != table_id_current && buffer[0] != table_id_other)
		return Py_None;
		
	int section_length = ((buffer[1] & 0x0f) << 8) | buffer[2];
	
	if (size != section_length + 3)
		return Py_None;

	header = ss_parse_header_2(buffer, section_length, "transport_stream_id");
	content = ss_parse_sdt(buffer, section_length);
	
	if (!header || !content)
		return Py_None;
		
	PyObject *ret = Py_BuildValue("{s:O,s:O}", "header", header, "content", content);
	Py_DECREF(header);
	Py_DECREF(content);
	return ret;
}

PyObject *ss_read_fastscan(PyObject *self, PyObject *args) {
	PyObject *content = NULL, *header = NULL;
	unsigned char buffer[4096], table_id;
	int fd;
	
	if (!PyArg_ParseTuple(args, "ib", &fd, &table_id))
		return Py_None;
	
	int size = read(fd, buffer, sizeof(buffer));
	if (size < 3)
		return Py_None;
		
	if (buffer[0] != table_id)
		return Py_None;
		
	int section_length = ((buffer[1] & 0x0f) << 8) | buffer[2];
	
	if (size != section_length + 3)
		return Py_None;

	header = ss_parse_header_2(buffer, section_length, "fastscan_id");
	content = ss_parse_fastscan(buffer, section_length);
	
	if (!header || !content)
		return Py_None;
		
	PyObject *ret = Py_BuildValue("{s:O,s:O}", "header", header, "content", content);
	Py_DECREF(header);
	Py_DECREF(content);
	return ret;
}

PyObject *ss_read_nit(PyObject *self, PyObject *args) {
	PyObject *content = NULL, *header = NULL;
	unsigned char buffer[4096], table_id_current, table_id_other;
	int fd;
	
	if (!PyArg_ParseTuple(args, "ibb", &fd, &table_id_current, &table_id_other))
		return Py_None;
	
	int size = read(fd, buffer, sizeof(buffer));
	if (size < 3)
		return Py_None;
		
	if (buffer[0] != table_id_current && buffer[0] != table_id_other)
		return Py_None;
		
	int section_length = ((buffer[1] & 0x0f) << 8) | buffer[2];
	
	if (size != section_length + 3)
		return Py_None;

	header = ss_parse_header(buffer, section_length, "network_id");
	content = ss_parse_nit(buffer, section_length);
	
	if (!header || !content)
		return Py_None;
		
	PyObject *ret = Py_BuildValue("{s:O,s:O}", "header", header, "content", content);
	Py_DECREF(header);
	Py_DECREF(content);
	return ret;
}

static PyMethodDef dvbreaderMethods[] = {
		{ "open", ss_open, METH_VARARGS },
		{ "close", ss_close, METH_VARARGS },
		{ "read_bat", ss_read_bat, METH_VARARGS },
		{ "read_nit", ss_read_nit, METH_VARARGS },
		{ "read_sdt", ss_read_sdt, METH_VARARGS },
		{ "read_fastscan", ss_read_fastscan, METH_VARARGS },
		{ "read_ts", ss_read_ts, METH_VARARGS },
		{ NULL, NULL }
};

void initdvbreader() {
	PyObject *m;
	m = Py_InitModule("dvbreader", dvbreaderMethods);
}