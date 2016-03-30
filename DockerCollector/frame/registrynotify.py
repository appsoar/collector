# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.


from common.util import LawResult
from frame.Logger import SysLog
from twisted.internet import defer
from twisted.web import resource, server
import json
import xmlrpclib
Fault = xmlrpclib.Fault

PAGE = 'Page'
TREE = 'Tree'
LIST = 'List'
SET = 'set'

class RegistryNotify(resource.Resource):
    NOT_FOUND = 8001
    FAILURE = 8002
    def __init__(self,service,handler,allow_none = True,useDateTime=False, encoding = "UTF-8"):
        resource.Resource.__init__(self)
        self.service = service     
        self.instance = handler
        self.isLeaf = True
        self.encoding = encoding
#        self.wwwroot = wwwroot
        
    def render_GET(self,request):
        arr = request.path.split("/")
        if len(arr) < 4:
            return 'The url is invalid!'
        
        return self.process(request, 'Read', arr[2:])
    
    def render_PUT(self,request):
        arr = request.path.split("/")
        if len(arr) < 4:
            return 'The url is invalid!'
        
        return self.process(request, 'Update', arr[2:] )
    
    def render_DELETE(self,request):
        arr = request.path.split("/")
        if len(arr) < 4:
            return 'The url is invalid!'
        
        return self.process(request, 'Delete',arr[2:])
    
    def render_POST(self,request):
        data = request.content.getvalue()
        SysLog(1,"render_POST[%s]"%(data))
        
#         data = json.loads(newdata)
        
        arr = request.path.split("/")
            
        act = 'Save'
        args = arr[2:]

        return self.process(request,act,data,args)
    
    
    def process(self,request,act,data,args):
        params = {}
        for key in request.args:
            txt = request.args[key][0]
            try:
                obj = json.loads(txt)
            except:
                params[key] = txt
            else:            
                params[key] = obj
                
        args.append(params)
        
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
            
            d = defer.maybeDeferred(function,act,data,*args)
            d.addErrback(self._ebRender)
            d.addCallback(self._cbRender, request, responseFailed)
        return server.NOT_DONE_YET 
        
    
    def _ebRender(self, failure):
        if isinstance(failure.value, Fault):
            return failure.value
        SysLog(1,failure)
        return Fault(self.FAILURE, "error")
    
    def _cbRender(self, result, request, responseFailed=None):
        ret = {"success":True,"message":""}
        if responseFailed:
            return
        
        if isinstance(result, Fault):
            ret["success"] = False
            ret["message"] = "faultCode:%d,faultString:%s"%(result.faultCode,result.faultString)
        elif isinstance(result,LawResult):
            ret = result.to_ext_result()
        else:
            ret = result

        try:
            content = json.dumps(ret)
            request.setHeader("content-length", str(len(content)))
            request.write(content)
        except Exception, e:
            SysLog(1,"TestResource._cbRender fail [%s]"%str(e))
        request.finish()
