# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.



from common.util import Result
from core.config import SysConfig
from frame.Logger import Log
from frame.authen import ring0
from frame.configmgr import ConfigMgr
from frame.errcode import CONFIG_OUT_OF_LIMIT_ERR
from mongodb.dbconst import ID
from mongoimpl.consoledb.configdbimpl import ConfigDBImpl


class ConfigureMgr(object):
    def __init__(self):
        pass

        
    @ring0
    def ReadConfigList(self,query=None):
        return ConfigDBImpl.instance().read_record_list(query)
    

    @ring0
    def SaveConfig(self,cfgInfo):
        value = cfgInfo.get("value")
        _id = cfgInfo.get(ID)
        if not str(_id).isdigit():
            return self.__save_to_file(_id,value)
        
        cfgInfo[ID] = int(_id)
        if str(value).isdigit():
            cfgInfo["value"] = int(value)
        else:
            cfgInfo["value"] = value
            
        rlt = self.check_input(cfgInfo)
        if not rlt.success:
            return rlt

        return self.save_input(cfgInfo,rlt.content)
        
    def __save_to_file(self,key,value):
        cfg = ConfigMgr.instance()
        cfg.update_key(key, value)
        cfg.save_to_file()
        return Result(key)
    
    @ring0
    def ReadConfigPage(self,query,orderby,pageNo,pagesize):
        """
        @param orderby: 
        @param pageNo: 
        @param pagesize: 
        # 在数据库中读取配置信息
        """
        rlt = ConfigDBImpl.instance().read_all_record_page(orderby, pageNo, pagesize)
        if not rlt.success:
            Log(1,"getConfigureList fail,as[%s]"%(rlt.message))
            
        return rlt

    def read_config_list(self,query=None):
        return ConfigDBImpl.instance().read_record_list(query)
    
    def read_config_page(self,query, orderby, pageNo, page_size):
        return ConfigDBImpl.instance().read_record_page(query, orderby, pageNo, page_size)
    
    def check_input(self,cfgInfo):
        rlt = ConfigDBImpl.instance().read_record(cfgInfo[ID])
        if not rlt.success:
            return rlt
        
        key = rlt.content["path"]
        value = cfgInfo["value"]
        if key not in SysConfig.store:
            return Result(key)
        
        handler = SysConfig.store[key]
        if handler.is_invalid(value):
            return Result(key,CONFIG_OUT_OF_LIMIT_ERR,"The input is out of limit.")
        return Result(key)

    def save_input(self,cfgInfo,key):
        _id = cfgInfo[ID]
        rlt = ConfigDBImpl.instance().save_config(cfgInfo)
        if not rlt.success:
            return rlt

        cfg = ConfigMgr.instance()
        cfg.update_key(key, cfgInfo["value"])
        cfg.save_to_file()
        return Result(_id)
    
