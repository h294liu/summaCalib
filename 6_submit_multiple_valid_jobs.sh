#!/bin/bash

current_path=$(pwd)
root_path=/glade/u/home/hongli/scratch/2020_06_02HRUcomplexity  # path where valid results will be.
basinId=06282000

best_calib_basePath=${root_path}/calib/${basinId}/analysis/5_best_calib_results
valid_basePath=${root_path}/valid/${basinId}
if [ ! -d ${valid_basePath} ]; then mkdir -p ${valid_basePath} ; fi

levelArray=(0 1a 1b 1c 2a 2b 2c 3)
# levelArray=(0)
domain_basename=DDS #SCE #GA #DDS #GLUE   # use as the domain folder name for the prepared data.

for complexity_level in ${levelArray[*]}; do

    domain_name=${complexity_level}
    echo $domain_name

    # 1. generate a new control.tpl
    file1=control_valid.tpl
    cp tpl/$file1 control.tpl
    sed -i "s/LEV/${complexity_level}/" control.tpl
    sed -i "s/xxxxxx/${domain_basename}/" control.tpl

    # 2. generate a new scripts/submit_run_Ostrich.sh
    file2=submit_run_model.tpl
    cp tpl/$file2 scripts/submit_run_model.sh
    sed -i "s/xxxxxx/${complexity_level}_valid/" scripts/submit_run_model.sh

    # 3. ./run_prepare_calib.sh with updated file1 and file2
    ./1_run_prepare_calib.sh

    # 4. copy the best calib param to valid trialParam.nc 
    src=$best_calib_basePath/${complexity_level}_${domain_basename}/trialParams.hru_lev${complexity_level}.nc
    dst=$valid_basePath/${complexity_level}_${domain_basename}/model/settings/SUMMA/trialParams.hru_lev${complexity_level}.nc
    cp $src $dst

    # 5. submit a job
    cd $valid_basePath/${complexity_level}_${domain_basename}/calib
    qsub submit_run_model.sh
#     ./submit_run_model.sh

    cd $current_path

done