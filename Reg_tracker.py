"""
Created on Fri Sep 27 11:21:00 2019
Run Command: python reg_tracker_syntax.py -i <input file> -n <function_name> -p <project_name>

NOTE:
    #Complete: 
    #1: Delays
    #2: AP WR & AP RD
    #3: AP RD - DATA VALIDATION

    #Pending:
    #1: Debug Switch
    #2: Polling While Loop Design 
    #3: Pass Fail - Error Handling Mechanism
    #4: Complete Syntax Review - Aswin
    #5: Remove Excel - Horizon Compaitable
"""

import re, sys, os, argparse
from collections import Counter
from xlrd import open_workbook
from xlutils.copy import copy

parser = argparse.ArgumentParser()                                               
parser.add_argument("--file", "-i", type=str, default="./reg_tracker_new.txt")
parser.add_argument("--name", "-n", type=str, default="reg_tracker_function")
parser.add_argument("--project", "-p", type=str,default="EA") #Customised for SPYDER 
args = parser.parse_args()
PollError = 0

#################################################################################################################################################
#DEFINITIONS
#################################################################################################################################################

def OutputFile(f):
    #Create Output File: 
    f.write ("// This file is generated based on the below simulation host transactions: \n")
    f.write ("// Input file : %s \n" %args.file)
    #f.write ("// Add: <int %s(void);> to <project>_functions.h \n\n" %args.name)

def ProjectPrefix(f):
    #Define Prefix
    f.write ("\n#include \"test_root.h\"\n")
    if args.project == "XI":    #Project Xian
        pre = "XI_REG_"     
        f.write ("#ifdef XIAN \n\n")
    elif args.project == "EA":  #Project Eagle
        pre = "EA_REG_"         
        f.write ("#ifdef EAGLE \n\n")
    else:
        print ("\n\tUndefined Project : -p <project> | eg. XI / EA \n")
    f.write ("int %s(void) {\n" %args.name)
    f.write ("\n\tint Rdata; \n \tint RdError, PollError = 0;\n\n")
    return pre
    
def HostConfig(f):
    with open(args.file, 'r') as inputfile:
        for line in inputfile: 
            if "Serial Interface Protocol" in line: f.write ("\n//SIFS PROTOCOL: %s\n" %line.split(":")[1].strip()) 
            if "spi_clk_freq" in line: f.write ("//SIFS CLOCK FREQ: %s\n" %line.split(":")[1].strip()) 
            if "spi_mode_selection" in line: f.write ("//SIFS MODE: %s\n" %line.split(":")[1].strip()) 

def ExcelDetectPoll(samples, pre):
    col_a = []
    for i in range(0,len(samples)):
        reg   = RegAccess(i, samples, pre)
        typ   = (samples[i].split("|")[5].strip())
        if typ == "RD": col_a.append(reg)
    counts = Counter(col_a)
    RdPoll = [item for item, count in counts.items() if count >= 2]
    return RdPoll

def AddDelay(ps, f):
    delay_us = round(int(ps) * 1e-6)
    f.write("\tDelayUs(%d);\n\n" %delay_us)

def AP_WR(reg, val, f):
    f.write ("\twrite_register(%s, 0x%s);\n\n" %(reg, val))  #Write Register 

def AP_RD(reg, val, f):  
    f.write ("\tRdata = read_register(%s, 0x%s);" %(reg, val))  #Write Register
    f.write ("\n\tif (Rdata != 0x%s) {RdError = RdError + 1;} \n\n" %(val))  #Write Register
    
def AP_RD_POLL(reg, val, f):  
    f.write ("\tTimeoutMs(1);")
    f.write ("\n\twhile((read_register(%s)!=0x%s) && TIMEOUT_NOT_EXPIRED);" %(reg,val))  #Write Register
    f.write ("\n\tif(!TIMEOUT_NOT_EXPIRED) {PollError = PollError + 1;}\n\n")  #Write Register

def ScoreBoard(f, RdError, PollError):
    f.write ("\tprintf(\"\\t REG-TRACKER SCOREBOARD \\n\");\n")
    f.write ("\tif (RdError!= %d && PollError!= %d) \n\t\tprintf(\"Test Failed! RdError = %%s RdError = %%s \",RdError, PollError);\n" %(RdError,PollError))
    f.write ("\telse \n\t\tprintf(\"\\t Test Passed!\\n\");\n")

def RegAccess(i,samples, pre):
    if i < len(samples):
        return (pre + samples[i].split("|")[4].strip())
    else:
        return 0
    
def RegTransaction(f, wb, pre):
    samples = []
    PollError = 0
    RdError = 0
    with open(args.file, encoding="utf8") as inputfile:
        for line in inputfile.readlines():
            if re.match(r'[(|)]', line): 
                samples.append(line)
        RdPoll = ExcelDetectPoll(samples, pre)      
        print(RdPoll)
                
        for i in range(0,len(samples)):
            ap  = (samples[i].split("|")[8].strip())        
            if ap == "AP":
                reg   = RegAccess(i, samples, pre)
                val   = (samples[i].split("|")[7].strip()[-2:])
                typ   = (samples[i].split("|")[5].strip())
                delay = int(samples[i].split("|")[9].strip())        
                
                if delay != 0 : AddDelay(delay, f)                 
                if reg in RdPoll :  #AP RD POLL Syntax
                    if reg == RegAccess(i+1, samples, pre) :continue
                    else: 
                        AP_RD_POLL(reg, val, f)     
                        PollError = PollError + 1                            
                elif typ == "RD" :                      #AP READ Syntax
                    AP_RD(reg, val, f)  
                    RdError = RdError + 1
                elif typ == "WR" :                      #AP WRITE Syntax 
                    AP_WR(reg, val, f)    
                    
        ScoreBoard(f, RdError, PollError)
        
def ClearDir():
    if os.path.exists('Data.xls'): os.remove('Data.xls')

def main():
    f= open("%s.c" %args.name,"w+")
    wb = xlwt.Workbook()
#    ClearDir()
    OutputFile(f)
    HostConfig(f)
    pre = ProjectPrefix(f)  
    RegTransaction(f, wb, pre)
    f.write ("\nreturn 0; } \n#endif \n")

#################################################################################################################################################
main() #MAIN
#################################################################################################################################################
