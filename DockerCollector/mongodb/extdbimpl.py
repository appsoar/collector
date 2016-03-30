# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.


from common.util import Result, TreeResult, PageResult
from frame.errcode import IDENTITY_KEY_NOT_EXIST_ERR, FILTER_IS_INVALID_ERR, \
    NO_SUCH_RECORD_ERR
from mongodb.dbbase import DBBase
from mongodb.dbconst import ID


PAGE = 'Page'
TREE = 'Tree'
LIST = 'List'


class ExtDBImpl(DBBase):

    def __init__(self,db,collection):
        super(ExtDBImpl, self).__init__(db,collection)
        
    def merge_filter(self,filters):
        query = {}
        for f in filters:
            if 'property' in f and 'value' in f:
                query[f['property']] = f['value']
                
            
        return query
    
    def parse_sort(self,sorts):
        order_by = {}
        for s in sorts:
            if 'property' in s:
                order_by[s['property']] = 0 if s.get('direction') == 'DESC' else 1
                
        return order_by

    def ext_read_page(self,params):
        sorts = params.get('sort',[])
        query = self.merge_filter(params.get('filter',[]))
        orderby = self.parse_sort(sorts)
        page_no = params.get('page',0)
        page_size = params.get('limit',0) - params.get('start',0)
        
        rlt = self.read_record_page(query, orderby, page_no, page_size)
        if rlt.success:
            return rlt.content
        return rlt  
    
    def ext_read_tree(self,params,key_map):
        query = self.merge_filter(params.get('filter',[]))
        node = params.get('node','root')
        if node != 'root':
            if not key_map.get('parent_key'):
                return TreeResult([],key_map)
            
            query[key_map['parent_key']] = node
            
        fields = []
        fields.append(key_map['id'])
        fields.append(key_map['text'])
        rlt = self.read_record_list(query,projection=fields,sort=key_map.get('sort',[]))
        if rlt.success:
            return TreeResult(rlt.content,key_map)
        return rlt

    def ext_read_list(self,params):
        query = self.merge_filter(params.get('filter',[]))
        sort = self.parse_sort(params.get('sort',[]));
        rlt = self.read_record_list(query,sort=sort.items())
        if rlt.success:
            return PageResult(rlt.content)
        return rlt
    
    def ext_read_info(self,params):
        query = self.merge_filter(params.get('filter',[]))
        if 'id' in params:
            query[ID] = params['id']
        rlt = self.read_record_list(query)
        if not rlt.success:
            return rlt
        if len(rlt.content):
            return PageResult(rlt.content)
        else:
            return Result("",NO_SUCH_RECORD_ERR,"No such record")
    
    def ext_update(self,record):
        if ID in record:
            _id = record.pop(ID)
            return self.update({ID:_id},record,True)
        else:
            return Result("ext_update",IDENTITY_KEY_NOT_EXIST_ERR,"The Identity key not exist.")
        
        
    
    def ext_delete(self,params):
        filters = params.get('filter',[])
        query = self.merge_filter(filters)
        if query:
            return self.remove(query)
        else:
            return Result('',FILTER_IS_INVALID_ERR,"can not delete all data")
        
        
    
    
        