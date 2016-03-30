# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
用于管理配置文件（纯文本文件，不会被编译）中保存的配置信息
"""

import os
import threading

from common.guard import LockGuard
from frame.Logger import Log
from frame.configbase import ConfigBase


class ConfigMgr(ConfigBase):
    '''
    classdocs
    '''
    __lock = threading.Lock()
    __config_path = None
    Env = {}

    @classmethod
    def instance(cls):
        with LockGuard(cls.__lock):
            if not hasattr(cls, "_instance"):
                cls._instance = cls()
        return cls._instance

    @classmethod
    def getValue(cls,key):
        return cls.instance().get_config(key)
    
    def __init__(self):
        '''
        Constructor
        '''
        ConfigBase.__init__(self)
         
    def init(self):
        config_path = self.get_config_path()
        if not os.path.isfile(config_path):
            Log(1,"The configure file [%s] is not exist."%(config_path))
            return
        self.__config_path = config_path
        self.loadConfig(config_path)
        
    def save_to_file(self):
        self.save_config(self.__config_path)
        
    def get_config_path(self):
        workdir = os.path.dirname(os.path.abspath(__file__))
        workdir = os.path.join(workdir,"conf")        
        return os.path.join(workdir,"config.conf")
    

    
    def get_int(self,key,default=0):
        v = self.get_config(key)
        if v is None:
            return default
        
        try:
            v = int(v)
        except Exception,e:
            Log(2,"get_int fail,key[%s],value[%s],err[%s]."%(key,v,str(e)))            
            return default
        else:
            return v
        
ConfigMgr.instance().init()
        
def GetSysConfig(key):
    return ConfigMgr.instance().get_config(key)

def GetSysConfigInt(key,default=0):
    return ConfigMgr.instance().get_int(key, default)
        


