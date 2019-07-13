#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:27:40 2019

@author: Zach Bare
"""

def surf_convergence(final_kpoints):

  step0 = ['\n0 Very_Rough_Converge\n',
           'PREC = Normal','ENCUT = 520','NSW = 5000',
           'EDIFFG = -0.8','EDIFF = 1e-3','NELMIN = 10',
           'NELM = 80','ALGO = Fast','LORBIT = 11','IOPT = 7',
           'IBRION = 3','POTIM = 0','ISTART = 0','ICHARG = 2',
           'ISMEAR = 0','ISYM = 0','\nKPOINTS 1 1 1']
  step1 = ['\n1 Rough_Converge\n',
           'EDIFF = 1e-5','EDIFFG = -0.1','NELMIN = 4',
           'NELM = 60','ISMEAR = -5','\nKPOINTS '+str(final_kpoints)]
  step2 = ['\n2 Full_Converge\n',
           'EDIFF = 1e-6','ISTART = 1','ICHARG = 1','EDIFFG = -0.03',
           'PREC = Accurate','NELM = 100']
  step3 = ['\n3 One_Step\n','LAECHG = .TRUE.','NSW = 0','NELM = 500']
  
  return step0 + step1 + step2 + step3


