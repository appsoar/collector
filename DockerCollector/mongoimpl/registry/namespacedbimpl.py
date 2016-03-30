# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
Implement Order data manage
"""


import threading

from common.guard import LockGuard
from common.util import NowMilli, Result
from frame.Logger import Log
from frame.errcode import INVALID_NAMESPACE_INFO_ERR, NAMESPACE_EXIST_ALREADY_ERR
from mongodb.dbbase import DBBase
from mongodb.dbconst import MAIN_DB_NAME, NAMESPACE_TABLE, ID


class NamespaceDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = NAMESPACE_TABLE
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
        
    def save_namespace(self, namespace, actor):
        rlt = self.count({ID:namespace})
        if rlt.success and rlt.content > 0:
            Log(1, 'save_namespace The name space exist. repository[%s]'%(namespace))
            return rlt

        data = {ID:namespace,'create_time':NowMilli(), 'owner_id':actor.get('name','system'), 'desc':'','permission':'public'}
        ret = self.insert(data)
        if not ret.success:
            Log(1, 'save namespace[%s] fail,as[%s]'%(namespace, rlt.message))
        return ret
    
    def create_new_nspc(self, info):
        namespace = info.get(ID, None)
        if not namespace:
            return Result('', INVALID_NAMESPACE_INFO_ERR, 'Namespace info invalid.')

        if self.is_exist({ID:namespace}):
            return Result('', NAMESPACE_EXIST_ALREADY_ERR, 'Namespace exist already.')
        
        info['create_time'] = NowMilli()
        rlt = self.insert(info)
        if not rlt.success:
            Log(1, 'create_new_nspc fail,as[%s]'%(rlt.message))
        return rlt
        
    def update_namespace(self, _id, info):
        info.pop(ID, None)
        
        info['update_time'] = NowMilli()
        rlt = self.update({ID:_id}, info)
        if not rlt.success:
            Log(1, 'create_new_nspc fail,as[%s]'%(rlt.message))
        return rlt
            
    def delete_namespace(self, namespace):
        return self.remove({ID:namespace}) 
    
        
        
            
            
            
            
            
            
            
            
            
            
            
        