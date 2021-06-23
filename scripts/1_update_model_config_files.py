#!/usr/bin/env python
# coding: utf-8

# #### Update simulation start and end times in fileManager.txt and mizuroute.control ####
# #### Update intput file name <fname_qsim> in mizuroute.control (eg, "run1_day.nc") ####

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
def read_from_summa_route_control(control_file, setting):

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
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_dst_path, summa_settings_relpath)
    route_settings_relpath = read_from_control(control_file, 'route_settings_relpath')
    route_settings_path = os.path.join(model_dst_path, route_settings_relpath)

    # read simulation start and end time from control_file.
    simStartTime = read_from_control(control_file, 'simStartTime')
    simEndTime = read_from_control(control_file, 'simEndTime')

    # #### 1. Update fileManager.txt by changing simStartTime and simEndTime. 
    # identify fileManager.txt and a temporary file. 
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager_temp = summa_filemanager.split('.txt')[0]+'_temp.txt'

    summa_filemanager = os.path.join(summa_settings_path, summa_filemanager)
    summa_filemanager_temp = os.path.join(summa_settings_path, summa_filemanager_temp)

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


    # #### 2. Update route_control by changing simStartTime and simEndTime. 
    # identify route_control and a temporary file. 
    route_control = read_from_control(control_file, 'route_control')
    route_control_temp = route_control.split('.txt')[0]+'_temp.txt'

    route_control = os.path.join(route_settings_path, route_control)
    route_control_temp = os.path.join(route_settings_path, route_control_temp)

    # change sim times in route_control           
    with open(route_control, 'r') as src:
        with open(route_control_temp, 'w') as dst:
            for line in src:
                if line.startswith('<sim_start>'):
                    simStartTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simStartTime_old, simStartTime)
                elif line.startswith('<sim_end>'):
                    simEndTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simEndTime_old, simEndTime)
                elif line.startswith('<fname_qsim>'):
                    fname_qsim_old = line.split('!',1)[0].strip().split(None,1)[1] # filename of input runoff from summa
                    outFilePrefix = read_from_summa_route_control(summa_filemanager, 'outFilePrefix') # summa outout FilePrefix
                    fname_qsim_old = outFilePrefix+'_day.nc'
                    line = line.replace(fname_qsim_old, fname_qsim_old)
                dst.write(line)
    shutil.copy2(route_control_temp, route_control);
    os.remove(route_control_temp);
