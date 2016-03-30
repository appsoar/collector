#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.

from common.util import IsStr
from frame.Logger import Log
import re
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')



class Template(object):
    variables = {}
    reObj = None
    tpl_txt = ""
    
    def __init__(self,regStr = None,pre=3,end=-2):
        if regStr is None:
            regStr = '<%=.*?%>'
        
        self.index_pre = pre
        self.index_end = end
            
        self.reObj = re.compile(regStr)
    
    def replace(self,match):
        tmpStr = match.group()
        key = tmpStr[self.index_pre:self.index_end].strip()
        if key in self.variables:
            return self.format_xml(self.variables[key])
        else:
            Log(1,"variable [%s] did not set value"%key) 
            return key
        
    def toString(self):
        return self.reObj.sub(self.replace,self.tpl_txt)
    
    def set_tpl_txt(self,txt):
        self.tpl_txt = txt        
    
    def append(self,key,value):
        self.variables[key] = value
        
    def append_keys(self,data):
        self.variables.update(data)
        
    def format_xml(self,txt):
        if not IsStr(txt):
            return str(txt)
        txt = txt.replace("<br>","<br />")
        txt = txt.replace("&nbsp;","&#160;")
        return txt
    
