# -*- coding: utf-8 -*-

__author__ = 'zhouhaichao@2008.sina.com'

import os
import string

import wx
import wx.animate
import qiniu
import urllib
from qiniu import put_file
from wx.lib import dialogs


from libs.dialogs import QiniuNameDialog
from libs.threads import AsynchronousThread
import libs.icons
import libs.mimetype
import libs.ID
import libs.config

PROGRESS_SIZE = 10000

class UploadifyPanel(wx.Panel):
    """上传图片按钮"""

    def __init__(self, auth, bucket, file, handler, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.__auth = auth
        self.__bucketName = bucket
        self.__callback = handler
        self._bucket = qiniu.BucketManager(self.__auth)
        self.__th = None

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        # type image
        self.file = file
        self.fileName = os.path.basename(file)
        image = libs.mimetype.showType("", self.fileName)
        typeImage = wx.StaticBitmap(parent=self, bitmap=libs.icons.mimeType("32x",image).GetBitmap(), size=(46, 46))
        mainSizer.Add(typeImage)

        gridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)
        self.nameLabel = wx.StaticText(self, -1, "")
        sizeLabel = wx.StaticText(self, -1, libs.config.fileSizeShow(os.path.getsize(self.file)))

        gridBagSizer.Add(self.nameLabel, pos=(0, 0), span=(1, 1), flag=wx.EXPAND)
        gridBagSizer.Add(sizeLabel, pos=(0, 1), span=(1, 1), flag=wx.ALIGN_RIGHT)

        # progress
        self._progress = wx.Gauge(self, -1, os.path.getsize(file), style=wx.GA_PROGRESSBAR)
        gridBagSizer.Add(self._progress, pos=(1, 0), span=(1, 2), flag=wx.EXPAND)

        mainSizer.Add(gridBagSizer, 1, wx.EXPAND)

        cancelBtn = wx.Button(self, libs.ID.ID_BTN_CANCEL, u"取消", size=(46, 46))
        cancelBtn.Bind(wx.EVT_BUTTON, self.onCancelFileEvent)
        mainSizer.Add(cancelBtn)

        self.SetSizer(mainSizer)
        AsynchronousThread(self.checkFile).start()

    def onCancelFileEvent(self, event):
        self.__callback(self, True)
        if self.__th != None:
            try:
                self.__th.stop()
            except Exception, e:
                print(e)
        self.__th = None

    def onStartFileEvent(self, event=None):
        self.__th = AsynchronousThread(self.startUpload)
        self.__th.start()

    def startUpload(self):
        """开始上传"""
        self.nameLabel.SetLabelText(self.fileName)
        self.GetSizer().Layout()

        key = self.fileName
        token = self.__auth.upload_token(self.__bucketName, key)
        ret, info = put_file(token, key, self.file, progress_handler=self.progressHandler)

        if info.ok() :
            wx.CallAfter(self.__callback, self, True)
            self._bucket.prefetch(self.__bucketName, key)
        else:
            wx.CallAfter(self.__callback, self, False)

        self.__th = None

    def progressHandler(self, progress, total):
        wx.CallAfter(self._progress.SetValue, progress)

    def checkFile(self):
        status = 0
        try:
            ret, info = self._bucket.stat(self.__bucketName, self.fileName)
            if ret != None:
                d = QiniuNameDialog(self.fileName)
                result = d.ShowModal()
                text = d.GetNewName()
                d.Destroy()

                if result == wx.ID_OK: # rename
                    if string.lstrip(text) != "":
                        self.fileName = text
                    self.checkFile()

                elif result == wx.ID_YES: # refresh
                    self.onStartFileEvent()
                else:
                    self.__callback(self, True)
            else:
                self.onStartFileEvent()
        except Exception, e:
            print(e)
            result = dialogs.textEntryDialog(self, "(" + self.fileName + u") 文件名错误，请重新命名！\n有关命名规则查阅七牛文档。", u"文件名错误", '')
            if result.accepted == True:
                if string.lstrip(result.text) != "":
                    self.fileName = result.text
                self.checkFile()
            else:
                self.__callback(self, True)



class DownloadPanel(wx.Panel):
    """下载图片"""
    def __init__(self, folder, fileInfo, handler, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.__folder = folder + "/"
        self.__callback = handler
        self.__th = None

        self.url = fileInfo[0]
        self.key = fileInfo[1]
        self.mimeType = fileInfo[2]
        self.fileSize = fileInfo[3]

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        # type image
        fileName = os.path.basename(self.key)
        image = libs.mimetype.showType(self.mimeType, fileName)
        bmp = libs.icons.mimeType("32x",image).GetBitmap()
        typeImage = wx.StaticBitmap(parent=self, bitmap=bmp, size=(46, 46))
        mainSizer.Add(typeImage)

        gridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)

        self.nameLabel = wx.StaticText(self, -1, fileName)
        self.sizeLabel = wx.StaticText(self, -1, libs.config.fileSizeShow(fileInfo[3]))
        gridBagSizer.Add(self.nameLabel, pos=(0, 0), span=(1, 1), flag=wx.EXPAND)
        gridBagSizer.Add(self.sizeLabel, pos=(0, 1), span=(1, 1), flag=wx.ALIGN_RIGHT)

        # progress
        self._progress = wx.Gauge(self, -1, PROGRESS_SIZE, style=wx.GA_PROGRESSBAR)
        gridBagSizer.Add(self._progress, pos=(1, 0), span=(1, 2), flag=wx.EXPAND)

        mainSizer.Add(gridBagSizer, 1, wx.EXPAND)

        cancelBtn = wx.Button(self, libs.ID.ID_BTN_CANCEL, u"取消", size=(46, 46))
        cancelBtn.Bind(wx.EVT_BUTTON, self.onCancelFileEvent)
        mainSizer.Add(cancelBtn)

        self.SetSizer(mainSizer)
        self.onStartFileEvent()

    def onCancelFileEvent(self, event):
        self.__callback(self, True)
        if self.__th != None:
            try:
                self.__th.stop()
            except Exception, e:
                print(e)
        self.__th = None

    def onStartFileEvent(self):
        self.__th = AsynchronousThread(self.downloading)
        self.__th.start()

    def downloading(self):
        """开始下载"""
        local = self.__folder + self.key
        libs.config.mkdirs(os.path.dirname(local))
        try:
            urllib.urlretrieve(self.url, local, self.progressHandler)
            wx.CallAfter(self.__callback, self, True)
        except:
            wx.CallAfter(self.__callback, self, False)

        self.__th = None

    def progressHandler(self, idx, buffer, total):
        progress = PROGRESS_SIZE * idx * buffer / total
        if progress > PROGRESS_SIZE:
            progress = PROGRESS_SIZE
        wx.CallAfter(self._progress.SetValue, progress)


