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
    output_path = os.path.join(analysis_path, '5_plot_state_variables')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    trialParamFile_temp = os.path.join(output_path, 'trialParam.temp.nc')  # temporary trialParam file   
    
    ofile_fig = os.path.join(output_path, 'experiment%d_best_state.png'%(experiment_id))  # output plot figure
    ofile_txt = os.path.join(output_path, 'experiment%d_best_summary.txt'%(experiment_id))  # output best param information
   
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

    # #### 2. Read model route outputs and observations (streamflow)
    print('Read model outputs and observations.')
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
    
     ### 2.2 Read summa outputs (states)
    # (1) read simulated states  
    with xr.open_dataset(summa_outFile) as f:
        time = f['time'].values
        stateVar_list = list(f.keys())
        stateVar_list_plot = stateVar_list.copy()
        for x in ['time','hru','gru','hruId','gruId']:
            if x in stateVar_list:
                stateVar_list_plot.remove(x)
        stateVar_num = len(stateVar_list_plot)
        
        # read each state variable and calculate GRU/HRU mean value
        for i in range(stateVar_num):
            stateVarName = stateVar_list_plot[i]
            stateVar_long_name = f[stateVarName].attrs['long_name']
            stateVar_units = f[stateVarName].attrs['units']
            stateVar_data = np.nanmean(f[stateVarName].values, axis=1) #(time,hru) or (time,gru)
            
            # save state data into dataframe
            if i == 0:
                df_state = pd.DataFrame({stateVarName:stateVar_data},index = time)
                df_sim.index = pd.to_datetime(df_sim.index)         
                stateVar_long_name_list = [stateVar_long_name]
                stateVar_units_list = [stateVar_units]
            else:
                df_state[stateVarName] = stateVar_data
                stateVar_long_name_list.append(stateVar_long_name)
                stateVar_units_list.append(stateVar_units)    

    # (2) truncate state dataframe based on time
    df_state = df_state.truncate(before=statStartDate, after=statEndDate)
    df_state = df_state.dropna()

    ### 2.3 Read summa outputs (rainfall and temperature forcing)
    # This step is conducted only if forcing outputs are in sub-daily output timestep. 
    # Otherwise, daily forcing outputs have been read in step 2.2.
