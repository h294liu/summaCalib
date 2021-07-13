#!/usr/bin/env python
# coding: utf-8

# This code plots the parameter trace during a parameter estimation process.
# Note: This code plots the incomplete trace of samples because it reads sampels from ostOutput.txt.
# Only the parameter sets that improve the objective function in comparison with the previous parameter set are plotted.

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os, sys, argparse, shutil, datetime
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt 

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    # Positional mandatory arguments
    parser.add_argument('controlFile', help='path of the active control file.')
    parser.add_argument("experiment_id", 
                        help="a list of calibration experiment ids to be plotted",
                        type=int, nargs='+')
    # experiment_id can take a list of integers.
    # when experiment_id = 0, it refers to files in the current calibration directory.
    
    args = parser.parse_args()
    return(args)

# Function to extract a given setting from the configuration file
def read_from_control(control_file, setting):
    
    # Open 'control_active.txt' and locate the line with setting
    with open(control_file) as ff:
        for line in ff:
            line = line.strip()
            if line.startswith(setting):
                break
    # Extract the setting's value
    substring = line.split('|',1)[1].split('#',1)[0].strip() 
    # Return this value    
    return substring

# Function to extract a given setting from the summa and mizuRoute manager/control files
def read_from_summa_route_control(control_file, setting):

    # Open fileManager.txt or route_control and locate the line with setting
    with open(control_file) as ff:
        for line in ff:
            line = line.strip()
            if line.startswith(setting):
                break
    # Extract the setting's value
    substring = line.split('!',1)[0].strip().split(None,1)[1].strip("'")
    # Return this value    
    return substring

def is_number(s):
    try:
        float(s)
        return True 
    except (ValueError,AttributeError):
        return False 
                    
def read_param_sample_from_ostOutput(ostOutput):    
    sample_ids=[]
    objs = []
    sample_values = []
    
    with open(ostOutput, 'r') as f:
        for line_number, line in enumerate(f):
            line = line.strip()
            if line and line.startswith('Ostrich Run Record'):
                line_param_name = line_number+1
                line_param_value_start = line_number+2
            elif line and line.startswith('Optimal Parameter Set'):
                line_param_value_end = line_number-2
                break
        if not 'Optimal Parameter Set' in f.read():
            line_param_value_end = line_number

    with open(ostOutput, 'r') as f:
        for line_number, line in enumerate(f):
            line = line.strip()
            if line and line_number >= line_param_value_start and line_number <= line_param_value_end:                      
                if all([is_number(s) for s in line.split()]) == True:

                    sample_ids.append(int(line.split()[0])) 
                    objs.append(float(line.split()[1]))
                    sample_values.append([float(x) for x in line.split()[2:-1]])
                
            elif line_number > line_param_value_end:
                break
    
    sample_ids=np.asarray(sample_ids)
    objs=np.asarray(objs)
    sample_values=np.asarray(sample_values)
    return  sample_ids,objs,sample_values

# Function to extract the param default values and bounds from basinParam and localParam.txt.
def read_basinParam_localParam(filename):
    param_names = []
    param_default = []
    param_min = []
    param_max =[]
    with open (filename, 'r') as f:
        for line in f:
            line=line.strip()
            if line and not line.startswith('!') and not line.startswith("'"):
                splits=line.split('|')
                if isinstance(splits[0].strip(), str):
                    param_names.append(splits[0].strip())
                    param_default.append(str_to_float(splits[1].strip()))
                    param_min.append(str_to_float(splits[2].strip()))
                    param_max.append(str_to_float(splits[3].strip()))
    return param_names, param_default, param_min, param_max

# Function to convert data from Fortran format to scientific format.
def str_to_float(data_str):
    if 'd' in data_str:
        x = data_str.split('d')[0]+'e'+data_str.split('d')[1]
        return float(x)
    else:
        return float(data_str)


