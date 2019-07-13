#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:27:40 2019
Creates magnetic structures and vasp input including bulk relax convergence file.
@author: Zach Bare
"""


import os
from pymatgen.io.vasp.sets import MPRelaxSet,batch_write_input
from pymatgen.io.vasp.inputs import Poscar
from materials-workflows.magnetism.analyzer import MagneticStructureEnumerator
from shutil import copyfile, move
from materials-workflows.vasp_functions import *
from materials-workflows.convergence_inputs import bulk_convergence

def gen_input():
  pwd = os.getcwd()
  structure = Poscar.from_file(os.path.join(pwd,'POSCAR'))
  mag_structures = MagneticStructureEnumerator(structure)
  batch_write_input(mag_structures.ordered_structures, vasp_input_set=MPRelaxSet,
                    output_dir=os.path.join(pwd,'vasp_bulk_mag_relax'))
  for root, dirs, files in os.walk(os.path.join(pwd,'vasp_bulk_mag_relax')):
      for file in files:
          if file == 'KPOINTS':
              with open('KPOINTS','r') as k:
                  linecount = 0
                  for line in k:
                      if linecount == 3:
                          kpts_line = line
                          break
                      linecount+=1
              k.close()
              convergence_writelines = bulk_convergence(str(kpts_line))
              write_vasp_convergence_file(root,convergence_writelines)
  
def check_converged():
  pwd = os.getcwd()
  if workflow_converged(pwd) == True:
    write_workflow_convergence_file(pwd, True)
    job_path = get_minimum_energy_job(pwd)
    stage_number = get_workflow_stage_number(pwd)
    job_to_pass = os.path.join(pwd,str(stage_number)+'_final')
    for root, dirs, files in os.walk(job_path):
        for file in files:
          move(os.path.join(root,file),job_to_pass)  
  else:
    write_workflow_convergence_file(pwd, False)
  
