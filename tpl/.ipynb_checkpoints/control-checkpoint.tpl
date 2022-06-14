# SUMMA parameter estimation workflow setting file.
# Characters '|' and '#' are used as separators to find the actual setting values. 
# Any text behind '|' is assumed to be part of the setting value, unless preceded by '#'.

# Note on path specification
# If deviating from default paths, a full path must be specified. E.g. '/home/user/non-default/path'

## ---- PART 1. Common path settings ---- 
root_path              | /glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/calib/06282000  # root path where parameter estimation will be stored.
complexity_level       | LEV
domain_name            | xxxxxx   # use as the domain folder name for the prepared data.

## ---- PART 2. Hydrologic model settings  ---- 
model_src_path         | /glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/06282000 # path of source hydrologic model.
model_dst_path         | default               # path of destination hydrologic model. If 'default', use '[root_path]/[domain_name]/model'.

summa_settings_relpath | settings/SUMMA        # relative path of summa model settings, relative to [model_dst_path]. 
summa_filemanager      | fileManager.txt # Name of the SUMMA master configuration file.
summa_exe_path         | /glade/u/home/andywood/proj/SHARP/models/summa/bin/summa_dev5.exe                   # summa executable path

route_settings_relpath | settings/mizuRoute    # relative path of summa model settings, relative to [model_dst_path]. 
route_control          | control.txt           # Name of the mizuRoute configuration file.
route_exe_path         | /glade/u/home/andywood/proj/SHARP/models/routing/mizuRoute/route/bin/mizuroute.exe     # muziroute executable path.

simStartTime           | 2005-10-01 00:00      # simualtion start time for parameter estimation, in format yyyy-mm-dd hh:mm. 
simEndTime             | 2012-09-30 24:00      # simualtion end time for parameter estimation, in format yyyy-mm-dd hh:mm.  
nGRU                   | 43                    # number of GRUs for whole basin, can query with ncinfo -d gru <attributes_file>.
domain_area            | 2216040386.101139     # domain area in sqaure meter, used to calculate the range of routingGammaScale.

## ---- PART 3. Evaluated parameter settings ---- 
object_parameters      | k_soil, theta_sat, aquiferBaseflowExp, aquiferBaseflowRate, qSurfScale, summerLAI, frozenPrecipMultip, heightCanopyTop, routingGammaScale, Fcapil, vGn_n # parameters to be optimized or evaluated.

## ---- PART 4. Paramerter estimation settings ---- 
calib_path             | default                      # path of parameter estimation. If 'default', use '[root_path]/[domain_name]/calib'.
ostIn_tpl              | ostIn.DDS.tpl                 # Name of ostIn template file. Workflow input in '[calib_path]/tpl/[ostIn_tpl]'. eg, ostIn.GLUE.tpl/ostIn.SCE.tpl/ostIn.GA.tpl/ostIn.DDS.tpl
ostrich_exe_path       | /glade/u/home/hongli/tools/ostrich/OstrichGCC # Path of Ostrich executable.
param_bounds           | summa_parameter_bounds.txt   # Name of file with summa parameter bounds. Workflow output in [calib_path].
multp_bounds           | multiplier_bounds.txt        # Name of file with multiplier bounds. Workflow output in [calib_path].
multp_tpl              | multipliers.tpl              # Name of file with a list of multiplier names. Workflow output in [calib_path]/tpl.
multp_value            | multipliers.txt              # Name of file with a list of multiplier values. Workflow output in [calib_path].

experiment_id          | 1	                          # Optimization experiment ID, used to archive optimization results.
max_iterations         | 100 # 1000                          # Maximum Number of iterations for optimization. Optional, depending on the optimization method.

## ---- PART 5. Calculate statistics settings ----
q_seg_index            | 1                           # segment index in routing file matching obs location (start from 1).
obs_file               | /glade/u/home/hongli/scratch/2020_06_02HRUcomplexity/model/obs/obs_flow.BBR_IN.cfs.csv  # path of observed streamflow data.
obs_unit               | cfs                          # observation streamflow data unit (cfs or cms).
stat_output            | trial_stats.txt              # Name of file with statistical metric results.
statStartDate          | 2007-10-01                   # Start date of statistics calculation period, in format yyyy-mm-dd. 
statEndDate            | 2012-09-30                   # End date of statistics calculation period, in format yyyy-mm-dd.  