#     forcing_list_plot = ['pptrate', 'airtemp']
    forcing_list_plot = []
    for item in ['pptrate', 'airtemp']:
        if item not in stateVar_list_plot:
            forcing_list_plot.append(item)
    forcing_num = len(forcing_list_plot)
    
    if forcing_num>0:
        # (1) identify the concatenated sub-daily summa output.
        summa_output_path = read_from_summa_route_control(summa_filemanager, "outputPath")
        summa_outFile_timestep = os.path.join(summa_output_path, summa_outFilePrefix+'_timestep.nc')

        # (2) concatenate sub-daily summa output files into one file.
        if not os.path.exists(summa_outFile_timestep):
            concat_timestep_output(control_file)  
        
        # (3) read sub-daily summa output.
        with xr.open_dataset(summa_outFile_timestep) as f:
            time = f['time'].values
            
            # read each forcing variable and calculate GRU/HRU mean value
            for i in range(forcing_num):
                forcingVarName = forcing_list_plot[i]
                forcingVar_long_name = f[forcingVarName].attrs['long_name']
                forcingVar_units = f[forcingVarName].attrs['units']
                forcingVar_data = np.nanmean(f[forcingVarName].values, axis=1) #(time,hru) 
                
                # save state data into dataframe
                if i == 0:
                    df_forcing = pd.DataFrame({forcingVarName:forcingVar_data},index = time)
                    df_forcing.index = pd.to_datetime(df_forcing.index)         
                    forcingVar_long_name_list = [forcingVar_long_name]
                    forcingVar_units_list = [forcingVar_units]
                else:
                    df_forcing[forcingVarName] = forcingVar_data
                    forcingVar_long_name_list.append(forcingVar_long_name)
                    forcingVar_units_list.append(forcingVar_units)        
    
        # (4) truncate forcing dataframe based on time
        df_forcing = df_forcing.truncate(before=statStartDate, after=statEndDate)
        df_forcing = df_forcing.dropna()
   
    # #### 3. Plot
    print('Plot.')
    col_num = 3        
    var_plot_total = forcing_num+stateVar_num+1
    row_num = int(np.ceil(var_plot_total/float(col_num))) # forcing + state + hydrograph
    
    fig, ax = plt.subplots(row_num,col_num, figsize=(5.5*col_num, 3.54*0.75*row_num))#, constrained_layout=True)
    fig.suptitle(domain_name, fontsize='medium', fontweight='bold')
    dpi_value=80    
    ax_id = 0

    # 3.1 plot forcing
    if forcing_num>0:
        for j in range(forcing_num):
            # identify subplot variable info
            forcingVarName = forcing_list_plot[j]
            forcingVar_long_name = forcingVar_long_name_list[j]
            forcingVar_units = forcingVar_units_list[j]

            # identify subplot ax
            ax_id = j
            iRow = ax_id//col_num
            iCol = ax_id%col_num
            
            # plot forcing variables 
            df_forcing[forcingVarName].plot(ax=ax[iRow,iCol], linewidth=0.75, markersize=0.0, color='blue')
            
            title = '('+chr(ord('a') + ax_id) +') ' + forcingVarName.capitalize() + '\n[ie, ' + forcingVar_long_name.capitalize().rstrip('(instant)')+ ']'
            ax[iRow,iCol].set_title(title, fontsize='medium', fontweight='semibold')
            ax[iRow,iCol].set_ylabel(forcingVarName+' ('+forcingVar_units+')', fontsize='small')

    # 3.2 plot states
    for j in range(stateVar_num):
        # identify subplot variable info
        stateVarName = stateVar_list_plot[j]
        stateVar_long_name = stateVar_long_name_list[j]
        stateVar_units = stateVar_units_list[j]

        # identify subplot ax
        ax_id = forcing_num + j
        iRow = ax_id//col_num
        iCol = ax_id%col_num

        # plot forcing variables 
        df_state[stateVarName].plot(ax=ax[iRow,iCol], linewidth=0.75, markersize=0.0, color='blue')
        
        title = '('+chr(ord('a') + ax_id) +') ' + stateVarName.replace('scalar','').capitalize() + '\n[ie, ' + stateVar_long_name.rstrip('(instant)').capitalize() + ']'
        ax[iRow,iCol].set_title(title, fontsize='medium', fontweight='semibold')
        ax[iRow,iCol].set_ylabel(stateVarName+' ('+stateVar_units+')', fontsize='small')

    # 3.3 plot hydrograph
    ax_id = forcing_num + stateVar_num 
    iRow = ax_id//col_num
    iCol = ax_id%col_num

    df_sim_obs.plot(ax=ax[iRow,iCol], linewidth=1, markersize=0.0, color=['black','red'])
    ax[iRow,iCol].legend(loc='upper right', fontsize='small')
    ax[iRow,iCol].set_title('('+chr(ord('a') + ax_id) +') ' + 'Hydrograph', fontsize='medium', fontweight='semibold')
    ax[iRow,iCol].set_ylabel('Flow (cms)', fontsize='small')

    # 3.4 make extra suplots blank
    for iRow in range(row_num):
        for iCol in range(col_num):
            ax_id = iRow*col_num + iCol
#             date_form = DateFormatter("%b-%Y")
#             ax[iRow,iCol].xaxis.set_major_formatter(date_form)
            if ax_id >= var_plot_total:
                ax[iRow,iCol].axis('off')           

    plt.rc('xtick',labelsize='small')
    plt.rc('ytick',labelsize='small')   
    fig.tight_layout()
    fig.subplots_adjust(top=0.95)
    fig.savefig(ofile_fig, dpi=dpi_value)
    plt.close(fig)  
