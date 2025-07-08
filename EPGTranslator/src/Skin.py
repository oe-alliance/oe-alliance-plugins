# Default skin data for EPGTranslator
# Only contains "class" data.  No instance data
#

class MySkinData:


# class translatorMain bits
#
#   "text" y-size is dynamic {size}
#
    TranslatorMain_skin = """
        <screen resolution="1920,1080" position="center,90" size="1500,925" title="EPG Translator">
            <ePixmap position="0,0" size="1500,75" pixmap="{plug_loc}/pic/fhd-translator.png" alphatest="blend" zPosition="1" scale="1"/>

            <widget source="key_blue" render="Pixmap" pixmap="{plug_loc}/pic/buttons/fhd-blue.png" position="15,9" size="27,27" alphatest="blend" conditional="key_blue" transparent="1" zPosition="2" scale="1">
                <convert type="ConditionalShowHide" />
            </widget>
            <widget source="key_blue" render="Label" position="51,9" size="300,30" backgroundColor="#FFFFFF" font="Regular;24" foregroundColor="black" halign="left" conditional="key_blue" transparent="1" valign="center" zPosition="2" />
            <widget source="key_yellow" render="Pixmap" pixmap="{plug_loc}/pic/buttons/fhd-yellow.png" position="15,39" size="27,27" alphatest="blend" conditional="key_yellow" transparent="1" zPosition="2" scale="1">
                <convert type="ConditionalShowHide" />
            </widget>
            <widget source="key_yellow" render="Label" position="51,39" size="300,30" backgroundColor="#FFFFFF" font="Regular;24" foregroundColor="black" halign="left" conditional="key_yellow" transparent="1" valign="center" zPosition="2" />
            <widget source="key_red" render="Pixmap" pixmap="{plug_loc}/pic/buttons/fhd-red.png" position="320,9" size="27,27" alphatest="blend" conditional="key_red" transparent="1" zPosition="2" scale="1">
                <convert type="ConditionalShowHide" />
            </widget>
            <widget source="key_red" render="Label" position="356,9" size="300,30" backgroundColor="#FFFFFF" font="Regular;24" foregroundColor="black" halign="left" conditional="key_red" transparent="1" valign="center" zPosition="2" />
            <widget source="key_green" render="Pixmap" pixmap="{plug_loc}/pic/buttons/fhd-green.png" position="320,39" size="27,27" alphatest="blend" conditional="key_green" transparent="1" zPosition="2" scale="1">
                <convert type="ConditionalShowHide" />
            </widget>
            <widget source="key_green" render="Label" position="356,39" size="300,30" backgroundColor="#FFFFFF" font="Regular;24" foregroundColor="black" halign="left" conditional="key_green" transparent="1" valign="center" zPosition="2" />

            <widget source="key_ok" render="FixedLabel" text="OK" position="840,9" size="90,29" backgroundColor="black" font="Regular;24" foregroundColor="white" halign="center" valign="center" conditional="key_ok" zPosition="2" >
                <convert type="ConditionalShowHide" />
            </widget>
            <widget source="key_ok" render="Label" position="935,9" size="230,30" backgroundColor="#FFFFFF" font="Regular;24" foregroundColor="black" halign="left" conditional="key_ok" transparent="1" valign="center" zPosition="2" />
            <widget source="key_back" render="FixedLabel" text="Back" position="840,40" size="90,29" backgroundColor="black" font="Regular;24" foregroundColor="white" halign="center"  valign="center" conditional="key_back" zPosition="2" >
                <convert type="ConditionalShowHide" />
            </widget>
            <widget source="key_back" render="Label" position="935,39" size="230,30" backgroundColor="#FFFFFF" font="Regular;24" foregroundColor="black" halign="left" conditional="key_back" transparent="1" valign="center" zPosition="2" />

            <widget source="key_menu" render="Label" text="Menu" position="1200,9" size="90,29"  backgroundColor="black" font="Regular;24" foregroundColor="white" halign="center" valign="center" conditional="key_menu" zPosition="2" >
                <convert type="ConditionalShowHide" />
            </widget>

            <widget render="Label" source="global.CurrentTime" position="10,90" size="250,75" font="Regular;36" foregroundColor="yellow" halign="center" valign="center" transparent="1" zPosition="1">
                <convert type="ClockToText">Format:%H:%M:%S</convert>
            </widget>
            <widget name="timing" position="318,90" size="1200,50" foregroundColor="orange" font="Bold;36" halign="left" zPosition="1" />

            <widget name="from_lang" position="15,200" size="288,250" font="Regular;44" foregroundColor="blue" valign="top" zPosition="2" />
            <widget name="u_title" position="318,140" size="1200,100" font="Regular;36" zPosition="2" />
            <widget name="u_descr" position="318,240" size="1200,{size}" font="Regular;36" zPosition="2" />
            <widget name="to_lang" position="15,590"  size="288,250" font="Regular;44" foregroundColor="blue" valign="top" zPosition="1" />
            <widget name="l_title" position="318,530" size="1200,100" font="Regular;36" zPosition="1" />
            <widget name="l_descr" position="318,630" size="1200,290" font="Regular;36" zPosition="1" />
        </screen>
        """
    tmyes = "290"
    tmno = "670"


MySD = MySkinData()
