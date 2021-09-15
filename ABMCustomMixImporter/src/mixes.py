import os
import xml.dom.minidom


class Mixes():
	MIXES_DIR = os.path.dirname(__file__) + "/mixes"

	def parseXML(self, filename):
		try:
			mix = open(filename, "r")
		except Exception as e:
			print("[ABMCustomMixImporter][Mixes] Cannot open %s: %s" % (filename, e))
			return None

		try:
			dom = xml.dom.minidom.parse(mix)
		except Exception as e:
			print("[ABMCustomMixImporter][Mixes] XML parse error (%s): %s" % (filename, e))
			mix.close()
			return None

		mix.close()
		return dom

	def read(self):
		mixes = {}
		for filename in os.listdir(self.MIXES_DIR):
			if filename[-4:] != ".xml":
				continue

			dom = self.parseXML(self.MIXES_DIR + "/" + filename)
			if dom is None:
				continue

			mix = {}
			mix["key"] = filename[:-4]
			if dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "custommiximport":
				for node in dom.documentElement.childNodes:
					if node.nodeType != node.ELEMENT_NODE:
						continue

					if node.tagName == "name":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							# mix["name"] = node.childNodes[0].data.encode("utf-8")
							mix["name"] = node.childNodes[0].data
					elif node.tagName == "provider":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							# mix["provider"] = node.childNodes[0].data.encode("utf-8")
							mix["provider"] = node.childNodes[0].data
					elif node.tagName == "url":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							# mix["url"] = node.childNodes[0].data.encode("utf-8")
							mix["url"] = node.childNodes[0].data

			if not ("name" in mix and "provider" in mix and "url" in mix):

				print("[ABMCustomMixImporter][Mixes] Incomplete XML %s" % filename)
				continue

			mixes[mix["key"]] = mix

		return mixes
