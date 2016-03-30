# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
Implement Order data manage
"""

import threading

from common.guard import LockGuard
from frame.Logger import Log
from mongodb.dbbase import DBBase
from mongodb.dbconst import MAIN_DB_NAME, IMAGE_TABLE, ID


class ImageDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = IMAGE_TABLE
    __lock = threading.Lock()
    
    @classmethod
    def instance(cls):
        with LockGuard(cls.__lock):
            if not hasattr(cls, "_instance"):
                cls._instance = cls()
        return cls._instance
    
    
    def __init__(self):
        DBBase.__init__(self, self.db, self.collection)
        
    def upsert_image_info(self, image_id, repository):       
        rlt = self.update({ID:image_id}, {'repository':repository}, True)
        if not rlt.success:
            Log(1, 'upsert_image_info[%s]fail,as[%s]'%(repository, rlt.message))
        
            
    def is_image_exist(self, digest):
        """
        # digest 指向一个文件，和repository无关，只要内容一样，digest值就是一样的
        """
        rlt = self.count({ID:digest})
        if rlt.success and rlt.content>0:
            return True
        return False       
            
    def create_image(self, repository, image, actor, source):
        size = 0
        for layer in image['fsLayers']:
            size += layer['size']
        
        data = {'repository':repository, ID:image['digest'], 'user_id':actor.get('name',''), 'size':size}
        data.update(source)
        rlt = self.insert(data)
        if not rlt.success:
            Log(1, 'create_image repository[%s]digest[%s]fail'%(repository, image['digest']))
        return rlt        
            
            
    def add_pull_num(self, digest):
        self.find_and_modify_num({ID:digest}, {'pull_num':1}, True)
            
            
    def get_image_info(self, digest):
        rlt = self.read_record(digest)
        if rlt.success:
            return rlt.content
        else:
            Log(1, 'get_image_info[%s] fail,as[%s]'%(digest, rlt.message))
            return {}
                
            
        