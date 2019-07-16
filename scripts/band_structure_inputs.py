# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 14:43:58 2019

''' Script to generate POSCAR and KPOINTS files for density of states and band structure calculations following bulk relaxation '''
''' Requires INCAR, POTCAR and CONTCAR files in the same working directory as band_structure.py '''
''' Reads INCAR, POTCAR from current working directory '''
''' Copies the CONTCAR file as the POSCAR file from current working directory '''
''' Generates a KPOINTS files specifying symmetry paths to sample using the primitive cell structure of CONTCAR '''

@author: rymo1354
"""

import os

from pymatgen.io.vasp.inputs import Kpoints 
from pymatgen.io.vasp.inputs import PotcarSingle 
from pymatgen.io.vasp.inputs import Poscar 
from pymatgen.io.vasp.inputs import Incar 

from pymatgen.core.structure import Structure
from pymatgen.symmetry.bandstructure import HighSymmKpath
from vasp_workflow.materials_workflows.vasp_convergence.convergence_inputs import band_structure_calculation

class BandStructureFiles():
    
    def __init__(self):
        
        self.cwd = os.getcwd()
        self.tags = self.Incar_tags()
        
        self.potcar = self.get_Potcar()
        self.poscar = self.get_Poscar()
        self.old_incar, self.new_incar = self.get_Incar()
        self.kpoints = self.get_path_dependent_Kpoints()
        
        return 
    
    def get_Potcar(self):
        
        ''' Reads the file titled POTCAR from the present working directory '''
        ''' Generates and returns pymatgen.io.vasp.inputs.PotcarSingle object from POTCAR '''
        
        potcar = PotcarSingle.from_file(self.cwd + '\POTCAR')
        
        return potcar
    
    def get_Poscar(self):
        
        ''' Reads the file titled CONTCAR from the present working directory '''
        ''' Generates and returns pymatgen.io.vasp.inputs.Poscar object from CONTCAR '''
        
        poscar = Poscar.from_file(self.cwd + '\CONTCAR')
        
        return poscar
    
    def Incar_tags(self):
    
        ''' Imports the band structure tags as list of strings from convergence_inputs.band_structure_calculation '''
        ''' Assumes first position in the list is not a VASP tag, converts list to bs_tags (list of tuples) '''
        ''' Tags in the set that aren't included in the old_incar object are added to the new_incar object in get_Incar '''
        ''' Tags in the old_incar object that aren't in the set are unchanged in the new_incar object in get_Incar '''
        
        bs_params = band_structure_calculation()
        bs_tags = []

        for i in range(1, len(bs_params)):
            tag = bs_params[i].split(' = ')
            bs_tags.append(tuple(tag))
             
        return bs_tags
    
    def get_Incar(self):
        
        ''' Reads the file titled INCAR from the current working directory '''
        ''' Updates the old_incar object to the new_incar object using self.tags '''
        ''' Returns both the old_incar and new_incar objects (pymatgen.io.vasp.inputs.Incar) '''
        
        old_incar = Incar.from_file(self.cwd + '\INCAR')
        new_incar = Incar.from_file(self.cwd + '\INCAR')
        new_incar.update(self.tags)
        
        return old_incar, new_incar
    
    def get_path_dependent_Kpoints(self, divisions = 10):
        
        ''' Gets the primitive unit cell from the CONTCAR file as primitive_structure '''
        ''' Gets the high symmetry k path of the primitive unit cell as k_path '''
        ''' Returns the pymatgen.io.vasp.inputs.Kpoints object, with symmetric k points specified '''
        ''' NOTE: divisions is the number of points sampled along each path between k points, default = 10'''
        
        primitive_structure = Structure.from_file(self.cwd + '\CONTCAR', primitive=True)
        k_path = HighSymmKpath(primitive_structure)
        kpoints = Kpoints.automatic_linemode(divisions, k_path)
        
        return kpoints
