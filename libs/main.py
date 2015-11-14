# -*- coding: utf-8 -*-
import qiniu

__author__ = 'zhouhaichao@2008.sina.com'

import wx, os
import libs.icons
from wx.lib import dialogs
from libs import ID
from libs import framework
from libs.dialogs import AboutAuthDialog, AboutSoftDialog
from libs.buckets import BucketPanel
from libs.schedule import UploadifyPanel, DownloadPanel
from libs.config import Config
from libs.versions import VERSION
import webbrowser

class FileDropUpLoadTarget(wx.FileDropTarget):
    def __init__(self, handler):
        wx.FileDropTarget.__init__(self)
        self.handler = handler

    def OnDropFiles(self, x, y, filenames):
        for file in filenames:
            if os.path.exists(file) :
                self.handler(file)

class MainFrame(framework.XFrame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, u'七牛文件管理('+VERSION+')', size=(800, 640))

        self.conf = Config()
        ak, sk = self.conf.getKeys()
        self.__auth = qiniu.Auth(ak, sk)

        self.SetIcon(libs.icons.desktop().GetIcon())
        #self.SetWindowStyle((self.GetWindowStyle() | wx.STAY_ON_TOP))

        self.createSplitter()
        self.createMenuBar(self.menuData())
        self.createToolBar(self.toolbarData())
        self.createStatusBar([-1, 100, 140, 70])
        self.createTaskBarIcon(self.taskMenuData())
        self.Bind(wx.EVT_CLOSE, self.onHideEvent)
        self.Center()

        for bucket in self.conf.getBuckets():
            self._bucketPanel.setBucketName(bucket)
            return

    def bucketMenuData(self):
        bucketsMenu = []
        for bucket in self.conf.getBuckets():
            bucketsMenu.append((bucket, bucket, self.onBucketChangedEvent, wx.ITEM_RADIO))

        bucketsMenu.append("---")
        bucketsMenu.append((u"新建空间", u"新建空间",self.onCreateBucketEvent))
        return (u"空间", bucketsMenu)

    def menuData(self):
        return [
            (u"文件", [
                (u"上传", u"上传文件到当前空间", self.onUploadFileEvent),
                "---",
                (u"最小化", u"最小化到系统托盘", self.onHideEvent),
                (u"退出", u"退出系统", self.onExitEvent)
            ]),
            (u"视图", [
                (u"查看方式", [
                    ([u"详细信息", u"列表", u"大图标", u"小图标"], "", self.onViewChangedEvent, wx.ITEM_RADIO)
                ]),
                "---",
                (u"排序方式", [
                    ([u"名称",u"大小",u"时间"], "", self.onSortChangedEvent, wx.ITEM_RADIO)
                ])
                ,"---"
                , (u"系统设置", u"系统运行视图参数设置", self.onConfigEvent)
            ]),
            self.bucketMenuData(),
            (u"关于", [
                (u"检查更新", u"连接服务器检测是否更新", self.onUploadEvent),
                (u"关于软件", u"关于软件简介", self.onAboutSoftEvent),
                (u"关于作者", u"作者简介", self.onAboutUserEvent)
            ])
        ]

    def toolbarData(self):
        return [
            (u"上传", u"上传文件到当前空间", "upload.png", self.onUploadFileEvent),
            ((ID.ID_TOOLBAR_DOWNLOAD, u"下载"), u"下载选中文件", ["download.png","download.dis.png"], self.onDownloadFileEvent, False),
            "---",
            ((ID.ID_TOOLBAR_TRASH, u"删除"), u"删除选中文件", ["trash.png","trash.dis.png"], self._bucketPanel.onDeleteEvent, False),
            "---",
            ((ID.ID_TOOLBAR_PREV_PAGE, U"上一页"), u"加载上一页文件", ["prev.png", "prev.dis.png"], self._bucketPanel.onPrevPageEvent, False),
            ((ID.ID_TOOLBAR_NEXT_PAGE, U"下一页"), u"加载下一页文件", ["next.png", "next.dis.png"], self._bucketPanel.onNextPageEvent, False),
            "---",
            (u"刷新", u"刷新当前页" , "refresh.png",self._bucketPanel.onRefreshEvent),
            "---",
            ((ID.ID_TOOLBAR_LIMIT,u"显示个数："),["10","20","50","100","200","500"],self._bucketPanel.onPageLimitEvent),
            "---",
            ((ID.ID_TOOLBAR_SEARCH_TEXT, u"搜索关键字"), (u"", u"文件前缀"), {wx.EVT_KEY_DOWN:self._bucketPanel.onSearchEvent}),
            (u"搜索", u"在当前空间搜索", "search.png", self._bucketPanel.onSearchEvent),
        ]

    def taskMenuData(self):
        return [
            (u"显示", u"", self.onShowEvent),
            "-",
            (u"关于软件", u"关于软件简介", self.onAboutSoftEvent),
            "-",
            (u"退出", u"", self.onExitEvent)
        ]

    def createSplitter(self):
        self._splitter = wx.SplitterWindow(self)
        self._items = self.createBucketsPanel(self._splitter)

        self._uploadify = wx.Panel(self._splitter, style=wx.BORDER_SIMPLE)
        self._uploadify.SetSizer(wx.BoxSizer(wx.VERTICAL))

        self._splitter.Initialize(self._items)
        return self._splitter

    def createBucketsPanel(self, parent):
        self._bucketPanel = BucketPanel(parent, self.__auth)
        self.SetDropTarget(FileDropUpLoadTarget(self.uploadFile))
        return self._bucketPanel

    def onScheduleFinally(self, panel=None, status=True):
        """上传动作结束（正确上传，上传错误，。。。）均会调用"""
        if status and panel:
            self._uploadify.GetSizer().Hide(panel)
            self._uploadify.GetSizer().Remove(panel)
            self._uploadify.RemoveChild(panel)

        children = len(self._uploadify.GetChildren())
        if children == 0 :
            self.__switchSplitWindow(False)

        self._uploadify.Layout()

    def onUploadFileEvent(self, event):
        wildcard = u"所有文件 (*.*) | *.*"
        result = dialogs.fileDialog(parent=self._uploadify, title=u'选择文件', filename='', wildcard=wildcard, style=wx.OPEN)
        if result.accepted:
            for file_path in result.paths:
                if os.path.isdir(file_path) :
                    continue
                self.uploadFile(file_path)
        event.Skip()

    def onDownloadFileEvent(self, event):
        self.__switchSplitWindow(True)

        folder = ""
        results = dialogs.dirDialog(self, u"选择下载位置")
        if results.accepted:
            folder = results.path
            files = self._bucketPanel.getSelectedFiles()
            for file in files :
                dnPanel = DownloadPanel(folder, file, self.onScheduleFinally, self._uploadify)
                boxSizer = self._uploadify.GetSizer()
                boxSizer.Add(dnPanel, flag=wx.EXPAND)
            self._uploadify.Layout()
            event.Skip()
        else:
            self.onScheduleFinally(None,False)

    def uploadFile(self,file_path):
        self.__switchSplitWindow(True)

        bucketName = self._bucketPanel.getBucketName()
        up = UploadifyPanel(self.__auth, bucketName, file_path, self.onScheduleFinally, self._uploadify)
        boxSizer = self._uploadify.GetSizer()
        boxSizer.Add(up, flag=wx.EXPAND)

        #self._uploadify.GetSizer().Fit(self._uploadify)
        #self._uploadify.GetSizer().SetSizeHints(self._uploadify)
        self._uploadify.Layout()

    def __switchSplitWindow(self,open=True):
        """选择上传下载队列窗口状态"""
        if open:
            if not self._splitter.IsSplit() :
                rect = self.GetScreenRect()
                self._splitter.SplitVertically(self._items, self._uploadify, rect.width - 370)
        else:
            if self._splitter.IsSplit():
                self._splitter.Unsplit()
            #self._bucketPanel.setBucketName(self._bucketPanel.getBucketName())

    def onBucketChangedEvent(self, event):
        item = event.EventObject.FindItemById(event.GetId())
        bucketName = item.GetText()
        self._bucketPanel.setBucketName(bucketName)

    def onViewChangedEvent(self, event):
        item = event.EventObject.FindItemById(event.GetId())
        text = item.GetText()
        wx.MessageBox(u"首先感谢您的支持！视图查看功能此版本不包含。该项功能正在加紧开发。",u"抱歉")

    def onSortChangedEvent(self, event):
        item = event.EventObject.FindItemById(event.GetId())
        text = item.GetText()
        self._bucketPanel.sortBy(text)

    def onCreateBucketEvent(self, event):
        wx.MessageBox(VERSION+u"版暂不支持此功能！",u"抱歉")

    def onConfigEvent(self, event):
        from libs.login import BucketConfigPanel

        class ConfigDialog(wx.Dialog):
            def __init__(self, parent):
                wx.Dialog.__init__(self, parent)
                conf = Config()
                boxSizer = wx.BoxSizer(wx.HORIZONTAL)
                b = BucketConfigPanel(self, conf.getBuckets().keys(), self.onOkBtn)
                boxSizer.Add(b, 1, wx.EXPAND)
                self.Layout()
                self.Center()

            def onOkBtn(self):
                self.Hide()
                self.Destroy()

        ConfigDialog(self).ShowModal()

    def onUploadEvent(self, event):
        webbrowser.open_new("http://github.com/ihaiker/QiniuAdminGui")

    def onAboutUserEvent(self, event):
        self.onUploadEvent(event)

    def onAboutSoftEvent(self, event):
        self.onUploadEvent(event)