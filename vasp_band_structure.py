#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 18:44:20 2019
@author: Ryan Morelock
"""

import os
import argparse
from shutil import copy

from scripts.band_structure_inputs import BandStructureFiles
from materials_workflows.vasp_convergence.convergence_inputs import band_structure_calculation

from materials_workflows.vasp_functions import write_vasp_convergence_file, workflow_is_converged

from materials_workflows.vasp_functions import write_workflow_convergence_file, move_job_to_pass_path, get_previous_pass_path
 

################################################

''' Define Global Variables '''

workflow_name = 'band_structure'

pwd = os.getcwd()
workflow_path = os.path.join(pwd,workflow_name)

################################################

def gen_input():
    start_path = get_previous_pass_path(pwd,workflow_name)
  
    os.mkdir(workflow_path)
    copy(start_path + '/WAVECAR', workflow_path)
    copy(start_path + '/CHGCAR', workflow_path)

    files = BandStructureFiles(start_path)
    files.kpoints.write_file(workflow_path + '/KPOINTS')
    files.new_incar.write_file(workflow_path + '/INCAR')
    files.poscar.write_file(workflow_path + '/POSCAR')
    files.potcar.write_file(workflow_path + '/POTCAR')

    write_workflow_convergence_file(workflow_path, False) # TASK_CONVERGENCE
    convergence_writelines = band_structure_calculation()
    write_vasp_convergence_file(workflow_path, convergence_writelines) # CONVERGENCE

def check_converged():

    ''' Checks for convergence; rewrites to 'TASK_CONVERGED = True' in 'TASK_CONVERGENCE' file if true '''
    
    if workflow_is_converged(workflow_path) == True:
        write_workflow_convergence_file(workflow_path, True)
        move_job_to_pass_path(pwd,workflow_path,workflow_name)
     
    else:
        write_workflow_convergence_file(workflow_path, False)

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
      gen_input()
    elif args.converged:
      check_converged()
    else:
      rerun_task()

