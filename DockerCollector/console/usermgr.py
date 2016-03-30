# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
from common.util import Result
from console.consoleauthen import ConsoleAuthen
from frame.authen import ring0, ring8
from frame.errcode import NO_SUCH_USER_ERR, INVALID_PASSWORD_ERR
from mongodb.dbconst import ID
from mongodb.dbutil import Condition4Page
from mongoimpl.consoledb.userdbimpl import UserDBImpl


_ALL = "All"

class UserMgr(object):
    def __init__(self):
        pass
    
    @ring0
    @Condition4Page
    def getUsersSummary(self,filterObj, orderby ,pageNo,pagesize):
        if "name" in filterObj:
            filterObj["name"]={'$regex':filterObj["name"].strip()}
        return UserDBImpl.instance().read_record_page(filterObj, orderby, pageNo, pagesize)
    
    @ring0
    def ReadUser(self,identy):
        return UserDBImpl.instance().read_record(identy)
    
    @ring8
    def Login(self,username,password):
        query = {"name":username}
        rlt = UserDBImpl.instance().read_record_list(query)
        if not rlt.success or len(rlt.content) == 0:
            return Result(username,NO_SUCH_USER_ERR,"No such User")
        
        user = rlt.content[0]
        if user["password"] != password:
            return Result(username,INVALID_PASSWORD_ERR,"Password is invalid")
        
        token = ConsoleAuthen.instance().create_token(user)
        token["hypervisor"] = "xcp"
        
        return Result(token)
    
    @ring0
    def Logout(self,access_uuid):
        return ConsoleAuthen.instance().remove_token(access_uuid)
    
    @ring0
    def SetPassword(self,username,old_word,new_word):
        query = {"name":username}
        rlt = UserDBImpl.instance().read_record_list(query)
        if not rlt.success or len(rlt.content) == 0:
            return Result(username,NO_SUCH_USER_ERR,"No such User")
        
        user = rlt.content[0]
        if user["password"] != old_word:
            return Result(username,INVALID_PASSWORD_ERR,"Password is invalid")
        return UserDBImpl.instance().update({ID:user[ID]},{"password":new_word})
    @ring0
    def ReadUserInfo(self,username):
        query = {"name":username}
        rlt = UserDBImpl.instance().read_record_list(query)
        if not rlt.success or len(rlt.content) == 0:
            return Result(username,NO_SUCH_USER_ERR,"No such User")
        
        user = rlt.content[0]
        del user["password"]
        del user["access_key"]
        return Result(user)
        
        
        
        
    
    
    