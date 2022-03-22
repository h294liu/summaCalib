#!/usr/bin/env python
# coding: utf-8

# This code plots the parameter trace during a parameter estimation process.
# Note: This code plots the incomplete trace of samples because it reads sampels from ostOutput.txt.
# Only the parameter sets that improve the objective function in comparison with the previous parameter set are plotted.

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os, sys, argparse, datetime
from glob import glob
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt 
import xarray as xr
import pandas as pd
from matplotlib.dates import DateFormatter

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    # Positional mandatory arguments
    parser.add_argument('controlFile', help='path of the active control file.')
    parser.add_argument("experiment_id", help="a list of calibration experiment ids to be plotted",type=int)
    # when experiment_id = 0, it refers to files in the current calibration directory.
    
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

def is_number(s):
    try:
        float(s)
        return True 
    except (ValueError,AttributeError):
        return False 
                    

def concat_timestep_output(control_file):
    
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
    outputPath = read_from_summa_route_control(summa_filemanager, 'outputPath')
    outFilePrefix = read_from_summa_route_control(summa_filemanager, 'outFilePrefix')
    
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

#                 print("combining file %d %s" % (i,file))
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
    return

# main
if __name__ == '__main__':
    
    # an example: python 1_plot_param_trace.py ../control_active.txt

    # --- process command line --- 
    # check args
    if len(sys.argv) < 2:
        print("Usage: %s <controlFile>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
    experiment_id = args.experiment_id
    
#     control_file = '/home/h294liu/project/proj/5_summaCalib/5_calib_test2/BowAtBanff5/calib/control_active.txt'
#     experiment_id = 4

    # --------------------------- Read settings -----------------------------
    # read paths from control_file.
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)
    
    # read calib path 
    calib_path = read_from_control(control_file, 'calib_path')
    if calib_path == 'default':
        calib_path = os.path.join(domain_path, 'calib')
    analysis_path = os.path.join(calib_path, 'analysis')

    # read new hydrologic model path
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')
    
    # read summa filemanager file paths from control_file.
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_dst_path, summa_settings_relpath)
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_settings_path, summa_filemanager)

    # read mizuRoute setting and control files paths from control_file.
    route_settings_relpath = read_from_control(control_file, 'route_settings_relpath')
    route_settings_path = os.path.join(model_dst_path, route_settings_relpath)
    route_control = read_from_control(control_file, 'route_control')
    route_control = os.path.join(route_settings_path, route_control)

    # identify plot output path and file
    output_path = os.path.join(analysis_path, '4_calculate_runoff_coeff')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    ofile_txt = os.path.join(output_path, 'experiment%d_runoff_coeff.txt'%(experiment_id)) 
   
    # --------------------------- End Read settings -----------------------------        
    
    # #### 1. Identify file paths and other information
    print('Identify file paths and other info.')
    # (1) read multiplier samples from OstOutput.txt 
    if experiment_id == 0:
        summa_output_path = read_from_summa_route_control(summa_filemanager, "outputPath")
        route_output_path = read_from_summa_route_control(route_control, '<output_dir>')
    else:
        archive_path = os.path.join(calib_path, 'output_archive', str(experiment_id))
        summa_output_path = archive_path
        route_output_path = archive_path
            
    # (input) summa and mizuRoute output files
    summa_outFilePrefix = read_from_summa_route_control(summa_filemanager, "outFilePrefix")
    summa_outFile = os.path.join(summa_output_path, summa_outFilePrefix+'_day.nc')
    
    route_outFilePrefix = read_from_summa_route_control(route_control, "<case_name>")
    route_outFile = os.path.join(route_output_path, route_outFilePrefix+'.mizuRoute.nc')

    # (input) segment id, observations, and time series configs.
    q_seg_index = int(read_from_control(control_file, 'q_seg_index')) # start from one.
    
    obs_file = read_from_control(control_file, 'obs_file')
    obs_unit = read_from_control(control_file, 'obs_unit')

    statStartDate = read_from_control(control_file, 'statStartDate') 
    statEndDate = read_from_control(control_file, 'statEndDate')

    time_format='%Y-%m-%d'
    statStartDate = datetime.datetime.strptime(statStartDate,time_format)
    statEndDate = datetime.datetime.strptime(statEndDate,time_format)    

    # #### 2. Read runoff from outputs and observations
    print('Read runoff.')
    ### 2.1 Read simulated and observed streamflow
    # --- read simulated flow (cms) --- 
    simVarName = 'IRFroutedRunoff'
    with xr.open_dataset(route_outFile) as f:
        time = f['time'].values
        sim  = f[simVarName][:,(q_seg_index-1)].values #(time, segments)
        df_sim = pd.DataFrame({'sim':sim},index = time)
        df_sim.index = pd.to_datetime(df_sim.index)

    # --- read observed flow (cfs or cms) --- 
    df_obs = pd.read_csv(obs_file, index_col='Date', na_values=["-99.0","-999.0","-9999.0"],
                         parse_dates=True, infer_datetime_format=True)  
    df_obs.columns = ['obs']
    
    # convert obs from cfs to cms
    if obs_unit == 'cfs':
        df_obs = df_obs/35.3147    
        
    # --- merge the two df based on time index--- 
    df_sim_eval = df_sim.truncate(before=statStartDate, after=statEndDate)
    df_obs_eval = df_obs.truncate(before=statStartDate, after=statEndDate)
    df_sim_obs = pd.concat([df_obs_eval, df_sim_eval], axis=1)
    df_sim_obs = df_sim_obs.dropna()
    
    # #### 3. Read rainfall from outputs (daily or sub-daily)
    print('Read precipitation.')
    pVarName = 'pptrate'    
    # Firstly, try to read from summa daily output.
    with xr.open_dataset(summa_outFile) as f_day:
        stateVar_list = list(f_day.keys())
        if pVarName in stateVar_list:
            time = f_day['time'].values
            p_data = f_day[pVarName].values #(time,hru)
            
        else:
            # Secondly, try to read form summa sub-daily output.
            # (1) identify the concatenated timestep summa output file
            summa_output_path = read_from_summa_route_control(summa_filemanager, "outputPath")
            summa_outFile_timestep = os.path.join(summa_output_path, summa_outFilePrefix+'_timestep.nc')
            
            # (2) concatenate timstep summa output files into one file
            if not os.path.exists(summa_outFile_timestep):
                concat_timestep_output(control_file)
            
            # (3) read sub-daily summa output.
            with xr.open_dataset(summa_outFile_timestep) as f_timestep:
                time = f_timestep['time'].values
                p_data = f_timestep[pVarName].values #(time,hru)

    # save precip into dataframe       
    df_p = pd.DataFrame(p_data,index = time) #(time,hru)
    df_p.index = pd.to_datetime(df_p.index) 
            
    # truncate precip dataframe based on time
    df_p = df_p.truncate(before=statStartDate, after=statEndDate)
    df_p = df_p.dropna()

    # calculate mean instant precip over a day, then convert unit. 1 kg/m2/s = 1 mm = 86400 mm/day.
    df_p_daily = df_p.resample('D').mean()* 86400 

    # #### 4. Read attribtues to get HRUarea
    print('Read attribute.')
    attributeFile = read_from_summa_route_control(summa_filemanager, 'attributeFile')
    attributeFile = os.path.join(summa_settings_path, attributeFile)
    with xr.open_dataset(attributeFile) as f:
        HRUarea = f['HRUarea'].values #(hru), m^2
    total_area = np.sum(HRUarea) 
    
    # #### 5. Calculate runoff coefficient
    print('Calculate coefficient.')
    # runoff coefficient = total runoff / total precip
    total_runoff = df_sim_obs/total_area * 86400 * 1000 # cms/m2*86400*1000 -> mm/day 
    total_runoff = total_runoff.sum(axis=0) # (obs, sim), cms. # mm
        
    total_p = df_p_daily.sum(axis=0)*HRUarea # total p per hru, then * hru area = (time). # mm*m2.
    total_p = total_p.sum()/total_area  # mm # ie, hru area-weighted precip
    
    coeff_sim =  total_runoff['sim']/total_p
    coeff_obs =  total_runoff['obs']/total_p
    
    print('total_runoff_sim = %.2fmm, total_runoff_obs = %.2fmm, total_p = %.2fmm'%(total_runoff['sim'],total_runoff['obs'],total_p))
    print('coeff_sim = %.2f, coeff_obs =%.2f'%(coeff_sim, coeff_obs))
    
    f = open(ofile_txt, "w")
    f.write('statStartDate=%s\n'%(statStartDate))
    f.write('statEndDate=%s\n'%(statEndDate))
    f.write('total_p = %.2fmm\n'%(total_p))
    f.write('total_runoff_sim = %.2fmm\n'%(total_runoff['sim']))
    f.write('total_runoff_obs = %.2fmm\n'%(total_runoff['obs']))
    f.write('coeff_sim = %.2f\n'%(coeff_sim))
    f.write('coeff_obs = %.2f\n'%(coeff_obs))
   