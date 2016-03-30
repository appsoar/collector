# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.


"""
Manager user security info and verify it  
"""

import os
import threading
import time

from common.guard import LockGuard
from common.util import Result
from frame.Logger import Log, PrintStack
from frame.authen import authen
from frame.configmgr import GetSysConfigInt
from frame.errcode import ERR_LOGIN_TIMEOUT, USER_UN_LOGIN_ERR, \
    INVALID_TOKEN_ERR
from frame.exception import OPException
from mongodb.dbconst import ID


class RegistryAuthen(authen):
    __lock = threading.Lock()
    __ulock = threading.Lock()
    
    @classmethod
    def instance(cls):
        '''
        Limits application to single instance
        '''
        with LockGuard(cls.__lock):
            if not hasattr(cls, "_instance"):
                cls._instance = cls()

        return cls._instance
    
    def __init__(self):
        self.__token = {}
        time_offset = GetSysConfigInt("time_offset",30)
        authen.__init__(self, time_offset)
        self.session_timeout = GetSysConfigInt("session_timeout",30) * 60
        
    def load_access_info(self):
        #self.__token["00000000-0000-0000-0000-000000000000"] = {"access_key":"00000000-0000-0000-0000-000000000000","ring":"ring0","timestamp":time.time()}
        pass

    def get_green_passport(self,method):
        passport = {}
        passport["method"] = method
        passport["ring"] = "ring8"
        
        return passport
    
#        if method == "whatTime" or method == "Login":
#            passport = {}
#            passport["method"] = method
#            passport["ring"] = "ring8"
#            return passport
#        return False
    
    
    def get_sec_path(self):
        workroot = "" # GetSysConfig("Env.workroot")
        sec_path = "" # GetSysConfig("secret_path")
        if workroot is None or sec_path is None:
            return None
        sec_path = os.path.join(workroot,sec_path)
        return sec_path
            
    def get_access_key(self,access_uuid):
        with LockGuard(self.__ulock):
            if access_uuid in self.__token:
                token = self.__token[access_uuid]
                offset = time.time() - token["timestamp"]
                if offset > self.session_timeout:
                    del self.__token[access_uuid]
                    raise OPException("Token [%s] Time out."%(access_uuid) ,ERR_LOGIN_TIMEOUT)
                else:
                    token["timestamp"] = time.time()
                return token["ring"],token["access_key"]
            Log(1,"%s not a valid uuid"%access_uuid)
            raise OPException("GetAccessKey fail,uuid [%s]"%(access_uuid) ,USER_UN_LOGIN_ERR)

    def remove_token(self,access_uuid):
        with LockGuard(self.__ulock):
            if access_uuid in self.__token:
                del self.__token[access_uuid]
                return Result(access_uuid)
            else:
                return Result(access_uuid,1,"User din't login.")
    
    def create_token(self,userinfo):
        with LockGuard(self.__ulock):
            role = userinfo["role"]
            access_uuid = userinfo[ID]
            access_key = userinfo["access_key"]
            
            if access_uuid not in self.__token:
                self.__token[access_uuid] = {"access_key":access_key,"ring":role,"timestamp":time.time()}
            else:
                token = self.__token[access_uuid]
                token["timestamp"] = time.time()
            
            #return {"access_key":self.encrypt(access_key),"access_uuid":access_uuid}
            return {"access_key":access_key,"access_uuid":access_uuid}
        
        
    def verify_token(self,method,token,*args):
        try:
            passport = self.check_token(method,token,*args)
            #passport["shortcut"] = "%s%s%s"%(method,args[0],args[1])
        except OPException,e:
            PrintStack()
            Log(1,"AuthenMgr.verify_token fail as [%s]"%(str(e)))
            return Result(method,e.errid,e.value)
        except Exception,e:
            PrintStack()
            Log(1,"AuthenMgr.verify_token fail as [%s]"%(str(e)))
            return Result(method,INVALID_TOKEN_ERR,str(e))
        else:
            return Result(passport)
            
    
   
        
        