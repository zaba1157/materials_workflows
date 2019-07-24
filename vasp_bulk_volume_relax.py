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

def get_number_of_subs(path):
    backup_path = os.path.join(path,'backup')
    max_num_sub = 0
    for root, dirs, files in os.walk(job_path):
        for di in dirs:
            if di.isdigit():
                if int(di) > max_num_sub:
                    max_num_sub = int(di)
    return max_num_sub

def remove_sys_incar(path):
    filepath = os.path.join(path,'INCAR')
    with open(filepath,'r') as f:
        data = f.readlines()
    for line in range(len(data)):
        if data[line].split()[0] == 'SYSTEM':
            data[line] = '\n'
    with open(filepath,'w') as f:
        f.writelines( data )
        
def volume_workflow_is_converged(pwd,max_num_sub,min_num_vols):
    workflow_converged_list = []
    E,V = [],[]
    minE = 100
    for root, dirs, files in os.walk(pwd):
            for file in files:
                if file == 'POTCAR' and check_vasp_input(root) == True:                  
                    if os.path.exists(os.path.join(root,'vasprun.xml')):
                        try: 
                            Vr = Vasprun(os.path.join(root, 'vasprun.xml'))
                            fizzled = False                                
                        except:
                            fizzled = True
                            workflow_converged_list.append(False)
                            
                        if fizzled == False:    
                            job = is_converged(root)
                            if job == 'converged':
                                workflow_converged_list.append(True)
                                vol = Poscar.from_file(os.path.join(root,'POSCAR')).structure.volume
                                if Vr.final_energy < minE:
                                    minE = Vr.final_energy
                                    minV = vol
                                    minE_path = root
                                    minE_formula = str(Poscar.from_file(os.path.join(path,'POSCAR')).structure.composition.reduced_formula)
                                E.append(Vr.final_energy)
                                V.append(vol)
                                
                        elif fizzled == True and get_incar_value(path, 'STAGE_NUMBER') == 0: #job is failing on initial relaxation
                            num_sub = get_number_of_subs(root)
                            if num_sub == max_num_sub:
                                os.remove(os.path.join(root,'POTCAR'))
                                #job failed too many times.... just ignore this job for the remainder of the workflow
                    else:
                        workflow_converged_list.append(False)

    num_jobs = check_num_jobs_in_workflow(pwd)
    if num_jobs < min_num_vols and len(E) > 0:
        scale_around_min = [0.98,1.02]   
        for s in scale_around_min:
            write_path = os.path.join(pwd,minE_formula+str(s*minV))
            os.mkdir(write_path)
            structure = Poscar.from_file(os.path.join(minE_path,'POSCAR')).structure
            structure.scale_lattice(s*minV)
            Poscar.write_file(structure,os.path.join(write_path,'POSCAR'))
            files_copy = ['INCAR','CONVERGENCE','KPOINTS','POTCAR']
            for fc in files_copy:
                copy_from_path = os.path.join(minE_path,fc)
                if os.path.exists(copy_from_path):
                    copy(copy_from_path,write_path)
            remove_sys_incar(write_path)
                    
            
            
        
            
        
        #create new jobs
    if False not in workflow_converged_list:
        return True
    else:
        return False

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
      scaled_structures.append(structure.scale_lattice(sf*init_volume))
  
  batch_write_input(scaled_structures, vasp_input_set=MPRelaxSet,
                    output_dir=workflow_path)
  for root, dirs, files in os.walk(workflow_path):
      for file in files:
        if file == 'POSCAR':
          kpoints1 = get_kpoints(os.path.join(root,'POSCAR'), 300)
          kpoints2 = get_kpoints(os.path.join(root,'POSCAR'), 1000)
          convergence_writelines = bulk_convergence(kpoints1,kpoints2)
          write_vasp_convergence_file(root,convergence_writelines)
  
def check_converged():
  pwd = os.getcwd()
  min_num_converged_vols = 4
  max_num_submission_failures = 2
  
  if workflow_is_converged(pwd) == True:
    write_workflow_convergence_file(pwd, True)
    job_path = get_minimum_energy_job(pwd)
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
from pymatgen.io.vasp.inputs import Poscar
import os


pwd = os.getcwd()
file1 = os.path.join(pwd,'CONTCAR')
file2 = os.path.join(pwd,'backup/Init/POSCAR')

print('V_final = '+str(Poscar.from_file(file1).structure.volume))
print('V_init = '+str(Poscar.from_file(file2).structure.volume))
