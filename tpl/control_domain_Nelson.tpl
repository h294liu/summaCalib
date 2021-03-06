# SUMMA parameter estimation workflow setting file.
# Characters '|' and '#' are used as separators to find the actual setting values. 
# Any text behind '|' is assumed to be part of the setting value, unless preceded by '#'.

# Note on path specification
# If deviating from default paths, a full path must be specified. E.g. '/home/user/non-default/path'

## ---- PART 1. Common path settings ---- 
root_path              | /home/h294liu/scratch/7_nelson/model  # root path where parameter estimation will be stored.
domain_name            | xxxxxx   # use as the domain folder name for the prepared data.

## ---- PART 2. Hydrologic model settings  ---- 
model_src_path         | /home/h294liu/project/proj/7_nelson/model/xxxxxx # path of source hydrologic model.
model_dst_path         | default               # path of destination hydrologic model. If 'default', use '[root_path]/[domain_name]/model'.

summa_settings_relpath | settings/SUMMA        # relative path of summa model settings, relative to [model_dst_path]. 
summa_filemanager      | fileManager.txt # Name of the SUMMA master configuration file.
summa_exe_path         | /home/h294liu/github/summa/bin/summa.exe                   # summa executable path

route_settings_relpath | settings/mizuRoute    # relative path of summa model settings, relative to [model_dst_path]. 
route_control          | mizuroute.control     # Name of the mizuRoute configuration file.
route_exe_path         | /home/h294liu/github/mizuroute/route/bin/mizuroute.exe     # muziroute executable path.

simStartTime           | SIMSTARTTIME     # simualtion start time for parameter estimation, in format yyyy-mm-dd hh:mm. 
simEndTime             | SIMENDTIME      # simualtion end time for parameter estimation, in format yyyy-mm-dd hh:mm.  
nGRU                   | NGRU                  # number of GRUs for whole basin, can query with ncinfo -d gru <attributes_file>.
domain_area            | DOMAIN_AREA           # domain area in sqaure meter, used to calculate the range of routingGammaScale.

## ---- PART 3. Evaluated parameter settings ---- 
object_parameters      | k_macropore, k_soil, theta_sat, aquiferBaseflowExp, aquiferBaseflowRate, qSurfScale, summerLAI, frozenPrecipMultip, heightCanopyTop, routingGammaScale, routingGammaShape, Fcapil # parameters to be optimized or evaluated.

## ---- PART 4. Paramerter estimation settings ---- 
calib_path             | default                      # path of parameter estimation. If 'default', use '[root_path]/[domain_name]/calib'.
ostIn_tpl              | ostIn.DDS.tpl                 # Name of ostIn template file. Workflow input in '[calib_path]/tpl/[ostIn_tpl]'. eg, ostIn.GLUE.tpl/ostIn.SCE.tpl/ostIn.GA.tpl/ostIn.DDS.tpl
ostrich_exe_path       | /home/h294liu/github/Ostrich_v17.12.19/Source/OstrichGCC # Path of Ostrich executable.
param_bounds           | summa_parameter_bounds.txt   # Name of file with summa parameter bounds. Workflow output in [calib_path].
multp_bounds           | multiplier_bounds.txt        # Name of file with multiplier bounds. Workflow output in [calib_path].
multp_tpl              | multipliers.tpl              # Name of file with a list of multiplier names. Workflow output in [calib_path]/tpl.
multp_value            | multipliers.txt              # Name of file with a list of multiplier values. Workflow output in [calib_path].

experiment_id          | 1	                          # Optimization experiment ID, used to archive optimization results.
max_iterations         | 500                            # Maximum Number of iterations for optimization. Optional, depending on the optimization method.

## ---- PART 5. Calculate statistics settings ----
q_seg_index            | Q_SEG_INDEX                  # segment index in routing file matching obs location (start from 1).
obs_file               | /home/h294liu/project/proj/7_nelson/Flow_data/Phase_0&1_Natural/Natural_gauge_stn_Qobs_calib_phase_1_cms.csv  # path of observed streamflow data.
obs_unit               | cms                          # observation streamflow data unit (cfs or cms).
stat_output            | trial_stats.txt              # Name of file with statistical metric results.
statStartDate          | STATSTARTTIME                   # Start date of statistics calculation period, in format yyyy-mm-dd. 
statEndDate            | STATENDTIME                   # End date of statistics calculation period, in format yyyy-mm-dd.  
