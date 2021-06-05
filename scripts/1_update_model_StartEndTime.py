#!/usr/bin/env python
# coding: utf-8

# #### Create a priori trial parameter file (trialParam.priori.nc) ####
# Given a list of to-be-evaluated parameters, create their corresponding a priori parameter values. 
# 1. update outputControl.txt by adding parameter names.
# 2. update fileManager.txt by changing simStartTime and simEndTime.
# 2. run SUMMA model to get a priori parameter values in summa outp
# 3. extract a priori parameter values from summa output and generate trialParam.priori.nc.

# import module
import os, sys, argparse, shutil, datetime
import netCDF4 as nc
import numpy as np

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    parser.add_argument('controlFile', help='path of the active control file.')
    args = parser.parse_args()
    return(args)

# Function to extract a given setting from the configuration file
def read_from_control(control_file, setting):
    
    # Open 'control_active.txt' and locate the line with setting
    with open(control_file) as ff:
        for line in ff:
            line = line.strip()
            if line.startswith(setting):
                break
    # Extract the setting's value
    substring = line.split('|',1)[1].split('#',1)[0].strip() 
    # Return this value    
    return substring

# Function to extract a given setting from the summa and mizuRoute manager/control files
def read_from_summa_mizuRoute_control(control_file, setting):

    # Open fileManager.txt or route_control and locate the line with setting
    with open(control_file) as ff:
        for line in ff:
            line = line.strip()
            if line.startswith(setting):
                break
    # Extract the setting's value
    substring = line.split('!',1)[0].strip().split(None,1)[1].strip("'")
    # Return this value    
    return substring


# main
if __name__ == '__main__':
    
    # an example: python update_sim_StartEndTime.py ../control_active.txt

    # --- process command line --- 
    # check args
    if len(sys.argv) != 2:
        print("Usage: %s <controlFile>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
    
    # read paths from control_file.
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)

    # read new hydrologic model path.
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')
    summa_setting_path = os.path.join(model_dst_path, 'settings/SUMMA')
    route_setting_path = os.path.join(model_dst_path, 'settings/mizuRoute')

    # read simulation start and end time from control_file.
    simStartTime = read_from_control(control_file, 'simStartTime')
    simEndTime = read_from_control(control_file, 'simEndTime')

    # #### 1. Update fileManager.txt by changing simStartTime and simEndTime. 
    # identify fileManager.txt and a temporary file. 
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager_temp = summa_filemanager.split('.txt')[0]+'_temp.txt'

    summa_filemanager = os.path.join(summa_setting_path, summa_filemanager)
    summa_filemanager_temp = os.path.join(summa_setting_path, summa_filemanager_temp)

    # change sim times in fileManager.txt            
    with open(summa_filemanager, 'r') as src:
        with open(summa_filemanager_temp, 'w') as dst:
            for line in src:
                if line.startswith('simStartTime'):
                    simStartTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simStartTime_old, simStartTime)
                elif line.startswith('simEndTime'):
                    simEndTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simEndTime_old, simEndTime)
                dst.write(line)
    shutil.copy2(summa_filemanager_temp, summa_filemanager);
    os.remove(summa_filemanager_temp);


    # #### 2. Update mizuroute_control by changing simStartTime and simEndTime. 
    # identify mizuroute_control and a temporary file. 
    mizuroute_control = read_from_control(control_file, 'mizuroute_control')
    mizuroute_control_temp = mizuroute_control.split('.txt')[0]+'_temp.txt'

    mizuroute_control = os.path.join(route_setting_path, mizuroute_control)
    mizuroute_control_temp = os.path.join(route_setting_path, mizuroute_control_temp)

    # change sim times in mizuroute_control           
    with open(mizuroute_control, 'r') as src:
        with open(mizuroute_control_temp, 'w') as dst:
            for line in src:
                if line.startswith('<sim_start>'):
                    simStartTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simStartTime_old, simStartTime)
                elif line.startswith('<sim_end>'):
                    simEndTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simEndTime_old, simEndTime)
                dst.write(line)
    shutil.copy2(mizuroute_control_temp, mizuroute_control);
    os.remove(mizuroute_control_temp);
