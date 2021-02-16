# Skin data for screenwidth > 1280
# Only contains "class" data.  No instance data
#

class MySkinData:

# class translatorConfig bits
#
    translatorConfig_skin = """
        <screen position="center,center" size="1218,788" backgroundColor="#20000000" title="EPG Translator Setup">
            <ePixmap position="200,0" size="818,75" pixmap="{plug_loc}/pic/fhd-translatorConfig.png" alphatest="blend" zPosition="1" />
            <ePixmap position="110,89" size="998,1" pixmap="{plug_loc}/pic/separator.png" alphatest="off" zPosition="1" />
            <widget name="config" position="15,90" size="1188,290" itemHeight="57" scrollbarMode="showOnDemand" font="Regular;36" secondfont="Regular;36" zPosition="1" />
            <ePixmap position="110,390" size="998,1" pixmap="{plug_loc}/pic/separator.png" alphatest="off" zPosition="1" />
            <ePixmap position="318,405" size="27,27" pixmap="{plug_loc}/pic/buttons/fhd-green.png" alphatest="blend" zPosition="1" />
            <ePixmap position="795,405" size="27,27" pixmap="{plug_loc}/pic/buttons/fhd-red.png" alphatest="blend" zPosition="1" />
            <eLabel position="355,414" size="270,40" font="Regular;36" halign="left" text="Save" transparent="1" zPosition="1" />
            <eLabel position="833,414" size="270,40" font="Regular;36" halign="left" text="Cancel" transparent="1" zPosition="1" />
            <widget name="flag" position="464,460" size="288,288" alphatest="blend" zPosition="1" />
        </screen>
        """

# class translatorMain bits
#
#   "text" y-size is dynamic {size}
#
    translatorMain_skin = """
        <screen position="center,120" size="1500,915" title="EPG Translator">
            <ePixmap position="0,0" size="1500,75" pixmap="{plug_loc}/pic/fhd-translator.png" alphatest="blend" zPosition="1" />
            <ePixmap position="15,9" size="27,27" pixmap="{plug_loc}/pic/buttons/fhd-blue.png" alphatest="blend" zPosition="2" />
            <ePixmap position="15,39" size="27,27" pixmap="{plug_loc}/pic/buttons/fhd-yellow.png" alphatest="blend" zPosition="2" />
            <widget name="label" position="51,9" size="300,30" font="Regular;24" foregroundColor="black" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label2" position="51,39" size="300,30" font="Regular;24" foregroundColor="black" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget render="Label" source="global.CurrentTime" position="1110,0" size="360,75" font="Regular;36" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
                <convert type="ClockToText">Format:%H:%M:%S</convert>
            </widget>
            <widget name="timing" position="318,90" size="1200,50" foregroundColor="orange" font="Bold;36" halign="left" zPosition="1" />
            <widget name="flag" position="15,140" size="288,288" alphatest="blend" zPosition="1" />
            <widget name="text" position="318,140" size="1200,{size}" font="Regular;36" halign="left" zPosition="2" />
            <widget name="flag2" position="15,530" size="288,288" alphatest="blend" zPosition="1" />
            <widget name="text2" position="318,530" size="1200,385" font="Regular;36" halign="left" zPosition="1" />
        </screen>
        """
    tMyes = "380"
    tMno  = "770"


MySD = MySkinData()
