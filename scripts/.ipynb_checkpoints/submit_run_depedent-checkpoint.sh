#!/bin/bash

script_folder=scripts
control_file=control_active.txt
max_iterations=1
summa_job_file="sbatch_summa.sh"  
route_job_file="sbatch_route.sh"  

# sbatch_summa.sh runs summa using job array
# sbatch_route.sh does: (1) postprocess summa outputs, (2) run mizuroute using MPI, (3) calcualte obj, (4) save best solutions, (5) generate a new parameter set, (6) clean summa outputs.

# -----------------------------------------------------------------------------------------
# ------------------------------------ Functions ------------------------------------------
# -----------------------------------------------------------------------------------------
read_from_control () {
    control_file=$1
    setting=$2
    
    line=$(grep -m 1 "^${setting}" $control_file)
    info=$(echo ${line##*|}) # remove the part that ends at "|"
    info=$(echo ${info%%#*}) # remove the part starting at '#'; does nothing if no '#' is present
    echo $info
}

read_from_summa_route_control () {
    input_file=$1
    setting=$2
    
    line=$(grep -m 1 "^${setting}" $input_file) 
    info=$(echo ${line%%!*}) # remove the part starting at '!'
    info="$( cut -d ' ' -f 2- <<< "$info" )" # get string after the first space
    info="${info%\'}" # remove the suffix '. Do nothing if no '.
    info="${info#\'}" # remove the prefix '. Do nothing if no '.
    echo $info
}

# -----------------------------------------------------------------------------------------
# -------------------------- Read settings from control_file ------------------------------
# -----------------------------------------------------------------------------------------
# Get common paths.
root_path="$(read_from_control $control_file "root_path")"
domain_name="$(read_from_control $control_file "domain_name")"
domain_path=${root_path}/${domain_name}

# Get calib path.
calib_path="$(read_from_control $control_file "calib_path")"
if [ "$calib_path" = "default" ]; then calib_path="${domain_path}/calib"; fi

# Get model and settings paths.
model_path="$(read_from_control $control_file "model_dst_path")"
if [ "$model_path" = "default" ]; then model_path="${domain_path}/model"; fi

summa_settings_relpath="$(read_from_control $control_file "summa_settings_relpath")"
summa_settings_path=$model_path/$summa_settings_relpath

# Get summa and mizuRoute controls/fileManager files.
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings_path/$summa_filemanager

# Extract summa output path and prefix from fileManager.txt (use to remove summa outputs).
summa_outputPath="$(read_from_summa_route_control $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_control $summa_filemanager "outFilePrefix")"

# -----------------------------------------------------------------------------------------
# -------------------- Run preparations and submit jobs -----------------------------------
# -----------------------------------------------------------------------------------------
# Update summa and mizuRoute sim start/end time based on control_active.txt.
python ${script_folder}/1_update_model_config_files.py $control_file

# submit depedent jobs by updating next and current
for id in $(seq 1 $max_iterations); do
    echo iteration $id

    # The first iteration jobs.
    if [ "$id" -eq 1 ]; then
    
        # Create logs and slurm output folders if not exist
        if [ ! -d logs ]; then mkdir logs; fi
	if [ ! -d slurmOutputs ]; then mkdir slurmOutputs; fi

        # Generate the initial parameter set using DDS
        python DDS.py multiplier_bounds.txt trial_stats.txt 1 $max_iterations UseInitialParamValues 1 tpl/multipliers.tpl multipliers.txt OstModel0.txt
        
        # Create summa output path if it does not exist; and remove previous outputs.
        if [ ! -d $summa_outputPath ]; then mkdir -p $summa_outputPath; fi
        rm -f $summa_outputPath/${summa_outFilePrefix}*

        # Submit the first indepedent job        
        current=$( sbatch ${summa_job_file} | awk '{ print $4 }' )  # $4 is used to return jobid
        echo summa $current
        
        next=$( sbatch --dependency=afterok:${current} ${route_job_file} ${id} $max_iterations | awk '{ print $4 }' )
        current=$next
        echo route $current

    # The following iteration jobs.
    else   
        next=$( sbatch --dependency=afterok:${current} ${summa_job_file} | awk '{ print $4 }' )
        current=$next
        echo summa $current
        
        next=$( sbatch --dependency=afterok:${current} ${route_job_file} ${id} $max_iterations | awk '{ print $4 }' )
        current=$next
        echo route $current
    fi
done
