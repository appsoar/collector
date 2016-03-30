# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
from common.util import Result
from frame.Logger import PrintStack, SysLog
from frame.authenmgr import AuthenMgr
from frame.errcode import ERR_METHOD_CONFLICT, ERR_SERVICE_INACTIVE, \
    PERMISSION_DENIED_ERR, INTERNAL_OPERATE_ERR, INTERNAL_EXCEPT_ERR
from frame.exception import OPException

"""
一个实现请求分发的类，基于ring认证方式
"""

class Dispatch(object):
    def __init__(self):
        self.method_list = {}
        self.__service_active = False
        
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
    
    
    def verify_token(self,method,token,*args):
        return AuthenMgr.instance().verify_token(method, token,args)
    
    def dispatch(self,method,token=None,*params,**kw):
        authRlt = self.verify_token(method, token, *params)
        if authRlt.success:
            passport = authRlt.content
        else:
            SysLog(4,"check token fail")
            return authRlt
            
        ret = None
        try:
            # check service available
            if not self.__service_active:
                raise OPException("Service inactive yet",ERR_SERVICE_INACTIVE)

            methodMod = self.get_method_path(passport)
            if methodMod:
                func = None
                if methodMod == self.moduleId:
                    func = getattr(self,method,None)
                else:
                    mod = getattr(self,methodMod,None)
                    func = getattr(mod,method,None)
                
                if  func.func_code.co_flags & 0x8 :
                    _return = func(*params,passport=passport)
                else:
                    _return = func(passport,*params)
            else:
                _return = Result("",PERMISSION_DENIED_ERR,"Sorry,The method not support.")
            ret = _return
        except OPException,e:
            PrintStack()
            # operation error logging and error handle
            ret = Result(e.errid,INTERNAL_OPERATE_ERR,str(e))
            SysLog(1,"Call method["+str(method)+"] error! "+str(e)+" Param:"+str(params))
        except Exception,e:
            PrintStack()            
            SysLog(1,"error:"+str(e))
            ret = Result(0,INTERNAL_EXCEPT_ERR,"internal errors")
            SysLog(1,"Dispatch.dispatch fail as [%s]"%str(e))
        finally:
            if isinstance(ret,Result):
                SysLog(4,"%s return value <%s>"%(method,str(ret)))
                return ret
            else:
                SysLog(4,"%s return value is <%s>"%(method,str(ret)))
                return Result(ret)
            
            