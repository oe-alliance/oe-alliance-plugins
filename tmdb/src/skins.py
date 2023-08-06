from enigma import getDesktop

if getDesktop(0).size().width() >= 1920:
	tmdbScreenSkin = """
			<screen position="30,90" size="1860,970" title="TMDb - The Movie Database" >
				<widget name="searchinfo" position="20,30" size="1350,40" font="Regular; 32" foregroundColor="#00fff000" transparent="1" />
				<widget name="list" position="20,90" size="1350,800" itemHeight="40" transparent="1" scrollbarMode="showNever"/>
				<widget name="cover" position="1500,250" size="320,480" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1920,1080" zPosition="-5" scale="1" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1920,1080" zPosition="-4" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/tmdb.png" position="1585,800" size="150,155" alphatest="blend" />
				<widget name="key_red" position="225,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_green" position="565,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_yellow" position="905,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_blue" position="1245,920" size="280,30" font="Regular; 25" transparent="1" />
				<ePixmap position="190,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="530,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="870,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="1210,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

	tmdbScreenMovieSkin = """
			<screen position="30,90" size="1860,970" title="TMDb - The Movie Database" >
				<widget name="searchinfo" position="20,30" size="1350,40" font="Regular; 32" foregroundColor="#00fff000" transparent="1" />
				<widget name="fulldescription" position="20,90" size="950,800" font="Regular; 28" transparent="1"/>
				<widget name="cover" position="1500,250" size="320,480" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1920,1080" zPosition="-6" scale="1" alphatest="blend" />
				<widget name="backdrop" position="0,0" size="1920,1080" zPosition="-5" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/tmdb.png" position="1585,800" size="150,155" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1920,1080" zPosition="-4" alphatest="blend" />
				<widget name="rating" position="1000,83" size="150,30" zPosition="2" font="Regular;27" halign="center" foregroundColor="black" backgroundColor="#00ffba00" transparent="1"/>
				<widget name="votes_brackets" position="1000,145" size="150,30" zPosition="2" font="Regular;27" halign="center" transparent="1"/>
				<ePixmap position="1025,45" size="100,100" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/star.png" transparent="1" alphatest="blend"/>
				<widget name="fsk" position="0,0" size="0,0" zPosition="2" font="Regular;27" halign="center" transparent="1"/>
				<widget name="fsklogo" position="1200,60" size="100,100" zPosition="2" alphatest="blend"/>
				<widget name="year_txt" position="1000,300" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="year" position="1130,300" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="country_txt" position="1000,335" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="country" position="1130,335" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="runtime_txt" position="1000,365" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="runtime" position="1130,365" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="votes_txt" position="1000,395" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="votes" position="1130,395" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="director_txt" position="1000,425" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="director" position="1130,425" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="author_txt" position="1000,455" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="author" position="1130,455" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="genre_txt" position="1000,485" size="100,33" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="genre" position="1130,485" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="studio_txt" position="1000,515" size="100,33" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="studio" position="1130,515" size="400,33" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="subtitle" position="0,0" size="0,0" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="description" position="0,0" size="0,0" zPosition="2" font="Regular;27" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="key_red" position="225,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_green" position="565,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_yellow" position="905,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_blue" position="1245,920" size="280,30" font="Regular; 25" transparent="1" />
				<ePixmap position="190,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="530,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="870,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="1210,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

	tmdbScreenPeopleSkin = """
			<screen position="30,90" size="1860,970" title="TMDb - The Movie Database" >
				<widget name="searchinfo" position="20,30" size="1350,40" font="Regular; 32" foregroundColor="#00fff000" transparent="1" />
				<widget name="list" position="20,90" size="1350,800" itemHeight="40" transparent="1" scrollbarMode="showNever"/>
				<widget name="cover" position="1500,250" size="320,480" alphatest="blend" />
				<widget name="data" position="0,0" size="0,0" font="Regular;21" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1920,1080" zPosition="-6" scale="1" alphatest="blend" />
				<widget name="backdrop" position="0,0" size="1920,1080" zPosition="-5" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/tmdb.png" position="1585,800" size="150,155" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1920,1080" zPosition="-4" alphatest="blend" />
				<widget name="key_red" position="225,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_green" position="565,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_blue" position="1245,920" size="280,30" font="Regular; 25" transparent="1" />
				<ePixmap position="190,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="530,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="870,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="1210,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

	tmdbScreenPersonSkin = """
			<screen position="30,90" size="1860,970" title="TMDb - The Movie Database" >
				<widget name="searchinfo" position="20,30" size="1350,40" font="Regular; 32" foregroundColor="#00fff000" transparent="1" />
				<widget name="fulldescription" position="20,90" size="1350,800" font="Regular;28" transparent="1"/>
				<widget name="cover" position="1500,250" size="320,480" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1920,1080" zPosition="-6" scale="1" alphatest="blend" />
				<widget name="backdrop" position="0,0" size="1920,1080" zPosition="-5" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/tmdb.png" position="1585,800" size="150,155" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1920,1080" zPosition="-4" alphatest="blend" />
				<widget name="key_red" position="225,920" size="280,30" font="Regular; 25" transparent="1" />
				<ePixmap position="190,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="530,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="870,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="1210,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

	tmdbScreenSeasonSkin = """
			<screen position="30,90" size="1860,970" title="TMDb - The Movie Database" >
				<widget name="searchinfo" position="20,30" size="1350,40" font="Regular; 32" foregroundColor="#00fff000" transparent="1" />
				<widget name="list" position="20,90" size="950,400" itemHeight="40" transparent="1" scrollbarMode="showNever"/>
				<widget name="cover" position="1000,90" size="848,480" alphatest="blend" />
				<widget name="data" position="20,510" size="950,400" font="Regular;28" transparent="1" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1920,1080" zPosition="-6" scale="1" alphatest="blend" />
				<widget name="backdrop" position="0,0" size="1920,1080" zPosition="-5" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/tmdb.png" position="1585,800" size="150,155" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1920,1080" zPosition="-4" alphatest="blend" />
				<widget name="key_red" position="225,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_green" position="565,920" size="280,30" font="Regular; 25" transparent="1" />
				<widget name="key_blue" position="1245,920" size="280,30" font="Regular; 25" transparent="1" />
				<ePixmap position="190,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="530,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="870,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="1210,925" size="25,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

else:
	tmdbScreenSkin = """
			<screen position="40,80" size="1200,600" title="TMDb - The Movie Database" >
				<widget name="searchinfo" position="20,10" size="1180,30" font="Regular;24" foregroundColor="#00fff000" transparent="1"/>
				<widget name="list" position="10,60" size="800,480" itemHeight="40" scrollbarMode="showOnDemand" transparent="1"/>
				<widget name="cover" position="860,180" size="250,375" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1280,720" zPosition="-6" scale="1" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1280,720" zPosition="-4" alphatest="blend" />
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/tmdb.png" position="915,10" size="150,155" zPosition="5" alphatest="blend" />
				<widget name="key_red" position="100,570" size="260,25" transparent="1" font="Regular;20"/>
				<widget name="key_green" position="395,570" size="260,25"  transparent="1" font="Regular;20"/>
				<widget name="key_yellow" position="690,570" size="260,25" transparent="1" font="Regular;20"/>
				<widget name="key_blue" position="985,570" size="260,25" transparent="1" font="Regular;20"/>
				<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

	tmdbScreenMovieSkin = """
			<screen position="40,80" size="1200,600" title="TMDb - The Movie Database">
				<widget name="searchinfo" position="10,10" size="930,30" font="Regular;24" foregroundColor="#00fff000" transparent="1"/>
				<widget name="fulldescription" position="10,60" size="620,490" font="Regular;24" transparent="1"/>
				<widget name="cover" position="950,30" size="200,300" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1280,720" zPosition="-6" scale="1" alphatest="blend" />
				<widget name="backdrop" position="0,0" size="1280,720" zPosition="-5" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1280,720" zPosition="-4" alphatest="blend" />
				<widget name="rating" position="640,85" size="150,25" zPosition="2" font="Regular;22" halign="center" foregroundColor="black" backgroundColor="#00ffba00" transparent="1"/>
				<widget name="votes_brackets" position="640,145" size="150,25" zPosition="2" font="Regular;22" halign="center" transparent="1"/>
				<ePixmap position="665,45" size="100,100" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/star.png" transparent="1" alphatest="blend"/>
				<widget name="fsk" position="0,0" size="0,0" zPosition="2" font="Regular;22" halign="center" transparent="1"/>
				<widget name="fsklogo" position="805,60" size="100,100" zPosition="2" alphatest="blend"/>
				<widget name="year_txt" position="650,300" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="year" position="780,300" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="country_txt" position="650,330" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="country" position="780,330" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="runtime_txt" position="650,360" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="runtime" position="780,360" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="votes_txt" position="650,390" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="votes" position="780,390" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="director_txt" position="650,420" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="director" position="780,420" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="author_txt" position="650,450" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="author" position="780,450" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="genre_txt" position="650,480" size="100,30" font="Regular; 22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="genre" position="780,480" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="studio_txt" position="650,510" size="100,30" font="Regular; 22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="studio" position="780,510" size="400,25" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="subtitle" position="0,0" size="0,0" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="description" position="0,0" size="0,0" zPosition="2" font="Regular;22" foregroundColor="#00ffffff" backgroundColor="#00303030" transparent="1"/>
				<widget name="key_red" position="100,570" size="260,25" font="Regular;20" transparent="1"/>
				<widget name="key_green" position="395,570" size="260,25" font="Regular;20" transparent="1"/>
				<widget name="key_yellow" position="690,570" size="260,25" font="Regular;20" transparent="1"/>
				<widget name="key_blue" position="985,570" size="260,25" font="Regular;20" transparent="1"/>
				<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

	tmdbScreenPeopleSkin = """
				<screen position="40,80" size="1200,600" title="TMDb - The Movie Database" >
					<widget name="searchinfo" zPosition="10" position="20,10" size="1180,40" font="Regular;24" foregroundColor="#00fff000" transparent="1"/>
					<widget name="list" position="10,60" size="900,480" itemHeight="40" scrollbarMode="showOnDemand" transparent="1"/>
					<widget name="cover" position="950,60" size="200,300" alphatest="blend"/>
					<widget name="data" position="0,0" size="0,0" font="Regular;21" />
					<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1280,720" zPosition="-6" scale="1" alphatest="blend" />
					<widget name="backdrop" position="0,0" size="1280,720" zPosition="-5" alphatest="blend"/>
					<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1280,720" zPosition="-4" alphatest="blend" />
					<widget name="key_red" position="100,570" size="260,25" font="Regular;20" transparent="1"/>
					<widget name="key_green" position="395,570" size="260,25" font="Regular;20" transparent="1"/>
					<widget name="key_blue" position="985,570" size="260,25" font="Regular;20" transparent="1"/>
					<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
					<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
					<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
					<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
				</screen>"""

	tmdbScreenPersonSkin = """
			<screen position="40,80" size="1200,600" title="TMDb - The Movie Database">
				<widget name="searchinfo" position="10,10" size="930,30" font="Regular;24" foregroundColor="#00fff000" transparent="1"/>
				<widget name="fulldescription" position="10,60" size="900,490" font="Regular;24" transparent="1"/>
				<widget name="cover" position="950,60" size="200,300" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1280,720" zPosition="-6" scale="1" alphatest="blend" />
				<widget name="backdrop" position="0,0" size="1280,720" zPosition="-5" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1280,720" zPosition="-4" alphatest="blend" />
				<widget name="key_red" position="100,570" size="260,25" font="Regular;20" transparent="1"/>
				<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""

	tmdbScreenSeasonSkin = """
			<screen position="40,80" size="1200,600" title="TMDb - The Movie Database" >
				<widget name="searchinfo" zPosition="10" position="20,10" size="1180,40" font="Regular;24" foregroundColor="#00fff000" transparent="1"/>
				<widget name="list" position="10,60" size="480,240" itemHeight="40" scrollbarMode="showOnDemand" transparent="1"/>
				<widget name="cover" position="550,60" size="530,300" zPosition="10" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop.jpg" position="0,0" size="1280,720" zPosition="-6" scale="1" alphatest="blend" />
				<widget name="backdrop" position="0,0" size="1280,720" zPosition="-5" alphatest="blend"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/backdrop_dark.png" position="0,0" size="1280,720" zPosition="-4" alphatest="blend" />
				<widget name="data" position="10,360" size="1180,200" font="Regular;21" transparent="1" />
				<widget name="key_red" position="100,570" size="260,25" font="Regular;20" transparent="1"/>
				<widget name="key_green" position="395,570" size="260,25" font="Regular;20" transparent="1"/>
				<widget name="key_blue" position="985,570" size="260,25" font="Regular;20" transparent="1"/>
				<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
				<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
				<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
				<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
			</screen>"""
