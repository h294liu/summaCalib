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
simStartTime = '2000-01-02 00:00' # simulation period
simEndTime = '2011-10-02 00:00'

statStartTime = '2000-10-01' # statistics calculation period
statEndTime = '2011-09-30'

# simStartTime = '2000-01-02 00:00' # simulation period
# simEndTime = '2000-02-01 00:00'

# statStartTime = '2000-01-02' # statistics calculation period
# statEndTime = '2000-01-31'

# gauge_df_cp = gauge_df.iloc[np.r_[137],:]
gauge_df_cp = gauge_df.iloc[126:137,:]
calib_type = 'DDS'
calib_num = 3 

for index, row in gauge_df_cp.iterrows():

# for index, row in gauge_df.iterrows():
    Gauge_ID = row['Gauge_ID']

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
    
    # Make multiple calib individually
    for calib_id in range(calib_num):
        
        print('---------------------------')
        print(Gauge_ID, calib_type+str(calib_id+1))
        print('---------------------------')

        # work on gauge calib
        calib_dir = os.path.join(output_basedir,Gauge_ID+'_'+calib_type+str(calib_id+1))
        if not os.path.exists(calib_dir):
            os.makedirs(calib_dir)  

        # 1. generate a new control.tpl
        src = os.path.join(current_path,'tpl','control_calib.tpl')
        dst = os.path.join(current_path,'control_active.txt')
        with open(src, 'r') as src:
            with open(dst, 'w') as dst:
                for line in src:
                    # update path
                    if ('xxxxxx' in line) and ("domain_name" in line):
                        line = line.replace('xxxxxx', Gauge_ID+'_'+calib_type+str(calib_id+1)) 
                    elif ('xxxxxx' in line) and ("model_src_path" in line):
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

        nMM  = int(10080)                         # --time (in minute) # Fixed request 3days.
        nMem = int(500+5*nCount)                          # --mem-per-cpu (in MB) # Fixed request 1000MB per cpu.

        # second, avoid nTask too large. This is actually for the entire model run.
        if nTask>110:
            nCount = 50 #100
            nTask = int(np.ceil(nGru/float(nCount)))  # --ntasks. eg., for the entire domain, ntask = 292.
            nMem = int(1800)                          # --mem-per-cpu (in MB) # Fixed request 1GB.

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
                        line = line.replace('JOBNAME', Gauge_ID+'calib'+str(calib_id+1))  
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

        # 5. copy OstModel.txt if it exists in old calib folder
        ostModel_src = os.path.join(output_basedir,Gauge_ID,'calib/OstModel0.txt')
        ostModel_dst = os.path.join(calib_dir,'calib/OstModel0.txt')
        shutil.copyfile(ostModel_src, ostModel_dst)

        # 6. submit a job
        os.chdir(os.path.join(calib_dir,'calib'))
        os.system('sbatch submit_run_Ostrich.sh')   
        os.chdir(current_path)
