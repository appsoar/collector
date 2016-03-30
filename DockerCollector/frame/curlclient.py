# -*- coding: utf-8 -*-
#!/usr/bin/python25
"""
/*
 * Title : 
 * 
 * Version : 
 * 
 * Last modified date : 2016-1-28
 * 
 * Description :
 *         This class provide fast-operation API to access Aspen Cloud Server.
 * 
 * Prerequisite :
 *         - Python v2.5.0 or above
 *         - pycurl
 *         - Another class, CServerAuth.py, in same folder of this class. It is for authentication.
 *
 * 
 * =========================================================================================================
 * How to use this class :
 * =========================================================================================================
 * 1) make sure required framework and class, class CServerAuth.py are setup before instantiate this class.
 * 2) Instantiate this class and passing the "user access id" and "user secret key" to the constructor.
 * 3) Call the functions for your purpose. The supported operations are shown in following.
 * 4) Different operation requests different parameter to passing in. 
 * 5) If the API is run successfully, boolean TRUE will be returned and vice versa.
 * 6) The responded XML result including http status code and XML content can be retrieved via member functions
 *    such as getRespond_body(), getRespond_http_status_code() and so on.
 * 7) For failure request, you can get the detail error by function, getError_message()
 *       Not all error has error message. Depends on what error is triggered.
 *   
 * 
 * =========================================================================================================
 * Function List :
 * =========================================================================================================
 * Cloud Server related functions :
 * 1) server_list                                  - Show subscribed cloud server in XML list
 
 * 
 * Functions for retrieval of Aspen Cloud Server responded value:
 * 1) getRespond_body()                            - Get the returned html body (i.e. most are XML) from Aspen Cloud Server.
 * 2) getRespond_headers_array()                - Get the returned http headers in array.
 * 3) getRespond_http_status_code()                - Get the returned http status code. e.g. 404, 201, 200...
 * 4) getRespond_http_status_message()            - Get the returned http status message. e.g. Created, OK, Deleted...
 * 
 * 
 * Other Functions:
 * 1) getError_message()                        - Get the error message for failed call.
 * 
 */
"""

import cStringIO
import re
import time
import traceback
import types
from xml.dom import Node
from xml.dom.minidom import parseString

import pycurl

from frame.Logger import Log
from frame.curlclientauth import CURLClientAuth
from frame.httpsclient import HttpsClient


#constants
DEFAULT_LANGUAGE = "en"        #en, zh_TW, and zh_CN
LANGUAGE_ENGLISH = "en"
LANGUAGE_TRADITIONAL_CHINESE = "zh_TW"
LANGUAGE_SIMPLIFIED_CHINESE = "zh_CN"


#Http constants
PUT = "PUT"
GET = "GET"
DELETE = "DELETE"
POST = "POST"



#Function constants
#supported function in Cloud Server via REST
SERVER_LIST = 'server_list'
EXECUTE_TASK = 'execute_task'


# schedule type constant
SCHEDULE_TYPE_WEEKLY = "W"
SCHEDULE_TYPE_MONTHLY = "M"

#Http status code
HTTP_EXCEPTION = 1
HTTP_OK_200 = 200   #OK
HTTP_CREATED_201 = 201  #resource created
HTTP_UNAUTHORIZED = 401  # authentication required
#Http header constants
HEADER_HOST = 'Host'
HEADER_DATE = 'Date'
HEADER_AUTH = 'Authorization'
HEADER_EXPIRES = 'Expires'
HEADER_ADMIN = 'x-pan-admin'

SUCCESS = "SUCCESS"
FAIL = "FAILURE"    


class Response(object):
    def __init__(self,respond_body, respond_headers, status_code=HTTP_OK_200, msg="done"):
        """
        respond_http_status_code = ch.getinfo( pycurl.HTTP_CODE )
            respond_headers_array = ch.respondheader.getvalue()
            respond_body = ch.response.getvalue()
        """
        super(Response, self).__init__()
        self.status_code = status_code
        self.respond_headers = respond_headers
        self.respond_body = respond_body
        self.message = msg
        
    @property
    def success(self):
        return self.status_code == HTTP_OK_200
    
    @property
    def fail(self):
        return self.status_code != HTTP_OK_200
       
    @property    
    def body(self):
        return getattr(self,"respond_body",0)
    
    @body.setter    
    def body(self,new_value):
        setattr(self,"respond_body",new_value)

    def __getitem__(self, key):
        if "body" ==key:
            return self.respond_body
        elif "status_code" ==key:
            return getattr(self,"status_code",0)
        elif "message" ==key:
            return self.message
        else:
            return None
        
    def __str__(self):
        return "Response<'status_code':%d,'headers':'%s','body':%s,'message':'%s'>"% \
            (self.status_code, self.respond_headers, self.respond_body, self.message)
            
    def log(self, act):
        if self.status_code == HTTP_OK_200:
            Log(3, '[%s] success, return [%s]'%(act, self.respond_body))
        else:
            Log(1, '[%s] fail, return [%s],massage[%s]'%(act, self.respond_body, self.message))
        
    

