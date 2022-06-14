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
# levelArray=['1a', '1b', '1c', '2a', '2b', '2c', '3']

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

output_dir = os.path.join(valid_dir,'analysis','9_plot_event_Q_seperate')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


# Part A: Read sim and obs data
print('Read sim & obs flow')
# read sim flow
df_sim_dic = {}
for complexity_level in levelArray:

    print('---%s---'%(complexity_level))
    simVarName = 'IRFroutedRunoff'
    simFile = os.path.join(valid_dir,complexity_level+'_DDS', 'model/simulations/mizuRoute',
                           route_outFilePrefix+'.mizuRoute.nc')

    f    = xr.open_dataset(simFile)
    time = f['time'].values
    sim  = f[simVarName][:,(q_seg_index-1)].values #(time, segments)
    df_sim = pd.DataFrame({'sim':sim},index = time)
    
    df_sim.index = pd.to_datetime(df_sim.index)
    df_sim = df_sim.dropna()    
    df_sim_dic[complexity_level] = df_sim

# read observed flow (cfs or cms) --- 
df_obs = pd.read_csv(obsFile, index_col='Date', na_values=["-99.0","-999.0","-9999.0"],
                     parse_dates=True, infer_datetime_format=True)  
df_obs.columns = ['obs']
df_obs = df_obs.dropna()

# convert obs from cfs to cms
if obs_unit == 'cfs':
    df_obs = df_obs/35.3147     
    
               
# Part B: Plot event hydrographs (two sets of 2*2 figures)
# events = ['10/30/2016', '10/08/2013','08/26/2004','01/02/1997', '09/11/1991',
#           '04/22/2010','04/29/2009', '04/15/2002','04/29/1999', '04/11/1996']
events = ['10/30/2016', '10/08/2013']

for event in events:
    
    print(event)
    event_format_str = datetime.datetime.strftime(datetime.datetime.strptime(event, '%m/%d/%Y'),'%Y-%m-%d')
    event_yr = datetime.datetime.strptime(event, '%m/%d/%Y').year
    
    eventStartDate = datetime.datetime.strftime(datetime.datetime.strptime(event, '%m/%d/%Y') \
                                       - datetime.timedelta(days=15), '%Y-%m-%d')     
    eventEndDate = datetime.datetime.strftime(datetime.datetime.strptime(event, '%m/%d/%Y') \
                                     + datetime.timedelta(days=15), '%Y-%m-%d')         
    
    # --- Plot the first figure
    nrow, ncol = 2, 2
    lwd = 1.0
    
    fig, ax = plt.subplots(nrow, ncol,figsize=[7.08, 7.08*0.3*nrow], constrained_layout=True)
    fig.suptitle(event_format_str+' Event Hydrograph (complexity levels 0-1c)', fontsize='small',weight='semibold')

    for i in range(nrow): 
        for j in range(ncol):

            comp_id = i*ncol + j
            complexity_level = levelArray[comp_id] 

            df_sim = df_sim_dic[complexity_level]    
            df_sim_eval = df_sim.truncate(before=eventStartDate, after=eventEndDate)
            df_obs_eval = df_obs.truncate(before=eventStartDate, after=eventEndDate)

            ax[i,j].plot(df_sim_eval.index, df_sim_eval['sim'], 'red', label='sim', linewidth=lwd)
            ax[i,j].plot(df_obs_eval.index, df_obs_eval['obs'], 'black', label='obs', linewidth=lwd)
            
            if i == nrow-1:
                ax[i,j].set_xlabel('Date [mm/dd, %d]'%(event_yr),fontsize='small')
            ax[i,j].set_ylabel('Flow (cms)',fontsize='small')

            date_form = DateFormatter("%m/%d") #"%Y-%m-%d"
            ax[i,j].xaxis.set_major_formatter(date_form)
            
            plt.sca(ax[i,j])
            plt.xticks(rotation = 35) #'vertical'            
            ax[i,j].tick_params(axis='both', direction='out', labelsize='small')
            
            subtitle = 'Complexity level ' + complexity_level
            ax[i,j].set_title(subtitle,fontsize='small')
            ax[i,j].legend(fontsize='small')

    ofile = event_format_str+'_part1.png'
    plt.savefig(os.path.join(output_dir,ofile), dpi=150)
    plt.close(fig) 
    
    # --- Plot the second figure
    nrow, ncol = 2, 2
    lwd = 1.0
    
    fig, ax = plt.subplots(nrow, ncol,figsize=[7.08, 7.08*0.3*nrow], constrained_layout=True)
    fig.suptitle(event_format_str+' Event Hydrograph (complexity levels 2a-3)', fontsize='small',weight='semibold')

    for i in range(nrow): 
        for j in range(ncol):

            comp_id = i*ncol + j
            complexity_level = levelArray[4 + comp_id]  
            
            df_sim = df_sim_dic[complexity_level]    
            df_sim_eval = df_sim.truncate(before=eventStartDate, after=eventEndDate)
            df_obs_eval = df_obs.truncate(before=eventStartDate, after=eventEndDate)

            ax[i,j].plot(df_sim_eval.index, df_sim_eval['sim'], 'red', label='sim', linewidth=lwd)
            ax[i,j].plot(df_obs_eval.index, df_obs_eval['obs'], 'black', label='obs', linewidth=lwd)

            if i == nrow-1:
                ax[i,j].set_xlabel('Date [mm/dd, %d]'%(event_yr),fontsize='small')
            ax[i,j].set_ylabel('Flow (cms)',fontsize='small')

            date_form = DateFormatter("%m/%d") #"%Y-%m-%d"
            ax[i,j].xaxis.set_major_formatter(date_form)
            
            plt.sca(ax[i,j])
            plt.xticks(rotation = 35) #'vertical'
            ax[i,j].tick_params(axis='both', direction='out', labelsize='small')
            
            subtitle = 'Complexity level ' + complexity_level
            ax[i,j].set_title(subtitle,fontsize='small')
            ax[i,j].legend(fontsize='small')
            
    ofile = event_format_str+'_part2.png'
    plt.savefig(os.path.join(output_dir,ofile), dpi=150)
    plt.close(fig)  

