#!/usr/bin/env python
# coding: utf-8


import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
import os, datetime
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.gridspec as gridspec
import argparse
import xarray as xr


def get_modified_KGE(obs,sim):    
    sd_sim=np.std(sim, ddof=1)
    sd_obs=np.std(obs, ddof=1)
    
    m_sim=np.mean(sim)
    m_obs=np.mean(obs)
    
    r=(np.corrcoef(sim,obs))[0,1]
    relvar=(float(sd_sim)/float(m_sim))/(float(sd_obs)/float(m_obs))
    bias=float(m_sim)/float(m_obs)
    
    kge=1.0-np.sqrt((r-1)**2 +(relvar-1)**2 + (bias-1)**2)
    return kge,r,relvar,bias

def get_RMSE(obs,sim):
    rmse = np.sqrt(np.nanmean(np.power((sim - obs),2)))
    return rmse

levelArray=['0', '1a', '1b', '1c', '2a', '2b', '2c', '3']

aw_apriori_baseDir = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/06282000'
aw_sim_basedir = os.path.join(aw_apriori_baseDir,'source_info/apriori_results')

calib_dir = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/calib/06282000'
domain_basename='DDS'

# obs_file = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/obs/obs_flow.06282000.cfs.csv'
obs_file = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/obs/obs_flow.BBR_IN.cfs.csv'
obsFile = obs_file
obs_unit = 'cfs'
q_seg_index=1
time_format='%Y-%m-%d'

output_baseDir = os.path.join(calib_dir,'analysis','4_apriori_results')
if not os.path.exists(output_baseDir):
    os.makedirs(output_baseDir)

# --- Read observed flow (cfs or cms) --- 

df_obs = pd.read_csv(obs_file, index_col='Date', na_values=["-99.0","-999.0","-9999.0"],
                     parse_dates=True, infer_datetime_format=True)  
df_obs.columns = ['obs']

# convert obs from cfs to cms
if obs_unit == 'cfs':
    df_obs = df_obs/35.3147       

    
# --- Calculate a-priori statistics from Andy's run
for complexity_level in levelArray:
    print(complexity_level)
    
    simFile = os.path.join(aw_sim_basedir,complexity_level,'sflow.h.1970-01-01-00000.nc')
    stat_output = os.path.join(output_baseDir,'trial_stats_lev%s_AW.txt'%(complexity_level))

    # --- read simulated flow (cms) --- 
    simVarName = 'IRFroutedRunoff'
    f    = xr.open_dataset(simFile)
    time = f['time'].values
    sim  = f[simVarName][:,(q_seg_index-1)].values #(time, segments)
    df_sim = pd.DataFrame({'sim':sim},index = time)
    df_sim.index = pd.to_datetime(df_sim.index)

    # --- merge the two df based on time index--- 
    statStartDate, statEndDate = '2000-10-01','2019-09-30'
    df_sim_eval = df_sim.truncate(before=statStartDate, after=statEndDate)
    df_obs_eval = df_obs.truncate(before=statStartDate, after=statEndDate)
    df_merge = pd.concat([df_obs_eval, df_sim_eval], axis=1)
    df_merge = df_merge.dropna()

    ######### Calculate valid period statistics #########
    # --- drop calibration period (for manuscript purpose) ---
    calibStartDate,calibEndDate = '2007-10-01','2012-09-30'
    calibStartDate = datetime.datetime.strptime(calibStartDate,time_format)
    calibEndDate = datetime.datetime.strptime(calibEndDate,time_format)    
    df_merge_new = df_merge.loc[(df_merge.index < calibStartDate) | (df_merge.index > calibEndDate)]
    
    # --- calculate diagnostics --- 
    kge,r,relvar,bias = get_modified_KGE(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values)
    rmse = get_RMSE(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values)
    # bias_err, abs_err = get_mean_error(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values)
    # obs_month_mean, sim_month_mean = get_month_mean_flow(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values, sim_time=sim_time)
    
    # --- save --- 
    stat_output_valid = stat_output.replace('.txt','_valid.txt')
    stat_output_valid = os.path.join(output_baseDir, stat_output_valid)

    f = open(stat_output_valid, 'w+')
    f.write('%.6f' %kge + '\t#KGE\n')
    f.write('%.6f' %rmse + '\t#RMSE (cms)\n')
    f.write('%.6f' %r + '\t#Correlation\n')
    f.write('%.6f' %relvar + '\t#Relative Variability \n')
    f.write('%.6f' %bias + '\t#Bias \n')
    # f.write('%.6f' %bias_err + '\t#MBE (cms)\n')
    # f.write('%.6f' %abs_err + '\t#MAE (cms)\n')
    f.close()
    print(kge,r,relvar,bias)

    ######### Calculate calib period statistics #########
    # --- extract calibration period (for manuscript purpose) ---
    calibStartDate,calibEndDate = '2007-10-01','2012-09-30'
    calibStartDate = datetime.datetime.strptime(calibStartDate,time_format)
    calibEndDate = datetime.datetime.strptime(calibEndDate,time_format)    
    df_merge_new = df_merge.loc[(df_merge.index >= calibStartDate) & (df_merge.index <= calibEndDate)]
    
    # --- calculate diagnostics --- 
    kge,r,relvar,bias = get_modified_KGE(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values)
    rmse = get_RMSE(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values)
    # bias_err, abs_err = get_mean_error(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values)
    # obs_month_mean, sim_month_mean = get_month_mean_flow(obs=df_merge_new['obs'].values, sim=df_merge_new['sim'].values, sim_time=sim_time)
    
    # --- save --- 
    stat_output_calib = stat_output.replace('.txt','_calib.txt')
    stat_output_calib = os.path.join(output_baseDir, stat_output_calib)

    f = open(stat_output_calib, 'w+')
    f.write('%.6f' %kge + '\t#KGE\n')
    f.write('%.6f' %rmse + '\t#RMSE (cms)\n')
    f.write('%.6f' %r + '\t#Correlation\n')
    f.write('%.6f' %relvar + '\t#Relative Variability \n')
    f.write('%.6f' %bias + '\t#Bias \n')
    # f.write('%.6f' %bias_err + '\t#MBE (cms)\n')
    # f.write('%.6f' %abs_err + '\t#MAE (cms)\n')
    f.close()
    print(kge,r,relvar,bias)
