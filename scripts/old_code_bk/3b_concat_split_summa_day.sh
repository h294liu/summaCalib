#!/bin/bash

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

control_file="control_active.txt"

# Get common paths.
root_path="$(read_from_control $control_file "root_path")"
domain_name="$(read_from_control $control_file "domain_name")"
domain_path=${root_path}/${domain_name}

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
summa_statePath="$(read_from_summa_route_control $summa_filemanager "statePath")"

# -----------------------------------------------------------------------------------------
# ---------------------------------- Execute trial ----------------------------------------
# -----------------------------------------------------------------------------------------

# define new directories
gruPath=$summa_outputPath/gru
hruPath=$summa_outputPath/hru
rm -rf $gruPath; mkdir -p $gruPath
rm -rf $hruPath; mkdir -p $hruPath

# define gru variables
gru1=gru
gru2=gruId
gru3=averageRoutedRunoff

# loop through files
echo Splitting gru and hru variables
for oldFile in $summa_outputPath/${summa_outFilePrefix}*G*_day.nc ; do

     # get the new file names
     fileName="$(basename $oldFile)"  # split out the file name
     gruFile=${gruPath}/$fileName     # new file name
     hruFile=${hruPath}/$fileName     # new file name
#      echo $oldFile

     # extract the hru and gru variables - this is necessary because `ncrcat` 
     # concatenates along the record dimension. In SUMMA outputs, `time` is the
     # record (unlimited) dimension by default. This means that for gru variables
     # we need to make the 'gru' dimension the record dimension and for `hru` 
     # variables, `hru` needs to be the record dimension. Here we separate `gru`
     # and `hru` variables into two separate files.
     ncks -h -O    -C -v${gru1},${gru2},${gru3} $oldFile $gruFile
     ncks -h -O -x -C -v${gru1},${gru2},${gru3} $oldFile $hruFile

     # reorder dimensions so that the gru/hru is the unlimited dimension, instead of time
     ncpdq -h -O -a gru,time $gruFile $gruFile
     ncpdq -h -O -a hru,time $hruFile $hruFile

done  # looping through files

# concatenate the files
echo Concatenating files
combineFile=$summa_outFilePrefix\_day.nc
ncrcat -h -O ${gruPath}/*G* ${gruPath}/${combineFile}
ncrcat -h -O ${hruPath}/*G* ${hruPath}/${combineFile}

# perturb dimensions - make time the unlimited dimension again
echo Perturbing dimensions
ncpdq -h -O -a time,gru ${gruPath}/${combineFile} ${gruPath}/${combineFile}
ncpdq -h -O -a time,hru ${hruPath}/${combineFile} ${hruPath}/${combineFile}

# combine gru and hru files
echo Combining files
cp ${hruPath}/${combineFile} $summa_outputPath/$summa_outFilePrefix\_day.nc
ncks -h -A ${gruPath}/${combineFile} $summa_outputPath/$summa_outFilePrefix\_day.nc

# rm -r $gruPath $hruPath

exit 0