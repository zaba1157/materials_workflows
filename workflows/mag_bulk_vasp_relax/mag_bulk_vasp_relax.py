#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:27:40 2019

Creates magnetic structures and vasp input including bulk relax convergence file.

@author: Zach Bare
"""


import os
from pymatgen.io.vasp.sets import MPRelaxSet,batch_write_input
from pymatgen.io.vasp.inputs import Poscar
from analyzer import MagneticStructureEnumerator
from shutil import copyfile



pwd = os.getcwd()
structure = Poscar.from_file(os.path.join(pwd,'POSCAR'))
mag_structures = MagneticStructureEnumerator(structure)
batch_write_input(mag_structures.ordered_structures, vasp_input_set=MPRelaxSet,
                  output_dir=os.path.join(pwd,'mag_bulk_vasp_relax'))

for root, dirs, files in os.walk(pwd):
    for file in files:
        if file == 'POTCAR':
            copyfile('CONVERGENCE',os.path.join(pwd,'CONVERGENCE'))
            
