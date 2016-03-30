# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.


import datetime
import random
import string

from common.util import Result, CResult, PageResult
from frame.Logger import Log, PrintStack
from frame.errcode import DATABASE_EXCEPT_ERR, NO_SUCH_RECORD_ERR, FAIL
from mongodb.dbconst import ID, IDENTITY_TABLE
from mongodb.dbmgr import DBMgr


class DBBase(object):
    NOT_EQUAL        = "$ne"
    GRATER           = "$gt"
    GRATER_OR_EQUAL  = "$gte"
    LESS             = "$lt"
    LESS_OR_EQUAL    = "$lte"
    LIKE             = "$regex"
    IN               = "$in" 
    NOT_IN           = "$nin"
    
    def __init__(self,db,collection,dbMgr=None):
        self.db = db
        self.cn = collection
        self.dbmgr = dbMgr or DBMgr.instance()
    
    def exec_db_script(self,script_name,*params):
        try:        
            result = self.dbmgr.db_exec(self.db,script_name,*params)
        except Exception, e:
            Log(1,"DBBase.exec_db_script fail,as [%s]"%str(e))
            return Result("inner error",DATABASE_EXCEPT_ERR,str(e))
        else:
            return CResult(result)
        
        
    def read_record(self,identy, **kwargs):
        try:            
            rlt = self.dbmgr.get_records(self.db, self.cn, {ID:identy}, **kwargs)
        except Exception,e:
            Log(1,"DBBase.ReadRecord fail [%s]"%str(e))
            return Result(identy,DATABASE_EXCEPT_ERR,str(e))
        else:
            if len(rlt) > 0:
                return Result(rlt[0])
            return Result(rlt,NO_SUCH_RECORD_ERR)
        
    def read_record_list(self, query = None, **kwargs):
        arr = []
        try:
            if query is None:                
                arr = self.dbmgr.get_all_record(self.db,self.cn, **kwargs)
            else:
                arr = self.dbmgr.get_records(self.db, self.cn, query, **kwargs)
        except Exception,e:            
            Log(1,"DBBase.read_record_list [%s.%s] fail [%s]"%(self.db,self.cn,str(e)))
            return Result(str(query),DATABASE_EXCEPT_ERR,str(e))
        else:
            return Result(arr)
        
    def read_record_data(self,query, **kwargs):
        try:            
            rlt = self.dbmgr.get_records(self.db, self.cn, query, **kwargs)
        except Exception,e:
            Log(1,"DBBase.read_record_info fail [%s]"%str(e))
            return Result("",DATABASE_EXCEPT_ERR,str(e))
        else:
            if len(rlt) > 0:
                return Result(rlt[0])
            return Result(rlt,NO_SUCH_RECORD_ERR)
    
    def read_record_page(self,query,orderby,pageNo,page_size,**kwargs):
        try:
            arr,count = self.dbmgr.get_record_page(self.db,self.cn, query, orderby, pageNo, page_size, **kwargs)
        except Exception,e:
            PrintStack()
            Log(1,"DBBase.read_record_page fail as [%s]"%(str(e)))
            return Result(str(query),DATABASE_EXCEPT_ERR,str(e))
        else:
            return Result(PageResult(arr,count))
        
    def read_all_record_page(self,orderby,pageNo,page_size, **kwargs):
        try:
            arr,count = self.dbmgr.get_all_record_page(self.db,self.cn, orderby, pageNo, page_size, **kwargs)
        except Exception,e:
            Log(1,"DBBase.read_record_page fail as [%s]"%(str(e)))
            return Result(0,DATABASE_EXCEPT_ERR,str(e))
        else:
            return Result(PageResult(arr,count))
        
    def read_next_id(self, step=1):
        try:
            r = self.dbmgr.getID(self.db,IDENTITY_TABLE, {"_id":self.cn},{"next":step})
            _id = r.get('next', 0)
        except Exception,e:
            Log(1,"Get id fail as [%s]"%(str(e)))
            return Result("",FAIL,"Get id fail as [%s]"%(str(e)))
        else:
            return Result(_id)
           
    def update(self,query,value,upsert=False):
        try:            
            rlt = self.dbmgr.find_and_modify(self.db,self.cn, query,value,upsert)
        except Exception,e:
            Log(1,"DBBase.update fail [%s]"%str(e))
            return Result(str(query),DATABASE_EXCEPT_ERR,str(e))
        else:
            if rlt and ID in rlt:
                return Result(rlt[ID])
            else:
                return Result(rlt,NO_SUCH_RECORD_ERR,"No such record.")
            
    def updates(self,query,value):
        try:
            rlt = self.dbmgr.update_records(self.db,self.cn, query,value)
        except Exception,e:
            Log(1,"DBBase.updates fail [%s]"%str(e))
            return Result(str(query),DATABASE_EXCEPT_ERR,str(e))
        else:
            return Result(rlt)
            
    def replace(self,query,value):
        try:            
            self.dbmgr.update_record(self.db,self.cn,query, value)
        except Exception,e:
            Log(1,"DBBase.replace fail [%s]"%str(e))
            return Result(str(query),DATABASE_EXCEPT_ERR,str(e))
        else:
            return Result("success")
            
            
            
    def create(self,nodeObj):
        rlt = self.read_next_id()
        if rlt.success:
            nodeObj[ID] = rlt.content
        else:
            return rlt
        
        try:
            ret = self.dbmgr.insert_record(self.db,self.cn,nodeObj)
            if ret == rlt.content:
                return Result(ret)
            else:
                return Result(ret,FAIL)
        except Exception,e:
            Log(1,"DBBase.create_record fail [%s]"%str(e))
            return Result("DBBase.create",DATABASE_EXCEPT_ERR,str(e))
        
        
    def remove(self,_filter):
        try:
            ret = self.dbmgr.delete_record(self.db,self.cn,_filter)
            if ret and ret["n"] > 0:
                return Result(ret["n"])
            else:
                return Result(ret,NO_SUCH_RECORD_ERR)
        except Exception,e:
            Log(1,"DBBase.remove_record fail [%s]"%str(e))
            return Result(ret,DATABASE_EXCEPT_ERR,str(e))
        
    def save(self,record):
        if ID in record:
            _id = record.pop(ID)
            return self.update({ID:_id},record)
        else:
            return self.create(record)
        
    def insert(self,record):
        try:
            ret = self.dbmgr.insert_record(self.db,self.cn,record)
        except Exception,e:
            Log(1,"DBBase.insert fail [%s]"%str(e))
            return Result(str(record),DATABASE_EXCEPT_ERR,"DBBase.insert fail [%s]"%str(e))
        else:
            return Result(ret)
        
    def batch_insert(self, record_list):
        if ID not in record_list[0]:
            rlt = self.read_next_id(len(record_list))
            if not rlt.success:
                Log(1,"batch_insert.read_next_id fail [%s]"%str(rlt.message))
                return rlt
            
            _id = rlt.content
            for record in record_list:
                record[ID] = _id
                _id += 1

        try:
            ret = self.dbmgr.insert_records(self.db,self.cn,record_list)
        except Exception,e:
            Log(1,"DBBase.batch_insert fail [%s]"%str(e))
            return Result(len(record_list),DATABASE_EXCEPT_ERR,"DBBase.batch_insert fail [%s]"%str(e))
        else:
            return Result(len(ret))
        
    def count(self,query):
        try:
            count = self.dbmgr.get_record_count(self.db,self.cn,query)
        except Exception,e:
            Log(1,"DBBase.count fail [%s]"%str(e))
            return Result("",DATABASE_EXCEPT_ERR,"DBBase.check_exist fail [%s]"%str(e))
        else:
            return Result(count)
        
    def get_record_id(self,prefix=""):
        """
        # 精确到秒,添加4位随机字符避免出现重复
        # eg：CT20130110173453609abcd
        """   
        letter = ''.join(random.sample(string.ascii_letters + string.digits, 4))
        return "%s%s%s"%(prefix,datetime.datetime.now().strftime("%Y%m%d%H%M%S"),letter)
    
    
    def find_and_modify_num(self,query,value,upsert=False):
        try:
            count = self.dbmgr.find_and_modify_num(self.db,self.cn,query,value,upsert)
        except Exception,e:
            Log(1,"DBBase.find_and_modify_num fail [%s]"%str(e))
            return Result("",DATABASE_EXCEPT_ERR,"DBBase.find_and_modify_num fail [%s]"%str(e))
        else:
            return Result(count)
            
    def is_exist(self, query):
        rlt = self.count(query)
        if not rlt.success:
            Log(1,'DBBase.is_exist return fail,as[%s]'%(rlt.message))
            return False
            
        if rlt.success and rlt.content > 0:
            return True
        return False    
        