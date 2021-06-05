#!/bin/bash
# H. Liu, A. Wood
# run interaction of Ostrich:  update params, run and route model, calculate diagnostics
# creates a time tracking log to monitor pace of calibration
# USES on cluster: module load python; module load nco 

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

read_from_summa_mizuRoute_control () {
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
summa_settings=$model_path/settings/SUMMA  # Be careful! Hard coded.
mizuRoute_settings=$model_path/settings/mizuRoute

# Get summa and mizuRoute controls/fileManager files.
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings/$summa_filemanager
route_control="$(read_from_control $control_file "mizuroute_control")"
route_control=$mizuRoute_settings/$route_control

# Get summa and mizuRoute executable paths.
summaExe="$(read_from_control $control_file "summa_exe_path")"
routeExe="$(read_from_control $control_file "mizuroute_exe_path")"

# Get numebr of GRUs for the whole basin (used for splitting summa run).
nGRU="$(read_from_control $control_file "nGRU")"
nCoresPerJob=1  # splits domain into 1 gru per job for now.

# Extract summa output path and prefix from fileManager.txt (use to remove summa outputs).
summa_outputPath="$(read_from_summa_mizuRoute_control $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_mizuRoute_control $summa_filemanager "outFilePrefix")"

# Extract mizuRoute output path and prefix from route_control (use for removing outputs).
route_outputPath="$(read_from_summa_mizuRoute_control $route_control "<output_dir>")"
route_outFilePrefix="$(read_from_summa_mizuRoute_control $route_control "<case_name>")"

# Get statistical output file from control_file.
stat_output="$(read_from_control $control_file "stat_output")"
stat_output=${calib_path}/${stat_output}

# -----------------------------------------------------------------------------------------
# ---------------------------------- Execute trial ----------------------------------------
# -----------------------------------------------------------------------------------------

echo "===== executing trial ====="
echo " "
date | awk '{printf("%s: ---- executing new trial ----\n",$0)}' >> $calib_path/timetrack.log

# ------------------------------------------------------------------------------
# --- 1.  update params (takes basin id as arg)                              ---
# ------------------------------------------------------------------------------

echo "--- updating params ---"
date | awk '{printf("%s: updating params\n",$0)}' >> $calib_path/timetrack.log
python $calib_path/scripts/3a_update_paramTrial.py $control_file
echo " "

# ------------------------------------------------------------------------------
# --- 2.  run summa                                                          ---
# ------------------------------------------------------------------------------
echo Running and routing 

# Remove previous outputs before we run
if [ ! -d $summa_outputPath ]; then mkdir -p $summa_outputPath; fi
rm -f $summa_outputPath/${summa_outFilePrefix}*

# --- Run Summa (split domain) and concatenate/adjust output for routing
date | awk '{printf("%s: running summa\n",$0)}' >> $calib_path/timetrack.log

for gru in $(seq 1 $nGRU); do
  echo "running $gru"
#   ${summaExe} -g $gru $nCoresPerJob -r never -m $summa_filemanager &  # parallel run
  ${summaExe} -g $gru $nCoresPerJob -r never -m $summa_filemanager   # seq. run by gru
done
wait

# merge output runoff into one file for routing
echo concatenating output files in $summa_outputPath
python $calib_path/scripts/3b_concat_split_summa.py $control_file

# shift output time back 1 day for routing model - only if computing daily outputs!
# Be careful. Hard coded summa _timestep.nc name.
ncap2 -O -s 'time[time]=time-86400' $summa_outputPath/$summa_outFilePrefix\_timestep.nc $summa_outputPath/$summa_outFilePrefix\_timestep.nc

# ------------------------------------------------------------------------------
# --- 3.  route summa output with mizuRoute                                  ---
# ------------------------------------------------------------------------------
date | awk '{printf("%s: routing summa\n",$0)}' >> $calib_path/timetrack.log

# # route, after removing existing output
# create summa output path if it does not exist.
if [ ! -d $route_outputPath ]; then mkdir -p $route_outputPath; fi
rm -f $route_outputPath/${route_outFilePrefix}*
${routeExe} $route_control

# ------------------------------------------------------------------------------
# --- 4.  calculate statistics for Ostrich                                   ---
# ------------------------------------------------------------------------------
echo calculating statistics
date | awk '{printf("%s: calculating statistics\n",$0)}' >> $calib_path/timetrack.log

# Remove the stats output file to make sure it is created properly with every run
rm -f $stat_output
python $calib_path/scripts/3c_calc_sim_stats.py $control_file

date | awk '{printf("%s: done with trial\n",$0)}' >> $calib_path/timetrack.log
wait
exit 0
