#!/bin/bash

current_path=$(pwd)
root_path=/home/h294liu/project/proj/5_summaCalib/BowAtBanff_LA_calib  # root path where parameter estimation will be stored.
domain_basename=GLUE #SCE #GA #DDS #GLUE   # use as the domain folder name for the prepared data.

startId=261 #1
endId=600

for id in $(seq ${startId} 1 ${endId}); do
    domain_name=${domain_basename}$id
    echo $domain_name
   
    # 1. generate a new control.tpl
    file1=control.tpl
    cp tpl/$file1 $file1
    sed -i "s/xxxxxx/${domain_name}/" $file1
   
    # 2. generate a new scripts/submit_run_Ostrich.sh
    file2=submit_run_Ostrich.tpl
    cp tpl/$file2 scripts/submit_run_Ostrich.sh
    sed -i "s/xxxxxx/${domain_name}/" scripts/submit_run_Ostrich.sh
   
    # 3. ./run_prepare_calib.sh with updated file1 and file2
    ./1_run_prepare_calib.sh
   
    # Hard coded!
    # copy trial_stat.txt to each calib folder to avoid failed model run at the beginning
    cp $root_path/GLUE1/calib/trial_stats.txt $root_path/$domain_name/calib/trial_stats.txt

    # 4. submit a job
    cd $root_path/$domain_name/calib
    sbatch submit_run_Ostrich.sh
   
    # 5. return
    cd $current_path
      
done
