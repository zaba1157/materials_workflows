#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 12:02:08 2019

@author: zaba1157
"""


import os
import argparse
from pymatgen.io.vasp.sets import MPRelaxSet,batch_write_input
from pymatgen.io.vasp.inputs import Poscar
from materials_workflows.magnetism.analyzer import MagneticStructureEnumerator
from shutil import  move, copy
from materials_workflows.vasp_functions import *
from materials_workflows.vasp_convergence.convergence_inputs import volume_bulk_convergence


def gen_input():
  pwd = os.getcwd()
  workflow_name = 'vol_rlx'
  workflow_path = os.path.join(pwd,workflow_name)
  os.mkdir(workflow_path)
  structure = Poscar.from_file(os.path.join(pwd,'POSCAR')).structure
  move(os.path.join(pwd,'POSCAR'),os.path.join(pwd,'POSCAR.orig'))
  write_workflow_convergence_file(workflow_path, False)
  inital_scale_factors = [0.8,1.0,1.2,1.4,1.6] 
  init_volume = structure.volume
  scaled_structures = []
  for sf in inital_scale_factors:
      structure.scale_lattice(sf*init_volume)
      scaled_structures.append(structure)
  
  batch_write_input(scaled_structures, vasp_input_set=MPRelaxSet,
                    output_dir=workflow_path)
  for root, dirs, files in os.walk(workflow_path):
      for file in files:
        if file == 'POSCAR':
          kpoints1 = get_kpoints(os.path.join(root,'POSCAR'), 300)
          kpoints2 = get_kpoints(os.path.join(root,'POSCAR'), 1000)
          convergence_writelines = volume_bulk_convergence(kpoints1,kpoints2)
          write_vasp_convergence_file(root,convergence_writelines)
  
def check_converged():
  min_num_converged_vols = 4
  max_num_submission_failures = 2
  vol_tolerance = 1 #ang^3
  pwd = os.getcwd()

  
  if volume_workflow_is_converged(pwd,max_num_submission_failures,min_num_converged_vols,vol_tolerance) == True:
    write_workflow_convergence_file(pwd, True)
    job_path = get_minimum_energy_job(pwd)
    copy(os.path.join(job_path,'CONTCAR'),os.path.join(pwd,'POSCAR')) #copy POSCAR for next workflow task
    stage_number = get_workflow_stage_number(pwd)
    job_to_pass = os.path.join(pwd,str(stage_number)+'_final')
    for root, dirs, files in os.walk(job_path):
        for file in files:
          move(os.path.join(root,file),job_to_pass)  
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
      gen_input()
    elif args.converged:
      check_converged()
    else:
      rerun_task()

