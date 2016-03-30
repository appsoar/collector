# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
from common.guard import LockGuard
from frame.Logger import Log
from mongodb.dbbase import DBBase
from mongodb.dbconst import MAIN_DB_NAME, CONFIG_TABLE, ID
import threading

"""
Implement Order data manage
"""
DHCP_CONFIG = "DHCPConfig"
SERVER_INFO = "ServerInfo"

class ConfigDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = CONFIG_TABLE
    __lock = threading.Lock()
    
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
        DBBase.__init__(self, self.db, self.collection)
        
    def save_config(self,config):
        try:
            _id = int(config.pop(ID))
        except Exception:
            return self.create(config)
        else:
            return self.update({ID:_id},config)
        
    def save_server_info(self,server_info):
        server_info.pop(ID,None)
        return self.update({ID:SERVER_INFO}, server_info, True)
    
    def save_dhcp_config(self,dhcp_cfg):
        dhcp_cfg.pop(ID,None)
        if 'vlan_range' in dhcp_cfg:
            dhcp_cfg['vlan_range'] = str(dhcp_cfg['vlan_range'])
        return self.update({ID:DHCP_CONFIG}, dhcp_cfg, True)
    
    def get_server_info(self):
        rlt = self.read_record(SERVER_INFO)
        if rlt.success:
            return rlt.content
        Log(1,"ConfigDBImpl.get_server_info fail,as[%s]."%(rlt.message))
        return None
    
    def set_registed(self):
        return self.update({ID:SERVER_INFO}, {"status":1}, True)
            
            
            
            
            
            
            
            
            
            
            
        