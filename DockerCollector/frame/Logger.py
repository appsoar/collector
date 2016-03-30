# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

"""
Implement the log manage
"""

from frame.errcode import FILE_OPERATE_ERR
from frame.exception import InternalException
from logging import handlers
import logging.config
import os
import threading
import time
import traceback

class Logger(object):
    '''
    classdocs
    '''
    __lock = threading.Lock()
    operlogger = None
    syslogger = None
    stack_file = None
    
    @classmethod
    def instance(cls):
        '''
        Limits application to single instance
        '''
        Logger.__lock.acquire()
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        Logger.__lock.release()
        return cls._instance
    

    def __init__(self):
        '''
        Constructor
        '''
        logging.basicConfig(level=logging.DEBUG)
        configpath = self.get_config_path()
        self.workdir = self.get_workdir()
        self.init_stack_file()
        if os.path.isfile(configpath):
            self.init_with_config(configpath)
        else:
            self.init_default()
            
    def init_stack_file(self):
        file_path = os.path.join(self.workdir,"exception.log")
        if not os.path.isfile(file_path):
            try:
                f = open(file_path,"a")
                f.close()
            except Exception,e:
                Log(1,"init_stack_file fail,as[%s]"%str(e))
                return
        
        Logger.stack_file = file_path
        
  
    def init_default(self):
        try:
            Logger.syslogger = self.get_logger("system", self.workdir)
            Logger.operlogger = self.get_logger("operation", self.workdir)
        except Exception,e:
            traceback.print_exc()
            raise InternalException("init_default fail as[%s]"%(str(e)))
        
    def init_with_config(self,config_path):
        try:
            logging.config.fileConfig(config_path)
            Logger.operlogger = logging.getLogger("operation")
            Logger.syslogger = logging.getLogger("system")
        except Exception,e:
            traceback.print_exc()
            raise InternalException("init_with_config fail as[%s]"%(str(e)))
        
    def get_config_path(self):
        workdir = os.path.abspath('.')
        workdir = os.path.join(workdir,"frame")
        workdir = os.path.join(workdir,"conf")
        return os.path.join(workdir,"log.conf")

    def get_workdir(self):
        workdir = os.path.abspath('.')
        workdir = os.path.join(workdir,"Trace")
        workdir = os.path.join(workdir,"logs")
        if not os.path.isdir(workdir):
            os.makedirs(workdir)
        return workdir
        
    def get_logger(self,logger_name,log_home,**args):
        log_name = args.get('log_name', "%s.log"%(logger_name))
        log_level = args.get('log_level', logging.DEBUG)
        log_size = args.get('log_size', 10240000)
        backupcount = args.get('backupcount', 10)
        
        log_path = os.path.join(log_home,log_name)        
        if not os.path.isfile(log_path):
            try:
                f = open(log_path,"a")
                f.close()
            except Exception,e:
                traceback.print_exc()
                raise InternalException("init logging fail: "+str(e),FILE_OPERATE_ERR)
        
        formatter = logging.Formatter("%(asctime)-15s %(levelname)s [%(process)d-%(thread)d] %(message)s")
        handler = handlers.RotatingFileHandler(log_path,"a",log_size,backupcount)
        handler.setFormatter(formatter)
    
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        logger.setLevel(log_level)
        return logger
        
    
        
    def updateConfig(self,cfginfo):
        '''
        update the logging configuration section
        @param cfginfo:
        @type cfginfo:schema_conf__logging
        @todo: Do more checking of the input; 
        '''
        for key in  cfginfo.keys():
            if key in self.configure and type(self.configure[key]) == type(1):
                cfginfo[key] = int(cfginfo[key])
        self.configure.update(cfginfo)
        return "success"
    
    def getConfig(self):
        return self.configure
    
    def getOperationLog(self):
        if not os.path.exists(self.configure["operation_log"]):
            raise InternalException("operation log file does not exist",FILE_OPERATE_ERR)
        logs = open(self.configure["operation_log"]).readlines()
        return logs
    
    def getSystemLog(self):
        if not os.path.exists(self.configure["system_log"]):
            raise InternalException("operation log file does not exist",FILE_OPERATE_ERR)
        logs = open(self.configure["system_log"]).readlines()
        return logs
    
    @classmethod    
    def SysError(cls,level,msg):
        if level == 1:
            cls.syslogger.error(msg)
        elif level == 2:
            cls.syslogger.warn(msg)
        elif level == 3:
            cls.syslogger.info(msg)
        elif level == 4:
            cls.syslogger.debug(msg)
        elif level == 5:
            cls.syslogger.exception(msg)
        else:
            cls.syslogger.info(msg)
            
    @classmethod    
    def OperError(cls,level,msg):
        if level == 1:
            cls.operlogger.error(msg)
        elif level == 2:
            cls.operlogger.warn(msg)
        elif level == 3:
            cls.operlogger.info(msg)
        elif level == 4:
            cls.operlogger.debug(msg)
        elif level == 5:
            cls.operlogger.exception(msg)
        else:
            cls.operlogger.info(msg)
            
def Log(level,msg):
    Logger.OperError(level,msg)
    
def SysLog(level,msg):
    Logger.SysError(level,msg)



class FileGuard(object):
    def __init__(self, filename,mode):
        self.mode = mode
        self.filename = filename
        self.f = None

    def __enter__(self):
        try:
            self.f = open(self.filename, self.mode)
            return self.f
        except IOError:
            #print str(e)
            return None

    def __exit__(self, _type, value, traceback):
        if self.f:
            self.f.close()
            #print str(_type), str(value), str(traceback)	
    
def PrintStack():
    if not Logger.stack_file:
        return
    with FileGuard(Logger.stack_file,"a") as stream:
        stream.writelines(["\n",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),"\n","-" * 100,"\n"]) 
        traceback.print_exc(None,stream)
        stream.flush()
           
Logger.instance()
