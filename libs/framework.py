# -*- coding: utf-8 -*-

__author__ = 'zhouhaichao@2008.sina.com'

import os

import wx

import libs.icons
import libs.config



# 菜单栏
TYPE_MENU = 0
# 任务栏菜单
TYPE_TASK_MENU = 1
# 工具栏
TYPE_TOOLBAR_MENU = 2

def startScreen():
    screen = wx.Bitmap(libs.icons.get("screen.png"), wx.BITMAP_TYPE_PNG)
    wx.SplashScreen(screen, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, 5000, None, -1)
    wx.Yield()

class CreateMenu:
    def __init__(self, menu, type = TYPE_MENU):
        self.menu = menu
        self.type = type

    def createMenu(self, menuData):
        """创建menu"""
        for eachMenuData in menuData:
            if isinstance(eachMenuData, basestring) or len(eachMenuData) == 1:
                self.menu.AppendSeparator()

            elif len(eachMenuData) == 2:
                if isinstance(eachMenuData[0], tuple):
                    menuId, menuLabel = eachMenuData[0]
                else :
                    menuId, menuLabel = wx.NewId(), eachMenuData[0]

                menuItems = eachMenuData[1]
                subMenu = self._createMenu(menuItems)
                if self.type == TYPE_MENU :
                    self.menu.Append(subMenu, menuLabel)
                else:
                    self.menu.AppendSubMenu(menuId, subMenu, menuLabel)
            else:
                self._createMenuItem(self.menu, *eachMenuData)


    def _createMenu(self, menuData):
        superMenu = wx.Menu()
        for eachItem in menuData:
            if isinstance(eachItem, basestring) or len(eachItem) == 1:
                superMenu.AppendSeparator()

            elif len(eachItem) == 2:
                if isinstance(eachItem[0],tuple) :
                    menuId, label = eachItem[0]
                else :
                    menuId, label = wx.NewId(), eachItem[0]

                subMenu = self._createMenu(eachItem[1])
                if self.type == TYPE_MENU:
                    superMenu.AppendMenu(menuId, label, subMenu)
                else:
                    superMenu.AppendSubMenu(menuId, label, subMenu)
            else:
                self._createMenuItem(superMenu, *eachItem)

        return superMenu

    def _createMenuItem(self, menu, label, status, handler, kind=wx.ITEM_NORMAL):
        labels = None

        if isinstance(label, [].__class__):
            labels = label
        else:
            labels = [label]

        for labelName in labels:
            if isinstance(labelName,tuple):
                menuId, showLabel = labelName
            else:
                menuId, showLabel = (wx.NewId(), labelName)

            menuItem = menu.Append(menuId, showLabel, status, kind)
            self.menu.Bind(wx.EVT_MENU, handler, menuItem)


class XTaskBarIcon(wx.TaskBarIcon):
    """
    状态栏图标
    """

    def __init__(self, frame, menuData):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame
        self.menuData = menuData
        self.SetIcon(libs.icons.desktop().GetIcon(), u'七牛文件管理')
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarLeftDClick)

    def OnTaskBarLeftDClick(self, event):
        if self.frame.IsIconized():
            self.frame.Iconize(False)
        if not self.frame.IsShown():
            self.frame.Show(True)
        self.frame.Raise()

    # override
    def CreatePopupMenu(self):
        menu = wx.Menu()
        CreateMenu(menu, TYPE_TASK_MENU).createMenu(self.menuData)
        return menu

