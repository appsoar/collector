# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
Implement Order data manage
"""

import threading

from common.guard import LockGuard
from common.util import Result
from frame.Logger import Log
from frame.errcode import INVALID_GROUP_INFO_ERR, GROUP_EXIST_ALREADY_ERR
from mongodb.dbbase import DBBase
from mongodb.dbconst import MAIN_DB_NAME, USER_GROUP_TABLE, ID


GROUP_RECORD_PREFIX = 'GRP'

class GroupDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = USER_GROUP_TABLE
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

        
    def create_group_record(self, group_info):
        if ID not in group_info:
            group_info[ID] = self.get_record_id(GROUP_RECORD_PREFIX)
        
        return self.insert(group_info)
    
        
    def update_group(self, _id, group_info):
        return self.update({ID:_id}, group_info)

            
    def create_new_group(self, group_info):
        namespace = group_info.get('namespace', None)
        group_name = group_info.get('group_name', None)
        if not namespace or not group_name:
            return Result('', INVALID_GROUP_INFO_ERR, 'User info invalid.')

        if self.is_exist({'namespace':namespace,'group_name':group_name}):
            return Result('', GROUP_EXIST_ALREADY_ERR, 'Group exist already.')
        
        rlt = self.create(group_info)
        if not rlt.success:
            Log(1, 'create_new_group fail,as[%s]'%(rlt.message))
        return rlt        

    def delete_group(self, group_id):
        return self.remove({ID:group_id})
            
            
        