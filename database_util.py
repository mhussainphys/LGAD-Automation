import time
import numpy as np
from numpy import loadtxt
import getpass
import os
import subprocess as sp
import socket
import sys
import glob


vmeRawDataDir = "/home/daq/Data/CMSTiming/"
scopeRawDataDir = "/home/daq/Data/NetScopeTiming/"
runRegistryDir = "/home/daq/Data/RunRegistry/"
fillRegistryDir = "/home/daq/Data/FillRegistry/"
labviewDirPath = "/media/network/a/LABVIEW PROGRAMS AND TEXT FILES/"

def run_exists(run_number, vors):
    if vors == 'vme':
        rawPath = "%s/RawDataSaver0CMSVMETiming_Run%i_0_Raw.dat" % (vmeRawDataDir, run_number)
    if vors == 'scope':
        rawPath = "%s/RawDataSaver0NetScopeTiming_Run%i_0_Raw.dat" % (scopeRawDataDir, run_number)        
    return os.path.exists(rawPath)

def run_registry_exists(run_number):
    rawPath = "%s/run%i.txt" % (runRegistryDir, run_number)
    print rawPath
    return os.path.exists(rawPath)

def get_run_number():

    labview_max = max([int(x.split("/media/network/a/LABVIEW PROGRAMS AND TEXT FILES/time_")[1].split(".txt")[0]) for x in glob.glob("/media/network/a/LABVIEW PROGRAMS AND TEXT FILES/time_*")])
    otsmax = max([int(x.split("/home/daq/Data/RunRegistry/run")[1].split(".txt")[0]) for x in glob.glob("/home/daq/Data/RunRegistry/run*")])
    run_number = max(labview_max,otsmax)
    return run_number


def get_next_run_number():
    #Find next run number, without conflict with labview or waveform files
    glob_arg = "%stime_*" %labviewDirPath
    split_arg = "%stime_" %labviewDirPath
    labview_max = max([int(x.split(split_arg)[1].split(".txt")[0]) for x in glob.glob(glob_arg)])

    glob_arg = "%srun*" %runRegistryDir
    split_arg = "%srun" %runRegistryDir
    #print glob_arg
    #print glob.glob(glob_arg)
    otsmax = max([int(x.split(split_arg)[1].split(".txt")[0]) for x in glob.glob(glob_arg)])
    next_run_number = max(labview_max,otsmax) + 1
    return next_run_number


def get_next_fill_num():
    path = "%s/next_fill_number.txt" % fillRegistryDir
    fill_number = open(path, "r")
    fill = int(fill_number.read())
    fill_number.close()
    return fill

def increment_fill_num():
    fill_number = get_next_fill_num()
    path = "%s/next_fill_number.txt" % fillRegistryDir
    fillNumberLog = open(path, "w")
    fillNumberLog.write(str(fill_number + 1))
    fillNumberLog.close()
    return

def append_fillfile(fill_number,run_number):
    fillFilePath = "%s/Fill%i.txt" % (fillRegistryDir,fill_number)
    fillFile = open(fillFilePath,"a")
    fillFile.write(str(run_number)+"\n")

def write_short_runfile(fill_number,run_number):
    runfile_handle = open("/home/daq/Data/RunRegistry/run%d.txt" % run_number, "w") 
    runfile_handle.write(str(run_number)+ "\n")
    runfile_handle.write(str(fill_number)+ "\n")
    runfile_handle.close()


def write_runfile(a, run_number, scan_number, vors, board_sn, bias_volt, laser_amp, laser_fre, amp_volt, scan_in, scan_stepsize, beam_spotsize, temp):
    runfile_handle = open("/home/daq/Data/RunRegistry/run%d.txt" % run_number, "a+") 
    runfile_handle.write(str(a) + "\n") #str(lab.motor_pos())
    runfile_handle.write(str(run_number)+ "\n")
    runfile_handle.write(str(scan_number)+ "\n")
    runfile_handle.write(vors+ "\n")
    runfile_handle.write(board_sn+ "\n")
    runfile_handle.write(bias_volt+ "\n")
    runfile_handle.write(laser_amp+ "\n")
    runfile_handle.write(laser_fre+ "\n")
    runfile_handle.write(amp_volt+ "\n")
    runfile_handle.write(scan_in+ "\n")
    runfile_handle.write(scan_stepsize+ "\n")
    runfile_handle.write(beam_spotsize+ "\n")
    runfile_handle.write(temp+ "\n")
    runfile_handle.close()

