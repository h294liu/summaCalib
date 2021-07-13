#!/usr/bin/env python
# coding: utf-8

# create coldstate.nc based on summa model output.
# Authors: Hongli Liu

import os, sys, shutil 
from glob import glob
import pandas as pd
import netCDF4 as nc
import numpy as np
from datetime import datetime
import argparse

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    parser.add_argument('controlFile', help='path of the overall control file.')
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

if __name__ == '__main__':
    
    # an example: python concat_split_summa ../control_active.txt

    # ---------------------------- Preparation -------------------------------
    # --- process command line --- 
    # check args
    if len(sys.argv) < 2:
        print("Usage: %s <control_file>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile

#     control_file = '/home/h294liu/project/proj/5_summaCalib/5_calib_test4/BowAtBanff_prepare_state/calib/control_active.txt'
    
    # read paths from control_file.
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)

    # read new hydrologic model path from control_file.
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')

    # read summa settings and fileManager paths from control_file.
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_dst_path, summa_settings_relpath)
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_settings_path, summa_filemanager)

    # read summa output path and prefix.
    outputPath = read_from_summa_route_control(summa_filemanager, 'outputPath')
    outFilePrefix = read_from_summa_route_control(summa_filemanager, 'outFilePrefix')
    
    # -----------------------------------------------------------------------

    # state name list
    stateVar_list = ['dt_init', 'nSoil', 'nSnow', 'scalarCanopyIce', 'scalarCanopyLiq',
                     'scalarSnowDepth', 'scalarSWE', 'scalarSfcMeltPond', 'scalarAquiferStorage',
                     'scalarSnowAlbedo', 'scalarCanairTemp', 'scalarCanopyTemp', 'mLayerTemp',
                     'mLayerVolFracIce', 'mLayerVolFracLiq', 'mLayerMatricHead', 'iLayerHeight',
                     'mLayerDepth']        

    #### 1. Concatenate summa timstep output files into one file
    summa_outFile_timestep = os.path.join(outputPath,outFilePrefix+'_timestep.nc') # Be careful. Hard coded.
    if not os.path.exists(summa_outFile_timestep):
        os.system('python 3b_concat_split_summa.py %s timestep'%(control_file))

    #### 2.Save state values to new coldstate.nc
    with nc.Dataset(summa_outFile_timestep) as f:
        # read time from summa output
        time = f['time'] 
        dtime = nc.num2date(time[:],time.units,only_use_cftime_datetimes=False,only_use_python_datetimes=True)
        time_end_str = datetime.strftime(dtime[-1], "%Y_%m_%d_%H_%M_%S")
        
        # identify old and new state files    
        initConditionFile = read_from_summa_route_control(summa_filemanager, 'initConditionFile')
        initConditionFile_new = initConditionFile.split('.nc')[0]+ '_' + time_end_str + '.nc'
        
        initConditionFile = os.path.join(summa_settings_path,initConditionFile) 
        initConditionFile_new = os.path.join(summa_settings_path,initConditionFile_new)
        
        with nc.Dataset(initConditionFile) as src:
            with nc.Dataset(initConditionFile_new, "w") as dst:
                
                # copy dimensions
                # a list of dimension that needs update based on summa output
                dims = ['midSoil', 'midToto', 'ifcToto'] 
                for name, dimension in src.dimensions.items():
                    if name in dims:
                        # read dim length from summa output
                        dim_length = len(f.dimensions[name])
                        dst.createDimension(name, (dim_length if not dimension.isunlimited() else None))
                    else:
                        dst.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))
           
                # copy variable attributes 
                for name, variable in src.variables.items():
                    x = dst.createVariable(name, variable.datatype, variable.dimensions)               
                    dst[name].setncatts(src[name].__dict__)

                    # assign different values for targeted state variables
                    if name in stateVar_list:

                        state_xr = f[name] # read value from summa output # dims: (time,...,gru/hru)            
                        state_value = state_xr[time==time[-1]].data # extract value at the last time step   
                        dst[name][:] = state_value                  # assign to dst          
                   
                    # copy other variables from src
                    else:
                        dst[name][:] = src[name][:] 
