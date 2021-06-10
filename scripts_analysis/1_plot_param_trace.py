#!/usr/bin/env python
# coding: utf-8

# This code plots the parameter trace during a parameter estimation process.

import os, sys, argparse, shutil, datetime
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt 

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    # Positional mandatory arguments
    parser.add_argument('controlFile', help='path of the active control file.')
    
    # Optional arguments
    parser.add_argument("-id", "--experiment_id", help="calibration experiment id", type=int, default=0)
    # When experiment_id = 0, print OstOutput.txt results in the calib path.
    # When experiment _id != 0, go to output_archive and print OstOutput.txt results in the corresponding experiment ID.
    
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
    sample_values=np.asarray(sample_values)
    return  sample_ids,objs,sample_values


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
    direct_param_list = [] # a list of parameters that are directly estimated, not depending on multiplier.

#     control_file = '../control_active.txt'
#     experiment_id = 1

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
    output_path = os.path.join(analysis_path, '1_plot_param_trace')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    trialParamFile_temp = os.path.join(output_path, 'trialParam.temp.nc')  # temporary trialParam file      
    ofile = os.path.join(output_path, 'experiment%d.png'%(experiment_id))  # output plot figure

    # identify OstOutput.txt and trialParam.priori.nc
    if experiment_id == 0:
        ostOutput = os.path.join(calib_path, 'OstOutput0.txt')
        trialParamFile_priori = os.path.join(summa_settings_path, trialParamFile_priori)        
    else:
        archive_path = os.path.join(calib_path, 'output_archive', str(experiment_id))
        ostOutput = os.path.join(archive_path, 'OstOutput0.txt')
        trialParamFile_priori = os.path.join(archive_path, trialParamFile_priori)        
    # --------------------------- End Read settings -----------------------------
         
    # (1) read multiplier samples from OstOutput.txt     
    sample_ids,objs,multp_values = read_param_sample_from_ostOutput(ostOutput)

    # (2) read parameter names from summa_parameter_bounds.txt
    # param_names is a list of params corresponding to multiplier, used to update trialParam file.
    param_names = list(np.loadtxt(os.path.join(calib_path, 'summa_parameter_bounds.txt'), usecols=[0], dtype='str', delimiter=','))
    param_range = np.loadtxt(os.path.join(calib_path, 'summa_parameter_bounds.txt'), usecols=[2,3], delimiter=',')
    
    # (3) get a more complete list of params, used for plot. 
    output_param_names = param_names.copy() 
    
    # add soil parameters if soil parameters are included in param_names.
    soil_params = ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity', 'theta_sat']
    if any(soil_param in param_names for soil_param in soil_params):
        for soil_param in soil_params:
            if not soil_param in output_param_names:
                output_param_names.append(soil_param)
                
    # add canopy height parameters if thickness if included in param_names.
    canopyHeigh_params = ['heightCanopyBottom', 'heightCanopyTop']
    if 'thickness' in param_names:
        output_param_names.remove('thickness')
        for canopyHeigh_param in canopyHeigh_params:
            if not canopyHeigh_param in output_param_names:
                output_param_names.append(canopyHeigh_param)
            
    # sort output_param_names.
    output_param_names.sort()

    # (4) update param values based on multipler value and param priori value. 
    # and store the updated param values in array output_param_values.
    Nsample = len(sample_ids)
    Nparam = len(output_param_names)
    output_param_values = np.zeros((Nsample, Nparam))
    
    with nc.Dataset(trialParamFile_priori, 'r') as src:

        # loop all multiplier samples to get corresponding parameter values       
        for iSample in range(Nsample):
            multp_iSample = multp_values[iSample]           
        
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

                        # if param is 'theta_sat', update other four soil variables using a priori param value fractions.
                        if param_name == 'theta_sat':
                            param_ma_priori  = src.variables[param_name][:]
                            param_ma = dst.variables[param_name][:]

                            for add_param in ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity']:
                                add_param_ma_priori  = src.variables[add_param][:]
                                fraction =  np.divide(add_param_ma_priori.data, param_ma_priori.data) # fraction based on priori variable values
                                add_param_value = param_ma.data * fraction
                                dst.variables[add_param][:]= np.ma.array(add_param_value,                                                                          mask=np.ma.getmask(add_param_ma_priori),                                                                          fill_value=add_param_ma_priori.get_fill_value())

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

    # (5) plot objective function and parameter trace.
    col_num = 4        
    row_num = int(np.ceil(Nparam/float(col_num)))
    
    fig, ax = plt.subplots(row_num,col_num, figsize=(3.0*col_num, 3.0*0.75*row_num), constrained_layout=True)
    fig.suptitle('Calibration Experiment %d'%(experiment_id), fontsize='medium', fontweight='semibold')
    dpi_value=150

    for i in range(row_num):
        for j in range(col_num):
            
            subplot_count = i*col_num + j
            param_index = subplot_count - 1
            
            if subplot_count <= Nparam: 
                # plot obj function 
                if i==0 and j==0: 
                    ax[i,j].plot(sample_ids, objs, 'k-o', linewidth=0.75, markersize=1.0)
                    fig_count = i*col_num + j
                    title_str = '('+chr(ord('a') + subplot_count) +') ' + 'Objective function'   
                    y_label = '-KGE'

                # plot parameters
                else: 
                    param_name = output_param_names[param_index]
                    ax[i,j].plot(sample_ids, output_param_values[:, param_index], 'k-o', linewidth=0.75, markersize=1.0)
                    title_str = '('+chr(ord('a') + subplot_count) +') ' + param_name
                    y_label = 'Parameter' #param_name

                # axis, label, title, legend
                ax[i,j].set_title(title_str, fontsize='small', fontweight='semibold')
                ax[i,j].set_xlabel('Iterations', fontsize='small')
                ax[i,j].set_ylabel(y_label, fontsize='small')
            
            # blank subplot           
            else: 
                ax[i,j].axis('off')

    plt.rc('xtick',labelsize='small')
    plt.rc('ytick',labelsize='small')                
    fig.savefig(ofile, dpi=dpi_value)
    plt.close(fig)  
    if os.path.exists(trialParamFile_temp): 
        os.remove(trialParamFile_temp)         
