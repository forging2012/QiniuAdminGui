
# 七牛云存储GUI管理客户端（AKSK版）
@version beta 0.1

### Requests

* qiniu
* wxpython
* requests

### 支持列表

#### 1、多空间(Bucket)管理
        
#### 2、上传

#### 3、批量下载（已配置下载域名）

关于域名配置请查阅七牛域名管理文档 [七牛下载安全机制][1]

#### 4、文件缓存更新

#### 5、重命名

#### 6、批量删除

#### 7、查阅方式增加（AKSK BEAT 0.2+）

+ 详细列表
+ 小图标显示
+ 大图标显示
+ 预览方式（此方式有会增加七牛API的使用次数）

### 打包

#### 把图片嵌入代码
    cd res
    python mkicons.py
    
#### 打成可运行包

    pyinstaller -F -w -i res/desktop.ico qiniu-gui.py
    
### 有关PyInstaller参数

查阅[PyInstaller][2]使用文档
    


[1]: http://developer.qiniu.com/docs/v6/api/overview/dn/security.html#anti-leech
[2]: http://pythonhosted.org/PyInstaller/

