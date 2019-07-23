#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 14:55:20 2019

@author: rymo1354
"""

import os
import random
from pymatgen.io.vasp.sets import MPRelaxSet, batch_write_input
from pymatgen.ext.matproj import MPRester

material_ids = ['mp-559756', 'mp-31118', 'mp-31117', 'mp-3466', 'mp-7405', 'mp-5899', 'mp-25005', 'mp-773298',
               'mp-18725', 'mp-542920', 'mp-19281', 'mp-754225', 'mp-703673', 'mp-1079111', 'mp-777503', 'mp-19063',
               'mp-600862', 'mp-19381', 'mp-1178351', 'mp-769920', 'mp-19598', 'mp-1189762', 'mp-769818', 'mp-24995',
               'mp-1105822', 'mp-24989', 'mp-1105788', 'mp-24990', 'mp-19269', 'mp-865758', 'mp-13863', 'mp-17761',
               'mp-17464', 'mp-1078295', 'mp-3858', 'mp-4571', 'mp-754853', 'mp-7375', 'mp-3614', 'mp-4019',
               'mp-4190', 'mp-4651', 'mp-5020', 'mp-4387', 'mp-3378', 'mp-2879', 'mp-3187', 'mp-3163', 'mp-998552',
               'mp-3834', 'mp-768505', 'mp-31116', 'mp-2920']

def get_Structures(id_list):

    m = MPRester('JicHL6n3RTB4qVfI')
    structures = []
    for t_id in id_list:
        structure = m.get_structures(t_id, final=True)[0]
        structures.append(structure)

    return structures

def generate_o_vacancies(id_list):

    pwd = os.getcwd()
    workflow_name = 'o_vacancies'
    workflow_path = os.path.join(pwd, workflow_name)

    if os.path.isdir(workflow_path) == False:
        os.mkdir(workflow_path)

    structures = get_Structures(id_list)

    for structure in structures:

        structure.make_supercell([2, 2, 2])
        o_indices = list(structure.indices_from_symbol('O'))
        random_O_index = random.choice(o_indices)
        structure.remove_sites([random_O_index])

        #composition = str(structure.formula)
        #composition_directory_name = composition.replace(' ', '_')
        #composition_path = os.path.join(workflow_path, composition_directory_name)

        batch_write_input([structure], vasp_input_set=MPRelaxSet, output_dir=workflow_path,
                      make_dir_if_not_present=True)

    return

generate_o_vacancies(material_ids)
