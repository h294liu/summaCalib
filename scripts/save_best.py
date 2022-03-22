#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import math as m
import os, sys, argparse 
import shutil

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


def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to save the best model outputs.')
    parser.add_argument('controlFile', help='path of the overall control file.')
    args = parser.parse_args()
    return(args)

if __name__ == "__main__":
    
    # Example: python save_best.py controlFile

    # --- process command line ---
    # check args
    if len(sys.argv) != 2:
        print("Usage: %s <control_file>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()
    control_file = args.controlFile

    # read paths from control_file.
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)

    # read new hydrologic model path from control_file.
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')

    # read calib path from control_file.
    calib_path = read_from_control(control_file, 'calib_path')
    if calib_path == 'default':
        calib_path = os.path.join(domain_path, 'calib')
        
    # read summa settings and fileManager paths from control_file.
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_dst_path, summa_settings_relpath)
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_settings_path, summa_filemanager)

    # read summa output path and prefix.
    summa_outputPath = read_from_summa_route_control(summa_filemanager, 'outputPath')
    summa_outFilePrefix = read_from_summa_route_control(summa_filemanager, 'outFilePrefix')
    summa_output_file = os.path.join(summa_outputPath,summa_outFilePrefix+'_day.nc')
    
    # read mizuRoute setting and control files paths from control_file.
    route_settings_relpath = read_from_control(control_file, 'route_settings_relpath')
    route_settings_path = os.path.join(model_dst_path, route_settings_relpath)
    route_control = read_from_control(control_file, 'route_control')
    route_control = os.path.join(route_settings_path, route_control)

    # read mizuRoute output path and prefix
    route_outputPath = read_from_summa_route_control(route_control, '<output_dir>')
    route_outFilePrefix=read_from_summa_route_control(route_control, "<case_name>")
    route_output_file = os.path.join(route_outputPath, route_outFilePrefix+'.mizuRoute.nc') 

    # summa param file.
    trialParamFile = read_from_summa_route_control(summa_filemanager, 'trialParamFile')
    trialParamFile = os.path.join(summa_settings_path, trialParamFile)
    
    # statistical output file.
    stat_filename = read_from_control(control_file, 'stat_output')
    stat_output = os.path.join(calib_path, stat_filename)

    #####################################
    # check/create output folder
    save_best_dir = os.path.join(calib_path,'save_best')
    if not os.path.exists(save_best_dir):
        os.makedirs(save_best_dir)    
    stat_best_output = os.path.join(save_best_dir, stat_filename)

    # save results if save_best_dir is empty or a new best solution appears.
    if not os.listdir(save_best_dir):
        shutil.copy2(summa_output_file, save_best_dir)
        shutil.copy2(route_output_file, save_best_dir)
        shutil.copy2(stat_output, save_best_dir)
        shutil.copy2(trialParamFile, save_best_dir)
    else:
        # check if the previous param gets better
        obj_previous = np.loadtxt(stat_output, usecols=[0])[0] * (-1) # obj = negative KGE 
        obj_best = np.loadtxt(stat_best_output, usecols=[0])[0] * (-1) 
        
        if obj_previous<obj_best:
            shutil.copy2(summa_output_file, save_best_dir)
            shutil.copy2(route_output_file, save_best_dir)
            shutil.copy2(stat_output, save_best_dir)
            shutil.copy2(trialParamFile, save_best_dir)
            

        

