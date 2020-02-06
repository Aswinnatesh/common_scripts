"""
Created on Fri Sep 27 11:21:00 2019
Run Command: python reg_tracker_syntax.py -i <input file> -n <function_name> -p <project_name>
NOTE:
    #Complete: 
    #1: Delays
    #2: AP WR & AP RD
    #3: AP RD - DATA VALIDATION
    #4: Polling While Loop Design 
    #5: Pass Fail - Error Handling Mechanism
    
    #Pending:
    #1: Complete Syntax Review - Aswin
    #2: Debug Switch
"""

import re, sys, os, argparse
from collections import Counter

parser = argparse.ArgumentParser()                                               
parser.add_argument("--file", "-i", type=str, default="./reg_tracker_new.txt")
parser.add_argument("--name", "-n", type=str, default="reg_tracker_function")
parser.add_argument("--project", "-p", type=str,default="EA") #Customised for SPYDER 
args = parser.parse_args()

#################################################################################################################################################
#DEFINITIONS
#################################################################################################################################################

def ProjectSpecifics(mode):
    #   MODE 0: INTIAL OUTPUT FILE CONFIG - Return Nothing
    #   MODE 1: RETURN PROJECT HEADER
    if mode == 0:  
        f.write ("// This file is generated based on the below simulation host transactions: \n")
        f.write ("// Input file : %s \n" %args.file)
        #f.write ("// Add: <int %s(void);> to <project>_functions.h \n\n" %args.name)
        HostConfig()
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
    
    if mode == 1: 
        if args.project     == "XI": return ("XI_REG_")  #Project Xian           
        elif args.project   == "EA": return ("EA_REG_")  #Project Eagle
        else: 
            print ("\n\tUndefined Project : -p <project> | eg. XI / EA \n")
            return 0
        
def HostConfig():
    with open(args.file, 'r') as inputfile:
        for line in inputfile: 
            if "Serial Interface Protocol" in line: f.write ("\n//SIFS PROTOCOL: %s\n" %line.split(":")[1].strip()) 
            if "spi_clk_freq" in line: f.write ("//SIFS CLOCK FREQ: %s\n" %line.split(":")[1].strip()) 
            if "spi_mode_selection" in line: f.write ("//SIFS MODE: %s\n" %line.split(":")[1].strip()) 

def AddDelay(ps):
    delay_us = round(int(ps) * 1e-6)
    f.write("\tDelayUs(%d);\n\n" %delay_us)

def AP_WR(inp, i):
    if GetData(inp, i, "DEL") != 0 : AddDelay(int(GetData(inp, i, "DEL")))
    f.write ("\twrite_register(%s, 0x%s);\n\n" %(GetData(inp, i, "REG"), GetData(inp, i, "VAL")))  #Write Register 

def AP_RD(inp, i):
    if GetData(inp, i, "DEL") != 0 : AddDelay(int(GetData(inp, i, "DEL")))
    f.write ("\tRdata = read_register(%s, 0x%s);" %(GetData(inp, i, "REG"), GetData(inp, i, "VAL")))  #Write Register
    f.write ("\n\tif (Rdata != 0x%s) {RdError = RdError + 1;} \n\n" %(GetData(inp, i, "VAL")))  #Write Register
    
def AP_RD_POLL(inp, i):  
    if GetData(inp, i, "DEL") != 0 : AddDelay(int(GetData(inp, i, "DEL")))
    f.write ("\tTimeoutMs(1);")
    f.write ("\n\twhile((read_register(%s)!=0x%s) && TIMEOUT_NOT_EXPIRED);" %(GetData(inp, i, "REG"),GetData(inp, i, "VAL")))  #Write Register
    f.write ("\n\tif(!TIMEOUT_NOT_EXPIRED) {PollError = PollError + 1;}\n\n")  #Write Register

def ScoreBoard(RdError, PollError):
    f.write ("\tprintf(\"\\t REG-TRACKER SCOREBOARD \\n\");\n")
    f.write ("\tif (RdError!= %d && PollError!= %d) \n\t\tprintf(\"Test Failed! RdError = %%s RdError = %%s \",RdError, PollError);\n" %(RdError,PollError))
    f.write ("\telse \n\t\tprintf(\"\\t Test Passed!\\n\");\n")

#################################################################################################################################################

def ExcelDetectPoll(inp):
    col_a = []
    for i in range(0,len(inp)):
        reg   = GetData(inp, i, "REG")
        typ   = GetData(inp, i, "TYP")
        if typ == "RD": col_a.append(reg)
    counts = Counter(col_a)
    RdPoll = [item for item, count in counts.items() if count >= 2]
    print(RdPoll)
    return RdPoll

def GetData(inp, i, typ): 
    #Returns Data in String Format
    if i < len(inp):
        if      typ    == "REG": return    (ProjectSpecifics(1) + inp[i].split("|")[4].strip())
        elif    typ    == "VAL": return    (inp[i].split("|")[7].strip()[-2:])
        elif    typ    == "TYP": return    (inp[i].split("|")[5].strip())  
        elif    typ    == "ACC": return    (inp[i].split("|")[8].strip())
        elif    typ    == "DEL": return int(inp[i].split("|")[9].strip()) 
        else:   print("INVALID TYP:%s" %typ) 
        return 0
    else:       
        print("INVALID LINE INDEX:%d" %i) 
        return 0
            
#################################################################################################################################################
        
def main():
    RdError,PollError = 0 , 0
    inp = []
    
    #Step 1: Print Project Specific Headers
    ProjectSpecifics(0)
    
    #Step 2: Open the given Input File and parse it to a list
    with open(args.file, encoding="utf8") as inputfile:
        for line in inputfile.readlines():
            if re.match(r'[(|)]', line): inp.append(line)
    
    #Step 3: Indetify Polling Registers
    RdPoll = ExcelDetectPoll(inp)      

    #Step 4: Iterate for each Register - Indetify type and call individual functions          
    for i in range(0,len(inp)):
        REG     = GetData(inp, i, "REG")
        VAL     = GetData(inp, i, "VAL")
        TYP     = GetData(inp, i, "TYP")
        DEL     = GetData(inp, i, "DEL")   
        
        if GetData(inp, i, "ACC") == "AP" : 
                               
            if REG in RdPoll and TYP == "RD":   
                AP_RD_POLL(inp, i); PollError = PollError + 1                            
            elif TYP == "RD" :   
                AP_RD(inp, i); RdError = RdError + 1
            elif TYP == "WR" : 
                AP_WR(inp, i)    
    
    #Step 5: Update Scoreboard look-up values      
    ScoreBoard(RdError, PollError)
    
    #Step 6: End and close Output file
    f.write ("\nreturn 0; } \n#endif \n")
    f.close()
#################################################################################################################################################
f= open("%s.c" %args.name,"w+")
main() #MAIN
#################################################################################################################################################
