#!/usr/bin/env python
# coding: utf-8

# #### Create ostIn.txt
# This code creates ostIn.txt based on the user specified parameter list.
# 1. prepare Ostrich parameter pair files based on multiplier bounds file.
# 2. write ostIn.txt based on ostIn.tpl.

# import module
import os, sys, argparse, shutil, time
import netCDF4 as nc
import numpy as np

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
    
    # an example: python create_ostIn.py ../control_active.txt

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

    # read calib path
    calib_path = read_from_control(control_file, 'calib_path')
    if calib_path == 'default':
        calib_path = os.path.join(domain_path, 'calib')

    # create a template folder to store template files.
    calib_tpl_path = os.path.join(calib_path, 'tpl')
    if not os.path.exists(calib_tpl_path):
        os.makedirs(calib_tpl_path)


    # #### 1. Prepare Ostrich parameter pair files
    # read multiplier bounds file.
    multp_bounds = read_from_control(control_file, 'multp_bounds')
    multp_bounds = os.path.join(calib_path, multp_bounds)
    multp_bounds_arr = np.loadtxt(multp_bounds, dtype='str', delimiter=',') # MultiplierName,InitialValue,LowerLimit,UpperLimit.

    # write multiplier template file.
    multp_tpl = read_from_control(control_file, 'multp_tpl')
    multp_tpl = os.path.join(calib_tpl_path, multp_tpl)

    if os.path.exists(multp_tpl):
        os.remove(multp_tpl)
    np.savetxt(multp_tpl, multp_bounds_arr[:,0], fmt='%s')

    # write multiplier txt file.
    multp_value = read_from_control(control_file, 'multp_value')
    multp_value = os.path.join(calib_path, multp_value)
    np.savetxt(multp_value, multp_bounds_arr[:,1], fmt='%s')
    

    # #### 2. Write ostIn.txt based on ostIn.tpl
    
    # identify ostIn template and txt file.
    ostIn_tpl = read_from_control(control_file, 'ostIn_tpl')
    ostIn_src = os.path.join(calib_tpl_path, ostIn_tpl)
    ostIn_dst = os.path.join(calib_path, 'ostIn.txt')

    # check if template ostIn file exists.
    if not os.path.exists(ostIn_src):
        print('Template ostIn file does not exist in %s'%(calib_tpl_path))
        sys.exit(0)

    # find out the line numbers with FilePairs and parameter configurations
    with open(ostIn_src,"r") as src:
        for number, line in enumerate(src):
            line_strip = line.strip()

            if line.startswith('EndFilePairs'):
                filePairs_line_number = number # to add filePairs config before this line

            elif line.startswith('EndParams'):
                param_line_number = number # to add param config before this line

    # write ostIn.txt based on ostIn.tpl
    with open(ostIn_src,"r") as src:
        with open(ostIn_dst,"w") as dst:
            for number, line in enumerate(src):
                line_strip = line.strip()

                if line_strip and (not (line_strip.startswith('#'))):  

                    # (1) add param configurations 
                    if number==filePairs_line_number:

                        # file pair paths relative to calib_path 
                        tpl_relpath = os.path.relpath(multp_tpl, start = calib_path)
                        value_relpath = os.path.relpath(multp_value, start = calib_path)
                        # define and write a new line
                        add_line = ('%s; %s\n')%(tpl_relpath, value_relpath)                                
                        dst.write(add_line)

                    # (2) add param ranges 
                    if number==param_line_number:
                        for i in range(len(multp_bounds_arr)):
                            # identify param configs
                            param_name = multp_bounds_arr[i,0]
                            param_ini  = multp_bounds_arr[i,1]
                            param_min  = multp_bounds_arr[i,2]
                            param_max  = multp_bounds_arr[i,3]
                            # define and write a new line
                            add_line = ('%s\t%s\t%.7f\t%.7f\tnone\tnone\tnone\tfree\n')% \
                            (param_name, param_ini, float(param_min), float(param_max))                                 
                            dst.write(add_line)

                    # (3) update random seed
                    if ('xxxxxxxxx' in line_strip):
                        rand_num_digit  = 9  # digit number of random seed
                        t          = int(time.time()*(10**rand_num_digit))
                        t_cut      = t-(int(t/(10**rand_num_digit)))*(10**rand_num_digit)
                        line_strip = line_strip.replace('xxxxxxxxx',str(t_cut))

                    # (4) update Ostrich restart based on the existence of 'OstModel0.txt'.
                    if (line_strip.startswith('OstrichWarmStart')):
                        if os.path.exists('OstModel0.txt'):
                            line_strip = 'OstrichWarmStart yes' # default is no 

                    # (5) update MaxIterations based on control_active.txt 
                    # Note: this is applied only if the DDS algorithm is used.
                    max_iterations = read_from_control(control_file, 'max_iterations')
                    if line_strip.startswith('MaxIterations'):
                        max_iterations_old = line.split('#',1)[0].strip().split(None,1)[1]
                        line_strip = line_strip.replace(max_iterations_old, max_iterations)                    

                new_line = line_strip+'\n'    
                dst.write(new_line)
