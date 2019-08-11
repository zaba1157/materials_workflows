#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input
from pymatgen.io.vasp.inputs import Poscar
from materials_workflows.magnetism.analyzer import MagneticStructureEnumerator
from materials_workflows.vasp_functions import get_mpids_from_file, get_structures_from_materials_project
from materials_workflows.vasp_functions import get_previous_pass_path, get_structure_from_pass_path, write_workflow_convergence_file
from materials_workflows.vasp_functions import get_kpoints, write_vasp_convergence_file, workflow_is_converged
from materials_workflows.vasp_functions import get_minimum_energy_job, move_job_to_pass_path, append_to_incars
from materials_workflows.vasp_convergence.convergence_inputs import bulk_convergence

################################################
''' Define Global Variables '''

workflow_name = 'bulk_mag'
mpids_filename = 'MPIDS' # name of the file from which MPIDS are read; should be in the same directory AND should all be magnetic
# if not all mp-ids are magnetic, the folder
pwd = os.getcwd()
workflow_path = os.path.join(pwd, workflow_name)
mp_key = '' # user-specified Materials Project API key
max_num_mag_structs = 20 # set the maximum number of magnetic samples
tags_to_add = ['NPAR = 1', 'ISYM = 0']
################################################

def generate_input_files(filename, mp_key):

    if os.path.isdir(workflow_path) == False:
        os.mkdir(workflow_path)

    id_list = get_mpids_from_file(os.path.join(pwd, filename))
    structures = get_structures_from_materials_project(id_list, mp_key)

    for structure in structures:
        try:
            mag_structures_obj = MagneticStructureEnumerator(structure)
            ordered_structures = mag_structures_obj.ordered_structures[:max_num_mag_structs]
        
            compound_parent_directory = str(structure.formula).replace(' ', '')
            compound_path = os.path.join(workflow_path, compound_parent_directory)
            
            if os.path.isdir(compound_path) == False:
                os.mkdir(compound_path)

            batch_write_input(ordered_structures, vasp_input_set=MPRelaxSet, output_dir=compound_path,
                          make_dir_if_not_present=True)
        except:
            print('%s is not magnetic!' % str(structure.formula).replace(' ', ''))
            continue
    
    append_to_incars(pwd, tags_to_add)
    
    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            if file == 'POTCAR':
                kpoints1 = get_kpoints(os.path.join(root, 'POSCAR'), 300)
                kpoints2 = get_kpoints(os.path.join(root, 'POSCAR'), 1000)
                natoms = len(Poscar.from_file(os.path.join(root, 'POSCAR')).structure)
                convergence_writelines = bulk_convergence(kpoints1, kpoints2, natoms)
                write_vasp_convergence_file(root, convergence_writelines)

    write_workflow_convergence_file(workflow_path, False)

    return

def check_converged():

    if workflow_is_converged(workflow_path) == True:
        write_workflow_convergence_file(workflow_path, True)
        minE_job_path = get_minimum_energy_job(workflow_path)
        move_job_to_pass_path(pwd,minE_job_path,workflow_name)

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
          generate_input_files(mpids_filename, mp_key)
      elif args.converged:
          check_converged()
      else:
          rerun_task()
