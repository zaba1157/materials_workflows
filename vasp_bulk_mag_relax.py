#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:27:40 2019
Creates magnetic structures and vasp input including bulk relax convergence file.
@author: Zach Bare
"""


import os
import argparse
from pymatgen.io.vasp.sets import MPRelaxSet,batch_write_input
from pymatgen.io.vasp.inputs import Poscar
from materials_workflows.magnetism.analyzer import MagneticStructureEnumerator
from shutil import  move
from materials_workflows.vasp_functions import *
from materials_workflows.vasp_convergence.convergence_inputs import bulk_convergence


def gen_input():
  pwd = os.getcwd()
  workflow_name = 'bulk_mag'
  stage_number = get_workflow_stage_number_from_name(workflow_name)
  workflow_path = os.path.join(pwd,workflow_name)
  os.mkdir(workflow_path)
  structure = Poscar.from_file(os.path.join(pwd,'POSCAR')).structure
  move(os.path.join(pwd,'POSCAR'),os.path.join(pwd,'POSCAR.orig'))
  write_workflow_convergence_file(workflow_path, False)
  mag_structures = MagneticStructureEnumerator(structure)
  batch_write_input(mag_structures.ordered_structures, vasp_input_set=MPRelaxSet,
                    output_dir=workflow_path)
  for root, dirs, files in os.walk(workflow_path):
      for file in files:
        if file == 'POSCAR':
          kpoints1 = get_kpoints(os.path.join(root,'POSCAR'), 300)
          kpoints2 = get_kpoints(os.path.join(root,'POSCAR'), 1000)
          natoms = len(Poscar.from_file(os.path.join(root,'POSCAR')).structure)
          convergence_writelines = bulk_convergence(kpoints1,kpoints2,natoms)
          write_vasp_convergence_file(root,convergence_writelines)
  
def check_converged():
  pwd = os.getcwd()
  workflow_name = 'bulk_mag'
  workflow_path = os.path.join(pwd,workflow_name)
  #os.chdir(workflow_path)
  if workflow_is_converged(workflow_path) == True:
    write_workflow_convergence_file(workflow_path, True)
    job_path = get_minimum_energy_job(workflow_path)
    stage_number = get_workflow_stage_number(pwd)
    job_to_pass = os.path.join(pwd,str(stage_number)+'_'+str(workflow_name)+'_final')
    for root, dirs, files in os.walk(job_path):
        for file in files:
          move(os.path.join(root,file),job_to_pass)  
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



  
