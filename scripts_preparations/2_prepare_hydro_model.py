#!/usr/bin/env python
# coding: utf-8

# ### Prepare hydrologic model for sensitivity analysis ###
# In control file, users need to provide a source hydrologic model. This source model works as a reference to build a new hydrologic model that is used for parameter estimation or sensitivity analysis. 
# This code creates the new hydrologic model by:<br>
# 1. copying settings folder from source model to new model.
# 2. creating simulations folder in new model.
# 2. linking all other folders from source model to new model.

# import module
import os, sys, argparse, shutil

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    parser.add_argument('controlFile', help='path of the active control file.')
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

# main
if __name__ == '__main__':
    
    # an example: python 2_prepare_hydro_model.py control_active.txt

    # --- process command line --- 
    # check args
    if len(sys.argv) != 2:
        print("Usage: %s <controlFile>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
    
    # read paths from control_file
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    domain_path = os.path.join(root_path, domain_name)
    model_src_path = read_from_control(control_file, 'model_src_path')

    # read new hydrologic model path
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')

    
    # #### 1. Copy settings folder from source model to new model.
    scr_settings = os.path.join(model_src_path, 'settings')
    dst_settings = os.path.join(model_dst_path, 'settings')
    if os.path.exists(dst_settings):
        shutil.rmtree(dst_settings)
    shutil.copytree(scr_settings, dst_settings, symlinks=False);

    
    # #### 2. Create simulations folder in new model 
    dst_simulations = os.path.join(model_dst_path, 'simulations')
    if not os.path.exists(dst_simulations):
        os.makedirs(dst_simulations)

    
    # #### 3. Link all other folders from source model to new model.
    # forcing, parameters, shapefiles folder
    for folder in ['forcing', 'parameters', 'shapefiles']:
        scr = os.path.join(model_src_path, folder)
        dst = os.path.join(model_dst_path, folder)
        if os.path.islink(dst):
            os.unlink(dst)
            os.symlink(scr, dst)

    
    # #### 4. Update model paths in settings/SUMMA/fileManager.txt 
    summa_setting_path = os.path.join(model_dst_path, 'settings/SUMMA')
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager_temp = summa_filemanager.split('.txt')[0]+'_temp.txt'

    summa_filemanager = os.path.join(summa_setting_path, summa_filemanager)
    summa_filemanager_temp = os.path.join(summa_setting_path, summa_filemanager_temp)

    with open(summa_filemanager, 'r') as src:
        with open(summa_filemanager_temp, 'w') as dst:
            for line in src:
                if model_src_path in line:
                    line = line.replace(model_src_path, model_dst_path)
                dst.write(line)
    shutil.copy2(summa_filemanager_temp, summa_filemanager);
    os.remove(summa_filemanager_temp);

    # #### 5. Update model paths in settings/mizuRoute/mizuroute.control
    route_setting_path = os.path.join(model_dst_path, 'settings/mizuRoute')
    route_control = read_from_control(control_file, 'mizuroute_control')
    route_control_temp = route_control.split('.txt')[0]+'_temp.txt'

    route_control = os.path.join(route_setting_path, route_control)
    route_control_temp = os.path.join(route_setting_path, route_control_temp)

    with open(route_control, 'r') as src:
        with open(route_control_temp, 'w') as dst:
            for line in src:
                if model_src_path in line:
                    line = line.replace(model_src_path, model_dst_path)
                dst.write(line)
    shutil.copy2(route_control_temp, route_control);
    os.remove(route_control_temp);
