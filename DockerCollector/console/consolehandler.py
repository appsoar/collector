# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
分发控制台提交的请求
"""

import time
import xmlrpclib

from common.util import Result, LawResult
from console.configuremgr import ConfigureMgr
from console.consoleauthen import ConsoleAuthen
from console.orgnizationmgr import OrgnizationMgr
from console.registrymgr import RegistryMgr
from console.taskmgr import TaskMgr
from console.usermgr import UserMgr
from frame.Logger import PrintStack, SysLog, Log
from frame.authen import ring8
from frame.errcode import ERR_METHOD_CONFLICT, ERR_SERVICE_INACTIVE, \
    PERMISSION_DENIED_ERR, INTERNAL_OPERATE_ERR, INTERNAL_EXCEPT_ERR
from frame.exception import OPException


Fault = xmlrpclib.Fault
_ALL = "All"

class ConsoleRequestHandler(object):
    moduleId = "Console"
    
    def __init__(self):
        self.method_list = {}
        self.__service_active = False
        self.init()
        
    def activate_server(self):
        self.__service_active = True
        
        
    def init_method(self,mod_instance,mod_name):
        for method in dir(mod_instance):
            if method[0] == "_":
                continue
            func = getattr(mod_instance,method)
            rings = None
            if type(func) == type(self.init_method) and hasattr(func,"ring"):
                rings = getattr(func,"ring")
            else:
                continue
            
            methodSign = "%s.%s"%(mod_name,method)
            if methodSign in self.method_list:
                raise OPException("merge method fail: "+str(methodSign)+" conflict!",ERR_METHOD_CONFLICT)
            else:
                self.method_list[methodSign] = rings
                
    def get_method_path(self,passport,mod_name):
        ring = passport["ring"]
        method = passport["method"]
        shortcut = passport["shortcut"]
        methodSign = "%s.%s"%(mod_name,method)
        shortcutSign = "%s.%s"%(mod_name,shortcut)
        
        # 如果快捷调用存在，要受快捷方式的权限控制
        if shortcutSign in self.method_list:
            if ring in self.method_list[shortcutSign]:
                return mod_name
            return None
        
        if methodSign in self.method_list and ring in self.method_list[methodSign]:
            return mod_name
        return None
        
    def init(self):
        self.init_method(self,self.moduleId)

        
        self.Configure = ConfigureMgr()
        self.init_method(self.Configure,"Configure")
        
        self.User = UserMgr()
        self.init_method(self.User,"User")
        
        self.Task = TaskMgr()
        self.init_method(self.Task,"Task")
        
        self.registry = RegistryMgr()
        self.init_method(self.registry,"registry")
        
        self.activate_server()
        
    
    def dispatch(self,method,token=None,module_name=None,*params,**kw):
        authRlt = ConsoleAuthen.instance().verify_token(method, token,*params)
        if authRlt.success:
            passport = authRlt.content            
        else:
            Log(4,"check token fail")
            return authRlt
            
        ret = None
        try:
            # check service available
            if not self.__service_active:
                raise OPException("Service inactive yet",ERR_SERVICE_INACTIVE)

            methodMod = self.get_method_path(passport,module_name)
            if methodMod:
                shortcut = passport["shortcut"]
                func = None
                if methodMod == self.moduleId:
                    func = getattr(self,shortcut,None) or getattr(self,method,None)
                else:
                    mod = getattr(self,methodMod,None)
                    func = getattr(mod,shortcut,None) or getattr(mod,method,None)

                if  func.func_code.co_flags & 0x8 :
                    _return = func(*params,passport=passport)
                else:
                    _return = func(*params)
            else:
                _return = Result("",PERMISSION_DENIED_ERR,"Sorry,The method not support.")
            ret = _return
        except OPException,e:
            PrintStack()
            # operation error logging and error handle
            ret = Result(e.errid,INTERNAL_OPERATE_ERR,str(e))
            Log(1,"Call method["+str(method)+"] error! "+str(e)+" Param:"+str(params))
        except Exception,e:
            PrintStack()            
            Log(1,"error:"+str(e))
            ret = Result(0,INTERNAL_EXCEPT_ERR,"internal errors")
            SysLog(1,"Dispatch.dispatch fail as [%s]"%str(e))
        finally:
            if isinstance(ret,LawResult):
                Log(4,"%s return value <%s>"%(method,str(ret)))
                return ret
            else:
                Log(4,"%s return value is <%s>"%(method,str(ret)))
                return Result(ret)
    
    @ring8    
    def whatTime(self):
        return Result("%ld"%(long(time.time() * 1000)))
    
    
        
        
