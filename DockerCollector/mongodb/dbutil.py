# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
from mongodb.dbconst import ID


_ALL = "All"

def Condition4Page(func):
    def newFun(*args,**kwargs):
        if len(args) < 3:
            return func(*args,**kwargs)
        
        query = {}
        filterObj = args[1]
        if isinstance(filterObj,dict):
            for k,v in filterObj.iteritems():
                if not v or v.strip() =="" or v.strip() ==_ALL:
                    continue
                else:
                    query[k] = v
        orderby = args[2]
        if isinstance(orderby,str):
            orderby = {orderby:1}
        elif not isinstance(orderby,dict):
            orderby = {ID:1}
        return func(args[0],query,orderby,*args[3:])
    return newFun
    
def regex_filter(_filter, regex_attrs):
    for regex_key in regex_attrs:
        if regex_key in _filter and _filter.get(regex_key).strip():
            _filter[regex_key] = {'$regex':_filter[regex_key].strip()}
    return _filter    
    
