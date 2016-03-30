# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
"""
实现数据库的连接，查询，等功能
"""

import os
import platform
import subprocess
import threading
import time

from pymongo.errors import AutoReconnect
from pymongo.mongo_client import MongoClient

from common.guard import LockGuard
from frame.Logger import Log, PrintStack
from frame.configmgr import GetSysConfigInt, GetSysConfig
from mongodb.dbconst import ID


def lost_connection_retry(func):
    def wappedFun(*args,**kwargs):
        try:
            result = func(*args,**kwargs)
        except AutoReconnect:
            dbmgr = args[0]
            getattr(dbmgr,"autoConnect")
            result = func(*args,**kwargs)
        return result
    return wappedFun


class DBMgr(object):
    __lock = threading.Lock()

    @classmethod
    def instance(cls):
        '''
        Limits application to single instance
        '''
        with LockGuard(cls.__lock):
            if not hasattr(cls, "_instance"):
                cls._instance = cls()
        
        if not cls._instance.isDBRuning():
            cls._instance.startDBserver()
        
        return cls._instance

    def __init__(self,db_host=None,db_port=None):
        self.conn = None
        self.port = db_port or GetSysConfigInt("db_port",27017)
        self.host = db_host or GetSysConfig("db_host")
        self.osname = None
        try:
            self.conn = MongoClient(self.host, self.port)
        except Exception,e:
            PrintStack()
            Log(1,"connect to Mongdb fail,as[%s]"%(str(e)))
        else:
            Log(3,"Connect to db success.")
        
    def autoConnect(self):
        self.conn = MongoClient(self.host, self.port)
        
    def init_db_config(self):
        if self.osname :
            return True
            
        self.db_work_path = GetSysConfig("db_work_path")
        self.DBConfPath = os.path.join(self.db_work_path,"conf")
        self.MongoPath = GetSysConfig("mongo_db_path")
        osname = platform.system()
        if osname == "Windows":
            self.DBConfPath = os.path.join(self.DBConfPath,"mongodb.conf") 
            self.shell = False
        else:
            self.DBConfPath = os.path.join(self.DBConfPath,"mongodb_linux.conf") 
            self.shell = True
            
        if not os.path.isfile(self.MongoPath):
            Log(1,"startDBserver fail,as[The mongo file not exist.]")
            return False
            
        if not os.path.isfile(self.DBConfPath):
            Log(1,"startDBserver fail,as[The mongo config file not exist.]")
            return False
        
        self.osname = osname
        return True
    
    def db_auto_check(self):
        while True:
            try:
                if not self.isDBRuning():
                    self.startDBserver()
            except:
                PrintStack()
                
            time.sleep(30)

    def init(self):
        '''
        initialize instance,and start database server
        '''
        t = threading.Thread(target=self.db_auto_check,name="db_auto_check")
        t.setDaemon(True)
        t.start()
        

    def startDBserver(self):
        '''
        startDBserver,wait 3 second for check server status
        '''
        
        if self.host not in ["127.0.0.1","localhost"]:
            Log(1,"Can not start the MongoDB server[%s]"%(self.host))
            return False
    
        if not self.init_db_config():
            Log(1,"startDBserver load MongoDB config fail.")
            return False            
            
        cmd = "%s --config %s"%(self.MongoPath,self.DBConfPath)
        print cmd
        try:
            if self.osname == "Windows":
                subPrc = subprocess.Popen(cmd,shell=self.shell, cwd=self.db_work_path)
            else:#必须加上close_fds=True，否则子进程会一直存在
                subPrc = subprocess.Popen(cmd,shell=self.shell, cwd=self.db_work_path,close_fds=True)
        except Exception,e:
            print str(e)
            return False
        else:
            # wait for 10 second,
            sec = 10
            while sec :
                code = subPrc.poll()
                if code:
                    return False
                elif self.isDBRuning():
                    break;
                sec -= 1
                time.sleep(1)
            return True


    def isDBRuning(self):
        '''
        try to connect to mongo server
        '''
        try:
            if self.conn is None:
                self.conn = MongoClient(self.host, self.port)
            self.conn.server_info()
        except Exception,e:
            Log(1,"Get mongodb server info fail,as[%s]"%(str(e)))
            return False
        else:
            return True

        
    
    def get_all_table(self):
        return self.conn.database_names()
    
    def drop_db(self,db_name):
        return self.conn.drop_database(db_name)

    def insert_record(self,db,collection,record):
        '''
        @record :{'key1':'value1',...}
        '''
        return self.conn[db][collection].save(record,True,True)
    
    def insert_records(self,db,collection,records):
        '''
        @record :{'key1':'value1',...}
        '''
        return self.conn[db][collection].insert(records)

    def get_collection(self,db,collection):
        return self.conn[db][collection]
    
    def get_records(self,db,collection, query, **kwargs):
        result = self.conn[db][collection].find(query, **kwargs)
        arr = []
        for i in result:
            arr.append(i)
        return arr
    
    def get_record_page(self,db,collection,query,orderby,pageNo,page_size, **kwargs):
        result = None
        count = self.conn[db][collection].find(query, **kwargs).count()
    
        if count < page_size:
            result =  self.conn[db][collection].find(query, **kwargs).sort(orderby.items())
        elif pageNo <= 1:
            result = self.conn[db][collection].find(query, **kwargs).sort(orderby.items()).limit(page_size)
        else:
            skip_count = (pageNo - 1) * page_size
            result = self.conn[db][collection].find(query, **kwargs).sort(orderby.items()).skip(skip_count).limit(page_size)
            
        arr = []
        for i in result:
            arr.append(i)        
            
        return arr,count

    def get_all_record(self,db,collection,**kwargs):
        arr = []
        for i in self.conn[db][collection].find(**kwargs):
            #del i[ID]
            arr.append(i)
        return arr 
    
    def get_all_records_sort(self,db,collection,sort_list, **kwargs):
        records = []
        result = self.conn[db][collection].find(**kwargs).sort(sort_list)
       
        for ret in result:
            records.append(ret)
        return records
    
    def get_record_count(self,db,collection,query=None):
        if query:
            return self.conn[db][collection].find(query).count()
        return self.conn[db][collection].count()
    
    def get_all_record_page(self,db,collection,orderby,pageNo,page_size, **kwargs):
        result = None
        count = self.conn[db][collection].count()
        if count < page_size:
            result =  self.conn[db][collection].find(**kwargs).sort(orderby.items())
        elif pageNo <= 1:
            result = self.conn[db][collection].find(**kwargs).sort(orderby.items()).limit(page_size)
        else:
            skip_count = (pageNo - 1) * page_size
            result = self.conn[db][collection].find(**kwargs).sort(orderby.items()).skip(skip_count).limit(page_size)
            
        arr = []
        for i in result:
            arr.append(i)
        return arr,count

    def delete_record(self,db,collection,_filter):
        return self.conn[db][collection].remove(_filter,True)

    def update_record(self,db,collection,query,value):
        return self.conn[db][collection].update(query,value)
    
    def update_records(self,db,collection,query,value):
        return self.conn[db][collection].update(query,{"$set":value},False,False,False,True)

    def find_and_modify(self,db,collection,query,value,upsert=False):
        return self.conn[db][collection].find_one_and_update(query,{'$set':value},upsert=upsert)

    
    def remove_all(self,db,collection):
        return self.conn[db][collection].remove(None,True)
    
    def getID(self,db,collection,query,step):
        return self.conn[db][collection].find_one_and_update(query,{"$inc":step},upsert=True)
    
    def find_and_modify_num(self,db,collection,query,value,upsert=False):
        return self.conn[db][collection].find_one_and_update(query,{'$inc':value}, upsert=upsert)
    
    def create_js(self,db,func_name,func_body):
        self.del_js(db,func_name)
        func_str = 'self.conn[db].system_js.%s="""%s"""'%(func_name,func_body)
        exec(func_str)
        return True
        
    def check_func_exist(self,db,func_name):
        count = self.conn[db].system.js.find({ID: func_name}).count()
        return 1 == count
    
    def db_exec(self,db,func_name,*args):
        if self.check_func_exist(db, func_name):
            func_str = "self.conn[db].system_js.%s(*args)"%(func_name)
            result = eval(func_str)
            return result
        else:
            return False
    
    def del_js(self,db,func_name):
        func_str = "del self.conn[db].system_js.%s"%(func_name)
        exec(func_str)
        return True

    
    
    ## ------define for configure which must save in database --------------------
    ## ------configure begin
    
    def insert_record_by_key(self,key,value):
        arr = key.split('.')
        if len(arr) <= 2:
            return False
        return self.insert_record(arr[0],arr[1],{'key':key,'value':value})
    
    def update_record_by_key(self,key,value):
        arr = key.split('.')
        if len(arr) <= 2:
            return False
        keymap = {}
        if isinstance(value,dict):
            for k,v in value.iteritems():
                keymap["value." + k] = v
        else:
            keymap["value"] = value

        return self.update_record(arr[0],arr[1],{'key':key},keymap)
    
    def get_records_by_key(self,key):
        '''
        return a record list
        '''
        arr = key.split('.')
        if len(arr) <= 2:
            return False
        arr = self.get_records(arr[0],arr[1],{'key':key})
        if len(arr) >0:
            return arr[0]["value"]
    
    def remove_all_by_key(self,key):
        arr = key.split('.')
        if len(arr) < 2:
            return False
        return self.conn[arr[0]][arr[1]].remove(None,True)
    
    def delete_record_by_key(self,key):
        '''
        delete record,call it like this delete_record("db.collection.key")
        '''
        arr = key.split('.')
        if len(arr) <= 2:
            return False
        return self.delete_record(arr[0],arr[1],{'key':key})
    
    ## ------configure end
DBMgr.instance().init()


        
