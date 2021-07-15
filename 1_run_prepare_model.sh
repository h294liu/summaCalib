#!/bin/bash

script_folder=scripts_prepare
control_tpl=control.tpl
control_active=control_active.txt

# Copy control file and make folders.
echo Prepare folders.
python ${script_folder}/1_prepare_folders.py $control_tpl

# Prepare hydrologic model based on a given hydro model.
echo Prepare hydrologic model.
python ${script_folder}/2_prepare_hydro_model.py $control_active

# Create a priori summa param trial from a one-day period summa run.
echo Prepare a priori parameter trial.
python ${script_folder}/3_prepare_priori_trialParam.py $control_active

# Define multiplier names and bounds.
echo Prepare multiplier names and bounds.
python ${script_folder}/4_prepare_multp_bounds.py $control_active

echo Done