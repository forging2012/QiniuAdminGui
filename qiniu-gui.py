# -*- coding: utf-8 -*-
__author__ = 'zhouhaichao@2008.sina.com'

import wx

from libs.login import LoginFrame
from libs import config

if __name__ == '__main__':
    app = wx.App()

    ##这尼玛算不算BUG呢，只能放在这里使用
    # 单例模式只运行一个检测
    instance_name = "%s-%s" % (app.GetAppName(), wx.GetUserId())
    instance_checker = wx.SingleInstanceChecker(instance_name, config.WORK_PATH)
    if instance_checker.IsAnotherRunning():
        dlg = wx.MessageDialog(
            None,
            u"已经在运行了或上次没有正常退出，要重新打开吗？",
            u"七牛管理台!",
            wx.YES_NO | wx.ICON_QUESTION
        )
        ret_code = dlg.ShowModal()
        if ret_code != wx.ID_YES:
            dlg.Destroy()
            app.Destroy()
            exit(1)
        dlg.Destroy()

    LoginFrame().Show()

    app.MainLoop()
