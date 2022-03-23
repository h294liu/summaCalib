#!/bin/bash
# A. Wood, 2018
# make a job list to run summa in parallel across requested cores

totGRU=nGRU
countGRU=nCount
# totTasks=`echo $totGRU $countGRU | awk '{r=$1/$2;if(int(r)!=r){print r+1}else{print r}}' `
totTasks=nTask
echo totTasks = $totTasks

# model settings
Exe=/home/h294liu/github/summa/bin/summa.exe 
fileMgr=../model/settings/SUMMA/fileManager.txt 

# copy $Exe to local to save summa_run_list.txt size
cp $Exe summa.exe

# remove existing file
jobList=summa_run_list.txt
rm -f $jobList

# write new summa_run_list.txt
J=0
while [ $J -lt $totTasks ]; do

  # set gru bounds per job; capping at max of totGRU
  startGRU=`echo $J $countGRU | awk '{print $1*$2+1}' `
  jCount=`echo $startGRU $countGRU | awk '{jend=$1+$2-1;t='$totGRU';if(jend>t){print t-$1+1}else{print $2}}' `

  # make joblist
  echo $J summa.exe -g $startGRU $jCount -r never -m $fileMgr >> $jobList   # slurm; can't do log files
  J=$(( $J + 1 ))
done

# echo now adjust LSF file to match nNodes"*"nCores ">" $totGRU
