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
from mongodb.dbconst import MAIN_DB_NAME, LAYER_TABLE, ID


class LayerDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = LAYER_TABLE
    __lock = threading.Lock()
    
    @classmethod
    def instance(cls):
        with LockGuard(cls.__lock):
            if not hasattr(cls, "_instance"):
                cls._instance = cls()
        return cls._instance
    
    
    def __init__(self):
        DBBase.__init__(self, self.db, self.collection)
        
    def save_layer_info(self, image_info):
        arr = []
        for layer in image_info['fsLayers']:
            if 'blobSum' in layer:
                arr.append({ID:layer['blobSum'],'image_id':image_info['digest']})
            else:
                layer[ID] = layer.pop('digest')
                layer['image_id'] = image_info['digest']
                arr.append(layer)
            
        if arr:
            rlt = self.batch_insert(arr)
            if not rlt.success:
                Log(1, "LayerDBImpl save_layer_info fail,as[%s]"%(rlt.message))
        
            
    def add_layer_pull_num(self, digest):
        self.find_and_modify_num({ID:digest}, {'pull_num':1}, True)
            
            
            
            
            
            
            
            
            
        