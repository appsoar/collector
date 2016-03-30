# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

from common.util import Result, MsgResult
from frame.Logger import SysLog
from frame.web import mimesuffix
from twisted.internet import defer
from twisted.web import resource, server
import json
import os
import xmlrpclib
import traceback
import time
Fault = xmlrpclib.Fault


class ImageResource(resource.Resource):
    NOT_FOUND = 8001
    FAILURE = 8002
    def __init__(self,service,wwwroot,allow_none = True,useDateTime=False, encoding = "UTF-8"):
        resource.Resource.__init__(self)
        self.service = service
        self.isLeaf = True
        self.encoding = encoding
        self.wwwroot = wwwroot
        basepath = os.path.normcase(self.wwwroot)
        self.img_root = os.path.join(basepath,"Images")
        if not os.path.isdir(self.img_root):
            os.makedirs(self.img_root)
    def render_GET(self,request):
        basepath = self.img_root
        name = os.path.normcase(request.path)

        if "\\" == name[0] or "\/" == name[0] or "/" == name[0]:
            name = name[7:]
        else:
            name = name[6:]
            

        fullpath = os.path.join(basepath,name)
        try:
            if name =="":
                name = "index.html"
            response = open(fullpath,"rb").read()
            suffix = os.path.basename(name).split(".")[-1]
            if suffix in mimesuffix:
                request.setHeader("content-type", mimesuffix[suffix])
        except:
            PrintStack()
            response = '''<body><h1>Error!</h1>
        Get file [%s] fail
        </body>''' % name
        request.setHeader("content-length", str(len(response)))
        return response
    def render_POST(self,request):
        responseFailed = []
        request.notifyFinish().addErrback(responseFailed.append)            
            
        d = defer.maybeDeferred(self.save_image,request.content)
        d.addErrback(self._ebRender)
        d.addCallback(self._cbRender, request, responseFailed)
        return server.NOT_DONE_YET 
    
    def get_filepath(self,suffix):
        #time.strftime( ISOTIMEFORMAT, time.localtime() )

        folder = time.strftime("%Y_%U",time.localtime())
        filepath = os.path.join(self.img_root,folder)
        if not os.path.isdir(filepath):
            os.makedirs(filepath)

        f = time.strftime("%m%d_%H%M%S",time.localtime())
        filename = "%s.%s"%(f,suffix)

        return os.path.join(filepath,filename),"/image/%s/%s"%(folder,filename)
        

    def save_image(self,content):
        filepath,src = self.get_filepath("jpg")
        fp = open(filepath,"wb")
        fp.write(content.read())
        fp.flush()
        fp.close()
        return Result(src)
    
    def _ebRender(self, failure):
        if isinstance(failure.value, Fault):
            return failure.value
        SysLog(1,failure)
        return Fault(self.FAILURE, "error")
    
    def _cbRender(self, result, request, responseFailed=None):
        ret = {"Success":True,"data":""}
        if responseFailed:
            return
        
        if isinstance(result, Fault):
            ret["success"] = False
            ret["data"] = "faultCode:%d,faultString:%s"%(result.faultCode,result.faultString)
        elif isinstance(result,Result):
            ret["data"] = result.to_msg_result()
        elif isinstance(result,MsgResult):
            ret["data"] = result.__dict__
        else:
            ret["data"] = result
                
        try:
            content = json.dumps(ret)
            request.setHeader("content-length", str(len(content)))
            request.write(content)
        except Exception, e:
            SysLog(1,"TestResource._cbRender fail [%s]"%str(e))
        request.finish()
