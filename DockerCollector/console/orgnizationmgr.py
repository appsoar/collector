# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
from common.util import Result
from frame.authen import ring0, ring8
from frame.errcode import NO_SUCH_USER_ERR
from mongodb.dbutil import Condition4Page
from mongoimpl.consoledb.userdbimpl import UserDBImpl


_ALL = "All"

class OrgnizationMgr(object):
    def __init__(self):
        pass
    
    @ring0
    @ring8
    @Condition4Page
    def getOrgnizationPage(self,filterObj, orderby ,pageNo,pagesize):
        if "name" in filterObj:
            filterObj["name"]={'$regex':filterObj["name"].strip()}
        return UserDBImpl.instance().read_record_page(filterObj, orderby, pageNo, pagesize)
    
    @ring0
    @ring8
    def ReadOrgnization(self,identy):
        return UserDBImpl.instance().read_record(identy)
    
    
    @ring0
    @ring8
    def ReadOrgnizationInfo(self,username):
        query = {"name":username}
        rlt = UserDBImpl.instance().read_record_list(query)
        if not rlt.success or len(rlt.content) == 0:
            return Result(username,NO_SUCH_USER_ERR,"No such User")
        
        user = rlt.content[0]
        del user["password"]
        del user["access_key"]
        return Result(user)
        
        
        
        
    
    
    