class CURLClient:
    def __init__( self, _id, key ,domain='127.0.0.1'): 
        self.domain = domain
        self.debug = False
        self.server_id = ""
        self.language = ""
        self.date_time = ""
        self.host = ""
        self.token = ""
        self.signature = ""
        self.url = ""
        self.xml_body = ""

        self.user_access_id = _id
        self.user_secret_key = key
        self.admin_code = ""

        self.respond_headers_array = []
        self.respond_http_status_code = 0
        self.respond_http_status_message = ""
        self.respond_body = ""

        self.error_message = ""

        
    def getUrl( self ) :
        return self.url
    
    def getRespond_body( self ) :
        return self.respond_body
    
    
    def getRespond_headers_array( self ):
        return self.respond_headers_array
    
    
    def getRespond_http_status_code( self ):
        return self.respond_http_status_code
    
    
    #get error message
    def getError_message( self ):
        return self.error_message

    
    def setAdmin_code(self,admin_code):
        self.admin_code = admin_code 
    
    def get_token(self, response):
        m = re.search(r"Www-Authenticate: (.+)\r", response.respond_headers)
        if not m:
            Log(1,"get_token fail,header[%s]"%(response.respond_headers))
            return False
        
        txt = m.group(1)
        data = {}
        keys = txt.split(',')
        if len(keys) != 3:
            return False
        
        for key in keys:
            arr = key.split('=')
            if len(arr) != 2:
                return False
            
            data[arr[0]] = arr[1].replace('"','')
        
        client = HttpsClient(self.user_access_id, self.user_secret_key)
        rlt = client.do_get(data['Bearer realm'], data['scope'], data['service'])
        if rlt.success:
            self.token = rlt.content['token']
            return True
        return False
        
    def do_get( self, url ):
        try:
            self.date_time = time.strftime( "%a, %d %b %Y %X +0000", time.gmtime() )
            Headers = self.getBasicHeaders()
            response = self.send_http_request(url, Headers, GET )
        
            if response.status_code == HTTP_UNAUTHORIZED and self.get_token(response):
                return self.do_get(url)
            else:
                return response
        except Exception, e:
            return Response('', '', HTTP_EXCEPTION, str(e))
        finally:
            self.token = ''
        
    def do_delete( self, url ):
        try:
            self.date_time = time.strftime( "%a, %d %b %Y %X +0000", time.gmtime() )
            Headers = self.getBasicHeaders()
            return self.send_http_request(url, Headers, DELETE )
        except Exception, e:
            return Response('', '', HTTP_EXCEPTION, str(e))

        
    def callRemote(self, url, method, post_data=None):
        try:
            nPos = url.index('?')
            if nPos < 0:
                url += '?method=' + method
            else:
                url += '&method=' + method
            
            if post_data is None or len(post_data)==0:
                http_method = GET
                http_body = ""
            else:
                http_method = PUT
                http_body = self.__createXML(post_data, 'data')

            #set http headers
            self.date_time = time.strftime( "%a, %d %b %Y %X +0000", time.gmtime())
            objAUTH = CURLClientAuth( self.user_access_id, self.user_secret_key )
            objAUTH.setParameter( http_method, self.date_time, method )
            self.signature = objAUTH.generateSignature()
            if self.signature == False:
                raise Exception( 'Fail to generate signature.' )

            Headers = self.getBasicHeaders()
            return ( ( self.send_http_request( url, Headers, http_method, http_body) == HTTP_OK_200 ) and True or False )

        except Exception, e:
            self.error_message = str( e )
            return False
    
    def server_list( self, thisLanguage = DEFAULT_LANGUAGE ):
        '''
         Description : Show subscribed cloud server in XML list 
         Parameters : 
                 thisLanguage (string) (optional) - language of output 
         Return value :
                 True if success and vice versa
                 The returned SERVER list (i.e. XML) is stored in self.respond_body.
                 You should retrieve via getRespond_body(self)
        '''
        try:
            #assign value
            self.date_time = time.strftime( "%a, %d %b %Y %X +0000", time.gmtime() )
            self.url = "http://" + self.domain + "/" + SERVER_LIST + "/locale/" + thisLanguage

            #set http headers
            objAUTH = CURLClientAuth( self.user_access_id, self.user_secret_key )
            objAUTH.setParameter( GET, self.date_time, SERVER_LIST )
            self.signature = objAUTH.generateSignature()
            if self.signature == False:
                raise Exception( 'Fail to generate signature.' )

            Headers = self.getBasicHeaders()

            return ( ( self.send_http_request( self.url, Headers, GET ) == HTTP_OK_200 ) and True or False )

        except Exception, e:
            self.error_message = str( e )
            return False
    
    
    def __createXML(self, array, rootname, save_result=False):
        xml_string = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>'
        xml_string += '<' + rootname + '>'
        xml_string +='</' + rootname +'>\n\r'
        dom = parseString( xml_string )
        root_dom = dom.getElementsByTagName(rootname)[0]
        
        if array.has_key("@attributes") and len(array["@attributes"]) > 0:
            for attribute,value in array["@attributes"].iteritems():
                root_dom.setAttribute(attribute,value)
            del array["@attributes"]
        self.__createDom(array, dom, root_dom)
        return dom.toxml('utf-8')
    
    
    def __createDom(self, array, dom, parent):
        for key, value in array.iteritems():
            child = dom.createElement(key)
            if type(value) == type({}):
                self.__createDom(value, dom, child)
                parent.appendChild(child)
            elif isinstance(value,list):
                for item in value:
                    self.__createChildDoms(item,dom,child)
                parent.appendChild(child)                
            else:
                child.appendChild(dom.createTextNode(value))
                parent.appendChild(child)
    
    
    def __createChildDoms(self,dataObj,dom,parent):
        if isinstance(dataObj,dict):
            self.__createDom(dataObj,dom,parent)
        elif isinstance(dataObj,list):
            self.__createChildDoms(dataObj,dom,parent)
        else:
            parent.appendChild(dom.createTextNode(str(dataObj)))
    

     
    def send_http_request( self, thisURL, thisArrHeader, thisHttpMethod, thisHttpBody="" ):
        try:

            ch = ""
            ch = pycurl.Curl()
            thisURL = str(thisURL)
            ch.setopt( pycurl.URL, thisURL )
            ch.setopt( pycurl.HTTPHEADER, thisArrHeader )
            ch.respondheader = cStringIO.StringIO()
            ch.setopt( pycurl.HEADERFUNCTION, ch.respondheader.write )
            #ch.setopt( pycurl.RETURNTRANSFER, True)
            ch.setopt( pycurl.HEADER, False )
            ch.setopt( pycurl.VERBOSE, self.debug )
            ch.setopt( pycurl.DNS_USE_GLOBAL_CACHE, False )

