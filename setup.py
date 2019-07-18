#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 18:05:24 2019

@author: zach1
"""

import os

scripts = ['vasp.py','vasp_bulk_mag_relax.py', 'vasp_band_structure.py', 'workflow_rerun.py']

for s in scripts:
    os.system('chmod 755 '+s)
