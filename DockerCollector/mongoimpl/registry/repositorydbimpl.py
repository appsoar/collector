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
from mongodb.dbconst import MAIN_DB_NAME, REPOSITORY_TABLE, ID


class RepositoryDBImpl(DBBase):
    db = MAIN_DB_NAME
    collection = REPOSITORY_TABLE
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
        
    def is_repository_exsit(self, repository):
        rlt = self.count({ID: repository})
        if rlt.success and rlt.content>0:
            return True
        return False
    
    def save_repository(self, namespace, repository, actor):
        rlt = self.count({ID: repository})
        if rlt.success and rlt.content>0:
            return rlt

        data = {ID:repository, 
                'push_time':NowMilli(),
                'permission':'public', 
                'delete':0, 
                'desc':'', 
                'namespace':namespace,
                'user_id':actor.get('name','system')}
        rlt = self.insert(data)
        if not rlt.success:
            Log(1, 'save_repository[%s]fail,as[%s]'%(rlt.content))
        return rlt
        
    def upsert_repository(self, repositories):
        rlt = self.read_record_list(projection=[])
        if not rlt.success:
            Log(1, 'upsert_repository.read_record_list fail,as[%s]'%(rlt.message))
            return rlt
        
        local_repos = []
        new_repos = []
        lost_repos = []
        for repo in rlt.content:
            local_repos.append(repo[ID])
            if repo[ID] not in repositories:
                lost_repos.append(repo[ID])
        
        for repo in repositories:
            if repo not in local_repos:
                new_repos.append({ID:repo, 'push_time':NowMilli(), 'is_public':True, 'delete':0, 'desc':''})

        if len(new_repos) > 0:
            rlt = self.batch_insert(new_repos)
            if rlt.success:
                Log(3, 'upsert_repository insert [%d] new record'%(rlt.content) )
            else:
                Log(1, 'upsert_repository insert record fail,as[%s]'%(rlt.message) )
        
        if len(lost_repos) > 0:
            rlt = self.updates({ID:{'$in':lost_repos}}, {'delete':NowMilli()})
            if rlt.success:
                Log(3, 'upsert_repository update [%d] old record'%(rlt.content) )
            else:
                Log(1, 'upsert_repository update record fail,as[%s]'%(rlt.message) )
                
        return Result(len(new_repos) + len(lost_repos))
        
        
    def list_repository(self, namespace='', user_id=''):
        query = {}
        if namespace:
            query['namespace'] = namespace
            #reg = '^%s\/'%(namespace)
            #return self.read_record_list({namespace:{'$regex':reg, '$options': 'i'}})
        if user_id:
            query['user_id'] = user_id
        return self.read_record_list(query)

        
    def read_repo_info(self, repo_name):
        return self.read_record(repo_name)
    
    def get_repo_num(self, namespace):
        rlt = self.count({'namespace':namespace})
        if rlt.success:
            return rlt.content
        return 0
            
            
            
            
            
            
            
            
            
            
            
        