#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 18:05:24 2019

@author: Zach Bare
"""
# makes the scripts listed executable

import os

scripts = ['vasp_bulk_mag_relax.py', 'vasp_band_structure.py',
           'workflow_rerun.py','vasp_bulk_volume_relax.py','FM_bulk_relax.py']

if str(os.environ["VASP_COMPUTER"]) == 'summit':
    scripts.append('vasp.py')
    
for s in scripts:
    os.system('chmod 755 '+s)
