# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.


import json
import os

from common.guard import FileGuard
from common.util import Result
from frame.Logger import Log
from frame.authen import ring8
from frame.errcode import INVALID_JSON_DATA_ERR, INVALID_PARAM_ERR, \
    LOG_FILE_NOT_EXIST_ERR
from mongoimpl.registry.imagedbimpl import ImageDBImpl
from mongoimpl.registry.namespacedbimpl import NamespaceDBImpl
from mongoimpl.registry.repositorydbimpl import RepositoryDBImpl
from mongoimpl.registry.tagdbimpl import TagDBImpl


class RegistryMgr(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    
    @ring8
    def repositories(self, scope='', key=''):
        scope = scope.strip()
        key = key.strip()
        if key != '' and scope == 'usr':
            query = {'user_id':key}
        elif scope:
            query = {'namespace':scope}
        else:
            query = {}

        
        rlt = RepositoryDBImpl.instance().exec_db_script('repositories', query, 10000, 0)
        return rlt
        
        
    
    @ring8
    def info(self):
        return RepositoryDBImpl.instance().exec_db_script('overview')
        
    @ring8    
    def namespaces(self):
        query = {}
        rlt = NamespaceDBImpl.instance().exec_db_script('namespaces',query, 10000, 0)
        if not rlt.success:
            Log(1, 'namespaces.read_record_list fail,as[%s]'%(rlt.message))
            
        return rlt
    
    @ring8    
    def add_namespace(self, post_data):
        try:
            namespace = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        else:
            return NamespaceDBImpl.instance().create_new_nspc(namespace)
        
    @ring8    
    def update_namespace(self, _id, post_data):
        _id = _id.strip()
        if _id=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid namespace id' )
        
        try:
            namespace = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        
        return NamespaceDBImpl.instance().update_namespace(_id, namespace)   
        
    @ring8    
    def namespace(self, namespace=''):
        namespace = namespace.strip()
        if namespace=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid namespace' )
        rlt = NamespaceDBImpl.instance().read_record(namespace)
        if not rlt.success:
            Log(1, 'namespace.read_record[%s]fail,as[%s]'%(namespace, rlt.message))
        
        rlt.content['repo_num'] = RepositoryDBImpl.instance().get_repo_num(namespace)
        return rlt
        
        
    @ring8
    def delete_namespace(self, post_data):
        try:
            _filter = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))

        namespace = _filter.get('namespace_id','')
        namespace = namespace.strip()
        if namespace=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid namespace' )
        
        rlt = NamespaceDBImpl.instance().delete_namespace(namespace)
        if not rlt.success:
            Log(1, 'delete_namespace[%s] fail,as[%s]'%(namespace, rlt.message))
        return rlt
        
    
    @ring8    
    def repository(self, namespace, repo_name=''):
        """
        # 返回仓库的tag列表
        """
        repo_name = repo_name.strip()
        namespace = namespace.strip()
        if repo_name.strip():
            namespace = '%s/%s'%(namespace, repo_name)
        rlt = TagDBImpl.instance().exec_db_script('tags', {'repository':namespace}, 10000, 0)
        if not rlt.success:
            Log(1, 'repository.read_tag_list fail,as[%s]'%(rlt.message))
            
        return rlt
    
    @ring8
    def tag(self, namespace, repo_name, tag_name=''):
        repo_name = repo_name.strip()
        namespace = namespace.strip()
        tag_name = tag_name.strip()
        if tag_name:
            namespace = '%s/%s'%(namespace, repo_name)
        else:
            tag_name = repo_name
        rlt = TagDBImpl.instance().get_tag_info(namespace, tag_name)
        if not rlt.success:
            Log(1, 'tag.get_tag_info[%s][%s]fail,as[%s]'%(namespace, tag_name, rlt.message))
            return rlt
        
        info = ImageDBImpl.instance().get_image_info(rlt.content['digest'])
        if not info:
            return rlt
        
        rlt.content['size'] = info['size']
        rlt.content['user_id'] = info['user_id']
        rlt.content['pull_num'] = info['pull_num']
        return rlt
        
    @ring8
    def logs(self, line_num, skip=0):
        try:
            line_num = int(line_num)
            skip = int(skip)
        except Exception:
            return Result('', INVALID_PARAM_ERR, 'Param invalid')
        
        workdir = os.path.abspath('.')
        workdir = os.path.join(workdir,"Trace")
        workdir = os.path.join(workdir,"logs")
        log_path = os.path.join(workdir,"operation.log")

        if not os.path.isfile(log_path):
            Log(1,"The log file [%s] is not exist."%(log_path))
            return Result('', LOG_FILE_NOT_EXIST_ERR, 'File not exist')
        arr = []
        size = skip
        with FileGuard(log_path, 'r') as fp:
            fp.seek(skip)
            
            for line in fp:
                if line_num == 0:
                    break;
                size += len(line)
                line_num -= 1
                arr.append(line)

        return Result(arr,0,size)

            
            
        
    
    
    
    