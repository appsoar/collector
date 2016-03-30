# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
from common.util import Result
from console.taskmgr import TREE_DEFINE
from frame.ajaxresource import PAGE, LIST, TREE
from frame.authen import ring8
from frame.errcode import NO_IMPLEMENT_INTERFACE_ERR
from mongodb.dbconst import MAIN_DB_NAME
from mongodb.extdbimpl import ExtDBImpl


_ALL = "All"

class RegistryMgr(object):
    db = MAIN_DB_NAME
    
    def __init__(self):
        pass
    
    @ring8
    def Read(self, cn, tag, operation=None):
        dbmgr = ExtDBImpl(self.db,cn)
        
        if operation is None:
            return dbmgr.read_info(tag)
        elif tag == PAGE:
            return dbmgr.ext_read_page(operation)
        elif tag == LIST:
            return dbmgr.ext_read_list(operation)
        elif tag == TREE:
            if cn in TREE_DEFINE:
                return dbmgr.ext_read_tree(operation, TREE_DEFINE[cn])
            return Result('NetWorkMgr.read',NO_IMPLEMENT_INTERFACE_ERR,"The collection no implement the tree interface.")
        else:
            return dbmgr.ext_read_info(operation)
            

    
    @ring8    
    def Update(self,cn,tag,operation):
        dbmgr = ExtDBImpl(self.db,cn)
        return dbmgr.ext_update(operation)
    
    @ring8
    def Delete(self,cn,tag,operation):
        dbmgr = ExtDBImpl(self.db,cn)
        return dbmgr.ext_delete(operation)
    
    @ring8
    def Save(self,cn,tag,data):
        dbmgr = ExtDBImpl(self.db,cn)
        return dbmgr.create(data)
        
        
        
    @ring8
    def ReadRequestInfo(self, cn,tag,data):
        return Result({'url':'/API','method':'GET'})
    
    
    