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
from mongodb.dbbase import DBBase
from mongodb.dbconst import MAIN_DB_NAME, TAG_TABLE, ID


class TagDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = TAG_TABLE
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
        
    def create_tag(self, repository, tag, image, actor):
        """
        # 接收通知消息的时候，不带Tag信息，所以这个函数已经没有使用
        """
        data = {'repository':repository, 'tag_name':tag, 'digest':image['digest'], 'user_id':actor.get('name',''),'create_time':NowMilli()}
        rlt = self.create(data)
        if not rlt.success:
            Log(1, 'create_tag repository[%s]tag_name[%s]digest[%s]fail'%(repository, tag, image['digest']))
        return rlt
        
        
    def update_tag_info(self, repository, tag, digest):
        rlt = self.update({'repository':repository, 'tag_name':tag}, {'digest':digest}, True)
        if not rlt.success:
            Log(1, 'update_tag_info[%s][%s]fail,as[%s]'%(repository, tag, rlt.message))
            
    def is_tag_exist(self, repository, tag, digest):
        """
        # digest 指向一个文件，和repository无关，只要内容一样，digest值就是一样的
        """
        query = {'digest':digest}
        if repository:
            query['repository'] = repository
        if tag:
            query['tag_name'] = tag
            
        rlt = self.count(query)
        if rlt.success and rlt.content>0:
            return True
        return False
    
    
        
        
    def upsert_tags(self, repository, tags):
        rlt = self.read_record_list({'repository':repository},projection=['tag_name'])
        if not rlt.success:
            Log(1, 'upsert_tags.read_record_list fail,as[%s]'%(rlt.message))
            return rlt
        
        local_tags = []
        new_tags = []
        lost_tags = []
        for tag in rlt.content:
            local_tags.append(tag['tag_name'])
            if tag['tag_name'] not in tags:
                lost_tags.append(tag[ID])
        
        for tag in tags:
            if tag not in local_tags:
                new_tags.append({'repository':repository, 'delete':0, 'pull_num':0, 'create_time':NowMilli(),'tag_name':tag,'alias':''})

                
        if len(new_tags) > 0:
            rlt = self.batch_insert(new_tags)
            if rlt.success:
                Log(3, 'upsert_tags insert [%s] new record'%(rlt.content) )
            else:
                Log(1, 'upsert_tags insert record fail,as[%s]'%(rlt.message) )
        
        if len(lost_tags) > 0:
            rlt = self.updates({ID:{'$in':lost_tags}}, {'delete':NowMilli()})
            if rlt.success:
                Log(3, 'upsert_tags update [%s] old record'%(rlt.content) )
            else:
                Log(1, 'upsert_tags update record fail,as[%s]'%(rlt.message) )
                
        return Result(len(new_tags) + len(lost_tags))
        
        
    def get_tag_info(self, repo_name, tag_name):
        return self.read_record_data({'repository':repo_name, 'tag_name':tag_name})
            
            
    def get_tag_list(self, repo_name):
        return self.read_record_list({'repository':repo_name})
            
            
            
            
            
            
        