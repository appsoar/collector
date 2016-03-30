# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
分发控制台提交的请求
"""

import time
import xmlrpclib

from api.accountmgr import AccountMgr
from api.apiauthen import APIAuthen
from api.registrymgr import RegistryMgr
from common.util import Result, LawResult
from frame.Logger import PrintStack, SysLog, Log
from frame.authen import ring8
from frame.errcode import ERR_METHOD_CONFLICT, ERR_SERVICE_INACTIVE, \
    PERMISSION_DENIED_ERR, INTERNAL_OPERATE_ERR, INTERNAL_EXCEPT_ERR
from frame.exception import OPException


Fault = xmlrpclib.Fault
_ALL = "All"

class APIHandler(object):
    moduleId = "API"
    
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

            for ring in rings:
                methodSign = "%s.%s"%(ring,method)
                if methodSign in self.method_list:
                    raise OPException("merge method fail: "+str(methodSign)+" conflict!",ERR_METHOD_CONFLICT)
                else:
                    self.method_list[methodSign] = mod_name
                
    def get_method_path(self,passport):
        ring = passport["ring"]
        method = passport["method"]
        methodSign = "%s.%s"%(ring,method)
        if methodSign in self.method_list:
            return self.method_list[methodSign]
        return None
        
    def init(self):
        self.init_method(self,self.moduleId)
        
        self.account = AccountMgr()
        self.init_method(self.account,"account")
        
        self.registry = RegistryMgr()
        self.init_method(self.registry,"registry")
        
        
        self.activate_server()
        
    
    def dispatch(self, method, token=None, *params, **kw):
        authRlt = APIAuthen.instance().verify_token(method, token,*params)
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

            methodMod = self.get_method_path(passport)
            if methodMod is None:
                return Result("",PERMISSION_DENIED_ERR,"Sorry,The method not support.")
            func = None
            if methodMod == self.moduleId:
                func = getattr(self,method,None)
            else:
                mod = getattr(self,methodMod,None)
                func = getattr(mod,method,None)

            if func and func.func_code.co_flags & 0x8 :
                ret = func(*params,passport=passport)
            else:
                ret = func(*params)

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
    
    
        
        
