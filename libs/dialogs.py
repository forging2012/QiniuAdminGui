# -*- coding: utf-8 -*-

__author__ = 'zhouhaichao@2008.sina.com'

import wx
import wx.html


class AboutAuthDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, u"关于作者")
        html = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()

        html.SetPage(
            "Here is some <b>formatted</b> <i><u>text</u></i> "
            "loaded from a <font color=\"red\">string</font>.")

        self.Center()


class AboutSoftDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, u"关于作者")
        html = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()

        html.SetPage(
            "Here is some <b>formatted</b> <i><u>text</u></i> "
            "loaded from a <font color=\"red\">string</font>.")

        self.Center()


class QiniuNameDialog(wx.Dialog):
    __newName = ""
    def __init__(self,fileName):
        wx.Dialog.__init__(self, None, -1, u'('+fileName+u')已经存在', size=(300, 100))
        x, y = 70, 40
        self.label = wx.TextCtrl(self,value=fileName,pos=(15, 10), size=(300-15*2, 25))
        self.label.Bind(wx.EVT_KEY_UP,self.onKeyUpEvent)
        wx.Button(self, wx.ID_OK, u"重命名", pos=(x, y), size=(60, 25))
        resetBtn = wx.Button(self, wx.ID_YES, u"覆盖", pos=(x + 60 + 15, y), size=(60, 25))
        wx.Button(self, wx.ID_CANCEL, u"取消上传", pos=(x + 60 + 15 + 60 + 15, y), size=(60, 25))
        resetBtn.Bind(wx.EVT_BUTTON,self.onResetButton)

    def onResetButton(self, event):
        self.SetReturnCode(wx.ID_YES)
        self.Hide()

    def onKeyUpEvent(self,event):
        self.__newName = self.label.GetValue()

    def GetNewName(self):
        return self.__newName

if __name__ == '__main__':
    app = wx.App()
    print(QiniuNameDialog().ShowModal())
