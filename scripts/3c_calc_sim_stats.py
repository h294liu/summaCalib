#!/usr/bin/env python
# coding: utf-8

# #### Calculate model performance evaluation/statistical metrics.
# Author: Hongli Liu, Andy Wood.

# import module
import os, sys
import numpy as np
import datetime
import pandas as pd
import xarray as xr
import argparse, glob

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    parser.add_argument('controlFile', help='path of the active control file.')
    args = parser.parse_args()
    return(args)

def get_modified_KGE(obs,sim):    
    sd_sim=np.std(sim, ddof=1)
    sd_obs=np.std(obs, ddof=1)
    
    m_sim=np.mean(sim)
    m_obs=np.mean(obs)
    
    r=(np.corrcoef(sim,obs))[0,1]
    relvar=(float(sd_sim)/float(m_sim))/(float(sd_obs)/float(m_obs))
    bias=float(m_sim)/float(m_obs)
    
    kge=1.0-np.sqrt((r-1)**2 +(relvar-1)**2 + (bias-1)**2)
    return kge

def get_RMSE(obs,sim):
    rmse = np.sqrt(np.nanmean(np.power((sim - obs),2)))
    return rmse

def get_mean_error(obs,sim):
    bias_err = np.nanmean(sim - obs)
    abs_err = np.nanmean(np.absolute(sim - obs))
    return bias_err, abs_err

def get_month_mean_flow(obs,sim,sim_time):
    month = [dt.month for dt in sim_time]

    data = {'sim':sim, 'obs':obs, 'month':month} 
    df = pd.DataFrame(data, index = sim_time)
    
    gdf = df.groupby(['month'])
    sim_month_mean = gdf.aggregate({'sim':np.nanmean})
    obs_month_mean = gdf.aggregate({'obs':np.nanmean})
    return obs_month_mean, sim_month_mean

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
    
    # an example: python calc_sim_stats.py ../control_active.txt

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

    # read mizuRoute setting and control files paths from control_file.
    route_settings_relpath = read_from_control(control_file, 'route_settings_relpath')
    route_settings_path = os.path.join(model_dst_path, route_settings_relpath)
    route_control = read_from_control(control_file, 'route_control')
    route_control = os.path.join(route_settings_path, route_control)

    # read calib path from control_file.
    calib_path = read_from_control(control_file, 'calib_path')
    if calib_path == 'default':
        calib_path = os.path.join(domain_path, 'calib')
    # -----------------------------------------------------------------------

    # #### 1. Read input and output arguments 
    # (input) mizuRoute output file
    output_dir = read_from_summa_route_control(route_control, '<output_dir>')
    route_outFilePrefix=read_from_summa_route_control(route_control, "<case_name>")
    
    # (input) segment id, observations, statistics relevant configs.
    q_seg_index = int(read_from_control(control_file, 'q_seg_index')) # start from one.
    
    obs_file = read_from_control(control_file, 'obs_file')
    obs_unit = read_from_control(control_file, 'obs_unit')

    statStartDate = read_from_control(control_file, 'statStartDate') 
    statEndDate = read_from_control(control_file, 'statEndDate')

    # (input) others
    time_format='%Y-%m-%d'
    statStartDate = datetime.datetime.strptime(statStartDate,time_format)
    statEndDate = datetime.datetime.strptime(statEndDate,time_format)    

    # (output) statistical output file.
    stat_output = read_from_control(control_file, 'stat_output')
    stat_output = os.path.join(calib_path, stat_output)

    # #### 2. Calculate 
    # --- read simulated flow (cms) --- 
    simVarName = 'IRFroutedRunoff'
    simFile = os.path.join(output_dir, route_outFilePrefix+'.mizuRoute.nc') # Hard coded file name. Be careful.
    f    = xr.open_dataset(simFile)
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
    df_merge = pd.concat([df_obs_eval, df_sim_eval], axis=1)
    df_merge = df_merge.dropna()

    # --- calculate diagnostics --- 
    kge = get_modified_KGE(obs=df_merge['obs'].values, sim=df_merge['sim'].values)
    rmse = get_RMSE(obs=df_merge['obs'].values, sim=df_merge['sim'].values)
    # bias_err, abs_err = get_mean_error(obs=df_merge['obs'].values, sim=df_merge['sim'].values)
    # obs_month_mean, sim_month_mean = get_month_mean_flow(obs=df_merge['obs'].values, sim=df_merge['sim'].values, sim_time=sim_time)
    
    # --- save --- 
    f = open(stat_output, 'w+')
    f.write('%.6f' %kge + '\t#KGE\n')
    f.write('%.6f' %rmse + '\t#RMSE (cms)\n')
    # f.write('%.6f' %bias_err + '\t#MBE (cms)\n')
    # f.write('%.6f' %abs_err + '\t#MAE (cms)\n')
    f.close()
