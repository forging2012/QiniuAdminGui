# -*- coding: utf-8 -*-

__author__ = 'zhouhaichao@2008.sina.com'

import sys
import os
import json

WORK_PATH = os.getcwd()

# 配置文件夹
ETC = WORK_PATH + "/etc"
if not os.path.exists(ETC):
    os.mkdir(ETC)

def getSystemType():
    u"""取得系统类型
        win
        linux
        mac
    """
    os_name = os.name
    if os_name == "posix":
        if sys.platform != "darwin":
            return "linux"
        else:
            return "mac"
    elif os_name == "nt":
        return "win"
    return "unknow"


class Config:
    __path = WORK_PATH + "/etc/config.json"
    __conf = {}

    def __init__(self):
        self.read()

    def getKeys(self):
        if self.__conf.get("key"):
            return (str(self.__conf.get("key").get("accessKey")), str(self.__conf.get("key").get("secretKey")))
        else:
            return ("", "")

    def setKeys(self, keys):
        """设置keys
            :param keys (ak,sk)
        """
        self.__conf["key"] = {
            "accessKey": keys[0],
            "secretKey": keys[1]
        }
        self.write()

    def getBuckets(self):
        return self.__conf.get("buckets") or {}

    def setBuckets(self,buckets):
        if buckets:
            self.__conf["buckets"] = buckets
            self.write()

    def addBuckets(self,bucketName,domain):
        buckets = self.getBuckets()
        buckets[bucketName] = domain
        self.setBuckets(buckets)

    def read(self):
        """读取json配置文件"""
        if not os.path.exists(WORK_PATH + "/etc"):
            os.mkdir(WORK_PATH + "/etc")

        if not os.path.exists(self.__path) or not os.path.isfile(self.__path):
            config = {}
            return

        config_file = None
        try:
            config_file = open(self.__path, 'r')
            json_str = config_file.read()
            self.__conf = json.loads(json_str)
            return
        except Exception, e:
            print("%s" % e)
        finally:
            if config_file != None:
                config_file.close()

    def write(self):
        config_file = None
        try:
            if os.path.exists(self.__path + ".bk"):
                os.remove(self.__path + ".bk")

            if os.path.exists(self.__path):
                os.rename(self.__path, self.__path + ".bk")

            config_file = open(self.__path, 'w')
            str_json = json.dumps(self.__conf, indent=2)
            config_file.write(str_json)
        except Exception, e:
            if os.path.exists(self.__path):
                os.remove(self.__path)

            if os.path.exists(self.__path + ".bk"):
                os.rename(self.__path + ".bk", self.__path)
        finally:
            if config_file != None:
                config_file.close()


def writeFile(file, data, status=0):
    """
        @param file
        @param data
        @param status
            0：一般模式，如果文件已经存在，跑出异常
            1：覆盖模式
            2：追加模式
    """
    output = None
    try:
        folder = os.path.dirname(file)
        mkdirs(folder)

        # 是文件跑出异常
        if os.path.isfile(folder) and status == 0:
            raise EOFError('%s is file!' % folder)
        mode = 'a' if status == 2 else 'wb'
        output = open(file, mode)
        output.write(data)
        return True
    except Exception, e:
        print(e)
        return False
    finally:
        if output != None:
            output.close()

def mkdirs(folder):
    if os.path.exists(folder):
        return True
    else:
        superFolder = os.path.dirname(folder)
        if superFolder == folder :
            return True
        if mkdirs(superFolder) :
            return os.mkdir(folder) == None
        else:
            return False

def fileSizeShow(fileSize):
    if fileSize < 1024:
        fileSize = str(fileSize) + u" 字节"
    elif fileSize / 1024.0 < 1024:
        fileSize = str(round(fileSize / 1024.0, 2)) + " KB"
    else:
        fileSize = str(round((fileSize / 1024.0) / 1024.0, 2)) + " MB"

    return fileSize