# main
if __name__ == '__main__':
    
    # an example: python 1_plot_param_trace.py ../control_active.txt

    # --- process command line --- 
    # check args
    if len(sys.argv) < 2:
        print("Usage: %s <controlFile>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
    experiment_id = args.experiment_id
    
#     control_file = '/home/h294liu/project/proj/5_summaCalib/5_calib_test2/BowAtBanff5/calib/control_active.txt'
#     experiment_id = [1,2,3,4]

    direct_param_list = [] # a list of parameters that are directly estimated, not depending on multiplier.

    # --------------------------- Read settings -----------------------------
    # read paths from control_file.
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)
    
    # read calib path 
    calib_path = read_from_control(control_file, 'calib_path')
    if calib_path == 'default':
        calib_path = os.path.join(domain_path, 'calib')
    analysis_path = os.path.join(calib_path, 'analysis')

    # read new hydrologic model path, settings, fileManager.txt, trialParam.nc.
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')
    
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_dst_path, summa_settings_relpath)

    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_settings_path, summa_filemanager)

    trialParamFile = read_from_summa_route_control(summa_filemanager, 'trialParamFile')
    trialParamFile_priori = trialParamFile.split('.nc')[0] + '.priori.nc' # a priori param file

    # identify plot output path and file
    output_path = os.path.join(analysis_path, '1_plot_param_trace_partial')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    trialParamFile_temp = os.path.join(output_path, 'trialParam.temp.nc')  # temporary trialParam file   
    
    experiment_id_str = '_'.join([str(x) for x in experiment_id])
    ofile_fig = os.path.join(output_path, 'experiment%s_trace_partial.png'%(experiment_id_str))  # output plot figure
    ofile_txt = os.path.join(output_path, 'experiment%s_summary_ostOutput.txt'%(experiment_id_str))  # output best param information
   
    # --------------------------- End Read settings -----------------------------
         
    print('Read multiplier samples.')
    # (1) read multiplier samples from OstOutput.txt 
    experiment_num = len(experiment_id)
    max_itrations = np.zeros((experiment_num))
    for i in range(experiment_num):
        
        # identify archive path, trialParamFile_priori, and ostModel.txt
        if experiment_id[i] == 0:
            archive_path = calib_path
            trialParamFile_priori = os.path.join(summa_settings_path, trialParamFile_priori)
        else:
            archive_path = os.path.join(calib_path, 'output_archive', str(experiment_id[i]))
            trialParamFile_priori = os.path.join(archive_path, trialParamFile_priori)
            
        ostOutput = os.path.join(archive_path, 'OstOutput0.txt')
        
        # read ostOutput
        sample_ids,objs,multp_values = read_param_sample_from_ostOutput(ostOutput)
        max_itrations[i] =sample_ids[-1] # record the max iteration of a calib experiment.
        
        # append 
        if i == 0:
            sample_ids_concat,objs_concat,multp_values_concat = sample_ids,objs,multp_values
        else:
            sample_ids_update = sample_ids + np.sum(max_itrations[0:i]) # calculate cumulative sampel id.
            sample_ids_concat = np.concatenate((sample_ids_concat, sample_ids_update), axis=0)
            objs_concat = np.concatenate((objs_concat, objs), axis=0)
            multp_values_concat = np.concatenate((multp_values_concat, multp_values), axis=0)
            
    # identify the best parameter sets
    best_obj = np.min(objs_concat)
    best_indices = np.argwhere(objs_concat == best_obj)
    best_iterations_str = ",".join(map(str,map(int, list(sample_ids_concat[best_indices]))))
    
    f = open(ofile_txt, "w")
    print('--- Best KGE = %.4f. Occur %d times. \nAt iterations %s. \n'%(best_obj, len(best_indices), best_iterations_str))
    f.write('Best KGE = %.4f. Occur %d times. \nAt iterations %s. \n\n'%(best_obj, len(best_indices), best_iterations_str))
                
    print('Read parameter names and ranges.')
    # (2a) read parameter names from summa_parameter_bounds.txt
    # param_names is a list of params corresponding to multiplier, used to update trialParam file.
    param_names = list(np.loadtxt(os.path.join(calib_path, 'summa_parameter_bounds.txt'), usecols=[0], dtype='str', delimiter=','))
    param_range = np.loadtxt(os.path.join(calib_path, 'summa_parameter_bounds.txt'), usecols=[2,3], delimiter=',')
    
    # (2b) read parameter ranges from localParam.txt and basinParam.txt.
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_setting_path = os.path.join(model_dst_path, summa_settings_relpath)

    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_setting_path, summa_filemanager)

    basinParam = read_from_summa_route_control(summa_filemanager, 'globalGruParamFile')
    localParam = read_from_summa_route_control(summa_filemanager, 'globalHruParamFile')

    basinParam = os.path.join(summa_setting_path, basinParam)
    localParam = os.path.join(summa_setting_path, localParam)

    basin_param_names, basin_param_default, basin_param_min, basin_param_max = read_basinParam_localParam(basinParam)    
    local_param_names, local_param_default, local_param_min, local_param_max = read_basinParam_localParam(localParam)

    # (3) get a more complete list of params, used for plot. 
    output_param_names = param_names.copy() 
    
