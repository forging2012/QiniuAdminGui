# -*- coding: utf-8 -*-
# 资源文件嵌入代码
# http://www.easyicon.net/iconsearch/iconset:small-and-flat-icons/1/
__author__ = 'zhouhaichao@2008.sina.com'

import os
import glob

def encode_file(fn, buffer):
    print 'Encode >>', fn
    _, ext = os.path.splitext(fn)

    if ext in ['.png', '.ico', '.jpg']:
        file = open(fn, 'rb')
        pic = file.read()
        b64 = pic.encode('base64').strip().replace('\n', '"\n"')
        file.close()
        name = fn.replace(os.path.dirname(__file__), "").replace(os.sep,"/")
        buffer.write('\t"%s": PyEmbeddedImage(\n"%s"),\n\n\n' % (name, b64))

def encode_folder(dir, buffer):
    if os.path.isdir(dir):
        lst = glob.glob(os.path.join(dir, '*'))
        for fn in lst:
            if os.path.isdir(fn):
                encode_folder(fn, buffer)
            else:
                encode_file(fn, buffer)
    else:
        encode_file(dir, buffer)


def mkIcons(res_file):
    src_dir = os.path.dirname(__file__)
    print 'Search File/Folder >> ', src_dir, '\n\n'

    output = open(res_file, 'w')
    output.write('# -×- coding:utf-8 -*-\n')
    output.write('from wx.lib.embeddedimage import PyEmbeddedImage\n\n')

    output.write('RES = {\n')
    encode_folder(src_dir, output)
    output.write('"":None}\n\n')


    output.write('def get(path): return RES[path]\n\n')
    output.write('def toolbar(name): return get("/toolbar/" + name)\n\n')
    output.write('def mimeType(size,name): return get("/mimeType/"+size+"/"+name)\n\n')
    output.write('def desktop(): return get("/desktop.ico")\n\n')
    output.write('def exists(name): return RES.has_key(name)\n\n')
    output.flush()
    output.close()



if __name__ == '__main__':
    mkIcons('../libs/icons.py')
