#!/usr/bin/env python
# coding: utf-8

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
import os, datetime
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.dates import DateFormatter


levelArray=['0', '1a', '1b', '1c', '2a', '2b', '2c', '3']

aw_apriori_baseDir = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/06282000'
aw_sim_basedir = os.path.join(aw_apriori_baseDir,'source_info/apriori_results')

valid_dir = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/valid/06282000'
domain_basename='DDS'

route_outFilePrefix = 'sflow'

# obs_file = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/obs/obs_flow.06282000.cfs.csv'
obs_file = '/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/obs/obs_flow.BBR_IN.cfs.csv'
obsFile = obs_file
obs_unit = 'cfs'
q_seg_index=1

output_dir = os.path.join(valid_dir,'analysis','10_plot_valid_Q_seperate')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


# Part A: Read sim and obs data
print('Read sim & obs flow')
# read sim flow before calib
df_sim_dic_priori = {}
for complexity_level in levelArray:

#     print('---%s---'%(complexity_level))
    simVarName = 'IRFroutedRunoff'
    simFile = os.path.join(aw_sim_basedir,complexity_level,'sflow.h.1970-01-01-00000.nc')

    f    = xr.open_dataset(simFile)
    time = f['time'].values
    sim  = f[simVarName][:,(q_seg_index-1)].values #(time, segments)
    df_sim = pd.DataFrame({'sim':sim},index = time)
    
    df_sim.index = pd.to_datetime(df_sim.index)
    df_sim = df_sim.dropna()    
    df_sim_dic_priori[complexity_level] = df_sim    

# read sim flow after calib
df_sim_dic_calib = {}
for complexity_level in levelArray:

#     print('---%s---'%(complexity_level))
    simVarName = 'IRFroutedRunoff'
    simFile = os.path.join(valid_dir,complexity_level+'_DDS', 'model/simulations/mizuRoute',
                           route_outFilePrefix+'.mizuRoute.nc')

    f    = xr.open_dataset(simFile)
    time = f['time'].values
    sim  = f[simVarName][:,(q_seg_index-1)].values #(time, segments)
    df_sim = pd.DataFrame({'sim':sim},index = time)
    
    df_sim.index = pd.to_datetime(df_sim.index)
    df_sim = df_sim.dropna()    
    df_sim_dic_calib[complexity_level] = df_sim

# read observed flow (cfs or cms) --- 
df_obs = pd.read_csv(obsFile, index_col='Date', na_values=["-99.0","-999.0","-9999.0"],
                     parse_dates=True, infer_datetime_format=True)  
df_obs.columns = ['obs']
df_obs = df_obs.dropna()

# convert obs from cfs to cms
if obs_unit == 'cfs':
    df_obs = df_obs/35.3147     
    
               
# Part B: Plot entire valid period hydrographs (two sets of 2*2 figures)
print('Plot')
calibStartDate = datetime.datetime.strptime('2007-10-01', '%Y-%m-%d')  
calibEndDate = datetime.datetime.strptime('2012-09-30', '%Y-%m-%d')         

# eventStartDate = datetime.datetime.strptime('1980-10-01', '%Y-%m-%d')  
# eventEndDate = datetime.datetime.strptime('2019-09-30', '%Y-%m-%d')         
eventStartDate = datetime.datetime.strptime('2007-10-01', '%Y-%m-%d')  
eventEndDate = datetime.datetime.strptime('2018-09-30', '%Y-%m-%d')         

# --- Plot the first figure
nrow, ncol = 4, 1
lwd = 1.0

fig, ax = plt.subplots(nrow, ncol,figsize=[7.08, 7.08*0.3*nrow], constrained_layout=True)
fig.suptitle('Hydrograph (complexity levels 0-1c)', fontsize='small',weight='semibold')

