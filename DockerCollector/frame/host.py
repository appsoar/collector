# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.
'''
Created on 2016年3月22日

@author: Jack
'''
"""
windows 环境需要安装PyMI
pip install PyMI

还要安装pywin32
https://sourceforge.net/projects/pywin32/files/pywin32/

。net framework
"""

from multiprocessing import cpu_count
import os
import re

import wmi

from common.guard import FileGuard


class Host(object):
    '''
    # 收集主机运行时信息
    '''
    info = None

    def __init__(self, os='linux'):
        '''
        Constructor
        '''
        self.os = os
        self.info = {}
    
    def cpuInfo(self):
        return {}
    
    def memInfo(self):
        return {}
    
    def diskInfo(self):
        return {}
    
    
class WindowsHost(Host):
    system = None
    def __init__(self):
        '''
        Constructor
        '''
        Host.__init__(self,"windows")
        self.system = wmi.WMI()
        
    def cpuInfo(self):
        self.info['cpuPercent'] = []
        index = 1
        for cpu in self.system.Win32_Processor():
            self.info['cpuPercent'][index] = cpu.loadPercentage
            index += 1
            
    def memInfo(self):
        cs = self.system.Win32_ComputerSystem()
        os = self.system.Win32_OperatingSystem()
        self.info['memTotal'] = int(int(cs[0].TotalPhysicalMemory)/1024/1024)
        self.info['memFree'] = int(int(os[0].FreePhysicalMemory)/1024)
        
    def diskInfo(self):
        self.info['diskTotal'] = 0
        self.info['diskFree'] = 0
        for disk in self.system.Win32_LogicalDisk(DriveType=3):
            self.info['diskTotal'] += int(disk.Size)
            self.info['diskFree'] += int(disk.FreeSpace)
        self.info['diskTotal'] = int(self.info['diskTotal']/1024/1024)
        self.info['diskFree'] = int(self.info['diskFree']/1024/1024)
        
class LinuxHost(Host):
    def __init__(self):
        '''
        Constructor
        '''
        Host.__init__(self)
        self.info['cpu_num'] = cpu_count()
        
    def get_mem_info(self):
        meminfo = {}
        with FileGuard('/proc/meminfo', 'r') as fp:
            for line in fp:
                arr = line.split(':')
                if len(arr) == 2:
                    if arr[1][-2:] == 'kB':
                        arr[1] = arr[1][0:-2]
                        meminfo[arr[0]] = arr[1].strip()
        self.info.update(meminfo)
        
    def get_cpu_info(self):
        CPUinfo={}
        procinfo={}
    
        nprocs = 0
        with FileGuard('/proc/cpuinfo', 'r') as fp:
            for line in fp:
                if not line.strip():
                    #end of one processor
                    CPUinfo['proc%s' % nprocs]=procinfo
                    nprocs = nprocs+1
                    #Reset
                    procinfo={}
                else:
                    if len(line.split(':')) == 2:
                        procinfo[line.split(':')[0].strip()] = line.split(':')[1].strip()
                    else:
                        procinfo[line.split(':')[0].strip()] = ''
        return CPUinfo
    
    def get_network_data(self, iface="eth0"):
        """
        $ cat /proc/net/dev
        Inter-|   Receive                                                |  Transmit
         face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
        vethfa61e9b:     648       8    0    0    0     0          0         0    13409      97    0    0    0     0       0          0
        veth024d62a:     648       8    0    0    0     0          0         0    13385      96    0    0    0     0       0          0
          eth0:       5523703    7237    0    0    0     0          0        51  1455967    5435    0    0    0     0       0          0
            lo:         9505     133    0    0    0     0          0         0     9505     133    0    0    0     0       0          0
        docker0:        996      15    0    0    0     0          0         0     8840      61    0    0    0     0       0          0
        """
        with FileGuard('/proc/net/dev', 'r') as fp:
            for line in fp:
                if line.index(iface) >= 0 :
                    index = line.index(':')
                    line = line[index:]
                    arr = re.findall(r"\d+", line)
                    return {'Receive':arr[0], 'Transmit':arr[8]}
        return {'Receive':0, 'Transmit':0}
    
    def parse_disk_info(self):
        with os.popen('df -l --total') as fp:
            for line in fp:
                if line[0:5] == 'total':
                    arr = re.findall(r"\d+", line)
                    return {'Size':arr[0], 'Used':arr[1],'Available':arr[2],'UsePercent':arr[3]}
                    
        return {'Size':0, 'Used':0,'Available':0,'UsePercent':0}

    
    def parse_top_info(self):
        """
        $ top -bi -n 1
        top - 15:15:43 up  1:13,  1 user,  load average: 0.00, 0.01, 0.05
        Tasks: 112 total,   1 running, 111 sleeping,   0 stopped,   0 zombie
        %Cpu(s):  0.4 us,  0.4 sy,  0.1 ni, 98.0 id,  1.1 wa,  0.1 hi,  0.0 si,  0.0 st
        KiB Mem:   1017852 total,   822092 used,   195760 free,   121492 buffers
        KiB Swap:  1046524 total,        0 used,  1046524 free.   470244 cached Mem
        """
        with os.popen('top -bi -n 1') as fp:
            for line in fp:
                if line[0:4] == '%Cpu':
                    cpu = self.parse_top_line(line)
                    self.info['cpu_user_percent'] = cpu.get('us', 0)
                    self.info['cpu_sys_percent'] = cpu.get('sy', 0)
                    self.info['cpu_level_change'] = cpu.get('ni', 0)
                    self.info['cpu_free_percent'] = cpu.get('id', 0)
                    self.info['cpu_wait_in_out'] = cpu.get('wa', 0)
                    self.info['cpu_hard_break_'] = cpu.get('hi', 0)
                    self.info['cpu_soft_break'] = cpu.get('si', 0)
                    self.info['cpu_vm_percent'] = cpu.get('st', 0)
                elif line[0:7] == 'KiB Mem':
                    mem = self.parse_top_line(line)
                    self.info['MemTotal'] = mem.get('total', 0)
                    self.info['MemUsed'] = mem.get('used', 0)
                    self.info['MemFree'] = mem.get('free', 0)
                    self.info['Buffers'] =mem.get('buffers', 0)

    def parse_top_line(self, txt):
        info = {}
        txt = txt.split(':')[1]
        arr = txt.split(',')
        for pair in arr:
            keys = pair.split(' ')
            info[keys[1].strip()] = keys[0].strip()
        return info

    def parse_proc_line(self, txt):
        info = {}
        arr = txt.split(':')
        info[arr[0].strip()] = arr[1].strip()


    
if __name__ == '__main__':
    host = LinuxHost()
    host.parse_top_info()
    host.get_network_data()
    host.get_mem_info()
    host.get_cpu_info()

    
       
        