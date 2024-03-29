# concatenate the outputs of a split domain summa run
# Authors: Manab Saharia, Hongli Liu, Andy Wood. 

import os, sys
from glob import glob
import netCDF4 as nc
import numpy as np
import argparse
from datetime import datetime
import concurrent.futures

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

# Function to read g(h)ru dimensioned variable values and return a dictionary.
def concat_summa_outputs(file):  
    # Employ global variables: gru_vars_num, gru_vars, hru_vars_num, hru_vars.
    Dict = {}
    f = nc.Dataset(file) 
    # Read and store variables into Dict
    for j in range(gru_vars_num):
        gru_var_name = gru_vars[j][0]
        data=f.variables[gru_var_name][:].data
        Dict[gru_var_name]=data
                
    for j in range(hru_vars_num):
        hru_var_name = hru_vars[j][0]
        data=f.variables[hru_var_name][:].data
        Dict[hru_var_name]=data            
    return Dict


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
    path_setting = args.path_setting
    suffix = args.suffix

#     # Example:
#     control_file='/home/h294liu/scratch/7_nelson/valid/XNELSON/calib/control_active.txt'
#     path_setting = 'outputPath'
#     suffix = 'day'
    
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
    merged_output_file = os.path.join(outputPath,outFilePrefix+'_' + suffix + '.nc') # Be careful. Hard coded.

    # # #### 2. Count number of g(h)rus and g(h)ruId list
    gru_num = 0
    hru_num = 0
    gru_list = []
    hru_list = []
    for file in outfilelist:
        f = nc.Dataset(file)
        gru_num = gru_num+len(f.dimensions['gru'])
        hru_num = hru_num+len(f.dimensions['hru'])
        
        gru_list.extend(list(f.variables['gruId'][:].data))
        hru_list.extend(list(f.variables['hruId'][:].data))
        
    # # #### 3. Get g(h)ru dimensioned variables and build base dictionary for storage
    Dict = {} 
    with nc.Dataset(outfilelist[0]) as src:
        
        time_num = len(src.dimensions['time'])
        
        # 3-1. identify g(h) dimensioned variables
        gru_vars = [] # variable name, gru axis in variable dimension for concatenation. 
        hru_vars = []
        for name, variable in src.variables.items():
            # Assign different values depending on dimension
            dims = variable.dimensions
            if 'gru' in dims:
                gru_vars.append([name,dims.index('gru')])                
            elif 'hru' in dims:
                hru_vars.append([name,dims.index('hru')]) 
        gru_vars_num = len(gru_vars)
        hru_vars_num = len(hru_vars)
        
        # 3-2. create the base dictionary Dict
        for j in range(gru_vars_num):
            gru_var_name = gru_vars[j][0]
            dim_index = gru_vars[j][1]
            if dim_index == 0:
                Dict[gru_var_name]=np.zeros((gru_num,))
            elif dim_index == 1:
                Dict[gru_var_name]=np.zeros((time_num,gru_num))
            else:
                print('Variable %s has more than two dimensions: time and gru. '%(gru_var_name))
                sys.exit()
        for j in range(hru_vars_num):
            hru_var_name = hru_vars[j][0]
            dim_index = hru_vars[j][1]
            if dim_index == 0:
                Dict[hru_var_name]=np.zeros((hru_num,))
            elif dim_index == 1:
                Dict[hru_var_name]=np.zeros((time_num,hru_num))
            else:
                print('Variable %s has more than two dimensions: time and hru. '%(gru_var_name))
                sys.exit()
    
    # # #### 4. Loop summa output files, parallel reading and serial saving.  
    # reference: https://docs.python.org/3/library/concurrent.futures.html
    print('concatenate outputs')
    start_time = datetime.now()   
    with concurrent.futures.ProcessPoolExecutor() as executor:    
        for file_i, Dict_i in zip(outfilelist, executor.map(concat_summa_outputs, outfilelist)):
            f = nc.Dataset(file_i) 

            # get gru and hru indices of file_i
            gruId = list(f.variables['gruId'][:].data)
            gru_start_idx = gru_list.index(gruId[0])
            gru_end_idx = gru_list.index(gruId[-1])

            hruId = list(f.variables['hruId'][:].data)
            hru_start_idx = hru_list.index(hruId[0])
            hru_end_idx = hru_list.index(hruId[-1])

            # store Dict_i variables into Dict
            for j in range(gru_vars_num):
                gru_var_name = gru_vars[j][0]
                dim_index = gru_vars[j][1]
                if dim_index == 0:
                    Dict[gru_var_name][gru_start_idx:gru_end_idx+1]=Dict_i[gru_var_name]
                elif dim_index == 1:
                    Dict[gru_var_name][:,gru_start_idx:gru_end_idx+1]=Dict_i[gru_var_name]

            for j in range(hru_vars_num):
                hru_var_name = hru_vars[j][0]
                dim_index = hru_vars[j][1]
                if dim_index == 0:
                    Dict[hru_var_name][hru_start_idx:hru_end_idx+1]=Dict_i[hru_var_name]
                elif dim_index == 1:
                    Dict[hru_var_name][:,hru_start_idx:hru_end_idx+1]=Dict_i[hru_var_name]
    print(datetime.now() - start_time)

    # # #### 5. Write output    
    print('write outputs')
    start_time = datetime.now()    
    with nc.Dataset(outfilelist[0]) as src:
        with nc.Dataset(merged_output_file, "w") as dst:

            # copy dimensions
            for name, dimension in src.dimensions.items():
                if name == 'gru':
                    dst.createDimension(name, gru_num)
                elif name == 'hru':
                    dst.createDimension(name, hru_num)
                else:
                    dst.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

            # copy variable attributes all at once via dictionary
            for name, variable in src.variables.items():
                x = dst.createVariable(name, variable.datatype, variable.dimensions)               
                dst[name].setncatts(src[name].__dict__)
                # Note here the variable dimension name is the same, but size has been updated for gru and hru.

                # Assign different values depending on dimension
                dims = variable.dimensions
                if not ('gru' in dims) and not ('hru' in dims):
                    dst[name][:]=src[name][:]                

            # assign values for gru and hru dimensioned variables
            for j in range(gru_vars_num):
                dst.variables[gru_vars[j][0]][:] = Dict[gru_vars[j][0]]
            for j in range(hru_vars_num):
                dst.variables[hru_vars[j][0]][:] = Dict[hru_vars[j][0]]

    print(datetime.now() - start_time)
