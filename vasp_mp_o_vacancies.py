#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import argparse
from pymatgen.io.vasp.inputs import Poscar
from materials_workflows.vasp_functions import write_workflow_convergence_file, workflow_is_converged
from materials_workflows.vasp_functions import get_mpids_from_file, get_structures_from_materials_project
from materials_workflows.vasp_functions import structure_scaler, append_to_incars, get_kpoints
from materials_workflows.vasp_functions import get_structures_with_element_removed
from materials_workflows.vasp_functions import get_paths_from_file, get_structures_from_paths
from materials_workflows.vasp_convergence.convergence_inputs import bulk_convergence
from materials_workflows.vasp_functions import write_vasp_convergence_file
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input

################################################

''' Define Global Variables '''

workflow_name = 'o_vacancies'
mpids_filename = 'MPIDS' # name of the file from which MPIDS are read; should be in the same directory
paths_filename = 'PATHS'
pwd = os.getcwd()
workflow_path = os.path.join(pwd, workflow_name)
mp_key = '' # user-specified Materials Project API key
tags_to_add = ['NPAR = 1', 'ISYM = 0'] # tags to add to all INCAR files generated
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

    for structure in scaled_structures:
        structure_list, compound_path = get_structures_with_element_removed(workflow_path, 'O', structure)
        batch_write_input(structure_list, vasp_input_set=MPRelaxSet, output_dir=compound_path,
                          make_dir_if_not_present=True)

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

def read_input_files(filename, to_scale=True):

    if os.path.isdir(workflow_path) == False:
        os.mkdir(workflow_path)

    paths_list = get_paths_from_file(os.path.join(pwd, filename))
    structures = get_structures_from_paths(paths_list)

    if to_scale == True:
        scaled_structures = structure_scaler(structures) # resizes structure to compare with o-vacancy calculations
    else:
        scaled_structures = structures # for just regular bulk relaxations of Materials Project structures
    
    for structure in scaled_structures:
        structure_list, compound_path = get_structures_with_element_removed(workflow_path, 'O', structure)
        batch_write_input(structure_list, vasp_input_set=MPRelaxSet, output_dir=compound_path,
                          make_dir_if_not_present=True)
    
    append_to_incars(pwd, tags_to_add)

    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            if file == 'POTCAR':
                kpoints1 = get_kpoints(os.path.join(root, 'POSCAR'), 300)
                kpoints2 = get_kpoints(os.path.join(root, 'POSCAR'), 1000)
                natoms = len(Poscar.from_file(os.path.join(root, 'POSCAR')).structure)
                convergence_writelines = bulk_convergence(kpoints1, kpoints2, natoms)
                write_vasp_convergence_file(root,convergence_writelines)

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
    parser.add_argument('-d', '--read_inputs', help='Reads inputs for workflow.',
                        action='store_true')
    parser.add_argument('-c', '--converged', help='Checks for convergence of workflow.',
                        action='store_true')
    parser.add_argument('-r', '--rerun', help='Reruns worklow. This does nothing if vasp workflow.',
                        action='store_true')
    args = parser.parse_args()

    if args.gen_inputs:
        generate_input_files(mpids_filename, mp_key, to_scale=True) # name of the file containing mp-ids and Materials Project API key
    elif args.read_inputs:
        read_input_files(paths_filename, to_scale=True)
    elif args.converged:
        check_converged()
    else:
        rerun_task()
