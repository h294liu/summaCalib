#!/usr/bin/env python
# coding: utf-8

# ### Make folder structure ###
# Make the initial folder structure based on a given control file. All other files in the workflow will look for the file 'control_active.txt' during their execution. This script:<br>
# 1. copy the template control file into 'control_active.txt'.
# 2. make folders and files for parameter estimation.

# import module
import os, sys, argparse, shutil
from datetime import datetime
from os.path import dirname, abspath

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to icalculate model evaluation statistics.')
    parser.add_argument('control_tpl', help='path of the template control file.')
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
    
    # an example: python 1_prepare_folders.py ../control.tpl

    # --- process command line --- 
    # check args
    if len(sys.argv) != 2:
        print("Usage: %s <control_tpl>" % sys.argv[0])
        sys.exit(0)
    # otherwise continue
    args = process_command_line()    
    control_tpl = args.control_tpl
    
    
    # #### Copy template control file into 'control_active.txt'
    control_file = 'control_active.txt'
    shutil.copyfile(control_tpl, control_file);

    
    # ####  Make folders  
    # read paths from control_file
    root_path = read_from_control(control_file, 'root_path')
    domain_name = read_from_control(control_file, 'domain_name')
    complexity_level = read_from_control(control_file, 'complexity_level')        
    domain_path = os.path.join(root_path, complexity_level+'_'+domain_name)

    # 1. Root and domain folders
    # create root_path where data will be stored. 
    if not os.path.exists(root_path):
        os.makedirs(root_path)

    # create domain_path where domain relevant data will be stored. 
    if not os.path.exists(domain_path):
        os.makedirs(domain_path)

    # 2. Hydrologic model folders
    # check if model_src_path exists which works as a template hydrlogic model. 
    model_src_path = read_from_control(control_file, 'model_src_path')
    if not os.path.exists(model_src_path):
        print('Source model does not eixst: %s.'%(model_src_path))

    # make model_dst_path
    model_dst_path = read_from_control(control_file, 'model_dst_path')
    if model_dst_path == 'default':
        model_dst_path = os.path.join(domain_path, 'model')
    if not os.path.exists(model_dst_path):
        os.makedirs(model_dst_path)

    # 3. Calibration folders
    # create calib_path where parameter estimation results will be stored.
    calib_path = read_from_control(control_file, 'calib_path')
    if calib_path == 'default':
        calib_path = os.path.join(domain_path, 'calib')
    if not os.path.exists(calib_path):
        os.makedirs(calib_path)

    # create analysis_path where analysis will be stored.
    analysis_path = os.path.join(calib_path, 'analysis')
    if not os.path.exists(analysis_path):
        os.makedirs(analysis_path)

    # make output_archive where the final best parameter information will be stored.
    model_output_path = os.path.join(calib_path, 'output_archive')

    # 4. Copy control_active.txt, tpl and scripts folders to Calib folder.
    # Be careful. Hard coded based on the current folder relationship.
    shutil.copy2(control_file, calib_path);
    
    src_path = dirname(dirname(abspath(__file__)))
    for folder in ['scripts', 'tpl']:
        folder_src = os.path.join(src_path,folder)
        folder_dst = os.path.join(calib_path,folder)
        if os.path.exists(folder_dst):
            shutil.rmtree(folder_dst)
        shutil.copytree(folder_src, folder_dst);
    
    # Move three codes in "scripts" folder to the same same directory as Ostrich.exe.
    for code in ['submit_run_Ostrich.sh', 'run_trial.sh', 'save_best.sh', 
                 'save_model_output.sh', 'submit_run_model.sh']:
        code_src = os.path.join(calib_path, 'scripts', code)
        code_dst = os.path.join(calib_path, code)
        if os.path.exists(code_dst):
            os.remove(code_dst)
        shutil.move(code_src, code_dst);

    # 5. Create Ostrich.exe symbolic link in Calib folder
    ostrich_exe_path = read_from_control(control_file, 'ostrich_exe_path')
    if not os.path.exists(os.path.join(calib_path,'Ostrich.exe')):
        os.symlink(ostrich_exe_path, os.path.join(calib_path,'Ostrich.exe'))

    
    # #### Code provenance 
    # Generates a basic log file in the domain folder and copies the control_active.txt and param_active.txt there.
    # create log_path where bakcup and log files will be stored.
    log_path = os.path.join(domain_path, '_workflow_log')
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # copy control_active.txt for backup
    shutil.copy(control_file, log_path);

    # Create a log file 
    logFile = 'log.txt'
    now = datetime.now()
    with open(os.path.join(log_path,logFile), 'w') as file:

        lines = ['%s. Generated folder structure.'%(now.strftime('%Y/%m/%d %H:%M:%S'))]
        for txt in lines:
            file.write(txt)   
