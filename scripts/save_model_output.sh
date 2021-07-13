#!/bin/bash
# save use-specified files associated with each model run.
# preserved files will be stored in directories named "runNNN", where NNN is a counter.
# Ostrich will pass the following arguments into this script: rank(1), trial(2), counter(3),
# and objective function category(4). Here counter is used.

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
    info=$(echo ${info##* }) # get string after space
    info="${info%\'}" # remove the suffix '. Do nothing if no '.
    info="${info#\'}" # remove the prefix '. Do nothing if no '.
    echo $info
}

# -----------------------------------------------------------------------------------------
# ------------------------- Settings based on control_file --------------------------------
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
route_settings_relpath="$(read_from_control $control_file "route_settings_relpath")"
route_settings_path=$model_path/$route_settings_relpath

# Get summa and mizuRoute controls/fileManager files.
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings_path/$summa_filemanager
route_control="$(read_from_control $control_file "route_control")"
route_control=$route_settings_path/$route_control

# Extract summa output path and prefix from fileManager.txt.
summa_outputPath="$(read_from_summa_route_control $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_control $summa_filemanager "outFilePrefix")"

# Extract summa parameter file from fileManager.txt.
trialParamFile="$(read_from_summa_route_control $summa_filemanager "trialParamFile")"
trialParamFile_priori=${trialParamFile%\.nc}.priori.nc

trialParamFile=$summa_settings_path/$trialParamFile
trialParamFile_priori=$summa_settings_path/$trialParamFile_priori

# Extract mizuRoute output path and prefix from route_control (use for removing outputs).
route_outputPath="$(read_from_summa_route_control $route_control "<output_dir>")"
route_outFilePrefix="$(read_from_summa_route_control $route_control "<case_name>")"

# Get statistical output file from control_file.
stat_output="$(read_from_control $control_file "stat_output")"
stat_output=${calib_path}/${stat_output}

# Get Ostrich experiment ID and multiplier.txt from control_file.
experiment_id="$(read_from_control $control_file "experiment_id")"
multp_value="$(read_from_control $control_file "multp_value")"

# -----------------------------------------------------------------------------------------
# --------------------------------------- Save --------------------------------------------
# -----------------------------------------------------------------------------------------

outDir="${calib_path}/output_archive/experiment$experiment_id"
runDir=$outDir/run$3
mkdir -p $runDir

echo "$(date +"%Y-%m-%d %T"): saving model output files for run $3."
date | awk '{printf("%s: saving model output\n",$0)}' >> $calib_path/timetrack.log

# save multipliers.txt.
cp $calib_path/$multp_value $runDir/

# save hydrologic model parameter file and outputs.
cp $trialParamFile $runDir/
cp $summa_outputPath/${summa_outFilePrefix}_day.nc $runDir/
cp $route_outputPath/${summa_outFilePrefix}.mizuRoute.nc $runDir/

# save model performance evaluation result and Ostrich exeOut files.
cp $stat_output $runDir/
cp $calib_path/OstExeOut.txt $runDir/

exit 0
