#!/bin/bash
#PBS -N summa_0_06282000
#PBS -A P48500028
#PBS -q regular
#PBS -l select=2:ncpus=36:mpiprocs=36
#PBS -l walltime=04:00:00
#PBS -m abe
#PBS -o %x-%j.out
#PBS -e %x-%j.err


mkdir -p /glade/u/home/hongli/scratch/temp
export TMPDIR=/glade/u/home/hongli/scratch/temp
export MPI_SHEPHERD=true

#### Note: This bash file must be put in the same directory as Ostrich.exe.

script_folder=scripts
control_active=control_active.txt

# Update summa and mizuRoute sim start/end time based on control_active.txt.
python ${script_folder}/1_update_model_config_files.py $control_active

# Create ostIn.txt by adding multiplier and other information.
python ${script_folder}/2_create_ostIn.py $control_active

# Run Ostrich.
./Ostrich.exe