#            c.setopt(pycurl.UPLOAD,1)
#            try:
#                c.setopt(pycurl.READFUNCTION, open(self.file_path, 'rb').read)
#                filesize = os.path.getsize(self.file_path)
#                c.setopt(pycurl.INFILESIZE, filesize)
#
#                c.response = cStringIO.StringIO()
#                c.setopt(c.WRITEFUNCTION, c.response.write)
#            except:
#                c.close()
#                raise CBSError("Open file <"+self.file_path+"> error!")
            
            if thisHttpMethod==PUT and thisHttpBody!="":
                handle = cStringIO.StringIO()
                handle.write(thisHttpBody)
                handle.seek(0)
                size = len(thisHttpBody)
                ch.setopt(pycurl.UPLOAD, True);
                ch.setopt(pycurl.READFUNCTION, handle.read);
                ch.setopt(pycurl.INFILESIZE, size);
            ch.setopt( pycurl.CUSTOMREQUEST, thisHttpMethod )
            ch.response = cStringIO.StringIO()
            ch.setopt( ch.WRITEFUNCTION, ch.response.write )

            ch.perform()
            respond_http_status_code = ch.getinfo( pycurl.HTTP_CODE )
            respond_headers_array = ch.respondheader.getvalue()
            respond_body = ch.response.getvalue()

            ch.close()
            return Response(respond_body, respond_headers_array, respond_http_status_code)
        except Exception, e:
            traceback.print_exc()
            if ch != '':
                ch.close()
            return Response('', '', HTTP_EXCEPTION, str(e))


    # read the respond header from Aspen Cloud Storage
    def read_respond_header( self, ch, thisHeader ):
        '''
        read the respond header from Aspen Cloud Storage
        '''
        header = thisHeader.split(":") 
        if len( header ) == 2:
            self.respond_headers_array[header[0]] = header[1]
        return len( thisHeader )

 
    # url encode of file name 
    #def urlencode_file_name(self):
    #    file = rawurlencode(self.file_name)
    #    self.url_encoded_file_name = str_replace("%2F", "/", file) 
    # return the basic required headers
    
    
    def getBasicHeaders( self ):
        '''
        return the basic required headers
        '''
        Header = []

        Header.append( HEADER_HOST + ": " + self.domain )
        Header.append( HEADER_DATE + ": " + self.date_time )

        if self.token:
            Header.append( HEADER_AUTH + ": Bearer %s"%(self.token) )
        return Header
    

    def debugonoff( self, flag ):
        self.debug = flag


    def __parseList(self,xmlstr,keyname):
        '''
        this method is for the common list format of Aspen cloud API, return the array. 
        @param xmlstr: the return string for xml 
        @type xmlstr: 
        @param keyname: the keyname for the list
        @type keyname:
        @return: return the array of the items
        '''
        try:
            itemlist = []
            dom = parseString( xmlstr )
            xmlitem = dom.getElementsByTagName( keyname )
            if xmlitem:
                for inode in xmlitem:
                #inode = xmlitem[0]
                    iteminfo = {}
                    for attrnode in inode.childNodes:
                        try:
                            if len( attrnode.childNodes ) > 0 :
                                iteminfo[str( attrnode.nodeName ).lower()] = attrnode.childNodes[0].data
                            else:
                                iteminfo[str( attrnode.nodeName ).lower()] = "-"
                        except AttributeError, e:
                            pass
                    itemlist.append(iteminfo)

            return itemlist

        except Exception, e :
            #traceback.print_exc() 
            self.error_message = str( e )
            return []
        
    def __parseObject(self,xmlstr,keyname):
        '''
        this method is for the common list format of Aspen cloud API, return the array. 
        @param xmlstr: the return string for xml 
        @type xmlstr: 
        @param keyname: the keyname for the list
        @type keyname:
        @return: return the array of the items
        '''
        try:
            iteminfo = {}
            dom = parseString( xmlstr )
            xmlitem = dom.getElementsByTagName( keyname )
            if xmlitem:
                
                for inode in xmlitem:
                #inode = xmlitem[0]
                    iteminfo = {}
                    for attrnode in inode.childNodes:
                        try:
                            if len( attrnode.childNodes ) > 0 :
                                iteminfo[str( attrnode.nodeName ).lower()] = attrnode.childNodes[0].data
                            else:
                                iteminfo[str( attrnode.nodeName ).lower()] = "-"
                        except AttributeError, e:
                            pass
                    iteminfo.update(iteminfo)

            return iteminfo

        except Exception, e :
            #traceback.print_exc() 
            self.error_message = str( e )
            return []
        

    def xml_node_to_dict(self, node):
        out = {}
        if node.nodeType!=Node.ELEMENT_NODE:
            return None
        for item in node.childNodes:
            if item.nodeType==Node.TEXT_NODE or item.nodeType==Node.CDATA_SECTION_NODE:
                if node.childNodes.length==1:
                    return item.nodeValue.encode('utf-8')
                else:
                    continue
            if item.nodeType!=Node.ELEMENT_NODE:
                continue
            temp_data = self.xml_node_to_dict(item)
            if out.has_key(item.tagName):
                if type(out[item.tagName])==types.ListType:
                    out[item.tagName.lower()].append(temp_data)
                else:
                    out[item.tagName.lower()] = [out[item.tagName], temp_data]
            else:
                out[item.tagName.lower()] = temp_data
        return out
 
    def xml_to_dict(self,str_xml):
        try:
            dom = parseString(str_xml)
        except Exception,err:
            print str(err)
            return None
        root = dom.documentElement
        return {root.tagName:self.xml_node_to_dict(root)}

    def xml_to_dict2(self, str_xml, nameNode):
        try:
            dom = parseString(str_xml)
        except Exception,err:
            print str(err)
            return None 
        result=[]
        root = dom.documentElement
        xmlitem = root.getElementsByTagName( nameNode )
        if xmlitem :
            for item in xmlitem:
                result.append(self.xml_node_to_dict(item)) 
        return result
    

