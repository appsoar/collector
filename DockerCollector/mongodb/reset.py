#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

from frame.Logger import SysLog
from mongodb import dbconst
from mongodb.dbconst import MAIN_DB_NAME, TASK_TABLE, SUB_TASK_TABLE, SYNCTASK
from mongodb.dbmgr import DBMgr
from mongodb.install import CommonDB
import getopt
import sys

"""
initialize database ,create table and insert some system info
"""

        

Tables = {
    TASK_TABLE:"CMO",

}

def main():
    ret = DBMgr.instance().isDBRuning()
    if not ret:
        SysLog(1,"setup fail,database error")
        return 0
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ch", ["clean","help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    if not len(opts):
        cleanSystem()
        sys.exit()
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c","--clean"):
            cleanSystem()
            sys.exit()
        


def usage():
    print "-h  --help  show help"
    print "python reset.py -c  [clean run time data.]"
    print "python reset.py -h  [show help]"
    
def resetSystem():
    cloud_db = CommonDB(MAIN_DB_NAME,{})
    cloud_db.setup()
    
    
def cleanSystem():
    table_list = [TASK_TABLE,
                  SUB_TASK_TABLE,
                  SYNCTASK,
                  dbconst.SCHEDULE_TABLE,
                  "jobs"]
    cloud_db = CommonDB(MAIN_DB_NAME,{})
    cloud_db.clean_data(table_list)
    
    # 清除subnet中的非初始数据
    DBMgr.instance().delete_record(MAIN_DB_NAME,TASK_TABLE,{"user_id": {"$ne":"system"}}) 


if __name__ == '__main__':
    main()
    
    

