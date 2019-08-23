#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 12:02:08 2019
@author: zaba1157
"""


import os
import argparse
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input
from pymatgen.io.vasp.inputs import Poscar
from materials_workflows.magnetism.analyzer import MagneticStructureEnumerator
from shutil import  move, copy
from pymatgen.core.structure import Structure
from materials_workflows.magnetism.analyzer import MagneticStructureEnumerator
from materials_workflows.vasp_functions import get_previous_pass_path, get_structure_from_pass_path, write_workflow_convergence_file
from materials_workflows.vasp_functions import get_kpoints, write_vasp_convergence_file, workflow_is_converged
from materials_workflows.vasp_functions import get_minimum_energy_job, move_job_to_pass_path, append_to_incars
from materials_workflows.vasp_functions import get_paths_from_file, get_structures_from_paths
from materials_workflows.vasp_convergence.convergence_inputs import volume_bulk_convergence

from scripts.substituted_structures_from_SQS import get_Structures
################################################

''' Define Global Variables '''

workflow_name = 'vol_rlx'
initial_scale_factors = [0.8, 1.0, 1.2, 1.4, 1.6]
paths_filename = 'PATHS'
pwd = os.getcwd()
workflow_path = os.path.join(pwd, workflow_name)
tags_to_add = ['NPAR = 1', 'ISYM = 0']
elements_to_ignore = ['O']
################################################


def gen_input(scale_factors):

    os.mkdir(workflow_path)
    
    start_path = get_previous_pass_path(pwd, workflow_name)
    structure = get_structure_from_pass_path(start_path)
    write_workflow_convergence_file(workflow_path, False)

    init_volume = structure.volume
    scaled_structures = []
    for sf in scale_factors:
        structure.scale_lattice(sf*init_volume)
        scaled_structures.append(structure)

    batch_write_input(scaled_structures, vasp_input_set=MPRelaxSet,
                      output_dir=workflow_path)

    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            if file == 'POTCAR':
                kpoints1 = get_kpoints(os.path.join(root, 'POSCAR'), 300)
                kpoints2 = get_kpoints(os.path.join(root, 'POSCAR'), 1000)
                convergence_writelines = volume_bulk_convergence(kpoints1, kpoints2)
                write_vasp_convergence_file(root, convergence_writelines)

    return

def read_input_files(filename, scale_factors):

    if os.path.isdir(workflow_path) == False:
        os.mkdir(workflow_path)

    paths_list = get_paths_from_file(os.path.join(pwd, filename))
    base_structures = []
    sub_structures = []

    for path in paths_list:
        base = Poscar.from_file(path).structure
        structures = get_Structures(path, elements_to_ignore)

        if structures != None:
            sub_structures.append(structures)
            base_structures.append(base)
        else:
            print('No structures to append')
            continue

    for base_ind in range(len(base_structures)):
        compound_parent_directory = str(base_structures[base_ind].formula).replace(' ', '')
        compound_path = os.path.join(workflow_path, compound_parent_directory)

        os.mkdir(compound_path)

        for structure in sub_structures[base_ind]:
            structure_directory = str(structure.formula).replace(' ', '')
            structure_path = os.path.join(compound_path, structure_directory)

            scaled_structures = []

            for sf in scale_factors:
                copy = structure.copy()
                init_volume = copy.volume
                copy.scale_lattice(sf*init_volume)
                scaled_structures.append(copy)

            batch_write_input(scaled_structures, vasp_input_set=MPRelaxSet, output_dir=structure_path,
                              make_dir_if_not_present=True)

    append_to_incars(pwd, tags_to_add)

    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            if file == 'POTCAR':
                kpoints1 = get_kpoints(os.path.join(root, 'POSCAR'), 300)
                kpoints2 = get_kpoints(os.path.join(root, 'POSCAR'), 1000)
                natoms = len(Poscar.from_file(os.path.join(root, 'POSCAR')).structure)
                convergence_writelines = volume_bulk_convergence(kpoints1, kpoints2)
                write_vasp_convergence_file(root, convergence_writelines)

    write_workflow_convergence_file(workflow_path, False)

    return

def check_converged():
    min_num_converged_vols = 4
    max_num_submission_failures = 2
    vol_tolerance = 1 #ang^3

    if volume_workflow_is_converged(pwd, max_num_submission_failures, min_num_converged_vols, vol_tolerance) == True:
        write_workflow_convergence_file(workflow_path, True)
        minE_job_path = get_minimum_energy_job(workflow_path)
        move_job_to_pass_path(pwd, minE_job_path, workflow_name)
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
    parser.add_argument('-d', '--read_inputs', help='Reads inputs for workflow.',
                        action='store_true')
    parser.add_argument('-r', '--rerun', help='Reruns worklow. This does nothing if vasp workflow.',
                        action='store_true')
    args = parser.parse_args()

    if args.gen_inputs:
        gen_input(initial_scale_factors)
    elif args.read_inputs:
        read_input_files(paths_filename, initial_scale_factors)
    elif args.converged:
        check_converged()
    else:
        rerun_task()


