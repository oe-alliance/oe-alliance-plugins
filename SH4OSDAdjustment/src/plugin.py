from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigInteger
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from enigma import getDesktop, fbClass
from os import path as os_path
config.OSDAdjustment = ConfigSubsection()
config.OSDAdjustment.top = ConfigInteger(default=0)
config.OSDAdjustment.bottom = ConfigInteger(default=0)
config.OSDAdjustment.left = ConfigInteger(default=0)
config.OSDAdjustment.right = ConfigInteger(default=0)
config.OSDAdjustment.settuxtxt2conf = ConfigInteger(default=0)
from __init__ import _

class Screen_adjust(Screen):
    if getDesktop(0).size().width() == 1280:
        skin = '\n\t\t\t<screen position="center,center" size="1280,720" backgroundColor="#000000" title="OSD Adjustment" >\n\t\t\t\t<widget source="title" render="Label" position="200,130" zPosition="1" size="880,60" font="Regular;58" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="introduction" render="Label" position="150,250" zPosition="1" size="980,100" font="Regular;40" halign="center" valign="center" transparent="1" />\n\t\t\t\t<widget source="infotext" render="Label" position="150,380" zPosition="1" size="980,100" font="Regular;40" halign="center" valign="center" transparent="1" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,0" size="1280,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,719" size="1280,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,0" size="1,720" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="1279,0" size="1,720" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,25" size="1230,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,694" size="1230,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,25" size="1,670" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="1254,25" size="1,670" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,50" size="1180,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,669" size="1180,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,50" size="1,620" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="1229,50" size="1,620" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,75" size="1130,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,644" size="1130,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,75" size="1,570" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="1204,75" size="1,570" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="189,627" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="443,627" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="697,627" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="951,627" size="140,3" zPosition="0" />\n\t\t\t\t<widget source="key_red" render="Label" position="189,605" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_green" render="Label" position="443,605" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_yellow" render="Label" position="697,605" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_blue" render="Label" position="951,605" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t</screen>'
    elif getDesktop(0).size().width() == 1024:
        skin = '\n\t\t\t<screen position="center,center" size="1024,576" backgroundColor="#000000" title="OSD Adjustment" >\n\t\t\t\t<widget source="title" render="Label" position="200,100" zPosition="1" size="624,40" font="Regular;38" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="introduction" render="Label" position="100,180" zPosition="1" size="824,50" font="Regular;24" halign="center" valign="center" transparent="1" />\n\t\t\t\t<widget source="infotext" render="Label" position="100,310" zPosition="1" size="824,50" font="Regular;24" halign="center" valign="center" transparent="1" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,0" size="1024,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,575" size="1024,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,0" size="1,576" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="1023,0" size="1,576" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,25" size="974,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,551" size="974,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,25" size="1,526" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="999,25" size="1,526" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,50" size="924,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,526" size="924,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,50" size="1,476" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="974,50" size="1,476" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,75" size="874,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,501" size="874,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,75" size="1,426" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="949,75" size="1,426" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="138,477" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="341,477" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="544,477" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="747,477" size="140,3" zPosition="0" />\n\t\t\t\t<widget source="key_red" render="Label" position="138,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_green" render="Label" position="341,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_yellow" render="Label" position="544,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_blue" render="Label" position="747,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t</screen>'
    else:
        skin = '\n\t\t\t<screen position="center,center" size="720,576" backgroundColor="#000000" title="OSD Adjustment" >\n\t\t\t\t<widget source="title" render="Label" position="75,100" zPosition="1" size="570,40" font="Regular;38" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="introduction" render="Label" position="75,180" zPosition="1" size="570,50" font="Regular;21" halign="center" valign="center" transparent="1" />\n\t\t\t\t<widget source="infotext" render="Label" position="75,310" zPosition="1" size="570,50" font="Regular;21" halign="center" valign="center" transparent="1" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,0" size="720,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,575" size="720,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="0,0" size="1,576" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="719,0" size="1,576" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,25" size="670,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,551" size="670,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="25,25" size="1,526" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="694,25" size="1,526" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,50" size="620,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,526" size="620,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="50,50" size="1,476" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="670,50" size="1,476" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,75" size="570,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,501" size="570,1" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="75,75" size="1,426" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="645,75" size="1,426" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="red" position="80,477" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="green" position="220,477" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="yellow" position="360,477" size="140,3" zPosition="0" />\n\t\t\t\t<eLabel backgroundColor="blue" position="500,477" size="140,3" zPosition="0" />\n\t\t\t\t<widget source="key_red" render="Label" position="80,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_green" render="Label" position="220,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_yellow" render="Label" position="360,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t\t<widget source="key_blue" render="Label" position="500,455" zPosition="1" size="140,22" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t\t</screen>'

    def __init__(self, session):
        global rightbottom
        self.skin = Screen_adjust.skin
        Screen.__init__(self, session)
        self['key_red'] = StaticText(_('cancel'))
        self['key_green'] = StaticText(_('save'))
        self['key_yellow'] = StaticText(_('set default'))
        self['key_blue'] = StaticText(_('change sides'))
        self['title'] = StaticText(_('OSD Adjustment'))
        self['introduction'] = StaticText(_('Here you can change the screen positions with the arrow buttons on your remote control!'))
        self['infotext'] = StaticText(_('Now you can change the position of the upper and left side. Press blue button to switch...'))
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions'], {'cancel': self.Exit,
         'ok': self.Ok,
         'red': self.Exit,
         'green': self.Ok,
         'yellow': self.yellow,
         'blue': self.blue,
         'left': self.left,
         'right': self.right,
         'up': self.up,
         'down': self.down}, -1)
        self.LoadConfig()
        rightbottom = False

    def LoadConfig(self):
        global right
        global bottom
        global top
        global oldbottom
        global oldright
        global oldtop
        global oldleft
        global left
        top = config.OSDAdjustment.top.value
        bottom = config.OSDAdjustment.bottom.value
        left = config.OSDAdjustment.left.value
        right = config.OSDAdjustment.right.value
        oldtop = top
        oldbottom = bottom
        oldleft = left
        oldright = right

    def left(self):
        global right
        global left
        if rightbottom is False:
            print '[OSD Adjustment] left'
            left = int(left) - 5
            if left < 0:
                left = 0
        else:
            print '[OSD Adjustment] right'
            right = int(right) - 5
            if right < -150:
                right = -150
        fbClass.getInstance().setFBdiff(int(top), int(left), int(right), int(bottom))
        fbClass.getInstance().clearFBblit()

    def right(self):
        global right
        global left
        if rightbottom is False:
            print '[OSD Adjustment] left'
            left = int(left) + 5
            if left > 150:
                left = 150
        else:
            print '[OSD Adjustment] right'
            right = int(right) + 5
            if right > 0:
                right = 0
        fbClass.getInstance().setFBdiff(int(top), int(left), int(right), int(bottom))
        fbClass.getInstance().clearFBblit()

    def up(self):
        global top
        global bottom
        if rightbottom is False:
            print '[OSD Adjustment] top'
            top = int(top) - 5
            if top < 0:
                top = 0
        else:
            print '[OSD Adjustment] bottom'
            bottom = int(bottom) - 5
            if bottom < -150:
                bottom = -150
        fbClass.getInstance().setFBdiff(int(top), int(left), int(right), int(bottom))
        fbClass.getInstance().clearFBblit()

    def down(self):
        global top
        global bottom
        if rightbottom is False:
            print '[OSD Adjustment] top'
            top = int(top) + 5
            if top > 150:
                top = 150
        else:
            print '[OSD Adjustment] bottom'
            bottom = int(bottom) + 5
            if bottom > 0:
                bottom = 0
        fbClass.getInstance().setFBdiff(int(top), int(left), int(right), int(bottom))
        fbClass.getInstance().clearFBblit()

    def yellow(self):
        global top
        global right
        global bottom
        global left
        print '[OSD Adjustment] set Default Screen Settings'
        top = 0
        bottom = 0
        left = 0
        right = 0
        fbClass.getInstance().setFBdiff(0, 0, 0, 0)
        fbClass.getInstance().clearFBblit()

    def blue(self):
        global rightbottom
        if rightbottom is False:
            rightbottom = True
            self['infotext'].setText(_('Now you can change the position of the lower and right side. Press blue button to switch...'))
        else:
            rightbottom = False
            self['infotext'].setText(_('Now you can change the position of the upper and left side. Press blue button to switch...'))

    def Exit(self):
        fbClass.getInstance().setFBdiff(int(oldtop), int(oldleft), int(oldright), int(oldbottom))
        fbClass.getInstance().clearFBblit()
        self.close()

    def Ok(self):
        config.OSDAdjustment.top.value = int(top)
        config.OSDAdjustment.bottom.value = int(bottom)
        config.OSDAdjustment.left.value = int(left)
        config.OSDAdjustment.right.value = int(right)
        config.OSDAdjustment.settuxtxt2conf.value = 1
        config.OSDAdjustment.save()
        self.close()


