#!/usr/sbin/python
# -*- coding: utf-8 -*-
'''
## Copyright (C) 2012-2013 The PowerallNetworks
## See LICENSE for details
'''


import os

from twisted.internet import reactor
from twisted.python import log, threadable
from twisted.python.logfile import DailyLogFile
from twisted.web import server
from core.server import WebService
from frame.Logger import PrintStack
from frame.configmgr import GetSysConfigInt


second = 0

def monitoring(): 
    global second
    second += 10
    log.msg('system running <%d> second'%second)
    reactor.callLater(10,monitoring) 

def main():   
    reactor.suggestThreadPoolSize(100)
    threadable.init(1)   # 设置线程安全
    workroot = os.path.dirname(os.path.abspath(__file__))
    logdir = os.path.join(workroot,"Trace")
    logdir = os.path.join(logdir,"twisted")
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    log_file = DailyLogFile("server.log", logdir)
    log.startLogging(log_file)
    webserver = WebService(workroot)
    port = GetSysConfigInt("server_port",8080)
    reactor.listenTCP(port, server.Site(webserver.get_resource()))
    reactor.callLater(10,monitoring) 
    reactor.run()
    


if __name__ == '__main__':
    try:
        main()
    except Exception:
        PrintStack()