#     # add soil parameters if soil parameters are included in param_names.
#     soil_params = ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity', 'theta_sat']
#     if any(soil_param in param_names for soil_param in soil_params):
#         for soil_param in soil_params:
#             if not soil_param in output_param_names:
#                 output_param_names.append(soil_param)
                
    # add canopy height parameters if thickness if included in param_names.
    canopyHeigh_params = ['heightCanopyBottom', 'heightCanopyTop']
    if 'thickness' in param_names:
        output_param_names.remove('thickness')
        for canopyHeigh_param in canopyHeigh_params:
            if not canopyHeigh_param in output_param_names:
                output_param_names.append(canopyHeigh_param)
            
    # sort output_param_names.
    output_param_names.sort()

    print('Update parameter values based on multipler samples.')
    # (4) update param values based on multipler value and param priori value. 
    # and store the updated param values in array output_param_values.
    Nsample = len(sample_ids_concat)
    Nparam = len(output_param_names)
    output_param_values = np.zeros((Nsample, Nparam))
    
    with nc.Dataset(trialParamFile_priori, 'r') as src:

        # loop all multiplier samples to get corresponding parameter values       
        for iSample in range(Nsample):
            multp_iSample = multp_values_concat[iSample]           
        
            # --- copy trialParamFile_priori to be the base of trialParamFile.
            shutil.copy(trialParamFile_priori, trialParamFile_temp)

            # --- update param values in a template trialParam file and save new param values to array.
            with nc.Dataset(trialParamFile_temp, 'r+') as dst:

                for iParam in range(len(param_names)):
                    param_name = param_names[iParam]

                    # Part A: update all params except 'thickness'
                    if (param_name != 'thickness') and param_name in dst.variables.keys():  

                        # update param values
                        if not param_name in direct_param_list:# new_value = multipler * default_value
                            param_ma_priori = src.variables[param_name][:]               # priori param value mask array 
                            param_value     = param_ma_priori.data * multp_iSample[iParam]     # update param value mask array
                            dst.variables[param_name][:] = np.ma.array(param_value, \
                                                                       mask=np.ma.getmask(param_ma_priori), \
                                                                       fill_value=param_ma_priori.get_fill_value())
                        elif param_name in direct_param_list: # new_value = Ostrich value
                            param_ma_priori = src.variables[param_name][:]                          # priori param value mask array 
                            param_value     = np.ones_like(param_ma_priori.data) * multp_iSample[iParam]  # update param value mask array
                            dst.variables[param_name][:] = np.ma.array(param_value, \
                                                                       mask=np.ma.getmask(param_ma_priori),  \
                                                                       fill_value=param_ma_priori.get_fill_value())                   

#                         # if param is 'theta_sat', update other four soil variables using a priori param value fractions.
#                         if param_name == 'theta_sat':
#                             param_ma_priori  = src.variables[param_name][:]
#                             param_ma = dst.variables[param_name][:]

#                             for add_param in ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity']:
#                                 add_param_ma_priori  = src.variables[add_param][:]
#                                 fraction =  np.divide(add_param_ma_priori.data, param_ma_priori.data) # fraction based on priori variable values
#                                 add_param_value = param_ma.data * fraction
#                                 dst.variables[add_param][:]= np.ma.array(add_param_value,                                                                          mask=np.ma.getmask(add_param_ma_priori),                                                                          fill_value=add_param_ma_priori.get_fill_value())

                # After updating all parameters, update 'thickness' if it exists. 
                # Actually, use 'thickness' to calculate TopCanopyHeight.
                if 'thickness' in param_names:
                    tied_param_name   = 'heightCanopyBottom'
                    target_param_name = 'heightCanopyTop'

                    # update TopCanopyHeight
                    TH_param_ma_priori = src.variables[target_param_name][:]         # priori TopCanopyHeight mask array 
                    BH_param_ma_priori = src.variables[tied_param_name][:]           # priori BottomCanopyHeight mask array 
                    BH_param_ma        = dst.variables[tied_param_name][:]           # updated BottomCanopyHeight mask array
                    param_value        = BH_param_ma.data + \
                    (TH_param_ma_priori.data-BH_param_ma_priori.data)*multp_iSample[iParam]    # updated TopCanopyHeight values
                    dst.variables[target_param_name][:] = np.ma.array(param_value, \
                                                                      mask=np.ma.getmask(TH_param_ma_priori),  \
                                                                      fill_value=TH_param_ma_priori.get_fill_value())
            
                #  Part B: Extract output parameter values for the first GRU/HRU.
                # Be careful. Hard coded!
                for jParam in range(Nparam):
                    param_name = output_param_names[jParam]
                    param_ma = dst.variables[param_name][:]
                    output_param_values[iSample, jParam]=param_ma.data.flat[0]

    print('Plot parameter traces.')
    # (5) plot objective function and parameter trace.
    col_num = 4        
    row_num = int(np.ceil(Nparam/float(col_num)))
    
    fig, ax = plt.subplots(row_num,col_num, figsize=(3.0*col_num, 3.0*0.75*row_num), constrained_layout=True)
