#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:27:40 2019
@author: Zach Bare
"""

def Sam_scan_convergence(inital_kpoints, final_kpoints, natoms, tags_to_remove):
    '''
    This function writes the CONVERGENCE file. This will overwrite any INCAR tags specified here.
    
    Returns: a list of commands to be printed to the CONVERGENCE file. A \n is added automatically 
    for each value (string) in the list .
    
    '''
    remove_tags_string = str(' '.join([t for t in tags_to_remove])) #string of INCAR tags to remove
   
    if natoms < 12:
        npar = 'NPAR = 3'
        kpar = 'KPAR = 4'
        auto_nodes = 'AUTO_NODES = 1'
    elif natoms > 100:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 2'
    else:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 1' 
        
    step0 = ['\n0 Rough_Converge\n', npar,kpar,auto_nodes,
             'LDAU = .FALSE.', 'METAGGA = SCAN',
             'LASPH = .TRUE.', 'ADDGRID = .TRUE.',
             'EDIFFG = -0.05', 'EDIFF = 1E-4','NSW = 500','ISTART = 0', 'LORBIT = 11',
             'ISYM = 2', 'ALGO = Fast', 'PREC = Normal', 'ISMEAR = 0',
             'SIGMA = 0.02', 'IOPT = 7', 'POTIM = 0', 'IBRION = 3',
             'ISIF = 3', 'ISPIN = 2'
             '\nKPOINTS '+str(inital_kpoints),
             '\nREMOVE '+ remove_tags_string]
    
    step1 = ['\n1 Converge\n',
             'EDIFFG = -0.02', 'ISYM = 0','NELMIN = 4','NELM = 60',
             'PREC = Accurate',
             '\nKPOINTS '+str(final_kpoints)]
      
    step2 = ['\n2 One_Step\n',
             'LAECHG = .TRUE.','NSW = 0','NELM = 500','ICHARG = 0','ISTART = 1',
             'LWAVE = False', 'LVHAR = True', 'ALGO = Normal','NELMIN = 10']
      
    return step0 + step1 + step2





def MP_bulk_convergence(natoms):

    if natoms < 12:
        npar = 'NPAR = 3'
        kpar = 'KPAR = 4'
        auto_nodes = 'AUTO_NODES = 1'
    elif natoms > 100:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 2'
    else:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 1'

    step0 = ['\n0 Init\n', npar,kpar,auto_nodes]

    step1 = ['\n1 Run2\n']

    return step0 + step1





def surf_convergence(inital_kpoints, final_kpoints):

    step0 = ['\n0 Very_Rough_Converge\n',
             'PREC = Normal','ENCUT = 520','NSW = 5000',
             'EDIFFG = -0.8','EDIFF = 1e-3','NELMIN = 10',
             'NELM = 80','ALGO = Fast','LORBIT = 11','IOPT = 7',
             'IBRION = 3','POTIM = 0','ISTART = 0','ICHARG = 2',
             'ISMEAR = 0','ISYM = 0','\nKPOINTS '+str(inital_kpoints)]
    step1 = ['\n1 Rough_Converge\n',
             'EDIFF = 1e-5','EDIFFG = -0.1','NELMIN = 4',
             'NELM = 60','ISMEAR = -5','\nKPOINTS '+str(final_kpoints)]
    step2 = ['\n2 Full_Converge\n',
             'EDIFF = 1e-6','ISTART = 1','ICHARG = 1','EDIFFG = -0.03',
             'PREC = Accurate','NELM = 100']
    step3 = ['\n3 One_Step\n','LAECHG = .TRUE.','NSW = 0','NELM = 500']
  
    return step0 + step1 + step2 + step3


def bulk_convergence(inital_kpoints, final_kpoints, natoms):
    
    if natoms < 12:
        npar = 'NPAR = 3'
        kpar = 'KPAR = 4'
        auto_nodes = 'AUTO_NODES = 1'
    elif natoms > 100:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 2'
    else:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 1'  
        
    step0 = ['\n0 Very_Rough_Converge\n', npar,kpar,auto_nodes,
             'EDIFFG = -0.1', 'NSW = 500','ISTART = 0', 'LORBIT = 11',
             'ISYM = 2', 'ALGO = Fast', 'PREC = Normal', 'ISMEAR = 0',
             'SIGMA = 0.05', 'IOPT = 7', 'POTIM = 0', 'IBRION = 3',
             'ISIF = 3','\nKPOINTS '+str(inital_kpoints)]
    
    step1 = ['\n1 Rough_Converge\n',
             'EDIFFG = -0.05', 'ISYM = 0','NELMIN = 4','NELM = 60',
             'PREC = Accurate',
             '\nKPOINTS '+str(final_kpoints)]
      
    step2 = ['\n2 One_Step\n',
             'LAECHG = .TRUE.','NSW = 0','NELM = 500','ICHARG = 0','ISTART = 1',
             'LWAVE = False', 'LVHAR = True', 'ALGO = Normal','NELMIN = 10']
    
    return step0 + step1 + step2

def old_1bulk_convergence(inital_kpoints, final_kpoints, natoms):
    
    if natoms < 12:
        npar = 'NPAR = 3'
        kpar = 'KPAR = 4'
        auto_nodes = 'AUTO_NODES = 1'
    elif natoms > 100:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 2'
    else:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 1'  
        
    step0 = ['\n0 Very_Rough_Converge\n', npar,kpar,auto_nodes,
             'EDIFFG = -0.1', 'NSW = 500','ISTART = 0', 'LORBIT = 11',
             'ISYM = 2', 'ALGO = Fast', 'PREC = Normal', 'ISMEAR = 0',
             'SIGMA = 0.05', 'IOPT = 7', 'POTIM = 0', 'IBRION = 3',
             'ISIF = 3','\nKPOINTS '+str(inital_kpoints)]
    
    step1 = ['\n1 Rough_Converge\n',
             'EDIFFG = -0.05', 'ISYM = 0','NELMIN = 4','NELM = 60',
             '\nKPOINTS '+str(final_kpoints)]
    
    step2 = ['\n2 Nonmag_Single\n',
             'NSW = 0','ISPIN = 1','NELM = 250']
    
    step3 = ['\n3 Full_Converge\n',
             'NSW = 500', 'ICHARG = 1', 'ISTART = 1', 'PREC = Accurate',
             'EDIFFG = -1e-2', 'EDIFF = 1e-6','NELM = 100', 'ISPIN = 2']
    
    step4 = ['\n4 One_Step\n',
             'LAECHG = .TRUE.','NSW = 0','NELM = 500','ICHARG = 0',
             'LWAVE = False', 'LVHAR = True', 'ALGO = Normal','NELMIN = 10']
    
    return step0 + step1 + step2 + step3 + step4


def old_bulk_convergence(inital_kpoints, final_kpoints, natoms):
    if natoms < 12:
        npar = 'NPAR = 3'
        kpar = 'KPAR = 4'
        auto_nodes = 'AUTO_NODES = 1'
    elif natoms > 100:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 2'
    else:
        npar = ' '
        kpar = ' '
        auto_nodes = 'AUTO_NODES = 1'  
        
    step0 = ['\n0 Very_Rough_Converge\n', npar,kpar,auto_nodes,
           'PREC = Normal','ENCUT = 520','NSW = 5000',
           'EDIFFG = 0.1','EDIFF = 1e-3','NELMIN = 10',
           'NELM = 80','ALGO = Fast','LAECHG = .FALSE.','SIGMA = 0.05',
           'IBRION = 2','ISIF = 3','ISTART = 0','ICHARG = 2',
           'ISMEAR = 0','ISYM = 0','\nKPOINTS '+str(inital_kpoints)]
    step1 = ['\n1 Rough_Converge\n',
             'EDIFF = 1e-5','EDIFFG = 1E-2','NELMIN = 4',
             'NELM = 60','ISMEAR = -5','\nKPOINTS '+str(final_kpoints)]
    step2 = ['\n2 Full_Converge\n',
             'EDIFF = 1e-6','ISTART = 1','ICHARG = 1','EDIFFG = 1E-4',
             'PREC = Accurate','NELM = 100']
    step3 = ['\n3 One_Step\n','LAECHG = .TRUE.','NSW = 0','NELM = 500','LORBIT = 11']
    
    return step0 + step1 + step2 + step3

def volume_bulk_convergence(inital_kpoints, final_kpoints):
  
    step0 = ['\n0 Very_Rough_Converge\n', 'NPAR = 1',
           'PREC = Normal','ENCUT = 520','NSW = 5000',
           'EDIFFG = 0.1','EDIFF = 1e-3','NELMIN = 10',
           'NELM = 80','ALGO = Fast','LAECHG = .FALSE.','SIGMA = 0.05',
           'IBRION = 2','ISIF = 4','ISTART = 0','ICHARG = 2',
           'ISMEAR = 0','ISYM = 0','\nKPOINTS '+str(inital_kpoints)]
    step1 = ['\n1 Rough_Converge\n',
             'EDIFF = 1e-5','EDIFFG = 1E-2','NELMIN = 4',
             'NELM = 60','ISMEAR = -5','\nKPOINTS '+str(final_kpoints)]
    step2 = ['\n2 Full_Converge\n',
             'EDIFF = 1e-6','ISTART = 1','ICHARG = 1','EDIFFG = 1E-4',
             'PREC = Accurate','NELM = 100']
    step3 = ['\n3 One_Step\n','LAECHG = .TRUE.','NSW = 0','NELM = 500','LORBIT = 11']
    
    return step0 + step1 + step2 + step3

def band_structure_calculation():
    
    step0 = ['\n0 Band_Structure_Calculation\n', 'EDIFF = 0.0001', 'ENCUT = 520',
             'IBRION = 2', 'ICHARG = 11', 'ISIF = 3', 'ISMEAR = 0', 'LWAVE = True',
             'NELM = 1000', 'NPAR = 1', 'NSW = 0','PREC = Accurate', 'SIGMA = 0.05']
    
    return step0

