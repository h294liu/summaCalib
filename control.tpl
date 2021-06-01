# SUMMA parameter estimation workflow setting file.
# Characters '|' and '#' are used as separators to find the actual setting values. 
# Any text behind '|' is assumed to be part of the setting value, unless preceded by '#'.

# Note on path specification
# If deviating from default paths, a full path must be specified. E.g. '/home/user/non-default/path'

## ---- PART 1. Common path settings ---- 
root_path              | /Users/hongliliu/Documents/prj/5_summaCalib/5_calib_test  # root path where parameter estimation will be stored.
domain_name            | BowAtBanff   # use as the domain folder name for the prepared data.

## ---- PART 2. Hydrologic model settings  ---- 
model_src_path         | /Users/hongliliu/Documents/prj/3_summaWorkflow/domain_BowAtBanff # path of source hydrologic model.
model_dst_path         | default               # path of destination hydrologic model. If 'default', use '[root_path]/[domain_name]/model'.
summa_filemanager      | fileManager.txt       # Name of the SUMMA master configuration file.
summa_basinParam       | basinParamInfo.txt    # Name of the file with default basin parameter values. 
summa_localParam       | localParamInfo.txt    # Name of the file with default local parameter values. 
summa_trialParams      | trialParams.nc        # Name of the file with specific parameter values. 
summa_attributes       | attributes.nc         # Name of the attributes file.
summa_coldstate        | coldState.nc          # Name of the file with intial states.
summa_outputControl    | outputControl.txt     # Name of the file that can contain trial parameter values 
summa_forcing_list     | forcingFileList.txt   # Name of the file that has the list of forcing files.

summa_exe_path         | /Users/hongliliu/Documents/github/summa/bin/summa.exe  # summa executable path
mizuroute_exe_path     | /Users/hongliliu/Documents/github/mizuroute/route/bin/mizuroute.exe     # muziroute executable path.
simStartTime           | 2008-01-01 00:00      # simualtion start time for parameter estimation. 
simEndTime             | 2008-01-31 23:00      # simualtion end time for parameter estimation. 

## ---- PART 3. Evaluated parameter settings ---- 
object_parameters         | k_macropore, k_soil, theta_sat, aquiferBaseflowExp, aquiferBaseflowRate, qSurfScale, summerLAI, frozenPrecipMultip, heightCanopyBottom, heightCanopyTop, routingGammaScale, routingGammaShape, Fcapil # parameters to be optimized or evaluated.
summa_trialParams_priori  | trialParams.priori.nc    # Name of the a priori trial parameter file.
simStartTime_priori       | 2008-01-01 00:00         # simualtion start time to get a priori param set.
simEndTime_priori         | 2008-01-02 23:00         # simualtion end time to get a priori param set.

## ---- PART 4. Paramerter estimation settings ---- 
calib_path               | default                      # path of parameter estimation. If 'default', use '[root_path]/[domain_name]/calib'.
param_bounds             | summa_parameter_bounds.txt   # Name of summa parameter bounds file. 
multp_bounds             | multiplier_bounds.txt        # Name of evaluateed multiplier bounds file. 
max_iterations           | 3	                        # Maximum Number of iterations for optimization.