#     fig.suptitle('Calibration Experiment %d'%(experiment_id), fontsize='medium', fontweight='semibold')
    dpi_value=80

    for i in range(row_num):
        for j in range(col_num):
            
            subplot_count = i*col_num + j
            param_index = subplot_count - 1
            
            if subplot_count <= Nparam: 
                
                if i==0 and j==0:
                    # plot obj function 
                    ax[i,j].plot(sample_ids_concat, objs_concat,color='green',marker='^',
                                 linewidth=0.75,markersize=1.0)
                    fig_count = i*col_num + j
                    title_str = '('+chr(ord('a') + subplot_count) +') ' + 'Objective function'   
                    y_label = '-KGE'
                    
                    # plot initial and best obj functions
                    ax[i,j].plot(sample_ids_concat[0], objs_concat[0], 
                                 'D', markerfacecolor="none", markeredgecolor="darkorange", markersize=4);
                    ax[i,j].plot(sample_ids_concat[best_indices], objs_concat[best_indices], 
                                 's', markerfacecolor="none", markeredgecolor="red", markersize=4);

                else: 
                    # plot parameters
                    param_name = output_param_names[param_index]
                    ax[i,j].plot(sample_ids_concat, output_param_values[:, param_index],color='blue',marker='o',
                                 linewidth=0.75,markersize=1.0)
                    title_str = '('+chr(ord('a') + subplot_count) +') ' + param_name
                    y_label = 'Value' 
                
                    # plot the initial and best points 
                    ax[i,j].plot(sample_ids_concat[0], output_param_values[0, param_index], 
                                 'D', markerfacecolor="none", markeredgecolor="darkorange", markersize=4);
                    
                    best_param_values = output_param_values[best_indices, param_index]
                    ax[i,j].plot(sample_ids_concat[best_indices], best_param_values, 
                                 's', markerfacecolor="none", markeredgecolor="red", markersize=4);
                    
                    # save best results to text
                    #  if there are multiple best param sets, and all best param values are the same, save a single param value.
                    if len(best_indices)>1 and np.all(best_param_values == best_param_values[0]):
                        print('--- %s = %.6f.'%(param_name, best_param_values[-1]))   
                        f.write('%s = %.6f.\n'%(param_name, best_param_values[-1]))
                    
                    # if best param values are different, save all param values.
                    else: 
                        best_param_values_str = ",".join(map(str,map(float, list(best_param_values))))
                        print('--- %s = %s.'%(param_name, best_param_values_str))   
                        f.write('%s = %s.\n'%(param_name, best_param_values_str))

                # ylimit, axis, label, title
                if not (i==0 and j==0):
                    if param_name in param_names:
                        param_min = param_range[param_names.index(param_name)][0]
                        param_max = param_range[param_names.index(param_name)][1]
                    elif param_name in local_param_names:
                        param_min = local_param_min[local_param_names.index(param_name)]
                        param_max = local_param_max[local_param_names.index(param_name)]
                    elif param_name in basin_param_names:
                        param_min = basin_param_min[basin_param_names.index(param_name)]
                        param_max = basin_param_max[basin_param_names.index(param_name)]            
                    ax[i,j].set_ylim([param_min, param_max])

                ax[i,j].set_title(title_str, fontsize='small', fontweight='semibold')
                ax[i,j].set_xlabel('Iterations', fontsize='small')
                ax[i,j].set_ylabel(y_label, fontsize='small')
                
            # blank subplots           
            else: 
                # plot legend
                if subplot_count == Nparam+1:
                    ax[i,j].set_frame_on(False)
                    ax[i,j].get_xaxis().set_visible(False)
                    ax[i,j].get_yaxis().set_visible(False)
                    ax[i,j].plot(np.nan, np.nan, marker='^', color='green', label = 'Objective function')
                    ax[i,j].plot(np.nan, np.nan, marker='o', color='blue', label = 'Parameter sample')
                    ax[i,j].plot(np.nan, np.nan, 'D', markerfacecolor="none", markeredgecolor="darkorange", markersize=4, label='Initial value')
                    ax[i,j].plot(np.nan, np.nan, 's', markerfacecolor="none", markeredgecolor="red", markersize=4, label='Best value')
                    ax[i,j].legend(loc = 'center left')
                else:
                    ax[i,j].axis('off')

    plt.rc('xtick',labelsize='small')
    plt.rc('ytick',labelsize='small')                
    fig.savefig(ofile_fig, dpi=dpi_value)
    plt.close(fig)  
    if os.path.exists(trialParamFile_temp): 
        os.remove(trialParamFile_temp)         
    f.close()
