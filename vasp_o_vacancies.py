#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 14:55:20 2019

Reads in a list of Materials Project IDs, queries for structures, creates a 2x2x2 supercell, removes a random oxygen from each 
structure, and writes the Vasp input files as those from pymatgen's MPRelaxSet in the directory 'o_vacancies.'

@author: rymo1354
"""

import os
import argparse
import random
from materials_workflows.vasp_functions import write_workflow_convergence_file, workflow_is_converged
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input
from pymatgen.ext.matproj import MPRester

material_ids = ['mp-559756', 'mp-31118', 'mp-31117', 'mp-3466', 'mp-7405', 'mp-5899', 'mp-25005', 'mp-773298',
               'mp-18725', 'mp-542920', 'mp-19281', 'mp-754225', 'mp-703673', 'mp-1079111', 'mp-777503', 'mp-19063',
               'mp-600862', 'mp-19381', 'mp-1178351', 'mp-769920', 'mp-19598', 'mp-1189762', 'mp-769818', 'mp-24995',
               'mp-1105822', 'mp-24989', 'mp-1105788', 'mp-24990', 'mp-19269', 'mp-865758', 'mp-13863', 'mp-17761',
               'mp-17464', 'mp-1078295', 'mp-3858', 'mp-4571', 'mp-754853', 'mp-7375', 'mp-3614', 'mp-4019',
               'mp-4190', 'mp-4651', 'mp-5020', 'mp-4387', 'mp-3378', 'mp-2879', 'mp-3187', 'mp-3163', 'mp-998552',
               'mp-3834', 'mp-768505', 'mp-31116', 'mp-2920']

def get_Structures(id_list):

    m = MPRester('JicHL6n3RTB4qVfI')
    structures = []
    for mp_id in id_list:
        structure = m.get_structures(mp_id, final=True)[0]
        structures.append(structure)

    return structures # list of the queried MP_ID structures

def generate_input_files(id_list):

    pwd = os.getcwd()
    workflow_name = 'o_vacancies' # needs to be the same workflow name as in vasp_o_vacancies.WORKFLOW_COMMANDS
    workflow_path = os.path.join(pwd, workflow_name)

    if os.path.isdir(workflow_path) == False:
        os.mkdir(workflow_path)

    structures = get_Structures(id_list) # gets the list of structures to perform supercell transformation and O removal

    for structure in structures:

        structure.make_supercell([2, 2, 2])
        O_indices = list(structure.indices_from_symbol('O'))
        random_O_index = random.choice(O_indices)
        structure.remove_sites([random_O_index])

        batch_write_input([structure], vasp_input_set=MPRelaxSet, output_dir=workflow_path,
                      make_dir_if_not_present=True) # writes the directories containing Vasp inputs to 'o_vacancies' directory

    dirs = [x[0] for x in os.walk(workflow_path)]
    dirs.remove(workflow_path) # list of directories within 'o_vacancies'

    for directory in dirs:
        for file in os.listdir(directory):
            if file == 'INCAR':

                f = open(directory + '/INCAR', "r+")
                f.write('NPAR = 2\n') # adds the NPAR tag to enable parallelization, not included in MPRelaxSet INCAR tags
                lines = f.readlines()
                with open(directory + '/CONVERGENCE', 'a') as c: 
                    c.write('0 MP_Converge\n\n') # writes CONVERGENCE file to each subdirectory in 'o_vacancies'
                    for line in lines:
                        c.write(line)
                f.close()

    write_workflow_convergence_file(workflow_path, False) # writes the TASK_CONVERGENCE file to 'o_vacancies'

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
        generate_input_files(material_ids)
    elif args.converged:
        check_converged()
    else:
        rerun_task()
