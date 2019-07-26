#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:27:40 2019
@author: Zach Bare
"""

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
        
    step0 = ['\n0 Very_Rough_Converge\n', npar,kpar,auto_nodes
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
