from mongodb.dbmgr import DBMgr
import getopt
import os
import sys


class MongoDBTool(object):
    def __init__(self,db):
        self.db = db
        self.DBMgr = DBMgr.instance()
        self.DBMgr.init()

        
    def create_js(self,func_name,func_body):
        return self.DBMgr.create_js(self.db,func_name,func_body)   
    
    def loadJs(self,file_path):    
        try:
            fd = open(file_path,"r")
            jsStr = fd.read()
            fd.close()
        except Exception,e:
            print "loadJs [%s] fail. as [%s]"%(file_path,str(e))
            return False
        else:
            return jsStr
        
    def parse_js(self,js_str):
        index = js_str.find("function")
        if index == -1:
            return
        func_name = js_str[0:index]
        eIndex = func_name.find("=")
        if eIndex == -1:
            return 
        func_name = func_name[0:eIndex]
        
        func_body = js_str[index:]
        self.create_js(func_name.strip(), func_body)
        
    def auto_load_js(self,file_name):
        workdir = os.path.dirname(os.path.abspath(__file__))
        workdir = os.path.join(workdir,"javascript")
        workdir = os.path.join(workdir,self.db)
        dirs = os.listdir(workdir)
        if file_name in dirs:
            file_path = os.path.join(workdir,file_name)
            if os.path.isfile(file_path) and file_path.endswith(".js") :
                jsStr = self.loadJs(file_path)
                self.parse_js(jsStr)
            else:
                print "%s is not a js file"%file_path       

def main():
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "lh", ["load","help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-l","--load"):
            LoadJS(*args)
            sys.exit()
        
            
def LoadJS(db_name,file_name):
    tool = MongoDBTool(db_name)
    tool.auto_load_js(file_name)

def usage():
    print "-h  --help  show help"
    print "python mongodbtool.py -l database_name js_file_name"
    print "python mongodbtool.py -h "
    
    

    
if __name__ == "__main__":
    main()