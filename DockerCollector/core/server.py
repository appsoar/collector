# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

"""
Implement the web server 
"""

import os
import xmlrpclib

from twisted.application import service
from twisted.web import resource

from api.apihandler import APIHandler
from console.consolehandler import ConsoleRequestHandler
from frame.Logger import PrintStack, Log
from frame.ajaxresource import AjaxResource
from frame.apiresource import APIResource
from frame.registrynotify import RegistryNotify
from frame.web import mimesuffix
from registry.notifyhandler import NotifyHandler


Fault = xmlrpclib.Fault


class RootResource(resource.Resource):
    isLeaf = False
    numberRequests = 0
    def __init__(self,service):
        resource.Resource.__init__(self)
        self.service = service
        work_root = os.path.normcase(self.service.workroot)
        work_root = os.path.split(work_root)[0]
        self.www_root = os.path.join(work_root,"desktop")
    
    def render_GET(self,request):
        path = os.path.normcase(request.path)[1:]
#         if "\\" == name[0] or "\/" == name[0]:
#             name = name[1:]
        
        try:
            suffix = "html"
            if len(path) == 0:
                fullpath = os.path.join(self.www_root,"index.html")
            else:
                fullpath = os.path.join(self.www_root,path)
                suffix = os.path.splitext(os.path.basename(path))[-1][1:]

            response = open(fullpath,"rb").read()
            if suffix in mimesuffix:
                request.setHeader("content-type", mimesuffix[suffix])
        except:
            PrintStack()
            response = '''<body><h1>Error!</h1>
        Get file [%s] fail
        </body>''' %(path)
        request.setHeader("content-length", str(len(response)))
        return response

    def render_POST(self,request):
        response = '''<body><h1>Error!</h1>
        Method POST is not allowed for root resource
        </body>'''
        request.setHeader("content-type", ["text/html"])
        request.setHeader("content-length", str(len(response)))
        request.write(response)
        request.finish()
    
    def getChild(self,path,request):
        if path not in ["server"]:
            return self
        else:
            print "error"
            
class WebService(service.Service):

    def __init__(self,workroot,conf_file = ""):
        self.workroot = workroot
        self.init_resource()
        Log(3,"WebService Starting completed")
        
        
            
    def init_resource(self):
        try:
            self.ConsoleHandler = ConsoleRequestHandler()
            self.NotifyHandler = NotifyHandler()
            self.APIHandler = APIHandler()
        except Exception,e:
            PrintStack()
            print "Error:"+str(e)
        
    def get_resource(self):
        r = RootResource(self)
        r.putChild("event", RegistryNotify(self, self.NotifyHandler))
        r.putChild("api", APIResource(self, self.APIHandler))
        r.putChild("console", AjaxResource(self, self.ConsoleHandler))
        
        return r
    


    

        
