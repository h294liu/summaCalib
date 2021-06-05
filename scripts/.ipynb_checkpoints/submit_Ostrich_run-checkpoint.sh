#!/bin/bash
# #PBS -N ostrich_BowRiverBelowCarselandDam
# #PBS -A P48500028
# #PBS -q regular
# #PBS -l select=10:ncpus=36:mpiprocs=36
# #PBS -l walltime=12:00:00
# #PBS -j oe
# #PBS -o ostrich.BowRiverBelowCarselandDam.out
# #PBS -e ostrich.BowRiverBelowCarselandDam.err

# mkdir -p /glade/scratch/hongli/temp
# export TMPDIR=/glade/scratch/hongli/temp
# export MPI_SHEPHERD=true

#### Note: This bash file must be put in the same directory as Ostrich.exe.

script_folder=scripts
control_active=control_active.txt

# Update summa and mizuRoute sim start/end time based on control_active.txt.
python ${script_folder}/1_update_model_StartEndTime.py $control_active

# Create ostIn.txt by adding multiplier and other information.
python ${script_folder}/2_create_ostIn.py $control_active

# Run Ostrich.
./Ostrich.exe
