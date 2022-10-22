#!/usr/bin/env python
# coding: utf-8

# #### Define multiplier lower/upper bounds ####
# Given the default parameter values and lower/upper bounds in localParam.txt and basinParam.txt, determine globally constant multiplier lower/upper bounds.
# 1. Determine evaluated multipliers.
# 2. Read default parameter values and lower/upper limits.
# 3. Determine multiplier lower/upper bounds.
# 4. Save param and multiplier information into text.

# import module
import os, sys, argparse, shutil
import numpy as np
import xarray as xr

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

# Function to extract the param limits from basinParam and localParam.txt.
def read_basinParam_localParam(filename):
    param_names = []
    param_min = []
    param_max =[]
    with open (filename, 'r') as f:
        for line in f:
            line=line.strip()
            if line and not line.startswith('!') and not line.startswith("'"):
                splits=line.split('|')
                if isinstance(splits[0].strip(), str):
                    param_names.append(splits[0].strip())
                    param_min.append(str_to_float(splits[2].strip()))
                    param_max.append(str_to_float(splits[3].strip()))
    return param_names, param_min, param_max

# Function to convert data from Fortran format to scientific format.
def str_to_float(data_str):
    if 'd' in data_str:
        x = data_str.split('d')[0]+'e'+data_str.split('d')[1]
        return float(x)
    else:
        return float(data_str)