def write_scanfile(start_run_number, stop_run_number, scan_number, a, b, vors, board_sn, bias_volt, laser_amp, laser_fre, amp_volt, scan_in, scan_stepsize, beam_spotsize, temp):
    scanfile_handle = open("/home/daq/Data/ScanRegistry/scan%d.txt" % scan_number, "a+") 
    scanfile_handle.write(str(start_run_number)+ "\n")
    scanfile_handle.write(str(stop_run_number)+ "\n")
    scanfile_handle.write(str(scan_number)+ "\n")
    scanfile_handle.write(vors+ "\n")
    scanfile_handle.write(scan_in+ "\n")
    scanfile_handle.write(board_sn+ "\n")
    scanfile_handle.write(bias_volt+ "\n")
    scanfile_handle.write(laser_amp+ "\n")
    scanfile_handle.write(laser_fre+ "\n")
    scanfile_handle.write(amp_volt+ "\n")
    scanfile_handle.write(scan_stepsize+ "\n")
    scanfile_handle.write(beam_spotsize+ "\n")
    scanfile_handle.write(temp+ "\n")
    if scan_in == 'x' or scan_in == 'y':
        scanfile_handle.write(str(a)+ "\n") #Initial motor position
        scanfile_handle.write(str(b)+ "\n") #Final motor position
    elif scan_in == 't':
        scanfile_handle.write(str(a)+ "\n") #Single position
    scanfile_handle.close()

def append_scanfile(i, scan_number):
    scanfile_handle = open("/home/daq/Data/ScanRegistry/scan%d.txt" % scan_number, "a+") 
    scanfile_handle.write(i + "\n")
    scanfile_handle.close()

def process_runs(scan_number):
    print '############################PROCESSING RUNS#############################'
    #Calling a script to combine the trees and make text files for plotting.
    scan_lines = [line.rstrip('\n') for line in open("/home/daq/Data/ScanRegistry/scan%d.txt"  % scan_number)]
    start_run_number = scan_lines[0]
    stop_run_number = scan_lines[1]
    vors = scan_lines[3]
    if vors == 'vme':
        isvme = 1
    elif vors == 'scope':
        isvme = 0
    print 'Start run number: ', int(start_run_number)
    print 'Stop run number: ', int(stop_run_number)
    n_processed = 0
    for i in range (int(start_run_number), int(stop_run_number) + 1):   
        if run_exists(i,vors) and run_registry_exists(i):       
            run_lines = [line.rstrip('\n') for line in open("/home/daq/Data/RunRegistry/run%d.txt"  % i)]
            motor_pos = run_lines[0]
            print 'Motor position: ', float(motor_pos)
            combineCmd = ''' root -l -q 'combine.c("%s",%d,%d,%f)' ''' % (str(i),scan_number,isvme, float(motor_pos))
            os.system(combineCmd)
            n_processed = n_processed + 1
    print 'Processed %i out of expected %i runs attempted in scan.' %(n_processed , int(stop_run_number)-int(start_run_number)+1)


def dattoroot(scan_number):
    print '############################CONVERTING TO ROOT FILES#############################'
    scan_lines = [line.rstrip('\n') for line in open("/home/daq/Data/ScanRegistry/scan%d.txt"  % scan_number)]
    start_run_number = scan_lines[0]
    stop_run_number = scan_lines[1]
    vors = scan_lines[3]

    print 'Start run number: ', int(start_run_number)
    print 'Stop run number: ', int(stop_run_number)
    n_processed = 0
    for i in range (int(start_run_number), int(stop_run_number) + 1):   
        if run_exists(i,vors) and run_registry_exists(i):
            if vors == 'vme':
                isvme = 1
                dattorootCmd = ". /home/daq/TimingDAQ/dattoroot.sh /home/daq/Data/CMSTiming/RawDataSaver0CMSVMETiming_Run%i_0_Raw.dat /home/daq/Data/CMSTiming/RawDataSaver0CMSVMETiming_Run%i_0_Raw.root" % ( i, i)        
            elif vors == 'scope':
                isvme = 0
                dattorootCmd = ". /home/daq/TimingDAQ/dattorootscope.sh /home/daq/Data/NetScopeTiming/RawDataSaver0NetScope_Run%i_0_Raw.dat /home/daq/Data/NetScopeTiming/RawDataSaver0NetScope_Run%i_0_Raw.root" %(i, i)       
            
            os.system(dattorootCmd);
            n_processed = n_processed + 1
    print 'Converted %i out of expected %i runs attempted in scan.' % (n_processed , int(stop_run_number)-int(start_run_number)+1)


