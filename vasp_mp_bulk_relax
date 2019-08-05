#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import argparse
from materials_workflows.vasp_functions import write_workflow_convergence_file, workflow_is_converged
from materials_workflows.vasp_functions import get_mpids_from_file, get_structures_from_materials_project
from materials_workflows.vasp_functions import structure_scaler
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input

################################################

''' Define Global Variables '''

workflow_name = 'bulk'
pwd = os.getcwd()
workflow_path = os.path.join(pwd, workflow_name)
mp_key = '' # user-specified Materials Project API key
################################################

def generate_input_files(filename, mp_key, to_scale=True):

    if os.path.isdir(workflow_path) == False:
        os.mkdir(workflow_path)

    try:
        id_list = get_mpids_from_file(os.path.join(pwd, filename), mp_key)
        structures = get_structures_from_materials_project(id_list)
    except:
        print('Specify mp_key variable in ''' Define Global Variables ''' section of vasp_mp_bulk_relax')
        
    if to_scale == True:
        scaled_structures = structure_scaler(structures) # resizes structure to compare with o-vacancy calculations
    else:
        scaled_structures = structures
        
    batch_write_input(scaled_structures, vasp_input_set=MPRelaxSet, output_dir=workflow_path,
                      make_dir_if_not_present=True)

    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            if file == 'INCAR':
                incar = open(os.path.join(dir, 'INCAR'), "r+")
                incar.write('NPAR = 2\n') # set to run on two cores
                incar.write('ISYM = 0\n') # removes symmetry from INCAR
                lines = incar.readlines()
                incar.close()
                
                with open(os.path.join(dir, 'CONVERGENCE'), 'a') as convergence:
                    convergence.write('0 MP_Bulk_Converge\n\n')
                    for line in lines:
                        convergence.write(line)
                convergence.close()

    write_workflow_convergence_file(workflow_path, False)

    return

def check_converged():

    pwd = os.getcwd()
    if workflow_is_converged(pwd) == True:
        write_workflow_convergence_file(pwd, True)
    else:
        write_workflow_convergence_file(pwd, False)

def rerun_task():
    #only needed for non-VASP calculations
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--gen_inputs', help='Generates inputs for workflow.',
                        action='store_true')
    parser.add_argument('-c', '--converged', help='Checks for convergence of workflow.',
                        action='store_true')
    parser.add_argument('-r', '--rerun', help='Reruns worklow. This does nothing if vasp workflow.',
                        action='store_true')
    args = parser.parse_args()

    if args.gen_inputs:
        generate_input_files('MPIDS', mp_key) # name of the file containing mp-ids and Materials Project API key
    elif args.converged:
        check_converged()
    else:
        rerun_task()