for i in range(nrow): 

    complexity_level = levelArray[i] 

    df_sim_priori = df_sim_dic_priori[complexity_level]    
    df_sim_priori_eval = df_sim_priori.truncate(before=eventStartDate, after=eventEndDate)
    df_sim_calib = df_sim_dic_calib[complexity_level]    
    df_sim_calib_eval = df_sim_calib.truncate(before=eventStartDate, after=eventEndDate)
    df_obs_eval = df_obs.truncate(before=eventStartDate, after=eventEndDate)

    ax[i].plot(df_obs_eval.index, df_obs_eval['obs'], 'black', label='Observed', linewidth=lwd,alpha=0.7)
    ax[i].plot(df_sim_priori_eval.index, df_sim_priori_eval['sim'], label='A priori', 
                 linewidth=lwd,linestyle='--',color='red',alpha=0.7)
    ax[i].plot(df_sim_calib_eval.index, df_sim_calib_eval['sim'], label='Calibrated',
                linewidth=lwd,linestyle=':',color='blue',alpha=0.7)
    
    ax[i].axvspan(calibStartDate, calibEndDate, facecolor='lightgrey',alpha=0.5, label='Calibration period')
    ax[i].set_xlim(eventStartDate,eventEndDate)
    
    if i == nrow-1:
        ax[i].set_xlabel('Time [yyyy/mm]',fontsize='small')
    ax[i].set_ylabel('Flow (cms)',fontsize='small')

    date_form = DateFormatter("%Y/%m") #"%Y-%m-%d","%m/%d"
    ax[i].xaxis.set_major_formatter(date_form)
    ax[i].tick_params(axis='both', direction='out', labelsize='small')

    subtitle = 'Complexity level ' + complexity_level
    ax[i].set_title(subtitle,fontsize='small')
    
#     if i == 0:
#         ax[i].legend(fontsize='small', ncol=2, loc='upper left')
    ax[i].legend(fontsize='x-small', ncol=2, loc='upper left')

ofile = 'part1.png'
plt.savefig(os.path.join(output_dir,ofile), dpi=150)
plt.close(fig) 

# --- Plot the second figure
nrow, ncol = 4, 1
lwd = 1.0

fig, ax = plt.subplots(nrow, ncol,figsize=[7.08, 7.08*0.3*nrow], constrained_layout=True)
fig.suptitle('Hydrograph (complexity levels 2a-3)', fontsize='small',weight='semibold')

for i in range(nrow): 

    complexity_level = levelArray[4 + i]  

    df_sim_priori = df_sim_dic_priori[complexity_level]    
    df_sim_priori_eval = df_sim_priori.truncate(before=eventStartDate, after=eventEndDate)
    df_sim_calib = df_sim_dic_calib[complexity_level]    
    df_sim_calib_eval = df_sim_calib.truncate(before=eventStartDate, after=eventEndDate)
    df_obs_eval = df_obs.truncate(before=eventStartDate, after=eventEndDate)

    ax[i].plot(df_obs_eval.index, df_obs_eval['obs'], 'black', label='Observed', linewidth=lwd,alpha=0.7)
    ax[i].plot(df_sim_priori_eval.index, df_sim_priori_eval['sim'], label='A priori', 
                 linewidth=lwd,linestyle='--',color='red',alpha=0.7)
    ax[i].plot(df_sim_calib_eval.index, df_sim_calib_eval['sim'], label='Calibrated',
                linewidth=lwd,linestyle=':',color='blue',alpha=0.7)
    
    ax[i].axvspan(calibStartDate, calibEndDate, facecolor='lightgrey',alpha=0.5, label='Calibration period')
    ax[i].set_xlim(eventStartDate,eventEndDate)
    
    if i == nrow-1:
        ax[i].set_xlabel('Time [yyyy/mm]',fontsize='small')
    ax[i].set_ylabel('Flow (cms)',fontsize='small')

    date_form = DateFormatter("%Y/%m") #"%Y-%m-%d","%m/%d"
    ax[i].xaxis.set_major_formatter(date_form)
    ax[i].tick_params(axis='both', direction='out', labelsize='small')

    subtitle = 'Complexity level ' + complexity_level
    ax[i].set_title(subtitle,fontsize='small')
#     if i == 0:
#         ax[i].legend(fontsize='small', ncol=2, loc='upper left')
    ax[i].legend(fontsize='x-small', ncol=2, loc='upper left')
    
ofile = 'part2.png'
plt.savefig(os.path.join(output_dir,ofile), dpi=150)
plt.close(fig)  