class XFrame(wx.Frame):
    _taskBar = None
    _toolbar = None
    _menuBar = None
    def createMenuBar(self,menuData):
        """创建menubar
        menudata: ID(X0000),(menu)
        [
            (u"&文件", [
                (u"&上传文件", u"上传文件到当前空间", self.onUploadFileEvent),
                "---",
                (u"&最小化", u"最小化到系统托盘", self.onHideEvent),
                (u"&退出", u"退出系统", self.onExitEvent)
            ]),
            ((wx.NewId(),u"&视图"), (
                (u"&查看方式", [
                    ((u"&详细信息",u"&列表",u"&大图标",u"&小图标"), "", self.onViewChangedEvent, wx.ITEM_RADIO)
                ]),
                "---",
                (u"&排序方式",[
                    (u"&名称", "", self.onSortChangedEvent, wx.ITEM_RADIO),
                    (u"&大小", "", self.onSortChangedEvent, wx.ITEM_RADIO),
                    (u"&时间", "", self.onSortChangedEvent, wx.ITEM_RADIO)
                ])
            )),
            (u"&关于", [
                (u"&检查更新", u"连接服务器检测是否更新", self.onExitEvent),
                (u"&关于作者", u"作者简介", lambda event: AboutAuthDialog(self).Show()),
                (u"&关于软件", u"关于软件简介", lambda event: AboutSoftDialog(self).Show())
            ])
        ]

        """
        self._menuBar = wx.MenuBar()
        CreateMenu(self._menuBar).createMenu(menuData)
        self.SetMenuBar(self._menuBar)
        return self._menuBar

    def createToolBar(self,toolbarData):
        """创建ToolBar
        (
            ((wx.NewId(),"New"), "new.bmp", "Create new sketch", self.OnNew,True),
            "---",
            ("Open", "open.bmp", "Open existing sketch", self.OnOpen,False),
            ("Save", "save.bmp", "Save existing sketch", self.OnSave),

            ((ID.ID_TOOLBAR_SEARCH_TEXT, u"text"), (u"搜索默认值", u"hit"), {wx.EVT_KEY_DOWN:self.onKeyDown}), ##text
        )
        """
        self._toolbar = self.CreateToolBar()
        for each in toolbarData:
            if isinstance(each, basestring):
                self._toolbar.AddSeparator()
            elif len(each) == 3:
                # input
                if isinstance(each[0], tuple):
                    toolId, showLabel = each[0]
                else:
                    toolId, showLabel = (wx.NewId(), each[0])

                if isinstance(each[1], [].__class__):  # choice
                    text = wx.StaticText(self._toolbar, -1, showLabel)
                    self._toolbar.AddControl(text, u"showLabel")

                    choice = wx.Choice(self._toolbar, toolId, choices=each[1])
                    choice.Bind(wx.EVT_CHOICE,each[2])
                    self._toolbar.AddControl(choice, showLabel)
                else: #input
                    text = wx.TextCtrl(self._toolbar, toolId)
                    # hit and the default show text
                    defText, hitText = each[1]
                    text.SetHint(hitText)
                    text.SetValue(defText)

                    # events
                    events = each[2]
                    if events != None:
                        for key in events:
                            event = events[key]
                            text.Bind(key, event)

                    self._toolbar.AddControl(text, showLabel)
            else:
                self._createButtonTool(self._toolbar, *each)

        self._toolbar.Realize()
        return self._toolbar

    def _createButtonTool(self, toolbar, labelOrLabel, help, bitmap, handler, enable=True, kind=0):
        if isinstance(bitmap, [].__class__):
            normalBitmap = libs.icons.toolbar(bitmap[0]).GetBitmap()
            disableBitmap = libs.icons.toolbar(bitmap[1]).GetBitmap()
        else:
            name,ext = os.path.splitext(bitmap)
            normalBitmap = libs.icons.toolbar(bitmap).GetBitmap()
            disableBitmap = normalBitmap

        if isinstance(labelOrLabel, tuple):
            toolId, showLabel = labelOrLabel
        else:
            toolId, showLabel = (wx.NewId(), labelOrLabel)

        tool = toolbar.AddLabelTool(toolId, showLabel, normalBitmap, disableBitmap, kind, showLabel, help)
        toolbar.EnableTool(toolId, enable)
        self.Bind(wx.EVT_MENU, handler, tool)

    def createStatusBar(self,status):
        # default | 空间:image | 已加载：100 |
        self._statusBar = self.CreateStatusBar()
        self._statusBar.SetFieldsCount(len(status))
        if status:
            self._statusBar.SetStatusWidths(status)
        return self._statusBar

    def createTaskBarIcon(self, menuData):
        self._taskBar = XTaskBarIcon(self, menuData)
        return self._taskBar

    def exitSys(self):
        if self._taskBar != None:
            self._taskBar.Destroy()
        self.Hide()
        self.Destroy()

    def onToggleShowEvent(self, event):
        if self.IsIconized():
            self.Iconize(False)
        if not self.IsShown():
            self.Show(True)
        self.Raise()

    def onHideEvent(self, event):
        self.Hide()

    def onShowEvent(self, event):
        self.Show()

    def onExitEvent(self, event):
        self.exitSys()

    def update(self):
        size = self.GetSize()
        size[0]+=1
        self.SetSize(size)
        size[0]-=1
        self.SetSize(size)