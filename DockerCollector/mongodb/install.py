#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

"""
initialize database ,create table and insert some system info
"""

import getopt
import imp
import os
import sys

from frame.Logger import SysLog
from mongodb.dbconst import ID, MAIN_DB_NAME, CONFIG_TABLE, \
    USER_TABLE, IDENTITY_TABLE, USER_GROUP_TABLE, REPOSITORY_TABLE, \
    NAMESPACE_TABLE, COMMENT_TABLE, TAG_TABLE, IMAGE_TABLE, \
    LAYER_TABLE, GROUP_NAMESPACE_TABLE, NOTIFICATION_TABLE
from mongodb.dbmgr import DBMgr


class CommonDB(object):
    def __init__(self,db_name,tables):
        self.db = db_name
        self.table_list = tables
        self.dbMgr = DBMgr.instance()
        
    def init_identity_table(self,id_key = None):
        if id_key is None:
            id_key = self.db
                    
        try:            
            arr = self.dbMgr.get_all_record(self.db,IDENTITY_TABLE)
            if len(arr) < 1:
                raise Exception("no record")
        except Exception,e:                   
            SysLog(1,"CommonDB.init_identity_table [%s], Create identity field,as [%s]"%(self.db,str(e)))
            self.add_identity_key(id_key)
        else:
            SysLog(1,"CommonDB.init_identity_table [%s] Create identity field success"%self.db)
            
    def clear_db(self):
        ret = True
        arr = self.dbMgr.get_all_table()
        if self.db in arr:
            try:
                self.dbMgr.drop_db(self.db)
            except Exception,e:
                SysLog(1,"CommonDB.init_db [%s] fail [%s]"%(self.db,str(e)))
                return False
                
        SysLog(1,"CommonDB.clear_db [%s], success"%self.db)
                
        return ret
    
    
    def clean_data(self,cn_list):
        for collection in cn_list:
            self.dbMgr.remove_all(self.db,collection)
    
    
    def add_identity_key(self,id_key,pre_txt = None):
        try:
            arr = self.dbMgr.get_records(self.db,IDENTITY_TABLE,{ID:id_key})
        except Exception,e:
            SysLog(1,"CommonDB.add_identity_key fail,[%s]"%str(e))
            return False
        else:
            if len(arr) > 0:
                return True
            
        record = {ID:id_key,"next":1000}
        if pre_txt is not None:
            record["pre"] = pre_txt
            
        try:
            self.dbMgr.insert_record(self.db,IDENTITY_TABLE,record)
        except Exception,e:
            SysLog(1,"CommonDB.add_identity_key fail,[%s]"%str(e))
            return False
        return True
    
    def del_identity_key(self,id_key):
        try:
            self.dbMgr.delete_record(self.db,IDENTITY_TABLE,{ID:id_key})
        except Exception,e:
            SysLog(1,"CommonDB.del_identity_key fail,[%s]"%str(e))
            return False
        return True

    def insert_record(self,cn,record): 
        return self.dbMgr.insert_records(self.db,cn,record)
    
    def insert_records(self,cn,records):
        for r in records:
            self.dbMgr.insert_record(self.db,cn,r)
        return len(records)
    
    def create_js(self,func_name,func_body):
        return self.dbMgr.create_js(self.db,func_name,func_body)
    
    def loadJs(self,file_path):    
        try:
            fd = open(file_path,"r")
            jsStr = fd.read()
            fd.close()
        except Exception,e:
            SysLog(1,"loadJs [%s] fail. as [%s]"%(file_path,str(e)))
            return False
        else:
            return jsStr
        
    def parse_js(self,js_str):
        index = js_str.find("function")
        if index == -1:
            return
        func_name = js_str[0:index]
        eIndex = func_name.find("=")
        if eIndex == -1:
            return 
        func_name = func_name[0:eIndex]
        
        func_body = js_str[index:]
        self.create_js(func_name.strip(), func_body)
        
    def auto_load_js(self):
        workdir = os.path.dirname(os.path.abspath(__file__))
        workdir = os.path.join(workdir,"javascript")
        workdir = os.path.join(workdir,self.db)
        dirs = os.listdir(workdir)
        for file_name in dirs:
            file_path = os.path.join(workdir,file_name)
            if os.path.isfile(file_path) and file_path.endswith(".js") :
                jsStr = self.loadJs(file_path)
                self.parse_js(jsStr)
            else:
                SysLog(3,"%s is not a js file"%file_path)
                
    def auto_import_data(self):
        workroot = os.path.dirname(os.path.abspath(__file__))
        datapath = os.path.join(workroot,"export")
        fullpath = os.path.join(datapath,"%s.py"%self.db)
        
        mod = self.load_from_file(fullpath)
        
        data = getattr(mod,"data",[])
        for t in data:
            ret = self.insert_records(t, data[t])
            SysLog(1,"CommonDB.auto_import_data success, insert [%d] record into %s"%(ret,t))
    
    def load_from_file(self,filepath):
        mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == '.py':
            py_module = imp.load_source(mod_name, filepath)
        elif file_ext.lower() == '.pyc':
            py_module = imp.load_compiled(mod_name, filepath)
                
        return py_module

    def setup(self):
        self.clear_db()
        self.init_identity_table()
        for table_name,prefix in self.table_list.iteritems():
            self.add_identity_key(table_name,prefix)
        self.auto_import_data()
        self.auto_load_js()
        

Tables = {
    CONFIG_TABLE:'CFG',                  # 存放支持修改的配置项    
    USER_TABLE:None,                     # 存放用户信息
    USER_GROUP_TABLE:None,               # 用户组
    REPOSITORY_TABLE:None,               # 仓库
    NAMESPACE_TABLE:None,                # 命名空间
    COMMENT_TABLE:None,                  # 评论 
    TAG_TABLE:None,                      # 标签
    IMAGE_TABLE:None,                    # 
    LAYER_TABLE:None,                    # 层 
    USER_GROUP_TABLE:None,               # 用户与组的关系表
    GROUP_NAMESPACE_TABLE:None,          # 用户组与命名空间的关系    
    NOTIFICATION_TABLE:None              # Registry 的通知消息
}



def main():
    ret = DBMgr.instance().isDBRuning()
    if not ret:
        SysLog(1,"setup fail,database error")
        return 0
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ilsh", ["install","loadData","loadScript","help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    if not len(opts):
        usage()
        sys.exit()
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i","--install"):
            install()
            sys.exit()
        elif opt in ("-l","--loadData"):
            loadData()
            sys.exit()
        elif opt in ("-s","--loadScript"):
            loadScript()
            sys.exit()
        


def usage():
    print "-h  --help  show help"
    print "python install.py -i  [new install,it will clear user data.]"
    print "python install.py -l  [reset the prepare data,won't delete user data.]"
    print "python install.py -h  [show help]"
    
def install():
    cloud_db = CommonDB(MAIN_DB_NAME,Tables)
    cloud_db.setup()
    
    
def loadData():
    cloud_db = CommonDB(MAIN_DB_NAME,{})
    cloud_db.auto_import_data()

def loadScript():
    cloud_db = CommonDB(MAIN_DB_NAME,{})
    cloud_db.auto_load_js()

if __name__ == '__main__':
    main()

