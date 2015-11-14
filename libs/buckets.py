# -*- coding: utf-8 -*-

__author__ = 'zhouhaichao@2008.sina.com'

import sys
import time

import wx
import qiniu
import wx.lib.mixins.listctrl
from qiniu import build_batch_delete
from wx.lib import dialogs
import wx.lib.mixins.listctrl as listmix

from libs import icons, ID
from libs.threads import AsynchronousThread
import libs.mimetype
from libs.config import Config
import libs.config

LIMIT = 100

class Store:
    def __init__(self):
        self.__store = []
        self.__storeIdx = -1

    def add(self, data):
        self.__store.append(data)
        self.__storeIdx = len(self.__store) - 1

    def next(self):
        if self.hasNext():
            self.__storeIdx += 1
            return self.__store[self.__storeIdx]
        return None

    def prev(self):
        if self.hasPrev():
            self.__storeIdx -= 1
            return self.__store[self.__storeIdx]
        return None

    def hasNext(self):
        return len(self.__store) > 1 and self.__storeIdx < len(self.__store) - 1

    def hasPrev(self):
        return self.__storeIdx > 0

    def current(self):
        if self.__storeIdx > -1:
            return self.__store[self.__storeIdx]
        return None

    def index(self):
        return self.__storeIdx

    def page(self):
        return self.__storeIdx + 1

    def length(self):
        return len(self.__store)


