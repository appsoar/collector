# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
'''
Created on 2016-3-8

@author: Jack
'''

import json
import re

from common.util import Result
from frame.Logger import Log, PrintStack
from frame.configmgr import GetSysConfig
from frame.curlclient import CURLClient
from frame.errcode import FAIL
from mongoimpl.registry.layerdbimpl import LayerDBImpl
from mongoimpl.registry.repositorydbimpl import RepositoryDBImpl
from mongoimpl.registry.tagdbimpl import TagDBImpl


class RegistryClient(CURLClient):
    '''
    # 实现 Dockers registry的接口
    '''

    def __init__(self):
        '''
        Constructor
        '''
        username = GetSysConfig('registry_username') or 'admin'
        pwd = GetSysConfig('registry_password') or 'badmin'
        domain = GetSysConfig('registry_domain') or '192.168.2.55:5000'
        #domain = '192.168.12.55:5000'
        CURLClient.__init__(self, username, pwd, domain)
        

    def load_registry_data(self):
        rlt = self.listing_repositories(100)
        if not rlt.success:
            return rlt
        
        data = rlt.content
        RepositoryDBImpl.instance().upsert_repository(data['repositories'])
        
        for repo in data['repositories']:
            self.load_repo_data(repo)
                
    def load_repo_data(self, repository):
        rlt = self.listing_image_tags(repository)
        if rlt.success:
            TagDBImpl.instance().upsert_tags(repository, rlt.content['tags'])
            self.load_tag_data(repository, rlt.content['tags'])
        else:
            Log(1, 'load_registry_data.listing_image_tags fail,as[no tags], repository[%s]'%(repository))
                
    def load_tag_data(self, repository_name, tags):
        for tag in tags:
            rlt = self.read_tag_detail(repository_name, tag)
            if rlt.success:
                if not TagDBImpl.instance().is_tag_exist(repository_name, tag, rlt.content['digest']):
                    TagDBImpl.instance().update_tag_info(repository_name, tag, rlt.content['digest'])
                    # @todo 此时数据库中的层记录已经无效，因为层的内容改变的时候，id也会变化
                    LayerDBImpl.instance().save_layer_info(rlt.content)
    
    def listing_repositories( self, num, last=0 ):
        url = "http://" + self.domain + '/v2/_catalog?n=%d&last=%d'%(num, last)
        response = self.do_get(url)
        if response.fail:
            response.log('listing_repositories')
            return Result(response.body, FAIL, response.message)
            
        try:
            return Result(json.loads(response.body))
        except Exception:
            PrintStack()
            Log(1,"listing_repositories format to json fail,body[%s]"%(response.body))
            return Result('', FAIL, 'json.loads fail')

        
    def listing_image_tags(self, repository_name):
        url = "http://" + self.domain + '/v2/%s/tags/list'%(repository_name)
        response = self.do_get(url)
        if response.fail:
            response.log('listing_image_tags')
            return Result(response.body, FAIL, response.message)
        
        try:
            return Result(json.loads(response.body))
        except Exception:
            PrintStack()
            Log(1,"listing_image_tags format to json fail,body[%s]"%(response.body))
            return Result('', FAIL, 'json.loads fail')
    
    
    def read_tag_detail(self, repository_name, tag='latest'):
        """
        # 读取指定tag的信息
        """
        url = "http://" + self.domain + '/v2/%s/manifests/%s'%(repository_name,tag)
        response = self.do_get(url)
        if response.fail:
            response.log('repository_detail')
            return Result(response.body, FAIL, response.message)
        
        info = {}
        try:
            data = json.loads(response.body)
            info['fsLayers'] = data.get('fsLayers',[])
        except Exception:
            PrintStack()
            Log(1,"repository_detail format to json fail,body[%s]"%(response.body))

            
        m = re.search(r"Docker-Content-Digest: ([^\s]+)*", response.respond_headers)
        if m:
            info['digest'] = m.group(1)
        else:
            Log(1,"repository_detail get Docker-Content-Digest fail,header[%s]"%(response.respond_headers))
            
        if info:
            return Result(info)
        else:
            return Result('', FAIL, 'Fail Get data from registry.')
        
    
        
    def read_tag_detail2(self, url):
        if url.find('127.0.0.1') >= 0:
            strinfo = re.compile('\/127.0.0.1[:]{0,1}\d*\/')
            url = strinfo.sub('/'+ self.domain + '/',url)
        elif url.find('localhost') >= 0:
            strinfo = re.compile('\/localhost[:]{0,1}\d*\/')
            url = strinfo.sub('/'+ self.domain + '/',url)
        
        response = self.do_get(url)
        if response.fail:
            response.log('repository_detail')
            return Result(response.body, FAIL, response.message)
        
        info = {}
        try:
            data = json.loads(response.body)
            info['fsLayers'] = data.get('layers',[])
        except Exception:
            PrintStack()
            Log(1,"repository_detail format to json fail,body[%s]"%(response.body))

            
        m = re.search(r"Docker-Content-Digest: ([^\s]+)", response.respond_headers)
        if m:
            info['digest'] = m.group(1)
        else:
            Log(1,"repository_detail get Docker-Content-Digest fail,header[%s]"%(response.respond_headers))
            
        if info:
            return Result(info)
        else:
            return Result('', FAIL, 'Fail Get data from registry.')
    
        
    def delete_image(self, repository_name, digest):
        url = "http://" + self.domain + '/v2/%s/manifests/%s'%(repository_name, digest)
        response = self.do_delete(url)
        if response.fail:
            response.log('delete_image')
        response.log('delete_image')
        
        

        
        

        
        
            
        
        
        
        