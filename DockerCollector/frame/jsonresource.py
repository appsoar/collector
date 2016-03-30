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
Fault = xmlrpclib.Fault


class JsonResource(resource.Resource):
    NOT_FOUND = 8001
    FAILURE = 8002
    def __init__(self,service,handler,wwwroot,allow_none = True,useDateTime=False, encoding = "UTF-8"):
        resource.Resource.__init__(self)
        self.service = service     
        self.instance = handler
        self.isLeaf = True
        self.encoding = encoding
        self.wwwroot = wwwroot
    def render_GET(self,request):
        basepath = os.path.normcase(self.wwwroot)
        name = os.path.normcase(request.path)

        if "\\" == name[0] or "\/" == name[0] or "/" == name[0]:
            name = name[1:]

        fullpath = os.path.join(basepath,name)
        try:
            if name =="":
                name = "index.html"
            response = open(fullpath,"rb").read()
            suffix = os.path.basename(name).split(".")[-1]
            if suffix in mimesuffix:
                request.setHeader("content-type", mimesuffix[suffix])
        except:
            traceback.print_exc()
            response = '''<body><h1>Error!</h1>
        Get file [%s] fail
        </body>''' % name
        request.setHeader("content-length", str(len(response)))
        return response
    def render_POST(self,request):
        args = request.args
        method = args["CallbackMethod"][0]
        ParmCount = args["CallbackParmCount"][0]
        Parms = []
        for i in range(int(ParmCount)):
            s = args["Parm%d"%(i+1)][0]
            try:
                obj = json.loads(s)
            except:
                Parms.append(s)
            else:            
                Parms.append(obj)
        
        function = getattr(self.instance, "dispatch", None)
        if function is None:
            f = Fault(self.FAILURE, "The Resource didn't implement the _dispatch method")
            self._cbRender(f, request)
        else:
            # Use this list to track whether the response has failed or not.
            # This will be used later on to decide if the result of the
            # Deferred should be written out and Request.finish called.
            responseFailed = []
            request.notifyFinish().addErrback(responseFailed.append)
            
            d = None
            
            if getattr(function, 'withRequest', False):
                d = defer.maybeDeferred(function,method,request,*Parms)
            else:
                #d.addCallback(function,functionPath, *args)
                d = defer.maybeDeferred(function,method,*Parms)
            d.addErrback(self._ebRender)
            d.addCallback(self._cbRender, request, responseFailed)
        return server.NOT_DONE_YET 
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
