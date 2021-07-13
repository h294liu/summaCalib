#!/usr/bin/env python
# coding: utf-8

# Script to plot timeseries (eg simulated versus obs flow)
# source: /glade/u/home/andywood/proj/SHARP/plotting/plot_simobs_flow.py

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import sys, os
import numpy as np
import pandas as pd
from scipy import stats
# import netCDF4 as nc
from datetime import datetime
import matplotlib.gridspec as gridspec
# import glob
import argparse
import xarray as xr

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    # Positional mandatory arguments
    parser.add_argument('controlFile', help='path of the active control file.')
    parser.add_argument("experiment_id", help="calibration experiment id", type=int) # experiment_id > 0
    # Go to output_archive and plot route results in the corresponding experiment ID.
    
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
    
    # an example: python 2_plot_simobs_flow.py ../control_active.txt 1

    # --- process command line --- 
    # check args
    if len(sys.argv) < 2:
        print("Usage: %s <controlFile>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
    experiment_id = args.experiment_id

#     control_file = '/home/h294liu/project/proj/5_summaCalib/5_calib_test/BowAtBanff1/calib/control_active.txt'
#     experiment_id = 1
    
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

    # read new hydrologic model path, settings, fileManager.txt, trialParam.nc.
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')

    # mizuRoute control file
    route_settings_relpath=read_from_control(control_file, "route_settings_relpath")
    route_settings_path=os.path.join(model_dst_path, route_settings_relpath)

    route_control = read_from_control(control_file, 'route_control')
    route_control = os.path.join(route_settings_path, route_control)

    # identify archieve output path and mizuRoute output prefix.
    archive_path = os.path.join(calib_path, 'output_archive', str(experiment_id))    
    route_outFilePrefix=read_from_summa_route_control(route_control, "<case_name>")
    q_seg_index = int(read_from_control(control_file, 'q_seg_index'))
    
    # identify observed streamflow file
    obsFile = read_from_control(control_file, "obs_file")
    obs_unit = read_from_control(control_file, "obs_unit")

    # identify dates of plot 
    statStartDate  = datetime.strptime(read_from_control(control_file, 'statStartDate'),'%Y-%m-%d') # %H:%M:%S
    statEndDate    = datetime.strptime(read_from_control(control_file, 'statEndDate'), '%Y-%m-%d')

    # identify plot output path and file
    output_path = os.path.join(analysis_path, '3_plot_simobs_flow')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    ofile = os.path.join(output_path, 'experiment%d.png'%(experiment_id))  # output plot figure

    # --------------------------- End Read settings -----------------------------
    
    # --- read simulated flow from netcdf file (cms)

    simVarName = 'IRFroutedRunoff'
    simFile = os.path.join(archive_path, route_outFilePrefix+'.mizuRoute.nc')
#     simFile = os.path.join(archive_path, route_outFilePrefix+'.nc') # for temporaty use
    f    = xr.open_dataset(simFile)
    time = f['time'].values
    sim  = f[simVarName][:,(q_seg_index-1)].values #(time, segments)
    df_sim = pd.DataFrame({'sim':sim},index = time)
    df_sim.index = pd.to_datetime(df_sim.index)
    
    # --- read observed flow (cfs or cms) --- 
    df_obs = pd.read_csv(obsFile, index_col='Date', na_values=["-99.0","-999.0","-9999.0"],
                         parse_dates=True, infer_datetime_format=True)  
    df_obs.columns = ['obs']
    
    # convert obs from cfs to cms
    if obs_unit == 'cfs':
        df_obs = df_obs/35.3147    
        
    # --- # combine daily sim & obs timeseries df based on time index--- 
    df_sim_eval = df_sim.truncate(before=statStartDate, after=statEndDate)
    df_obs_eval = df_obs.truncate(before=statStartDate, after=statEndDate)
    df_merge = pd.concat([df_obs_eval, df_sim_eval], axis=1)
    df_merge = df_merge.dropna()
    df_merge.index = pd.to_datetime(df_merge.index)

    # --- make dataframes ---
    df_final          = df_merge  # combine daily sim & obs timeseries
    df_final_calib    = df_merge   # daily, calib. period only, defined in config file

    df_final_WY       = df_final.resample('AS-OCT').mean()  # resampled to annual mean starting in October
    df_final_calib_WY = df_final_calib.resample('AS-OCT').mean()

    df_final_AJ       = df_final[(df_final.index.month>=4) & (df_final.index.month<=7)].resample('AS-OCT').mean()
    df_final_calib_AJ = df_final_calib[(df_final_calib.index.month>=4) & (df_final_calib.index.month<=7)].resample('AS-OCT').mean()
    df_final_M        = df_final.resample('M').mean()[df_final.resample('M').count()>=28]  # only for months with at least 28 days
    df_final_MA       = df_final.groupby(df_final.index.month).mean()                     # monthly avg
    df_final_MA.columns   = ['Sim (all yrs)', 'Obs (all yrs)']
    df_final_calib_MA = df_final_calib.groupby(df_final_calib.index.month).mean()         # monthly avg, cal period
    df_final_calib_MA.columns = ['Sim (calib)','Obs (calib)']

    # --- calculate some statistics ---
    # calc some statistics
    if len(df_final_AJ) > 1:
        corr_AJ = stats.pearsonr(df_final_AJ.iloc[:,0], df_final_AJ.iloc[:,1]) 
        corr_WY = stats.pearsonr(df_final_calib_WY.iloc[:,0], df_final_calib_WY.iloc[:,1]) 
        print("correlations (AJ, WY): ", corr_AJ[0], corr_WY[0])
    else:
        corr_AJ = [None, None]
        corr_WY = [None, None]

    # --- make plot --- 
    # fig, ax = plt.subplots(4, 1)
    width  = 6.5  # in inches
    height = 9.0
    lwd    = 0.8  # line thickness

    # plot layout
    print("plot layout")
    fig = plt.figure()

    AX = gridspec.GridSpec(4,2)
    AX.update(wspace = 0.5, hspace = 0.3)
    ax1  = plt.subplot(AX[0,:])
    ax2 = plt.subplot(AX[1,:])
    ax3 = plt.subplot(AX[2,:])
    ax4 = plt.subplot(AX[3,0])
    ax5 = plt.subplot(AX[3,1])

    # plot monthly
    print("plot monthly")
    df_final_M.plot(ax=ax1, figsize=(width,height), color=['red','black'], linewidth=lwd)

    # plot daily calibration period
    print("plot daily calibration period")
    df_final_calib.plot(ax=ax2, figsize=(width,height), color=['red','black'], linewidth=lwd)

    # plot monthly long term averages for period
    print("plot monthly long term averages")
    df_final_calib_MA.plot(ax=ax3, figsize=(width,height), color=['red','black'], linewidth=lwd)
    df_final_MA.plot(ax=ax3, figsize=(width,height), color=['red','black'], linewidth=lwd, linestyle=':')

    # plot scatter for water year mean flow
    print("plot scatter for water year mean flow")
    axmax = df_final_WY.max().max()
    ax4.scatter(df_final_WY.iloc[:,0], df_final_WY.iloc[:,1], c='black', s=5)
    ax4.scatter(df_final_calib_WY.iloc[:,0], df_final_calib_WY.iloc[:,1], c='red', s=10, label='Calib')
    ax4.plot((0, axmax), (0, axmax), c='orange', linestyle=':')
    if corr_WY[0] is not None:
        ax4.annotate('corr: '+str(round(corr_WY[0], 3)), xy=(axmax*0.97, axmax*0.03), horizontalalignment='right')

    # plot scatter for spring runoff period (Apr-Jul)
    print("plot scatter for for spring runoff period")
    axmax = df_final_AJ.max().max()
    ax5.scatter(df_final_AJ.iloc[:,0], df_final_AJ.iloc[:,1],c='black', s=5)
    ax5.scatter(df_final_calib_AJ.iloc[:,0], df_final_calib_AJ.iloc[:,1], c='red', s=10, label='Calib')
    ax5.plot((0, axmax), (0, axmax), c='orange', linestyle=':')
    if corr_AJ[0] is not None:
        ax5.annotate('corr: '+str(round(corr_AJ[0], 3)), xy=(axmax*0.97, axmax*0.03), horizontalalignment='right')

    # other plot details
    print("other plot details")
    ax1.axvline(x=statStartDate, color='grey', linewidth=0)
    ax1.axvline(x=statEndDate, color='grey', linewidth=0)
    ax1.axvspan(statStartDate, statEndDate, color='grey', alpha=0.2, label='Calib Period')
    ax1.set_ylabel('Flow, Monthly (cms)')
    ax2.set_ylabel('Flow, Daily (cms)')
    ax3.set_ylabel('Flow, Monthly (cms)')
    ax3.set_xlabel('Calendar Month')
    ax4.set_ylabel('WY Obs (cms)')
    ax4.set_xlabel('WY Sim (cms)')
    ax5.set_ylabel('Apr-Jul Obs (cms)')
    ax5.set_xlabel('Apr-Jul Sim (cms)')
    ax1.legend(loc='upper right')
    ax2.legend().remove()
    ax3.legend(loc='upper right')
    ax4.legend()
    # ax5.legend().remove()
    ax1.set_title('Streamflow: ' + domain_name, fontsize='medium',weight='semibold')

    # --- save plot
    print("save plot")
    plt.savefig(ofile, dpi=80)