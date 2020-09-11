
SKHEADTOP = '<eLabel position="0,0" size="{headw},60" backgroundColor="#FFFFFF" /><ePixmap position="0,0" size="{headw},60" pixmap="{picpath}tvspielfilmHD.png" alphatest="blend" zPosition="1" />'

SKTIME = """
        <widget render="Label" source="global.CurrentTime" position="_1000,0" size="225,60" font="Regular;26" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
        <convert type="ClockToText">Format:%H:%M:%S</convert>
        </widget>"""


SKHEADBOTTOM = """
        <widget name="searchtimer" position="420,5" size="400,50" pixmap="{picpath}search_timer.png" alphatest="blend" zPosition="3" />
        <widget name="searchlogo" position="5,75" size="200,50" pixmap="{picpath}search.png" alphatest="blend" zPosition="1" />
        <widget name="searchtext" position="245,75" size="955,65" font="Regular;26" valign="center" zPosition="1" />
        <widget name="searchmenu" position="10,140" size="1220,480" scrollbarMode="showNever" zPosition="1" /> 
        <widget name="picpost" position="_375,70" size="490,245" alphatest="blend" zPosition="1" />
        <widget name="piclabel" position="_476,265" size="100,25" font="Regular;22" foregroundColor="#FFFFFF" backgroundColor="#CD006C" halign="center" valign="center" zPosition="2" />
        <widget name="piclabel2" position="_476,290" size="100,25" font="Regular;18" foregroundColor="#CD006C" backgroundColor="#FFFFFF" halign="center" valign="center" zPosition="2" />
        <widget name="infotext" position="10,_70" size="_310,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
        <widget name="infotext2" position="10,_105" size="_375,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
        <widget name="infotext3" position="10,_140" size="_375,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
        <widget name="infotext4" position="10,_175" size="_375,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="left" zPosition="1" />
        <widget name="infotext5" position="_855,_70" size="_375,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
        <widget name="infotext6" position="_855,_105" size="_375,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
        <widget name="infotext7" position="_855,_140" size="_375,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
        <widget name="infotext8" position="_855,_175" size="_375,_25" font="Regular;{fontsize}" foregroundColor="#AAB2BA" halign="right" zPosition="1" />
        <widget name="tvinfo1" position="10,215" size="60,20" alphatest="blend" zPosition="1" />
        <widget name="tvinfo2" position="80,215" size="60,20" alphatest="blend" zPosition="1" />
        <widget name="tvinfo3" position="150,215" size="60,20" alphatest="blend" zPosition="1" />
        <widget name="tvinfo4" position="10,245" size="60,20" alphatest="blend" zPosition="1" />
        <widget name="tvinfo5" position="80,245" size="60,20" alphatest="blend" zPosition="1" />
        <widget name="cinlogo" position="_325,70" size="60,29" pixmap="{picpath}icons/cin.png" alphatest="blend" zPosition="1" />
        <widget name="playlogo" position="_565,163" size="109,58" pixmap="{picpath}icons/playHD.png" alphatest="blend" zPosition="2" />
        <widget name="textpage" position="10,325" size="_1220,{slider}" font="Regular;{fontsize}" halign="left" zPosition="0" />
        <widget name="slider_textpage" position="_1214,325" size="22,{slider}" pixmap="{picpath}/slider/slider_{slider}.png" alphatest="blend" zPosition="1" />
        <widget name="label" position="_220,10" size="800,22" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="center" transparent="1" zPosition="2" />
        <widget name="label2" position="_469,32" size="100,22" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
        <widget name="label3" position="_594,32" size="100,22" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
        <widget name="label4" position="_719,32" size="100,22" font="Regular;18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
        <ePixmap position="445,33" size="18,18" pixmap="{picpath}buttons/red.png" alphatest="blend" zPosition="2" />
        <ePixmap position="570,33" size="18,18" pixmap="{picpath}buttons/yellow.png" alphatest="blend" zPosition="2" />
        <ePixmap position="695,33" size="18,18" pixmap="{picpath}buttons/green.png" alphatest="blend" zPosition="2" />""" + SKTIME

SKMENU = '<widget name="menu" position="10,75" size="{menusize}" scrollbarMode="showNever" zPosition="1" />' 

SKHEADPIC =  """
        <widget name="pic1" position="1095,75" size="135,90" alphatest="blend" zPosition="1" />
        <widget name="pic2" position="1095,165" size="135,90" alphatest="blend" zPosition="1" />
        <widget name="pic3" position="1095,255" size="135,90" alphatest="blend" zPosition="1" />
        <widget name="pic4" position="1095,345" size="135,90" alphatest="blend" zPosition="1" />
        <widget name="pic5" position="1095,435" size="135,90" alphatest="blend" zPosition="1" />
        <widget name="pic6" position="1095,525" size="135,90" alphatest="blend" zPosition="1" />"""

SKHEADPLAY =  """
        <widget name="play1" position="36,91" size="109,58" alphatest="blend" zPosition="1" />
        <widget name="play2" position="36,181" size="109,58" alphatest="blend" zPosition="1" />
        <widget name="play3" position="36,271" size="109,58" alphatest="blend" zPosition="1" />
        <widget name="play4" position="36,361" size="109,58" alphatest="blend" zPosition="1" />
        <widget name="play5" position="36,451" size="109,58" alphatest="blend" zPosition="1" />
        <widget name="play6" position="36,541" size="109,58" alphatest="blend" zPosition="1" />"""