def analysis_plot(scan_number):
    scan_lines = [line.rstrip('\n') for line in open("/home/daq/Data/ScanRegistry/scan%d.txt"  % scan_number)]
    vors = scan_lines[3]
    if vors == 'vme':
        isvme = 1
    elif vors == 'scope':
        isvme = 0
    scan_in = scan_lines[4]
    if scan_in == 'x' or scan_in == 'y':
        istime = 0 
    elif scan_in == 't':
        istime = 1
    os.system(''' root -l 'plot.c(%d,%d,%d)' ''' % (scan_number,isvme, istime))




def processing_lab_meas(fill_number):
    scan_lines = [line.rstrip('\n') for line in open("/home/daq/Data/ScanRegistry/scan%d.txt"  % scan_number)]
    vors = scan_lines[3]
    if vors == 'vme':
        isvme = 1
    elif vors == 'scope':
        isvme = 0
    scan_in = scan_lines[4]
    if scan_in == 'x' or scan_in == 'y':
        istime = 0 
    elif scan_in == 't':
        istime = 1
    os.system(''' root -l 'plot.c(%d,%d,%d)' ''' % (scan_number,isvme, istime))

def sync_labview_files(run_number):
    #ots file 
    ots_file_name = "/media/network/a/LABVIEW PROGRAMS AND TEXT FILES/timestamp%d.txt" % run_number
    ots_time_list = loadtxt(ots_file_name, delimiter=' ', unpack=False).tolist()
    otstime_lines = [line.rstrip('\n') for line in open(ots_file_name)]
    ots_time_start = otstime_lines[0]
    ots_time_stop = otstime_lines[len(otstime_lines) - 1]

    #labview files
    labview_file_list = [int(x.split("/media/network/a/LABVIEW PROGRAMS AND TEXT FILES/FNAL_Testbeam/lab_meas_raw_")[1].split(".txt")[0]) for x in glob.glob("/media/network/a/LABVIEW PROGRAMS AND TEXT FILES/FNAL_Testbeam/lab_meas_raw_*")]
    exact_labview_file_start = min(labview_file_list, key=lambda x:abs(x-float(ots_time_start)))
    exact_labview_file_stop = min(labview_file_list, key=lambda x:abs(x-float(ots_time_stop)))
    index_labview_file_start = labview_file_list.index(int(exact_labview_file_start))
    index_labview_file_stop = labview_file_list.index(int(exact_labview_file_stop))


    for i in range(len(ots_time_list)):
        #Current file
        labview_file_name = "/media/network/a/LABVIEW PROGRAMS AND TEXT FILES/FNAL_Testbeam/lab_meas_raw_%d.txt" % exact_labview_file_start       
        labview_array = loadtxt(labview_file_name, delimiter=' ', unpack=False)
        labview_time_list = labview_array[:,0].tolist() 

        current_labview_file_time = index_labview_file_start
        next_labview_file_time = labview_file_list(index_labview_file_start + 1)
        
        if ots_time_list[i] < next_labview_file_time and ots_time_list[i] >= current_labview_file_time:
            labview_time = min(labview_time_list, key=lambda x:abs(x-float(ots_time_list[i])))
            index_labview_time = labview_time_list.index(float(labview_time))
            synced_array[i,:] = labview_array[i,:]
        else:
            index_labview_file_start = index_labview_file_start + 1

    np.savetxt('lab_meas_raw_%d.txt', synced_array, delimiter=' ') % run_number

