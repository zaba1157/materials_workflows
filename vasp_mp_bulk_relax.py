#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import argparse
from pymatgen.io.vasp.inputs import Poscar
from materials_workflows.vasp_functions import write_workflow_convergence_file, workflow_is_converged
from materials_workflows.vasp_functions import get_mpids_from_file, get_structures_from_materials_project
from materials_workflows.vasp_functions import structure_scaler, append_to_incars
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input

################################################

''' Define Global Variables '''

workflow_name = 'bulk'
mpids_filename = 'MPIDS' # name of the file from which MPIDS are read; should be in the same directory 
pwd = os.getcwd()
workflow_path = os.path.join(pwd, workflow_name)
mp_key = '' # user-specified Materials Project API key
tags_to_add = ['NPAR = 2', 'ISYM = 0'] # tags to add to all INCAR files generated
################################################

def generate_input_files(filename, mp_key, to_scale=True):

    if os.path.isdir(workflow_path) == False:
        os.mkdir(workflow_path)

    id_list = get_mpids_from_file(os.path.join(pwd, filename))
    structures = get_structures_from_materials_project(id_list, mp_key)

    if to_scale == True:
        scaled_structures = structure_scaler(structures) # resizes structure to compare with o-vacancy calculations
    else:
        scaled_structures = structures # for just regular bulk relaxations of Materials Project structures

    batch_write_input(scaled_structures, vasp_input_set=MPRelaxSet, output_dir=workflow_path,
                      make_dir_if_not_present=True)
    
    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            if file == 'POTCAR':
                kpoints1 = get_kpoints(os.path.join(root, 'POSCAR'), 300)
                kpoints2 = get_kpoints(os.path.join(root, 'POSCAR'), 1000)
                natoms = len(Poscar.from_file(os.path.join(root, 'POSCAR')).structure)
                convergence_writelines = bulk_convergence(kpoints1, kpoints2, natoms)
                write_vasp_convergence_file(root,convergence_writelines)
    
    append_to_incars(pwd, tags_to_add)
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
        generate_input_files(mpids_filename, mp_key, to_scale=True) # name of the file containing mp-ids and Materials Project API key
    elif args.converged:
        check_converged()
    else:
        rerun_task()
