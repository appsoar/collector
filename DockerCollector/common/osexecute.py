# -*- coding: utf-8 -*-
 
import subprocess

def rawExec(rcmd):
    '''
    run command and wait command finished.
    @param rcmd: tuple type value for subprocess modules.
    @return: return {"result":0,"return":"","message":""}
        result: 0 for success, none zero for error.
        message: record the stderr if fail
        return: record the stdout if success
    '''
    ret = {"result":0,"return":"","message":""}
    print rcmd
    f = subprocess.Popen(rcmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
    f.wait()
    
    if f.returncode != 0:
        ret["message"] = repr(f.stderr.read())
        ret["result"] = f.returncode
    else:
        ret["message"] = "done"
        ret["result"] = 0
        ret["return"] = repr(f.stdout.read())
        
    return ret


def ShellExec(rcmd):
    '''
    run command(with shell=True) and wait command finished.
    @param rcmd: tuple type value for subprocess modules.
    @return: return {"result":0,"return":"","message":""}
        result: 0 for success, none zero for error.
        message: record the stderr if fail
        return: record the stdout if success
    '''
    ret = {"result":0,"return":"","message":""}
    print rcmd
    f = subprocess.Popen(rcmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
    f.wait()
    
    if f.returncode != 0:
        ret["message"] = repr(f.stderr.read())
        ret["result"] = f.returncode
    else:
        ret["message"] = "done"
        ret["result"] = 0
        ret["return"] = repr(f.stdout.read())
        
    return ret
