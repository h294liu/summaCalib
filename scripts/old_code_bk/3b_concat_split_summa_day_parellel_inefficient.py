#!/usr/bin/env python
# coding: utf-8
# concatenate the outputs of a split domain summa run

import os, sys, shutil, subprocess
from glob import glob
import netCDF4 as nc
import numpy as np
import argparse
# from joblib import Parallel, delayed
import multiprocessing as mp
from datetime import datetime
import concurrent.futures
from tqdm import tqdm

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    parser.add_argument('controlFile', help='path of the overall control file.')
    parser.add_argument('path_setting', default='outputPath', type=str,
                       help='Optional argument. Setting name in fileManger.txt for path of files to be concatenate. \
                       Example options: outputPath, statePath', )
    parser.add_argument('suffix', nargs='?', default='', type=str,
                       help='Optional argument. Suffix of summa output files to be concatenate. \
                       Example options: day, timestep, (none)', )
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

def split_summa_outputs(file):
    # get the new file names
    fileName = os.path.basename(file)           # split out the file name
    gruFile=os.path.join(gruPath, fileName)     # new file name
    hruFile=os.path.join(hruPath, fileName)     # new file name

    # extract the hru and gru variables - this is necessary because `ncrcat` 
    # concatenates along the record dimension. In SUMMA outputs, `time` is the
    # record (unlimited) dimension by default. This means that for gru variables
    # we need to make the 'gru' dimension the record dimension and for `hru` 
    # variables, `hru` needs to be the record dimension. Here we separate `gru`
    # and `hru` variables into two separate files.
    process = subprocess.run('ncks -h -O -C -v gru,gruId,averageRoutedRunoff_mean %s %s'%(file,gruFile),
                             shell=True, stdout=subprocess.PIPE)
    process = subprocess.run('ncks -h -O -C -x -v gru,gruId,averageRoutedRunoff_mean %s %s'%(file,hruFile),
                             shell=True, stdout=subprocess.PIPE)

     # reorder dimensions so that the gru/hru is the unlimited dimension, instead of time
    process = subprocess.run('ncpdq -h -O -a gru,time %s %s'%(gruFile,gruFile),
                             shell=True, stdout=subprocess.PIPE)
    process = subprocess.run('ncpdq -h -O -a hru,time %s %s'%(hruFile,hruFile),
                             shell=True, stdout=subprocess.PIPE)
    return 

if __name__ == '__main__':
    
    # an example: python concat_split_summa ../control_active.txt

    # ---------------------------- Preparation -------------------------------
#     # --- process command line --- 
#     # check args
#     if len(sys.argv) < 2:
#         print("Usage: %s <control_file>" % sys.argv[0])
#         sys.exit(0)
#     # otherwise continue
#     args = process_command_line()    
#     control_file = args.controlFile
#     path_setting = args.path_setting
#     suffix = args.suffix
    
    control_file='/home/h294liu/scratch/7_nelson/valid/XNELSON/calib/control_active.txt'
    path_setting = 'outputPath'
    suffix = 'day'
    
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

    # read summa output path and prefix
    outputPath = read_from_summa_route_control(summa_filemanager, path_setting)
    outFilePrefix = read_from_summa_route_control(summa_filemanager, 'outFilePrefix')
    
    # -----------------------------------------------------------------------

    # # #### 1. Read input and output arguments
    # get list of split summa output files (hard coded)
    outfilelist = glob((outputPath + outFilePrefix + '*G*' + suffix +'.nc'))   
    outfilelist.sort()   # not needed, perhaps
    outfilelist=outfilelist[50:] # for test only
    merged_output_file = os.path.join(outputPath,outFilePrefix+'_' + suffix + '.nc') # Be careful. Hard coded.

    # collect results from different files (parallel)
    
    print('CPU # is ',mp.cpu_count())
    
    # create folders gru and hru
    gruPath=os.path.join(outputPath,'gru')
    hruPath=os.path.join(outputPath,'hru')
    for folder in [gruPath, hruPath]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            os.makedirs(folder)
    
    combineFile  = outFilePrefix+'_' + suffix + '.nc' 
    gru_concat   = os.path.join(gruPath,combineFile)
    hru_concat   = os.path.join(hruPath,combineFile)    
    final_concat = os.path.join(outputPath,combineFile)
    
    print('split')
    start_time = datetime.now()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        tqdm(executor.map(split_summa_outputs, outfilelist))
    print(datetime.now() - start_time)
                      
    # concatenate the files -> Time consuming!
    print('Concatenating files')
    start_time = datetime.now()
    gru_filelist = gruPath+'/*G*'
    hru_filelist = hruPath+'/*G*'
    process = subprocess.run('ncrcat -h -O %s %s'%(gru_filelist, gru_concat), shell=True,stdout=subprocess.PIPE)
    process = subprocess.run('ncrcat -h -O %s %s'%(hru_filelist, hru_concat), shell=True,stdout=subprocess.PIPE)
    print(datetime.now() - start_time)

    # perturb dimensions - make time the unlimited dimension again -> Time consuming!
    print('Perturbing dimensions')
    start_time = datetime.now()
    process = subprocess.run('ncpdq -h -O -a time,gru %s %s'%(gru_concat,gru_concat), shell=True, stdout=subprocess.PIPE)
    process = subprocess.run('ncpdq -h -O -a time,hru %s %s'%(hru_concat,hru_concat), shell=True, stdout=subprocess.PIPE)
    print(datetime.now() - start_time)

    # combine gru and hru files
    print('Combining files')
    start_time = datetime.now()
    process = subprocess.run('cp %s %s'%(hru_concat, final_concat), shell=True, stdout=subprocess.PIPE)
    process = subprocess.run('ncks -h -A %s %s'%(gru_concat, final_concat), shell=True, stdout=subprocess.PIPE)
    print(datetime.now() - start_time)
