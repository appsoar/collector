# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
Implement Order data manage
"""

import threading

from common.guard import LockGuard
from mongodb.dbbase import DBBase
from mongodb.dbconst import MAIN_DB_NAME, NOTIFICATION_TABLE


class NotifyDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = NOTIFICATION_TABLE
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
        
    
            
    
             
            
            
            
            
            
            
            
            
            
        