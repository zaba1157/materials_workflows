#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 18:05:24 2019

@author: Zach Bare
"""
# makes the scripts listed executable

import os

scripts = [script for script in os.listdir('.') if os.path.isfile(script)] # list of all files in present directory, including setup.py

if str(os.environ["VASP_COMPUTER"]) == 'summit':
    scripts.append('vasp.py')
    
for s in scripts:
    os.system('chmod 755 '+s)
