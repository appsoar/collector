# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

#import bcrypt

import json

from common.util import Result
from frame.Logger import Log
from frame.authen import ring8
from frame.errcode import INVALID_PARAM_ERR, INVALID_JSON_DATA_ERR
from mongodb.dbconst import ID
from mongoimpl.consoledb.userdbimpl import UserDBImpl
from mongoimpl.registry.groupdbimpl import GroupDBImpl


_ALL = "All"

class AccountMgr(object):
    def __init__(self):
        pass
    
    
    @ring8
    def accounts(self, user_id=''):
        if user_id:
            query = {ID:user_id}
        else:
            query = None
        
        rlt = UserDBImpl.instance().read_record_list(query, projection=['nick_name','join_time', 'avatar'])
        if rlt.success:
            for user in rlt.content:
                user['user_id'] = user.pop(ID)
        return rlt
    
    @ring8
    def account(self, user_id):
        user_id = user_id.strip()
        if user_id=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid user id' )
        
        rlt = UserDBImpl.instance().read_record(user_id)
        if rlt.success:
            rlt.content['user_id'] = rlt.content.pop(ID)
            rlt.content['password'] = '$2a$10$f4UrYQDuijGdWkxO0GTA5uyHwjExLVll/o6Bdg629qfiFctqzijZW'
        return rlt
        
    @ring8
    def login(self, post_data):
        try:
            account = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        else:
            user_name = account.get('user_name')
            password = account.get('password')
            return UserDBImpl.instance().is_exist({ID:user_name,'password':password})
    
    @ring8    
    def is_user_exist(self, user_name=''):
        user_id = user_name.strip()
        if user_id=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid user id' )
        
        return UserDBImpl.instance().is_exist({ID:user_name})
        
        
    @ring8
    def delete_account(self, post_data):
        try:
            _filter = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        
        user_id = _filter.get('user_id','')
        user_id = user_id.strip()
        if user_id=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid user id' )
        
        rlt = UserDBImpl.instance().delete_user(user_id)
        if not rlt.success:
            Log(1, 'delete_account[%s] fail,as[%s]'%(user_id, rlt.message))
        return rlt
        
    
        
    @ring8
    def logout(self, user_name):
        return Result(user_name)
       
    @ring8
    def add_account(self, post_data):
        try:
            account = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        else:
            return UserDBImpl.instance().create_new_user(account)
    
    @ring8    
    def update_account(self, _id, post_data):
        _id = _id.strip()
        if _id=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid user id' )
        
        try:
            info = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"update_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        
        return UserDBImpl.instance().update_user(_id, info)
    
    @ring8    
    def groups(self, namespace):
        return GroupDBImpl.instance().read_record_list({'namespace':namespace}) 
    
    @ring8    
    def group(self, group_id):
        return GroupDBImpl.instance().read_record({ID:group_id}) 
    
    @ring8    
    def is_group_exist(self, namespace, group_name):
        namespace = namespace.strip()
        group_name = group_name.strip()
        
        if not namespace or not group_name:
            return Result('', INVALID_PARAM_ERR, 'Param is invalid.')
        
        return GroupDBImpl.instance().is_exist({'namespace':namespace,'group_name':group_name})
    
    @ring8    
    def add_group(self, post_data):
        try:
            group_info = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_grp.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        else:
            return GroupDBImpl.instance().create_new_group(group_info)
    
    @ring8
    def delete_group(self, post_data):
        try:
            _filter = json.loads(post_data.replace("'", '"'))
        except Exception,e:
            Log(1,"save_account.parse data to json fail,input[%s]"%(post_data))
            return Result('',INVALID_JSON_DATA_ERR,str(e))
        
        group_id = _filter.get('group_id','')
        group_id = group_id.strip()
        if group_id=='':
            return Result('', INVALID_PARAM_ERR, 'Invalid group id' )
        
        rlt = GroupDBImpl.instance().delete_group(group_id)
        if not rlt.success:
            Log(1, 'delete_grp[%s] fail,as[%s]'%(group_id, rlt.message))
        return rlt
    
    
    