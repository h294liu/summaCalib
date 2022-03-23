#!/bin/bash
# A. Wood, 2018
# make a job list to run summa in parallel across requested cores

totGRU=32024
countGRU=32
# totTasks=`echo $totGRU $countGRU | awk '{r=$1/$2;if(int(r)!=r){print r+1}else{print r}}' `
totTasks=1000
echo totTasks = $totTasks

# model settings
Exe=/home/h294liu/github/summa/bin/summa.exe 
fileMgr=../model/settings/SUMMA/fileManager.txt 
jobList=summa_run_list.txt

fileMgrShort=fileManager.txt
ExeShort=summa.exe

# create soft links and clean files
if [ ! -f $ExeShort ]; then
   ln -s $Exe $ExeShort
fi

if [ ! -f $fileMgrShort ]; then
   ln -s $fileMgr $fileMgrShort
fi

if [ -f $jobList ]; then
   rm -f $jobList
fi

# # option 1. make run file
# J=0
# while [ $J -lt $totTasks ]; do

#   # set gru bounds per job; capping at max of totGRU
#   startGRU=`echo $J $countGRU | awk '{print $1*$2+1}' `
#   jCount=`echo $startGRU $countGRU | awk '{jend=$1+$2-1;t='$totGRU';if(jend>t){print t-$1+1}else{print $2}}' `

#   # make joblist
#   echo $J $ExeShort -g $startGRU $jCount -r never -m $fileMgrShort >> $jobList   # slurm; can't do log files
#   J=$(( $J + 1 ))
# done

# option 2. copy run file
cp /home/h294liu/project/proj/7_nelson/scripts/9_check_wallClockTime_numFluxCalls_2nd/summa_run_list.txt $jobList