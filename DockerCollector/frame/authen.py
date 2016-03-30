# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

"""
Manager user security info and verify it  
"""

from common.guard import LockGuard
from common.timer import Timer
from frame.Logger import SysLog
from frame.errcode import ERR_NO_TOKEN_PARAM, ERR_TIME_MISMATCH, \
    ERR_ACCESS_AUTHENFAIL, ERR_TIMESTAMP_REPEAT, ERR_ACCESS_IDNOTEXIST
from frame.exception import OPException
from keyczar import keyczar
import base64
import hmac
import os
import sha
import threading
import time

##################################### Ring defined ##############################

# VFOS using "ring" concept to identify different feature of service interface, with different ring you may have different privilege.

# RING_SUPER_ADMIN can do almost everything directly or indirectly, 
# RING_SUPER_ADMIN's main task is to maintain the configuration file and do the LOCAL_ADMIN account management  
RING_SUPER_ADMIN = "ring0"

# RING_LOCAL_ADMIN can do resource maintain, and some task maintain, and OPERATE_ADMIN account management 
RING_LOCAL_ADMIN = "ring1"

# RING_LOCAL_ADMIN_ASSIST is a assist ring for RING_LOCAL_ADMIN.
# Within this ring, user can see the thing that RING_LOCAL_ADMIN can see, but CANNOT change it. just like a read only feature.
RING_LOCAL_ADMIN_ASSIST = "ring2"

# RING_OPERATE_ADMIN's main task is to manage the USER_ADMIN account. 
# the USER_ADMIN account is grouping to special OPERATE_ADMIN group.
RING_OPERATE_ADMIN = "ring3"

# RING_OPERATE_ADMIN_ASSIST is a assist ring for RING_OPERATE_ADMIN
# Within this ring, user can see the thing that RING_OPERATE_ADMIN can see, but CANNOT change it. just like a read only feature.
RING_OPERATE_ADMIN_ASSIST = "ring4"

# RING_USER_ADMIN is to management the task and using the resource (service interface) that the VFOS service had provided.
RING_USER_ADMIN = "ring5"

# RING_USER_ADMIN_ASSIST is a assist ring for RING_USER_ADMIN
# Within this ring, user can see the thing that RING_USER_ADMIN can see, but CANNOT change it. just like a read only feature.
RING_USER_ADMIN_ASSIST = "ring6"

# RING_HELP is a assist ring, would try to identify the user by the access_id, and return the corresponding informations.
# Equals ring0|ring1|...|ring7
# usually, the vfos service should provide a common user with "77777777-7777-7777-7777-777777777777" as access id and access key. 
RING_HELP = "ring7"

# RING_USER_ADMIN_ASSIST is a assist ring, User can use the feature in this ring without authenticate.
RING_HELP_ASSIST = "ring8"
#@todo:  Developer might also defined their own rings.

   
def ring0(func):
    ring = []
    if hasattr(func,"ring"):
        ring = getattr(func,"ring")
    if RING_SUPER_ADMIN not in ring:
        ring.append(RING_SUPER_ADMIN)
    setattr(func,"ring",ring)
    return func


def ring1(func):
    ring = []
    if hasattr(func,"ring"):
        ring = getattr(func,"ring")
    if RING_LOCAL_ADMIN not in ring:
        ring.append(RING_LOCAL_ADMIN)
    setattr(func,"ring",ring)
    return func


def ring2(func):
    ring = []
    if hasattr(func,"ring"):
        ring = getattr(func,"ring")
    if RING_LOCAL_ADMIN_ASSIST not in ring:
        ring.append(RING_LOCAL_ADMIN_ASSIST)
    setattr(func,"ring",ring)
    return func


def ring3(func):
    ring = []
    if hasattr(func,"ring"):
        ring = getattr(func,"ring")
    if RING_OPERATE_ADMIN not in ring:
        ring.append(RING_OPERATE_ADMIN)
    setattr(func,"ring",ring)
    return func


def ring4(func):
    ring = []
    if hasattr(func,"ring"):
        ring = getattr(func,"ring")
    if RING_OPERATE_ADMIN_ASSIST not in ring:
        ring.append(RING_OPERATE_ADMIN_ASSIST)
    setattr(func,"ring",ring)
    return func


def ring5(func):
    ring = []
    if hasattr(func,"ring"):
        ring = getattr(func,"ring")
    if RING_USER_ADMIN not in ring:
        ring.append(RING_USER_ADMIN)
    setattr(func,"ring",ring)
    return func


def ring6(func):
    ring = []
    if hasattr(func,"ring"):
        ring = getattr(func,"ring")
    if RING_USER_ADMIN_ASSIST not in ring:
        ring.append(RING_USER_ADMIN_ASSIST)
    setattr(func,"ring",ring)
    return func


def ring7(func):
    ring = [RING_SUPER_ADMIN,
            RING_LOCAL_ADMIN,
            RING_LOCAL_ADMIN_ASSIST,
            RING_OPERATE_ADMIN,
            RING_OPERATE_ADMIN_ASSIST,
            RING_USER_ADMIN,
            RING_USER_ADMIN_ASSIST]
    setattr(func,"ring",ring)
    return func


