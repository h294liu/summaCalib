#!/usr/bin/env python
# coding: utf-8

# This code submits a priori model run for each gauge. 

import os,shutil
import pandas as pd
import numpy as np

root_dir = '/home/h294liu/project/proj/7_nelson'
gauge_csv = os.path.join(root_dir,'Flow_data/Phase_0&1_Natural/Natural_gauge_stn_info_calib_phase_0&1.csv')
gauge_df = pd.read_csv(gauge_csv)

current_path=os.getcwd()
output_basedir = '/home/h294liu/scratch/7_nelson/calib'

# other settings
# simStartTime = '2000-01-02 00:00' # simulation period
# simEndTime = '2011-10-02 00:00'

# statStartTime = '2000-10-01' # statistics calculation period
# statEndTime = '2011-09-30'

simStartTime = '2000-01-02 00:00' # simulation period
simEndTime = '2000-02-01 00:00'

statStartTime = '2000-01-02' # statistics calculation period
statEndTime = '2000-01-31'

gauge_df_cp = gauge_df.iloc[np.r_[8],:]
for index, row in gauge_df_cp.iterrows():

# for index, row in gauge_df.iterrows():
    Gauge_ID = row['Gauge_ID']
    print('---------------------------')
    print(Gauge_ID)
    print('---------------------------')
    
    # read upstream GRUs.
    gauge_upstream_txt = os.path.join(root_dir, 'scripts/1_find_gauge_upstream_GRUs', 
                                      Gauge_ID, Gauge_ID+'_upstreamGRUs.txt')
    upstream_grus = np.loadtxt(gauge_upstream_txt,dtype='str')
    try:
        upstream_grus = [int(upstream_grus)]
    except:
        upstream_grus = list(upstream_grus)
    nGru = len(upstream_grus)

    # read  drainage area, and segID.
    gauge_seg_area_txt = os.path.join(root_dir, 'scripts/1_find_gauge_upstream_GRUs', 
                                      Gauge_ID, Gauge_ID+'_Seg_Area.txt')
    data = np.loadtxt(gauge_seg_area_txt,dtype='str',delimiter='#',usecols=[0])
    area,SegId = data[0],data[1]    
    
    # work on gauge model
    gauge_model_dir = os.path.join(output_basedir,Gauge_ID)
    if not os.path.exists(gauge_model_dir):
        os.makedirs(gauge_model_dir)  
        
    # 1. generate a new control.tpl
    src = os.path.join(current_path,'tpl','control_calib.tpl')
    dst = os.path.join(current_path,'control_active.txt')
    with open(src, 'r') as src:
        with open(dst, 'w') as dst:
            for line in src:
                # update path
                if 'xxxxxx' in line:
                    line = line.replace('xxxxxx', Gauge_ID)  
                elif 'NGRU' in line:
                    line = line.replace('NGRU', str(nGru))  
                elif 'SIMSTARTTIME' in line:
                    line = line.replace('SIMSTARTTIME', simStartTime)  
                elif 'SIMENDTIME' in line:
                    line = line.replace('SIMENDTIME', simEndTime)  
                elif 'DOMAIN_AREA' in line:
                    line = line.replace('DOMAIN_AREA', area)  
                elif 'Q_SEG_INDEX' in line:
                    line = line.replace('Q_SEG_INDEX', SegId)
                elif 'STATSTARTTIME' in line:
                    line = line.replace('STATSTARTTIME', statStartTime)  
                elif 'STATENDTIME' in line:
                    line = line.replace('STATENDTIME', statEndTime)  
                dst.write(line)
                    
    # 2. generate a new scripts/submit_run_Ostrich.sh
    
    # There are two criteria when generating nCount and nTask.  
    # Set 2 days as time limit. Then calcualte nMaxIter.
    
    # first, try to use a fixed nCount.
    nCount = 10 #25
    nTask = int(np.ceil(nGru/float(nCount)))  # --ntasks
    nMaxIter = 250                            # max number of iterations for DDS
    
    nMM  = int(10 + 2.5*nCount)*nMaxIter # --time (in minute) # Assume 3min per GRU for 2000-2011. 20min for others.
    nMem = int(500 + 5*nCount)           # --mem-per-cpu (in MB) # Assume 5MB per GRU. 500MB for others.

    # second, further reduce time based on nGru<>nCount
    if nGru<nCount:
        nMM  = int(10 + 2*nGru)*nMaxIter
        
    # third, avoid nTask too large.
    if nTask>110:
        nCount = 85 #100
        nTask = int(np.ceil(nGru/float(nCount)))  # --ntasks. eg., for the entire domain, ntask = 292.
        nMaxIter = 100
        nMM  = int(60)*nMaxIter  # --time (in minute) # Assume 4min per GRU for 2000-2011. 10min for others.
        nMem = int(4000) # --mem-per-cpu (in MB) # Assume 5MB per GRU. 350MB for others.
        
    src = os.path.join(current_path,'tpl','submit_run_Ostrich.sh')
    dst = os.path.join(current_path,'scripts','submit_run_Ostrich.sh')
    with open(src, 'r') as src:
        with open(dst, 'w') as dst:
            for line in src:
                if 'NTASK' in line:
                    line = line.replace('NTASK', str(nTask))  
                elif 'MM' in line:
                    line = line.replace('MM', str(nMM))  
                elif 'MEMX' in line:
                    line = line.replace('MEMX', str(nMem))  
                elif 'JOBNAME' in line:
                    line = line.replace('JOBNAME', Gauge_ID+'calib')  
                dst.write(line)
                
    # 3. generate a new scripts/make_summa_run_list.sh
    src = os.path.join(current_path,'tpl','make_summa_run_list.sh')
    dst = os.path.join(current_path,'scripts','make_summa_run_list.sh')
    with open(src, 'r') as src:
        with open(dst, 'w') as dst:
            for line in src:                                    
                if 'nGRU' in line:
                    line = line.replace('nGRU', str(nGru))  
                elif 'nCount' in line:
                    line = line.replace('nCount', str(nCount))
                elif 'nTask' in line:
                    line = line.replace('nTask', str(nTask))                  
                dst.write(line)
    
    # 4. ./run_prepare_calib.sh with updated file1 and file2
    os.system('./1_run_prepare_calib.sh')
   
#     # 5. submit a job
#     os.chdir(os.path.join(output_basedir,Gauge_ID,'calib'))
#     os.system('sbatch submit_run_Ostrich.sh')   
#     os.chdir(current_path)