class SetScreen:

    def __init__(self, session):
        self.ScreenOnStartup()

    def ScreenOnStartup(self):
        print '[OSD Adjustment] Set Screen on startup'
        top = config.OSDAdjustment.top.value
        bottom = config.OSDAdjustment.bottom.value
        left = config.OSDAdjustment.left.value
        right = config.OSDAdjustment.right.value
        fbClass.getInstance().setFBdiff(int(top), int(left), int(right), int(bottom))
        fbClass.getInstance().clearFBblit()
        if config.OSDAdjustment.settuxtxt2conf.value == 1 or os_path.isfile('/etc/.getbootvid'):
            config.OSDAdjustment.settuxtxt2conf.value = 0
            config.OSDAdjustment.save()
            VTStartX = 40 + int(left)
            VTEndX = 680 + int(right)
            VTStartY = 20 + int(top)
            VTEndY = 555 + int(bottom)
            adir = '/etc/tuxbox/tuxtxt2.conf'
            self.e = []
            if os_path.isfile(adir) is True:
                f = open(adir, 'r')
                self.e = f.readlines()
                f.close
                for line in self.e:
                    if line.find('ScreenMode16x9Normal ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        ScreenMode16x9Normal = line
                    elif line.find('ScreenMode16x9Divided ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        ScreenMode16x9Divided = line
                    elif line.find('Brightness ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        Brightness = line
                    elif line.find('MenuLanguage ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        MenuLanguage = line
                    elif line.find('AutoNational ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        AutoNational = line
                    elif line.find('NationalSubset ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        NationalSubset = line
                    elif line.find('SwapUpDown ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        SwapUpDown = line
                    elif line.find('ShowHexPages ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        ShowHexPages = line
                    elif line.find('Transparency ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        Transparency = line
                    elif line.find('TTFWidthFactor16 ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        TTFWidthFactor16 = line
                    elif line.find('TTFHeightFactor16 ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        TTFHeightFactor16 = line
                    elif line.find('TTFShiftX ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        TTFShiftX = line
                    elif line.find('TTFShiftY ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        TTFShiftY = line
                    elif line.find('Screenmode ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        Screenmode = line
                    elif line.find('ShowFLOF ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        ShowFLOF = line
                    elif line.find('Show39 ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        Show39 = line
                    elif line.find('ShowLevel2p5 ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        ShowLevel2p5 = line
                    elif line.find('DumpLevel2p5 ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        DumpLevel2p5 = line
                    elif line.find('UseTTF ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        UseTTF = line
                    elif line.find('StartX ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        StartX = line
                    elif line.find('EndX ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        EndX = line
                    elif line.find('StartY ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        StartY = line
                    elif line.find('EndY ') > -1:
                        line = line.split(' ')
                        line = line[1]
                        EndY = line

                if not VTStartX == int(StartX) or not VTEndX == int(EndX) or not VTStartY == int(StartY) or not VTEndY == int(EndY):
                    print '[OSD Adjustment] Write tuxtxt2.conf with new OSD settings'
                    self.e = []
                    self.e.append('ScreenMode16x9Normal ' + ScreenMode16x9Normal + '\n')
                    self.e.append('ScreenMode16x9Divided ' + ScreenMode16x9Divided + '\n')
                    self.e.append('Brightness ' + Brightness + '\n')
                    self.e.append('MenuLanguage ' + MenuLanguage + '\n')
                    self.e.append('AutoNational ' + AutoNational + '\n')
                    self.e.append('NationalSubset ' + NationalSubset + '\n')
                    self.e.append('SwapUpDown ' + SwapUpDown + '\n')
                    self.e.append('ShowHexPages ' + ShowHexPages + '\n')
                    self.e.append('Transparency ' + Transparency + '\n')
                    self.e.append('TTFWidthFactor16 ' + TTFWidthFactor16 + '\n')
                    self.e.append('TTFHeightFactor16 ' + TTFHeightFactor16 + '\n')
                    self.e.append('TTFShiftX ' + TTFShiftX + '\n')
                    self.e.append('TTFShiftY ' + TTFShiftY + '\n')
                    self.e.append('Screenmode ' + Screenmode + '\n')
                    self.e.append('ShowFLOF ' + ShowFLOF + '\n')
                    self.e.append('Show39 ' + Show39 + '\n')
                    self.e.append('ShowLevel2p5 ' + ShowLevel2p5 + '\n')
                    self.e.append('DumpLevel2p5 ' + DumpLevel2p5 + '\n')
                    self.e.append('UseTTF ' + UseTTF + '\n')
                    self.e.append('StartX ' + str(VTStartX) + '\n')
                    self.e.append('EndX ' + str(VTEndX) + '\n')
                    self.e.append('StartY ' + str(VTStartY) + '\n')
                    self.e.append('EndY ' + str(VTEndY) + '\n')
                    if os_path.isfile(adir) is True:
                        f = open(adir, 'w')
                        f.writelines(self.e)
                        f.flush()
                        f.close


ScreenInstance = None

def sessionstart(reason, session):
    global ScreenInstance
    if ScreenInstance is None:
        ScreenInstance = SetScreen(session)
    return


def main(session, **kwargs):
    session.open(Screen_adjust)


def menu(menuid, **kwargs):
    if menuid == 'osd_menu':
        return [(_('OSD Adjustment'),
          main,
          'OSD_Adjustment',
          11)]
    return []


def Plugins(**kwargs):
    return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart), PluginDescriptor(name='OSD Adjustment', description=_('change the OSD screen size'), where=PluginDescriptor.WHERE_MENU, fnc=menu)]