class BucketPanel(wx.Panel, wx.lib.mixins.listctrl.ColumnSorterMixin):
    def __init__(self, parent, auth):
        wx.Panel.__init__(self, parent)
        self.__frame = self.GetParent().GetParent()

        self.__auth = auth
        self.__bucketManger = qiniu.BucketManager(self.__auth)
        self.__conf = Config()

        self.__bucketName = ""
        self.__download_url = None
        self.__prefix = ""
        self.__marker = None
        self.__limit = LIMIT

        self.__initImages()

        self.__boxSizer = wx.BoxSizer()
        self.__dataList = self.__initList()
        self.__boxSizer.Add(self.__dataList, 1, wx.EXPAND)

        self.__initPopMenu()

        self.SetSizer(self.__boxSizer)

        # init column sorter
        wx.lib.mixins.listctrl.ColumnSorterMixin.__init__(self, LIMIT)

    def GetListCtrl(self):
        return self.__dataList

    def GetSortImages(self):
        return (self.down, self.up)

    def OnSortOrderChanged(self):
        self.__downloadButtonAndDeleteButtonStatus()

    def setBucketName(self, bucketName):

        ## 之所以放在这是因为，在初始化此面板的时候还未初始化toolbar
        self.__toolbar = self.__frame._toolbar

        self.__bucketName = bucketName  # 当前空间名称
        self.__download_url = self.__conf.getBuckets()[self.__bucketName]
        self.__resetStartLoad()

    def setPrefix(self, prefix):
        self.__prefix = prefix
        self.__enableToolbar(ID.ID_TOOLBAR_SEARCH_BTN,False)
        self.__enableToolbar(ID.ID_TOOLBAR_SEARCH_TEXT,False)
        self.__resetStartLoad()

    def setLimit(self, limit):
        self.__limit = limit
        self.__enableToolbar(ID.ID_TOOLBAR_LIMIT,False)
        self.__resetStartLoad()

    def getBucketName(self):
        return self.__bucketName

    def __resetStartLoad(self):
        """从头开始重新加载"""
        self.__marker = None    # 下一页marker，加载下一页的时候需要
        self.__store = Store()  # 保存数据
        self.__dataList.DeleteAllItems()
        AsynchronousThread(self.__loadData).start()

    def __initImages(self):
        # load some images into an image list
        self.__images_16x = wx.ImageList(16, 16, False)

        self.__icons = []
        for types, image in libs.mimetype.typeImage:
            self.__images_16x.Add(icons.mimeType('16x',image).GetBitmap())
            self.__icons.append(image)

        self.up = self.__images_16x.AddWithColourMask(icons.get("/sorter/up.png").GetBitmap(),"blue")
        self.down = self.__images_16x.AddWithColourMask(icons.get("/sorter/down.png").GetBitmap(),"blue")

    def __initList(self):
        list = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_SORT_ASCENDING | wx.BORDER_SUNKEN)
        # assign the image list to it
        list.AssignImageList(self.__images_16x, wx.IMAGE_LIST_SMALL)

        # Add some columns
        for col, text in enumerate([u"路径", u"类型", u"大小", u"上传时间"]):
            list.InsertColumn(col, text, wx.CENTER)

        # set the width of the columns in various ways
        list.SetColumnWidth(0, 320)
        list.SetColumnWidth(1, 120)
        list.SetColumnWidth(2, 80)
        list.SetColumnWidth(3, 140)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__onTreeSelected, list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.__onTreeSelected, list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.__onTreeSelected, list)

        # rename event
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.__onEditNameStart, list)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.__onEditNameEnd, list)
        # key up event (rename & delete)
        list.Bind(wx.EVT_KEY_UP, self.__onListKeyUp)

        #drop to download, bug bug
        #self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDragEvent, list)

        return list

    def _startDragEvent(self, e):
        # create temp folder
        # folder = libs.config.WORK_PATH + "/temp"
        # libs.config.mkdirs(folder)

        text = self.__dataList.GetItem(e.GetIndex()).GetText()
        text = text if text[0] == "/" else "/" + text
        # temp_file = os.path.join(folder, os.path.basename(text if text[0] == "/" else "/" + text))

        # Create drag data
        data = wx.FileDataObject()
        data.AddFile(text)

        # Create drop source and begin drag-and-drop.
        dropSource = wx.DropSource(self.__dataList)
        dropSource.SetData(data)

        # Get Source
        res = dropSource.DoDragDrop(flags=wx.Drag_AllowMove)
        if res == wx.DragMove or res == wx.DragCopy:
            ## 下载
            print("DragMove & DragCopy")

        return text


    def __onTreeSelected(self, event):
        self.__downloadButtonAndDeleteButtonStatus()

    def __pageButtonStatus(self):
        self.__enableToolbar(ID.ID_TOOLBAR_SEARCH_BTN,True)
        self.__enableToolbar(ID.ID_TOOLBAR_SEARCH_TEXT,True)
        self.__enableToolbar(ID.ID_TOOLBAR_LIMIT,True)

        self.__enableToolbar(ID.ID_TOOLBAR_NEXT_PAGE, self.__store.hasNext() or self.__marker != None)
        self.__enableToolbar(ID.ID_TOOLBAR_PREV_PAGE, self.__store.hasPrev())
        self.__updateStatus()
        self.__downloadButtonAndDeleteButtonStatus()

    def __downloadButtonAndDeleteButtonStatus(self):
        selected = self.__dataList.GetSelectedItemCount() > 0
        self.__enableToolbar(ID.ID_TOOLBAR_DOWNLOAD,
                             selected and self.__download_url != None and self.__download_url != "")
        self.__enableToolbar(ID.ID_TOOLBAR_TRASH, selected)

    def __loadNextData(self):
        if self.__store.hasNext():
            self.__showData(self.__store.next())
            self.__pageButtonStatus()
        elif self.__marker != None:
            AsynchronousThread(self.__loadData).start()

    def __loadPrevData(self):
        if self.__store.hasPrev():
            self.__showData(self.__store.prev())
        self.__pageButtonStatus()

    def __loadData(self):
        ret, eof, info = self.__bucketManger.list(bucket=self.__bucketName, marker=self.__marker,limit=self.__limit, prefix=self.__prefix)
        if info.ok():
            items = ret.get("items")
            self.__store.add(items)
            wx.CallAfter(self.__showData,items)
            if not eof:
                self.__marker = ret.get("marker")
            else:
                self.__marker = None
        else:
            if self.__marker != None:
                self.__enableToolbar(ID.ID_TOOLBAR_NEXT_PAGE, True)
            wx.MessageBox(info.error)

        self.__pageButtonStatus()

    def __showData(self, items):
        self.itemDataMap = {}
        for row, item in enumerate(items):
            name = item.get(u"key")
            fsize = libs.config.fileSizeShow(item.get(u"fsize"))
            putTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(round(item.get("putTime") / 10000 / 1000)))
            mimeType = item.get(u"mimeType")
            image = libs.mimetype.showType(mimeType, name)

            index = self.__dataList.InsertStringItem(sys.maxint, name)
            self.__dataList.SetStringItem(index, 1, mimeType)
            self.__dataList.SetStringItem(index, 2, fsize)
            self.__dataList.SetStringItem(index, 3, putTime)
            self.__dataList.SetItemData(index, row)

            # sort data
            self.itemDataMap[index] = (name, mimeType, item.get("fsize"), item.get("putTime"))

            # 设置图标
            self.__dataList.SetItemImage(index, self.__icons.index(image))

    def __initPopMenu(self):
        self.popupMenu = wx.Menu()

        urlMenu = self.popupMenu.Append(-1, u"复制地址", u"复制地址")
        self.Bind(wx.EVT_MENU, self.onCopyUrlEvent, urlMenu)

        self.popupMenu.AppendSeparator()

        deleteMenu = self.popupMenu.Append(-1, u"删除",u"删除选中文件")
        self.Bind(wx.EVT_MENU, self.onDeleteEvent, deleteMenu)

        refreshMenu = self.popupMenu.Append(-1, u"更新", u"强制更新缓存，保证上传的文件可以显示最新")
        self.Bind(wx.EVT_MENU, self.onRefreshCacheEvent, refreshMenu)

        renameMenu = self.popupMenu.Append(-1, u"重命名", u"重命名")
        self.Bind(wx.EVT_MENU, self.onRenameEvent, renameMenu)

        downloadMenu = self.popupMenu.Append(-1, u"下载", u"下载选中文件")
        self.Bind(wx.EVT_MENU, self.__frame.onDownloadFileEvent, downloadMenu)

        self.Bind(wx.EVT_CONTEXT_MENU, self.__onShowPopup)

    def __onShowPopup(self, event):
        if len(self.getSelectedFiles()) != 0 :
            pos = event.GetPosition()
            pos = self.ScreenToClient(pos)
            self.PopupMenu(self.popupMenu, pos)
        else:
            ##没有选中文件，不可操作
            pass

    def __onPopupItemSelected(self, event):
        item = self.popupMenu.FindItemById(event.GetId())
        text = item.GetText()
        wx.MessageBox("You selected item '%s'" % text)

    def __onListKeyUp(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_DELETE:
            self.onDeleteEvent(event)

        elif keyCode == wx.WXK_F2:
            if len(self.getSelectedFiles()) == 1:
                self.onRenameEvent(event)

        elif event.ControlDown() and keyCode == 67:
            self.onCopyUrlEvent(event)

        elif event.ControlDown() and keyCode == 65:
            for index in range(self.__dataList.GetItemCount()):
                self.__dataList.Select(index, True)

        event.Skip()

    def __onEditNameStart(self, event):
        print("重命名开始")

    def __onEditNameEnd(self, event):
        print("重命名结束")

    def getSelectedFiles(self):
        files = []
        index = self.__dataList.GetFirstSelected()
        while index != -1:
            item = self.__dataList.GetItem(index)
            key = item.GetText()
            mimeType = self.itemDataMap[index][1]
            fileSize = self.itemDataMap[index][2]
            base_url = 'http://%s/%s' % (self.__download_url, key)
            private_url = self.__auth.private_download_url(base_url, expires=3600)
            files.append((private_url,key,mimeType,fileSize))
            index = self.__dataList.GetNextSelected(index)

        return files

    def onRefreshEvent(self,event):
        self.__resetStartLoad()

    def onNextPageEvent(self, event):
        self.__dataList.DeleteAllItems()
        self.__enableToolbar(ID.ID_TOOLBAR_NEXT_PAGE)
        self.__loadNextData()

    def onPrevPageEvent(self, event):
        self.__dataList.DeleteAllItems()
        self.__enableToolbar(ID.ID_TOOLBAR_PREV_PAGE)
        self.__loadPrevData()

    def onCopyUrlEvent(self, event):
        files = self.getSelectedFiles()
        value = ""
        for url, key, mimeType, fileSize in files:
            value += url + "\n"

        data = wx.TextDataObject()
        data.SetText(value)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox(u"不能打开剪切板！", u"复制错误")

    def onDeleteEvent(self, event):
        """删除文件"""
        self.__enableToolbar(ID.ID_TOOLBAR_TRASH,False)
        message = u"您确定删除以下文件？\n"
        files = []
        index = self.__dataList.GetFirstSelected()
        while index != -1:
            item = self.__dataList.GetItem(index)
            key = item.GetText()
            message += key + "\n"
            files.append(key)
            index = self.__dataList.GetNextSelected(index)

        results = dialogs.messageDialog(self,message,"Sure?")
        if results.accepted :
            AsynchronousThread((self.deleteSelectedFile,files)).start()
        else:
            self.__downloadButtonAndDeleteButtonStatus()

    def deleteSelectedFile(self,files):
        ops = build_batch_delete(self.__bucketName, files)
        ret, info = self.__bucketManger.batch(ops)
        if info.ok() :
            wx.CallAfter(wx.MessageBox,u"删除成功",u"提示")
            wx.CallAfter(self.setBucketName, self.__bucketName)
        else:
            wx.CallAfter(wx.MessageBox,info.error)

    def onRefreshCacheEvent(self, event):
        """刷新缓存"""
        files = self.getSelectedFiles()
        for url,key,mimeType,fileSize in files :
            self.__bucketManger.prefetch(self.__bucketName, key)

        wx.MessageBox(u"更新成功",u"Note")

    def onRenameEvent(self, event):
        """重命名"""
        selected = len(self.getSelectedFiles())
        if selected == 1:
            # self.__onEditNameStart(event)
            index = self.__dataList.GetFirstSelected()
            key = self.itemDataMap[index][0]
            results = dialogs.textEntryDialog(self, u"请输入修改的名字", u"重命名", key)
            if results.accepted :
                newKey = results.text
                try:
                    ret, info = self.__bucketManger.rename(self.__bucketName, key, newKey)
                    if info.ok():
                        wx.MessageBox(u"重命名成功！", u"成功")
                    else:
                        wx.MessageBox(info.error, u"错误")
                except:
                    wx.MessageBox(u"名字错误，查阅七牛文档！", u"错误")
        else:
            wx.MessageBox(u"不能同时重命名多个文件！", u"错误")


    def onSearchEvent(self, event):
        if isinstance(event,wx.KeyEvent):
            keycode = event.GetKeyCode()
            if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER :
                pass
            else:
                event.Skip()
                return True

        textCtrl = self.__frame._toolbar.FindById(ID.ID_TOOLBAR_SEARCH_TEXT).GetControl()
        self.setPrefix(textCtrl.GetValue())

    def onPageLimitEvent(self, event):
        limit = int(event.EventObject.GetStringSelection(), 10)
        self.setLimit(limit)
        event.Skip()

    def sortBy(self, type):
        dict = {u"名称": 0, u"大小": 2, u"时间": 3}
        idx = dict[type]
        def compare_func(row1, row2):
            val1 = self.itemDataMap[row1][idx]
            val2 = self.itemDataMap[row2][idx]
            if val1 < val2:
                return -1
            elif val1 > val2:
                return 1
            else:
                return 0

        self.__dataList.SortItems(compare_func)

    def __enableToolbar(self, id, enable=False):
        """禁用或者启用某个菜单"""
        self.__toolbar.EnableTool(id, enable)

    def __updateStatus(self):
        moreMark = "+"
        if self.__marker == None:
            moreMark = ""
        statusText = (u"空间：%s" % (self.__bucketName))
        self.__frame.SetStatusText(statusText, 2)
        statusText = (u"页码：%d/%d%s" % (self.__store.page(), self.__store.length(),moreMark))
        self.__frame.SetStatusText(statusText, 3)