# main
if __name__ == '__main__':
    
    # an example: python 4_prepare_multp_bounds.py control_active.txt

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

    # read calib path
    calib_path = read_from_control(control_file, 'calib_path')
    if calib_path == 'default':
        calib_path = os.path.join(domain_path, 'calib')


    # #### 1. Determine evaluated multipliers 
    object_params = read_from_control(control_file, 'object_parameters')    # users provided object params.
    object_multps = [x.strip()+'_multp' for x in object_params.split(',')]  # a list of params to be evaluated. 

    # add thickness if heightCanopyTop is included in object_parameters.
    if 'heightCanopyTop' in object_params:
        object_multps.append('thickness'+'_multp')  
        object_multps.remove('heightCanopyTop'+'_multp')


    # #### 2. Read param lower/upper limits
    # read variable range from Local and Basin param files
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_setting_path = os.path.join(model_dst_path, summa_settings_relpath)

    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_setting_path, summa_filemanager)

    basinParam = read_from_summa_route_control(summa_filemanager, 'globalGruParamFile')
    localParam = read_from_summa_route_control(summa_filemanager, 'globalHruParamFile')

    basinParam = os.path.join(summa_setting_path, basinParam)
    localParam = os.path.join(summa_setting_path, localParam)

    basin_param_names, basin_param_min, basin_param_max = read_basinParam_localParam(basinParam)    
    local_param_names, local_param_min, local_param_max = read_basinParam_localParam(localParam)

    # #### 3. Read a priori param values
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_dst_path, summa_settings_relpath)

    trialParamFile = read_from_summa_route_control(summa_filemanager, 'trialParamFile')
    trialParamFile = os.path.join(summa_settings_path, trialParamFile)

    trialParamFile_priori = trialParamFile.split('.nc')[0] + '.priori.nc' # a priori param file
    trialParamFile_priori = os.path.join(summa_settings_path, trialParamFile_priori)
 
    # #### 4. Determine multiplier lower/upper bounds
    # Determine min and max for multipliers
    multp_bounds_list = []   # list of [multilier name, initial, lower, upper]. 

    with xr.open_dataset(trialParamFile_priori) as f:
        for i in range(len(object_multps)):
            multp_name = object_multps[i]
            param_name = multp_name.replace('_multp','')

            # (1) read priori param values
            if param_name != 'thickness': 
                param_priori_array = f[param_name].values                                     
            elif param_name == 'thickness': 
                bottom_priori_array = f['heightCanopyBottom'].values
                top_priori_array = f['heightCanopyTop'].values
                param_priori_array = top_priori_array - bottom_priori_array
            
            param_priori_array_shp = np.shape(param_priori_array)
            param_priori_ma = np.ma.masked_array(param_priori_array, mask=(param_priori_array==0.0))
            if all(param_priori_array == 0.0):
                print('Error: Parameter %s a-prioir values are all 0.0, \
                so the mutiplier-based calibration is not applicable to it.' %(param_name))
                sys.exit()
        
            # (2) get param upper and lower limits                
            if param_name in local_param_names:
                if param_name != 'theta_sat': 
                    index   = local_param_names.index(param_name)
                    param_min = local_param_min[index]*np.ones(param_priori_array_shp)
                    param_max = local_param_max[index]*np.ones(param_priori_array_shp)              
                
                elif param_name == 'theta_sat': 
                    index   = local_param_names.index(param_name)

                    # min 'theta_sat' should be larger than the max of all other soil_params.
                    with xr.open_dataset(trialParamFile_priori) as f:
                        soil_params = ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity']

                        # collect a-priori values
                        soil_params_priori_layers = np.ones((len(f[param_name]),len(soil_params)+1))                    
                        for i in range(len(soil_params)):
                            soil_param = soil_params[i]
                            soil_params_priori_layers[:,i] = f[soil_param].values

                        soil_params_priori_layers[:,-1] = local_param_min[index]*np.ones(param_priori_array_shp)                 
                        param_min = np.max(soil_params_priori_layers, axis=1)
                        param_max = local_param_max[index]*np.ones(param_priori_array_shp)

            elif param_name in basin_param_names:
                if param_name != 'routingGammaScale': 
                    index   = basin_param_names.index(param_name)
                    param_min = basin_param_min[index]*np.ones(param_priori_array_shp)
                    param_max = basin_param_max[index]*np.ones(param_priori_array_shp)

                elif param_name == 'routingGammaScale': 
                    # calculate scale bounds based on GRU river length and runoff velocity.
                    # (a) calculate gru streamline length (m)
                    # assume GRU is a round circle, take its radius as the mean chennel length. 
                    
                    attributeFile = read_from_summa_route_control(summa_filemanager, 'attributeFile')
                    attributeFile = os.path.join(summa_setting_path, attributeFile)
                    with xr.open_dataset(attributeFile) as ds:
                        nGRU = ds.dims['gru']
                        domain_area = ds['HRUarea'].values.sum()

                    GRU_area = domain_area/nGRU  # mean GRU area in square meter
                    GRU_channel_length = np.sqrt(GRU_area/np.pi)  # mean GRU chennel length in meter

                    # (b) calculate routingGammaScale lower and upper bounds.
                    # assume lower and upper runoff velocity
                    v_lower, v_upper = 0.1, 10 # unit: m/s # v_lower, v_upper = 0.01, 10
                    param_min = np.divide((GRU_channel_length/v_upper), param_priori_array)
                    param_max = np.divide((GRU_channel_length/v_lower), param_priori_array)

            elif param_name == 'thickness': 
                # read bottom and top heights
                index = local_param_names.index('heightCanopyBottom')
                bottom_min = local_param_min[index]*np.ones(param_priori_array_shp)
                bottom_max = local_param_max[index]*np.ones(param_priori_array_shp)   

                index = local_param_names.index('heightCanopyTop')
                top_min = local_param_min[index]*np.ones(param_priori_array_shp)
                top_max = local_param_max[index]*np.ones(param_priori_array_shp)    

                # get lower/upper bounds
                param_min = top_min - bottom_min
                param_max = top_max - bottom_max

            else:
                print('Error: Parameter %s does not exist in localParam.txt and basinParam.txt'%(param_name))
                sys.exit()


            # (3) determine multiplier feasible range
            multp_min = np.max(param_min/param_priori_ma)
            multp_max = np.min(param_max/param_priori_ma)
            
            if multp_min>=multp_max:
                print('Error: %s multiplier does not have a feasible range (multp_min>=multp_max).'%(param_name))
                sys.exit()
    
            # (4) update initial multiplier value.
            # When lower_bound < 1 < upper_bound, set initial multp = 1.0.
            # If not, set initial multp = 0.5*(lower_bound + upper_bound).
            if (multp_max<1) or (multp_min>1): 
                multp_initial = np.nanmean([multp_min, multp_max])
            else:
                multp_initial = 1.0            
            multp_bounds_list.append([multp_name, multp_initial, multp_min, multp_max]) 


    # #### 5. Save multiplier information into text.
    multp_bounds = read_from_control(control_file, 'multp_bounds')
    multp_bounds = os.path.join(calib_path, multp_bounds)
    np.savetxt(multp_bounds, multp_bounds_list, fmt='%s', delimiter=',',header='MultiplierName,InitialValue,LowerLimit,UpperLimit.')    
