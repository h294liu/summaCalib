#!/bin/bash
# make a job list to run summa in parallel across requested cores

startGRU=$1
countGRU=$2
endGRU=$3
cpuPerJob=$4
offset=$5

# model settings
Exe=/home/h294liu/github/summa_nelson/bin/summa.exe 
fileMgr=../model/settings/SUMMA/fileManager.txt 

# copy $Exe to local to save summa_run_list.txt size
cp $Exe summa.exe

# remove existing summa_run_list.txt.
jobList=summa_run_list/GRU_run_list_${offset}.txt
rm -f $jobList

# write new summa_run_list.txt.
J=0
while [ $J -lt $cpuPerJob ]; do

  # set gru bounds per job; capping at max of endGRU
  startGRU_J=`echo $startGRU $J $countGRU | awk '{print $1+$2*$3}' `
  countGRU_J=`echo $startGRU_J $countGRU | awk '{jend=$1+$2-1;t='$endGRU';if(jend>t){print t-$1+1}else{print $2}}' `

  # make joblist
  echo $J summa.exe -g $startGRU_J $countGRU_J -r never -m $fileMgr >> $jobList   # slurm; can't do log files
  J=$(( $J + 1 ))
done
