# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
from common.range import DigitRange, strRange

class SysConfig(object):
    RequestOffset    = DigitRange(30,5,300)        # 请求超前或滞后服务器时间的最大值.
    RequestTimeout   = DigitRange(30,30,60)        # 与云节点通信超时时间.
    XMLRPCPort       = DigitRange(8080,4000,65535) # 服务器XMLRPC服务的端口号.
    HeartInterval    = DigitRange(60,30,120)       # 与扩展节点心跳的时间间隔.
    LinkTestCount    = DigitRange(5,1,30)          # 云节点失去连接后，主动连接的次数.
    CMOSyncInterval  = DigitRange(30,10,480)       # 与扩展节点自动同步商品的时间间隔(分钟).
    #OperateTimeout   = DigitRange(60,30,1440)     # 同步操作超时时间(分钟).
    SessionTimeout   = DigitRange(60,10,720)       # 管理后台session超时时间(分钟).
    FactoryNum4Order = DigitRange(1,1,10)          # 处理（VOFS下达的）订单的线程的个数.
    FactoryNum4Operate = DigitRange(1,1,10)        # 处理（开机关机等操作）指令的线程的个数.
    CloudBootTimeout = DigitRange(15,10,60)        # cloudboot报告进度的超时时间(分钟).
    CheckStockInterval = DigitRange(3,1,60)        # 补货的间隔时间.
    CloudBootSign     = strRange("CloudBoot",1,60) # cloudBoot模板的标记.
    
    store = {
        "time_offset":RequestOffset,
        "request_timeout":RequestTimeout,
        "server_port":XMLRPCPort,
        "heart_interval":HeartInterval,
        "link_test_count":LinkTestCount,
        "cmo_sync_interval":CMOSyncInterval,
        "session_timeout":SessionTimeout,
        "factory_num_4_order":FactoryNum4Order,
        "factory_num_4_operate":FactoryNum4Operate,
        "msg_timeout":CloudBootTimeout,
        "check_stock_interval":CheckStockInterval,
        "cloud_boot_sign":CloudBootSign
    }