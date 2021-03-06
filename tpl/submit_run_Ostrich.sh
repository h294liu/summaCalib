#!/bin/bash
#SBATCH --account=rpp-kshook
#SBATCH --time=00:MM:00
#SBATCH --ntasks=NTASK
#SBATCH --mem-per-cpu=MEMXMB
#SBATCH --job-name=JOBNAME
#SBATCH --output=%x-%j.out

mkdir -p /home/h294liu/scratch/temp
export TMPDIR=/home/h294liu/scratch/temp
export MPI_SHEPHERD=true

#### Note: This bash file must be put in the same directory as Ostrich.exe.

script_folder=scripts
control_active=control_active.txt

# Update summa and mizuRoute sim start/end time based on control_active.txt.
python ${script_folder}/1_update_model_config_files.py $control_active

# Create ostIn.txt by adding multiplier and other information.
python ${script_folder}/2_create_ostIn.py $control_active

# Make summa run list.
chmod 744 scripts/make_summa_run_list.sh
./scripts/make_summa_run_list.sh

# Run Ostrich.
./Ostrich.exe
