#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

"""
initialize database ,create table and insert some system info
"""
#reload(sys)
#sys.setdefaultencoding('utf-8')

import codecs
import os
import shutil

from frame.Logger import SysLog
from mongodb.dbconst import MAIN_DB_NAME, USER_TABLE, CONFIG_TABLE
from mongodb.dbmgr import DBMgr


class CommonDB(object):
    db = ""
    def __init__(self,db_name):
        self.db = db_name

    def insert_resord(self,cn,record): 
        return DBMgr.instance().insert_records(self.db,cn,record)
    
    def read_all_record(self,cn):
        return DBMgr.instance().get_all_record(self.db,cn)
    
    def exporttofile(self,cn,recover):
        arr = self.read_all_record(cn)
        output = "data['%s'] = ["%(cn)
        for r in arr:
            txt = '{"_id":%s,"ParentKey":"%s","TagName":"%s","TagNameEn":"%s","Weights":"%s","GroupName":"%s","HasChildren":"%s","Remark":"%s","CreateDate":date_now()},\n'\
            %(r["_id"],r["ParentKey"],r["TagName"],r["TagNameEn"],r["Weights"],r["GroupName"],r["HasChildren"],r["Remark"])
            output += txt
        if output[-1] == "," or output[-2] == ",":
            output = output[0:-2]
        output += "]\n\n\n" 
        fileName = "%s.py"%(self.db)
            
        self.SaveFile(output,fileName,recover)
        
    def export_js_column(self,cn,recover):
        arr = self.read_all_record(cn)
        output = "data['%s'] = ["%(cn)
        for r in arr:
            Binding = ""
            if "Binding" in r:
                Binding = r["Binding"]
            BindingSchema = ""
            if "BindingSchema" in r:
                BindingSchema = r["BindingSchema"]
                
            ColumnTitle = ""
            if "ColumnTitle" in r:
                ColumnTitle = r["ColumnTitle"]
            
            txt = '{"_id": %s, "TableID": "%s","ColumnXtype": "%s", "BindingSchema": "%s","Binding": "%s","ColumnTitle": "%s","Size": "%s","DefaultValue": "%s", "PrimaryKey": "%s", "ColumnName": "%s", "ColumnDescription": "%s", "Hidden": "%s", "NativeType": "%s", "AllowEmpty": "%s", "Example": "%s", "Size": "%s"},\n'\
            %(r["_id"],r["TableID"],r["ColumnXtype"],BindingSchema,Binding,ColumnTitle,r["Size"],r["DefaultValue"].replace("\"", "\'"),r["PrimaryKey"],r["ColumnName"],r["ColumnDescription"].replace("\"", "\'"),r["Hidden"],r["NativeType"],r["AllowEmpty"],r["Example"].replace("\"", "\'"),r["Size"])
            output += txt
        if output[-1] == "," or output[-2] == ",":
            output = output[0:-2]
        output += "]\n\n\n" 
        fileName = "%s_new.py"%(self.db)
        self.SaveFile(output,fileName,recover)
        
        
    def export_PduType(self,cn,recover):
        arr = self.read_all_record(cn)
        output = "\n\n\ndata['%s'] = ["%(cn)
        for r in arr:
            txt = '{"_id": "%s","type_id": "%s","parent_type": "%s","type_name": "%s","alias": "%s","status": "%s", "version": "%s", "type_desc": "%s", "last_modify_time": "%s", "create_time": "%s", "atomic": "%s",  "rely_type": "%s"},\n'\
            %(r["_id"],r["type_id"],r["parent_type"],r["type_name"],r["alias"],r["status"],r["version"],r["type_desc"],r["last_modify_time"],r["create_time"],r["atomic"],r["rely_type"])
            output += txt
        if output[-1] == "," or output[-2] == ",":
            output = output[0:-2]
        output += "]\n\n\n" 
        fileName = "%s_new.py"%(self.db)
            
        self.SaveFile(output,fileName,recover)
        
    def to_string(self,data):
        txt = "{"
        for k,v in data.iteritems():
            txt += '"%s":"%s",'%(str(k),str(v))
        
        if len(txt) > 2:
            txt = txt[0:-1]
        txt += "},\n"
        return txt
        
    def parst_data(self,cn):
        arr = self.read_all_record(cn)
        output = "\ndata['%s'] = ["%(cn)
        for r in arr:
            output += self.to_string(r)
        if output[-1] == "," or output[-2] == ",":
            output = output[0:-2]
        output += "]\n\n" 
        
        return output
        
    def export_to_file(self,cn,recover):
        output = self.parst_data(cn)
        fileName = "%s_new.py"%(self.db)            
        self.SaveFile(output,fileName,recover)           
        
            
    def SaveFile(self,text,fileName,recover=False):
        workroot = os.path.dirname(os.path.abspath(__file__))
        export_folder = os.path.join(workroot,"Export")
        if not os.path.isdir(export_folder):
            os.mkdir(export_folder)
        
        fullpath = os.path.join(export_folder,fileName)
        if not os.path.isfile(fullpath):
            fullpath = self.get_tmp_file(export_folder,fileName)
        if not os.path.isfile(fullpath):           
            SysLog(1,"move file fail")
            return
        fd = codecs.open(fullpath,'a','utf-8')
        fd.write(text.decode('utf-8'))
        fd.close()
        
    def get_tmp_file(self,tar_dir,filename):
        workroot = os.path.dirname(os.path.abspath(__file__))
        fullpath = os.path.join(workroot,"temp.py")
        
        tarpath = os.path.join(workroot,tar_dir)
        tarfile = os.path.join(tarpath,filename)
        shutil.copyfile(fullpath, tarfile)
        return tarfile
    
def ExportData():
    db = CommonDB(MAIN_DB_NAME)
    db.export_to_file(USER_TABLE, True)
    db.export_to_file(CONFIG_TABLE, True)


def main():
    ret = DBMgr.instance().isDBRuning()
    if not ret:
        SysLog(1,"setup Collector fail,database error")
        return 0
    
    ExportData()


    
if __name__ == '__main__':
    main()
