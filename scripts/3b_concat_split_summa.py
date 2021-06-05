# concatenate the outputs of a split domain summa run
# Authors: Manab Saharia, Hongli Liu, Andy Wood. 

import os, sys 
from glob import glob
import netCDF4 as nc
import numpy as np
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

if __name__ == '__main__':
    
    # an example: python concat_split_summa ../control_active.txt

    # ---------------------------- Preparation -------------------------------
    # --- process command line --- 
    # check args
    if len(sys.argv) != 2:
        print("Usage: %s <control_file>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
    
    # read paths from control_file.
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)

    # read new hydrologic model path from control_file.
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')

    # read summa settings and fileManager paths from control_file.
    summa_setting_path = os.path.join(model_dst_path, 'settings/SUMMA')
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_setting_path, summa_filemanager)

    # read summa output path and prefix
    outputPath = read_from_summa_mizuRoute_control(summa_filemanager, 'outputPath')
    outFilePrefix = read_from_summa_mizuRoute_control(summa_filemanager, 'outFilePrefix')
    
    # -----------------------------------------------------------------------

    # # #### 1. Read input and output arguments
    # get list of split summa output files (hard coded)
    outfilelist = glob((outputPath + outFilePrefix + '_G*_timestep.nc'))   # assumes daily outputs.
    outfilelist.sort()   # not needed, perhaps
    merged_output_file = os.path.join(outputPath,outFilePrefix+'_timestep.nc') # Be careful. Hard coded.

    # # #### 2. Count the number of gru and hru
    gru_num = 0
    hru_num = 0
    for file in outfilelist:
        f = nc.Dataset(file)
        gru_num = gru_num+len(f.dimensions['gru'])
        hru_num = hru_num+len(f.dimensions['hru'])

    # # #### 3. Write output    
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
            gru_vars = [] # variable name, gru axis in variable dimension for concatenation. 
            hru_vars = []
            for name, variable in src.variables.items():
                x = dst.createVariable(name, variable.datatype, variable.dimensions)               
                dst[name].setncatts(src[name].__dict__)
                # Note here the variable dimension name is the same, but size has been updated for gru and hru.

                # Assign different values depending on dimension
                dims = variable.dimensions
                if 'gru' in dims:
                    gru_vars.append([name,dims.index('gru')])                
                elif 'hru' in dims:
                    hru_vars.append([name,dims.index('hru')]) 
                else:
                    dst[name][:]=src[name][:]                

            # read values for gru and hru dimensioned variables
            Dict = {} 
            gru_vars_num = len(gru_vars)
            hru_vars_num = len(hru_vars)
            for i,file in enumerate(outfilelist):

                print("combining file %d %s" % (i,file))
                # f = nc.Dataset(os.path.join(outputPath, file))
                f = nc.Dataset(file)
                for j in range(gru_vars_num):
                    gru_var_name = gru_vars[j][0]
                    dim_index = gru_vars[j][1]
                    data=f[gru_var_name][:]
                    if i == 0:
                        Dict[gru_var_name]=data
                    else:
                        Dict[gru_var_name]=np.concatenate((Dict[gru_var_name],data),axis=dim_index)

                for j in range(hru_vars_num):
                    hru_var_name = hru_vars[j][0]
                    dim_index = hru_vars[j][1]
                    data=f[hru_var_name][:]
                    if i == 0:
                        Dict[hru_var_name]=data
                    else:
                        Dict[hru_var_name]=np.concatenate((Dict[hru_var_name],data),axis=dim_index)

            # assign values for gru and hru dimensioned variables
            for j in range(gru_vars_num):
                dst.variables[gru_vars[j][0]][:] = Dict[gru_vars[j][0]]
            for j in range(hru_vars_num):
                dst.variables[hru_vars[j][0]][:] = Dict[hru_vars[j][0]]

    print("wrote output: %s\nDone" % merged_output_file) 
