#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 22:25:09 2019

@author: zach1
"""


import os
import argparse
from pymatgen.io.vasp.inputs import Poscar
from materials_workflows.vasp_functions import write_workflow_convergence_file, workflow_is_converged
from materials_workflows.vasp_functions import structure_scaler
from materials_workflows.vasp_functions import get_structures_with_element_removed, get_kpoints
from materials_workflows.vasp_convergence.convergence_inputs import bulk_convergence
from materials_workflows.vasp_functions import write_vasp_convergence_file
from materials_workflows.vasp_functions import get_minimum_energy_job, move_job_to_pass_path
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input
from materials_workflows.vasp_functions import get_previous_pass_path, get_structure_from_pass_path

################################################

''' Define Global Variables '''

workflow_name = 'o_vacancies'
pwd = os.getcwd()
workflow_path = os.path.join(pwd, workflow_name)
start_path = get_previous_pass_path(pwd,workflow_name)
################################################

def gen_input():
  
  os.mkdir(workflow_path)
  structure = get_structure_from_pass_path(start_path) 
  write_workflow_convergence_file(workflow_path, False)
  scaled_structure = structure_scaler([structure]) # resizes structure to compare with o-vacancy calculations
  structure_list, compound_path = get_structures_with_element_removed(workflow_path, 'O', scaled_structure)
  
  batch_write_input(structure_list, vasp_input_set=MPRelaxSet,
                    output_dir=compound_path,make_dir_if_not_present=True)
  
  for root, dirs, files in os.walk(workflow_path):
      for file in files:
        if file == 'POTCAR':
          kpoints1 = get_kpoints(os.path.join(root,'POSCAR'), 300)
          kpoints2 = get_kpoints(os.path.join(root,'POSCAR'), 1000)
          natoms = len(Poscar.from_file(os.path.join(root,'POSCAR')).structure)
          convergence_writelines = bulk_convergence(kpoints1,kpoints2,natoms)
          write_vasp_convergence_file(root,convergence_writelines)

def check_converged():

    pwd = os.getcwd()
    if workflow_is_converged(pwd) == True:
        write_workflow_convergence_file(pwd, True)
        minE_job_path = get_minimum_energy_job(workflow_path)
        move_job_to_pass_path(pwd,minE_job_path,workflow_name)
    else:
        write_workflow_convergence_file(pwd, False)

def rerun_task():
    #only needed for non-VASP calculations
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--gen_input', help='Generates inputs for workflow.',
                        action='store_true')
    parser.add_argument('-c', '--converged', help='Checks for convergence of workflow.',
                        action='store_true')
    parser.add_argument('-r', '--rerun', help='Reruns worklow. This does nothing if vasp workflow.',
                        action='store_true')
    args = parser.parse_args()

    if args.gen_input:
        gen_input() # name of the file containing mp-ids and Materials Project API key
    elif args.converged:
        check_converged()
    else:
        rerun_task()
