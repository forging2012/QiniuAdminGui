# -*- coding:utf-8 -*-
import qiniu

__author__ = 'zhouhaichao@2008.sina.com'

import wx
import libs.icons

from libs.main import MainFrame
from libs.threads import wxAsynchronousThread
from libs.config import Config
from libs.versions import VERSION


class LoginPanel(wx.Panel):
    def __init__(self, parent, onLoginSuccess):
        wx.Panel.__init__(self, parent, style=wx.BORDER_SIMPLE)
        self.frame = parent
        self.onLoginSuccess = onLoginSuccess

        self.conf = Config()
        accessKey, secretKey = self.conf.getKeys()

        loginTitle = wx.StaticText(self, -1, u" 登 陆 ")
        loginTitle.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

        accessKeyLabel = wx.StaticText(self, -1, "AccessKey:")
        self.accessKey = wx.TextCtrl(self, -1, accessKey)

        secretKeyLabel = wx.StaticText(self, -1, "SecretKey:")
        self.secretKey = wx.TextCtrl(self, -1, secretKey, style=wx.PASSWORD)

        self.rememberMe = wx.CheckBox(self, -1, u"记住账号")
        if accessKey != "" and secretKey != "":
            self.rememberMe.SetValue(True)

        self.loginBtn = wx.Button(self, -1, u"登陆")
        self.loginBtn.Bind(wx.EVT_BUTTON, self.OnLogin)

        self.exitBtn = wx.Button(self, -1, u"退出")
        self.exitBtn.Bind(wx.EVT_BUTTON, self.OnExit)

        # title
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add((0, 10))
        mainSizer.Add(loginTitle, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        # ak and sk
        keySizer = wx.FlexGridSizer(cols=2, hgap=7, vgap=7)
        keySizer.AddGrowableCol(1)
        keySizer.Add(accessKeyLabel, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        keySizer.Add(self.accessKey, 0, wx.EXPAND)
        keySizer.Add(secretKeyLabel, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        keySizer.Add(self.secretKey, 0, wx.EXPAND)
        mainSizer.Add(keySizer, 0, wx.EXPAND | wx.ALL, 5)

        mainSizer.Add(self.rememberMe, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        mainSizer.Add((10, 10))  # some empty space

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((30, 20))
        btnSizer.Add(self.loginBtn,1)
        btnSizer.Add((30, 20))
        btnSizer.Add(self.exitBtn,1)
        btnSizer.Add((30, 20))

        mainSizer.Add(btnSizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        self.SetSizer(mainSizer)

    def onAuth(self):
        ak = str(self.accessKey.GetLabelText())
        sk = str(self.secretKey.GetLabelText())
        buckets, info = qiniu.BucketManager(qiniu.Auth(ak, sk)).buckets()
        if info.ok():
            if self.rememberMe.IsChecked():
                self.conf.setKeys((ak, sk))

            self.onLoginSuccess(buckets)
        else:
            self.onAuthError(info.error)

    def onAuthError(self, errMsg):
        self.loginBtn.Enable()
        wx.MessageBox(errMsg, u"错误")

    def OnLogin(self, event):
        self.loginBtn.Disable()
        wxAsynchronousThread(self.onAuth, self.onAuthError).start()

    def OnExit(self, evt):
        self.frame.Hide()
        self.frame.Destroy()


class BucketConfigPanel(wx.Panel):
    def __init__(self, parent, buckets, onConfigSuccess):
        wx.Panel.__init__(self, parent, style=wx.BORDER_SIMPLE)
        self.frame = parent
        self.onConfigSuccess = onConfigSuccess
        self.buckets = buckets
        self.conf = Config()

        self.startConfigBucket()

    def startConfigBucket(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self, -1, u"配置空间下载域名")
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))

        mainSizer.Add((0, 10))
        mainSizer.Add(title, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)
        mainSizer.Add((0, 10))
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        configBuckets = self.conf.getBuckets()

        self.bucketsSizer = wx.FlexGridSizer(cols=3, hgap=3, vgap=3)
        for idx, bucket in enumerate(self.buckets):
            domain = configBuckets.get(bucket) or ""
            bucketName = wx.StaticText(self, -1, bucket)
            self.bucketsSizer.Add(bucketName, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)

            bucketDomain = wx.TextCtrl(self, -1, domain, size=(160,25))
            bucketDomain.SetHint(u"未配置部分功能不可使用")
            self.bucketsSizer.Add(bucketDomain, 2, wx.EXPAND)

            bmp = libs.icons.get("/status/question.png").GetBitmap()
            button = wx.BitmapButton(self, -1, bmp)
            self.bucketsSizer.Add(button, 0, wx.EXPAND)

        self.bucketsSizer.AddGrowableCol(1)
        mainSizer.Add(self.bucketsSizer, 0, wx.EXPAND | wx.ALL, 5)

        okBtn = wx.Button(self, -1, u"确定")
        okBtn.Bind(wx.EVT_BUTTON, self.endConfigBucket)

        exitBtn = wx.Button(self, -1, u"退出")
        exitBtn.Bind(wx.EVT_BUTTON, self.OnExit)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((50, 20))
        btnSizer.Add(okBtn,1)
        btnSizer.Add((50, 20))
        btnSizer.Add(exitBtn,1)
        btnSizer.Add((50, 20))
        mainSizer.Add(btnSizer, 0, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(mainSizer)

    def endConfigBucket(self, event):
        items = self.bucketsSizer.GetChildren()
        buffers = {}
        for idx in range(0, len(items) / 3):
            if idx * 3 + 1 < len(items):
                input = items[idx * 3 + 1]
                bucketName = items[idx*3].GetWindow().GetLabelText()
                oldDomain = input.GetWindow().GetLabelText()
                domain = input.GetWindow().GetValue()
                if oldDomain != domain:
                    print(u"检查【%s】下载地址: http://%s"%(bucketName,domain))

                buffers[bucketName] = domain

        self.conf.setBuckets(buffers)
        self.onConfigSuccess()

    def OnExit(self, evt):
        self.frame.Hide()
        self.frame.Destroy()


class LoginFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, u"七牛文件管理("+VERSION+u")",
                          style=((wx.DEFAULT_FRAME_STYLE ^ wx.MINIMIZE_BOX) ^ wx.RESIZE_BORDER) ^ wx.MAXIMIZE_BOX)

        self.SetIcon(libs.icons.desktop().GetIcon())

        self.loginPanel = LoginPanel(self, self.onLoginSuccess)

        self.boxSizer = wx.BoxSizer(wx.VERTICAL)
        self.boxSizer.Add(self.loginPanel, 1, wx.EXPAND)
        self.SetSizer(self.boxSizer)

        self.Fit()
        self.Center()

    def onLoginSuccess(self, buckets):
        self.configBucketPanel = BucketConfigPanel(self, buckets, self.onConfigSuccess)
        self.boxSizer.Hide(self.loginPanel)
        self.boxSizer.Remove(self.loginPanel)
        self.RemoveChild(self.loginPanel)
        self.boxSizer.Add(self.configBucketPanel, 1, wx.EXPAND)
        self.Fit()
        self.Layout()
        self.Center()

    def onConfigSuccess(self):
        MainFrame().Show()
        self.OnExit(self)

    def OnExit(self, evt):
        self.Hide()
        self.Destroy()