#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 18:05:24 2019

@author: Zach Bare
"""

import os
from pathlib import Path

scripts = [script for script in os.listdir('.') if os.path.isfile(script) and Path(script).suffix == '.py']

for s in scripts:
    os.system('chmod 755 '+s)

# makes all python scripts (including setup.py) in the present working directory executable
# run with command line command python3 setup.py, if scripts turn green in terminal it was performed correctly
