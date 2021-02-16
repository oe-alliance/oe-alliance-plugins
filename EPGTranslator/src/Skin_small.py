# Skin data for screenwidth <= 1280
# Only contains "class" data.  No instance data
#

class MySkinData:

# class translatorConfig bits
#
    translatorConfig_skin = """
        <screen position="center,center" size="811,575" backgroundColor="#20000000" title="EPG Translator Setup">
            <ePixmap position="133,0" size="545,50" pixmap="{plug_loc}/pic/translatorConfig.png" alphatest="blend" zPosition="1" />
            <ePixmap position="70,59" size="671,1" pixmap="{plug_loc}/pic/separator.png" alphatest="off" zPosition="1" />
            <widget name="config" position="10,60" size="780,197" itemHeight="38" scrollbarMode="showOnDemand" font="Regular;24" secondfont="Regular;24" zPosition="1" />
            <ePixmap position="70,260" size="671,1" pixmap="{plug_loc}/pic/separator.png" alphatest="off" zPosition="1" />
            <ePixmap position="210,270" size="18,18" pixmap="{plug_loc}/pic/buttons/green.png" alphatest="blend" zPosition="1" />
            <ePixmap position="525,270" size="18,18" pixmap="{plug_loc}/pic/buttons/red.png" alphatest="blend" zPosition="1" />
            <eLabel position="235,269" size="180,26" font="Regular;24" halign="left" text="Save" transparent="1" zPosition="1" />
            <eLabel position="550,269" size="180,26" font="Regular;24" halign="left" text="Cancel" transparent="1" zPosition="1" />
            <widget name="flag" position="261,280" size="288,288" alphatest="blend" zPosition="1" />
        </screen>
        """

# class translatorMain bits
#
#   "text" y-size is dynamic {size}
#
    translatorMain_skin = """
        <screen position="center,80" size="1000,610" title="EPG Translator">
            <ePixmap position="0,0" size="1000,50" pixmap="{plug_loc}/pic/translator.png" alphatest="blend" zPosition="1" />
            <ePixmap position="10,6" size="18,18" pixmap="{plug_loc}/pic/buttons/blue.png" alphatest="blend" zPosition="2" />
            <ePixmap position="10,26" size="18,18" pixmap="{plug_loc}/pic/buttons/yellow.png" alphatest="blend" zPosition="2" />
            <widget name="label" position="34,6" size="200,20" font="Regular;16" foregroundColor="black" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget name="label2" position="34,26" size="200,20" font="Regular;16" foregroundColor="black" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget render="Label" source="global.CurrentTime" position="740,0" size="240,50" font="Regular;24" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
                <convert type="ClockToText">Format:%H:%M:%S</convert>
            </widget>
            <widget name="timing" position="308,55" size="750,32" foregroundColor="orange" font="Bold;24" halign="left" zPosition="1" />
            <widget name="flag" position="10,90" size="288,288" alphatest="blend" zPosition="1" />
            <widget name="text" position="308,90" size="750,{size}" font="Regular;24" halign="left" zPosition="2" />
            <widget name="flag2" position="10,350" size="288,288" alphatest="blend" zPosition="1" />
            <widget name="text2" position="308,350" size="750,255" font="Regular;24" halign="left" zPosition="1" />
        </screen>
        """
    tMyes = "255"
    tMno  = "515"


MySD = MySkinData()
