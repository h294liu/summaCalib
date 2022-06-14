#!/bin/bash
#PBS -N 3_DDS5
#PBS -A P48500028
#PBS -q regular
#PBS -l select=2:ncpus=36:mpiprocs=36
#PBS -l walltime=12:00:00
#PBS -o 3_DDS5.out
#PBS -e 3_DDS5.err

TmpDir=/glade/scratch/hongli/temp
mkdir -p $TmpDir

#### Note: This bash file must be put in the same directory as Ostrich.exe.

script_folder=scripts
control_active=control_active.txt

# Update summa and mizuRoute sim start/end time based on control_active.txt.
python ${script_folder}/1_update_model_config_files.py $control_active

# Create ostIn.txt by adding multiplier and other information.
python ${script_folder}/2_create_ostIn.py $control_active

# Run Ostrich.
./Ostrich.exe
