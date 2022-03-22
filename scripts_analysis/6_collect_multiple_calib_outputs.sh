#!/bin/bash

current_path=$(pwd)
root_path=/home/h294liu/project/proj/5_summaCalib/BowAtBanff_LA_calib  # root path where parameter estimation will be stored.
domain_basename=GLUE   # use as the domain folder name for the prepared data.
target_file=OstModel0.txt

startId=1
endId=260

# 1. make a folder to store collective results
target_dir=$root_path/${domain_basename}_results_${startId}_${endId}
mkdir -p $target_dir

# 2. loop to save results
for id in $(seq ${startId} 1 ${endId}); do
    domain_name=${domain_basename}$id
    echo $domain_name
   
    src=$root_path/$domain_name/calib/$target_file
    dst=$target_dir/${domain_name}_${target_file}
    cp $src $dst

done
