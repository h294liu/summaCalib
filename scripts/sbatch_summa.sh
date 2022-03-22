#!/bin/bash
#SBATCH --account=rpp-kshook
#SBATCH --time=10:00:00
#SBATCH --array=0-18
#SBATCH --ntasks=32
#SBATCH --mem-per-cpu=1000MB
#SBATCH --job-name=NelsonSumma
#SBATCH --output=slurmOutputs/%x-%A_%a.out

mkdir -p /home/h294liu/scratch/temp
export TMPDIR=/home/h294liu/scratch/temp
export MPI_SHEPHERD=true

#-----------------------------------------------------------------------------------------
# RUN WITH:
# sbatch --array1-[number of jobs] [script name]
# sbatch --array=0-842 1_summa_array_to_copernicus.sh
# reference: https://docs.computecanada.ca/wiki/Job_arrays
# ----------------------------------------------------------------------------------------------

script_folder=scripts
control_file="control_active.txt"

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

# Get model and settings paths.
model_path="$(read_from_control $control_file "model_dst_path")"
if [ "$model_path" = "default" ]; then model_path="${domain_path}/model"; fi

summa_settings_relpath="$(read_from_control $control_file "summa_settings_relpath")"
summa_settings_path=$model_path/$summa_settings_relpath

# Get summa fileManager files.
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings_path/$summa_filemanager

# Get summa and mizuRoute executable paths.
summaExe="$(read_from_control $control_file "summa_exe_path")"

# -----------------------------------------------------------------------------------------
# ------------------------------------ Run summa ------------------------------------------
# -----------------------------------------------------------------------------------------
# (1) Define the GRU settings
gruMax="$(read_from_control $control_file "nGRU")"
cpuPerJob=32 # each job uses 32 cpus/node.
gruCount=53  # each summa runs 53 grus per cpu.

# (2) Get the array ID for further use
offset=$SLURM_ARRAY_TASK_ID 

# (3) Start at 1 for array ID 1, 2022 for array ID 2, etc
gruStart=$(( 1 + gruCount*cpuPerJob*offset ))
gruEnd=$(( gruCount*cpuPerJob*(offset+1) ))

# Check that we don't specify too many basins
if [ $gruEnd -gt $gruMax ]; then
gruEnd=$gruMax
fi

# (4) Run job array commands
# $summaExe -g $gruStart $gruCount -r never -m $summa_filemanager > logs/summa_log_${offset}.txt

./scripts/make_summa_run_list.sh $gruStart $gruCount $gruEnd $cpuPerJob $offset
srun --kill-on-bad-exit=0 --multi-prog summa_run_list/GRU_run_list_${offset}.txt > logs/summa_log_${offset}.txt
