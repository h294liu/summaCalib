#!/bin/bash

current_path=$(pwd)
root_path=/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/calib/06282000  # root path where parameter estimation will be stored.

levelArray=(0 1a 1b 1c 2a 2b 2c 3)
# levelArray=(1a 1b 1c 2a 2b 2c 3)
domain_basename=DDS #SCE #GA #DDS #GLUE   # use as the domain folder name for the prepared data.

startId=1
endId=2


for complexity_level in ${levelArray[*]}; do
# for complexity_level in 0  1a; do
    for id in $(seq ${startId} 1 ${endId}); do
        domain_name=${complexity_level}_${domain_basename}$id
        echo $domain_name

        # 1. generate a new control.tpl
        file1=control.tpl
        cp tpl/$file1 $file1
        sed -i "s/LEV/${complexity_level}/" $file1
        sed -i "s/xxxxxx/${domain_basename}$id/" $file1

        # 2. generate a new scripts/submit_run_Ostrich.sh
        file2=submit_run_Ostrich.tpl
        cp tpl/$file2 scripts/submit_run_Ostrich.sh
        sed -i "s/xxxxxx/${domain_name}/" scripts/submit_run_Ostrich.sh

        # 3. ./run_prepare_calib.sh with updated file1 and file2
        ./1_run_prepare_calib.sh

    #     # Hard coded!
    #     # copy trial_stat.txt to each calib folder to avoid failed model run at the beginning
    #     cp $root_path/GLUE1/calib/trial_stats.txt $root_path/$domain_name/calib/trial_stats.txt

        # 4. submit a job
        cd $root_path/$domain_name/calib
#         qsub submit_run_Ostrich.sh

        # Or, submit a series of jobs
        job_file=submit_run_Ostrich.sh
        # part 1. submit the 1st job
        current=$(qsub $job_file)

        # part 2. submit the other jobs by updating next and current
        for id in $(seq 2 10); do
               next=$(qsub -W depend=afterany:$current $job_file)
               current=$next
        done
        
        cd $current_path

    done
done