def ring8(func):
    ring = [RING_HELP_ASSIST]
    setattr(func,"ring",ring)
    return func

class authen(object):
    
    def __init__(self,offset=30):
        self.stamp_list = {}
        self.access_store = {} 
        self.__stamp_lock = threading.Lock()
        self.time_offset = offset
        self.load_access_info()
        guard = Timer(5,self,"AuthenDriver")
        guard.start()
        
    def timeout(self):
        now = int(time.time()) * 1000
        with LockGuard(self.__stamp_lock):
            for k in self.stamp_list.keys():
                if now - long(k) > self.time_offset:
                    del self.stamp_list[k]
                else:
                    continue

    
    def add_timestamp(self,timestamp,security_hash):
        "Time stamp is a number ,it equal to the millisecond of request time"
        ret = True
        with LockGuard(self.__stamp_lock):
            if timestamp in self.stamp_list:
                if security_hash in self.stamp_list[timestamp]:
                    ret = False
                else:
                    self.stamp_list[timestamp].append(security_hash)
            else:
                self.stamp_list[timestamp] = [security_hash]

        return ret
    
    def load_access_info(self):
        '''
        # 将安全信息加载到内存
        '''
        self.access_store["admin_access_uuid"] =("ring0","admin_security_key")
        self.access_store["vfos_access_uuid"] = ("ring0","vfos_security_key")
        self.access_store["awego"] = ("ring0","awego")
        self.access_store["aweju"] = ("ring0","aweju")

    def check_token(self,method,token,*args):
        SysLog(3,"call [%s] at [%f]"%(method,time.time()))
        passport = self.get_green_passport(method)
        if passport:
            SysLog(3,"call [%s] by green passport"%(method))
            return passport
        
        if not token:
            raise OPException("The request not take a token" ,ERR_NO_TOKEN_PARAM)
         
        SysLog(3,"uuid:[%s],timestamp:[%s],method:[%s],args:[%s]"%(token["access_uuid"],token["timestamp"],method,repr(args)))
        
        self.check_timestamp(token)
        passport = {}
        passport["method"] = method
        passport["access_uuid"] = token["access_uuid"]
        
        ring = self.verify_sec_key(method,token)
        
        passport["ring"] = ring
        return passport
    
    def get_token(self,method,access_uuid,access_key):
        timestamp = long(time.time() * 1000)
        msg = "<%d><%s>"%(timestamp,method)
        access_key = str(access_key)
        
        token = {}
        token["timestamp"] = str(timestamp)
        token["security_hash"] = base64.encodestring(hmac.new(access_key, msg, sha).hexdigest()).strip()
        token["access_uuid"] = str(access_uuid)
        return token        
    
    def get_green_passport(self,method):
        '''default no green passport'''
        return False

        
    def check_timestamp(self,token):
        timestamp = long(time.time())
        if "timestamp" not in  token or not isinstance(token,dict):
            raise OPException("The request did not set quest time",ERR_TIME_MISMATCH)
            
        postTime = long(token["timestamp"])
        postTime = postTime /1000
        if postTime - timestamp < - self.time_offset or  postTime - timestamp > self.time_offset:
            raise OPException("Time not match, Please call whatTime method to adjust the timestamp.",ERR_TIME_MISMATCH)

    def verify_sec_key(self,method,token):
        security_string = "<"+str(token["timestamp"])+"><"+ method+">"
        ring,security_key = self.get_access_key(token["access_uuid"])
        security_key = str(security_key)
        security_hash     = base64.encodestring(hmac.new(security_key, security_string, sha).hexdigest()).strip()
        if str(security_hash) != token['security_hash']:
            raise OPException("Check authenication fail" ,ERR_ACCESS_AUTHENFAIL)
        else:
            if not self.add_timestamp(token["timestamp"],token['security_hash']):
                raise OPException("timestamp repeat",ERR_TIMESTAMP_REPEAT)
        return ring

        
    def get_access_key(self,access_uuid):
        if access_uuid in self.access_store:
            return self.access_store[access_uuid]
        
        SysLog(1,"authen.get_access_key fail %s not a valid uuid"%access_uuid)
        raise OPException("authen.get_access_key fail" ,ERR_ACCESS_IDNOTEXIST)
    
    def get_sec_path(self):
        return None
    
    def encrypt(self,msg,sec_dir=None):
        if sec_dir is None:
            sec_dir = self.get_sec_path()
        if not os.path.isdir(sec_dir):
            return False
        crypter = keyczar.Crypter.Read(sec_dir)
        return crypter.Encrypt(msg)
    
    def decrypt(self,text,sec_dir=None):
        if sec_dir is None:
            sec_dir = self.get_sec_path()
        if not os.path.isdir(sec_dir):
            return False

        crypter = keyczar.Crypter.Read(sec_dir)
        return crypter.Decrypt(text)
           






