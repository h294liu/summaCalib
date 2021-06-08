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
    
    # an example: python 3_prepare_priori_trialParam.py control_active.txt

    # --- process command line --- 
    # check args
    if len(sys.argv) != 2:
        print("Usage: %s <controlFile>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
    
    # read paths from control_file
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)

    # read new hydrologic model path
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_setting_path = os.path.join(model_dst_path, summa_settings_relpath)


    # #### 1. Update summa outputControl.txt by adding parameter names.
    # determine summa output parameters
    object_params = read_from_control(control_file, 'object_parameters')  # users provided object params
    output_params = [x.strip() for x in object_params.split(',')]        # a more complete list of params that should be output in a priori parameter file 

    # add more parameters if soil water content parameters are included in object_params.
    soil_params = ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity', 'theta_sat']
    if any(soil_param in object_params for soil_param in soil_params):
        for soil_param in soil_params:
            if not soil_param in object_params:
                output_params.append(soil_param)            

    # identify outputControl.txt and a temporary file.
    summa_filemanager = os.path.join(summa_setting_path, read_from_control(control_file, 'summa_filemanager'))
    outputControlFile = read_from_summa_route_control(summa_filemanager, 'outputControlFile')

    outputControlFile_temp = outputControlFile.split('.txt')[0]+'_temp.txt'
    outputControlFile = os.path.join(summa_setting_path, outputControlFile)
    outputControlFile_temp = os.path.join(summa_setting_path, outputControlFile_temp)

    # add output_params to outputControl.txt            
    with open(outputControlFile, 'r') as src:
        content = src.read()
        with open(outputControlFile_temp, 'w') as dst:
            for param in output_params:
                if not param in content:
                    dst.write(param)
                    dst.write('\n')
            dst.write(content)
    shutil.copy2(outputControlFile_temp, outputControlFile);
    os.remove(outputControlFile_temp);

    
    # #### 2. Update fileManager.txt by changing simStartTime and simEndTime. 
    simStartTime = read_from_control(control_file, 'simStartTime')
    simStartTime_priori = simStartTime # in format 'yyyy-mm-dd hh:mm'
    simEndTime_priori = datetime.datetime.strftime(datetime.datetime.strptime(simStartTime, '%Y-%m-%d %H:%M') + datetime.timedelta(days=1), '%Y-%m-%d %H:%M') 

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
                    line = line.replace(simStartTime_old, simStartTime_priori)
                elif line.startswith('simEndTime'):
                    simEndTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simEndTime_old, simEndTime_priori)
                dst.write(line)
    shutil.copy2(summa_filemanager_temp, summa_filemanager);
    os.remove(summa_filemanager_temp);


    # #### 3. Run SUMMA model to get a priori parameter values in summa outp
    # summa executable and settings paths 
    summa_exe_path = read_from_control(control_file, 'summa_exe_path')

    # create summa output path if it does not exist.
    outputPath = read_from_summa_route_control(summa_filemanager, 'outputPath')
    if not os.path.exists(outputPath):
        print('outputPath does not exist. Create it.')
        os.makedirs(outputPath)

    # run SUMMA
    cmd = summa_exe_path + ' -m '+ summa_filemanager
    os.system(cmd)


    # #### 4. Extract a priori parameter values from summa output and generate trialParam.priori.nc.
    # specify summa output, attribtue, and trialParam files
    outFilePrefix = read_from_summa_route_control(summa_filemanager, 'outFilePrefix')
    summa_ofile = os.path.join(outputPath, outFilePrefix+'_timestep.nc')

    trialParamFile = read_from_summa_route_control(summa_filemanager, 'trialParamFile')
    trialParamFile_priori = trialParamFile.split('.nc')[0] + '.priori.nc' # a priori param file

    trialParamFile = os.path.join(summa_setting_path, trialParamFile)
    trialParamFile_priori = os.path.join(summa_setting_path, trialParamFile_priori)

    attributeFile = read_from_summa_route_control(summa_filemanager,'attributeFile')
    attributeFile = os.path.join(summa_setting_path, attributeFile)

    # open summa output file for reading
    with nc.Dataset(summa_ofile, 'r') as ff:

        # if trialParamFile does not exist, create trialParamFile based on attributeFile.
        if not os.path.exists(trialParamFile):
            with nc.Dataset(attributeFile) as src:
                with nc.Dataset(trialParamFile, "w") as dst:

                    # copy dimensions
                    for name, dimension in src.dimensions.items():
                         dst.createDimension(
                            name, (len(dimension) if not dimension.isunlimited() else None))

                    # copy gurId and hruId variables
                    include = ['gruId', 'hruId']
                    for name, variable in src.variables.items():
                        if name in include:
                            x = dst.createVariable(name, variable.datatype, variable.dimensions)               
                            dst[name].setncatts(src[name].__dict__)
                            dst[name][:]=src[name][:] 

                    # create parameter varibles 
                    for param_name in output_params:
                        param_value = ff[param_name][:].flat[0] # the first element of the array regardless dimensions                    
                        summa_ofile_dims = ff[param_name].dimensions
                        if 'hru' in summa_ofile_dims:
                            param_dim = 'hru'
                        elif 'gru' in summa_ofile_dims:
                            param_dim = 'gru'
                        else:
                            print('Variable %s is not in dimension gru or hru in summa outp'%(param_name))
                            sys.exit()

                        dst.createVariable(param_name, 'float', param_dim, fill_value=np.nan) 
                        dst[param_name][:] = param_value

        # if trialParamFile exists, add to trialParamFile based on attributeFile.
        else:
            with nc.Dataset(attributeFile) as src:
                with nc.Dataset(trialParamFile, "w") as dst:

                    # copy dimensions 
                    for name, dimension in src.dimensions.items():
                         dst.createDimension(
                            name, (len(dimension) if not dimension.isunlimited() else None))

                    # copy gurId and hruId variables
                    include = ['gruId', 'hruId']
                    for name, variable in src.variables.items():
                        if name in include:
                            x = dst.createVariable(name, variable.datatype, variable.dimensions)               
                            dst[name].setncatts(src[name].__dict__)
                            dst[name][:]=src[name][:] 

                    # create parameter varibles 
                    dst_vars=(dst.variables.keys()) # get all variable names of dst 
                    for param_name in output_params:
                        param_value = ff[param_name][:].flat[0] # the first element of the array regardless dimensions                    
                        summa_ofile_dims = ff[param_name].dimensions
                        if 'hru' in summa_ofile_dims:
                            param_dim = 'hru'
                        elif 'gru' in summa_ofile_dims:
                            param_dim = 'gru'
                        else:
                            print('Variable %s is not in dimension gru or hru in summa outp'%(param_name))
                            sys.exit()

                        if not param_name in dst_vars:                    
                            dst.createVariable(param_name, 'float', param_dim, fill_value=np.nan) 
                            dst[param_name][:] = param_value

    # copy trialParamFile to get trialParamFile_priori
    shutil.copy2(trialParamFile, trialParamFile_priori);
