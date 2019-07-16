# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 13:00:54 2019

''' Script to generate and monitor the progress of a band structure calculation '''
''' This script necessitates that INCAR, POTCAR, CONTCAR and vasprun.xml files are in the directory specified by files_path '''
''' This means that a previous VASP relaxation run is required before the band structure can be calculated '''
''' Path-dependent KPOINTS file is generated from the read-in CONTCAR file '''
''' KPOINTS parameters can be adjusted in the band_structure_inputs script, INCAR parameters in the convergence_inputs script '''

@author: rymo1354
"""

import os
import argparse
from shutil import copy, move

from materials_workflows.scripts.band_structure_inputs import BandStructureFiles
from materials_workflows.vasp_convergence.convergence_inputs import band_structure_calculation
from materials_workflows.vasp_functions import write_workflow_convergence_file, write_vasp_convergence_file
from materials_workflows.vasp_functions import workflow_is_converged

def generate_input_files():
    
    ''' Generates 'band_structure' folder in the present working directory if 'band_structure' folder doesn't exist '''
    ''' Copies 'vasprun.xml' file from the files_path directory to 'band_structure'; writes input files from BandStructureFiles() '''
    ''' Writes "TASK_CONVERGENCE" to pwd and "CONVERGENCE" file to 'band_structure' directory inside pwd '''
    
    pwd = os.getcwd() 
    workflow_name = 'band_structure'
    workflow_path = os.path.join(pwd, workflow_name)
    if os.path.isdir(workflow_path) == False: 
        os.mkdir(workflow_path) 
    
    files_path = pwd + '/bulk_mag' + '/0_final'  
    copy(files_path + '/vasprun.xml', workflow_path) 
    
    files = BandStructureFiles(files_path)
    files.kpoints.write_file(workflow_path + '/KPOINTS') 
    files.new_incar.write_file(workflow_path + '/INCAR')
    files.poscar.write_file(workflow_path + '/POSCAR')
    files.potcar.write_file(workflow_path + '/POTCAR')
    
    write_workflow_convergence_file(pwd, False) 
    convergence_writelines = band_structure_calculation() 
    write_vasp_convergence_file(workflow_path, convergence_writelines) 
    
    return

def check_converged():
    
    ''' Checks for convergence; rewrites to 'TASK_CONVERGED = True' in 'TASK_CONVERGENCE' file if true '''
    
    pwd = os.getcwd()

    if workflow_is_converged(pwd) == True:
        write_workflow_convergence_file(pwd, True)    
    else:
        write_workflow_convergence_file(pwd, False)
            
    return

def rerun_task():
    ''' Only needed for non-VASP calculations '''
    
    pass

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-i', '--gen_inputs', help='Generates inputs for workflow.',
                        action='store_true')
    parser.add_argument('-c', '--converged', help='Checks for convergence of workflow.',
                        action='store_true')
    parser.add_argument('-r', '--rerun', help='Reruns workflow. This does nothing if vasp workflow.',
                        action='store_true')
    args = parser.parse_args()
    
    if args.gen_inputs:
        generate_input_files()
    
    elif args.converged:
        check_converged()
    
    else:
        rerun_task()
