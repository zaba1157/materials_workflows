#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 20:25:03 2019
@author: rymo1354
"""
from pymatgen.io.vasp.inputs import Poscar
from pymatgen import Specie, Element, DummySpecie
from itertools import permutations, product
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.transformations.standard_transformations import AutoOxiStateDecorationTransformation
from pymatgen.analysis.structure_prediction.substitutor import Substitutor

elements_to_include = ['Li', 'Be', 'Na', 'Mg', 'Al', 'Si', 'K', 'Ca', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co',
                       'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'Se', 'Sr', 'Y', 'Zr', 'Nb', 'In', 'Sn', 'Sb','Ba','Hf',
                       'Ta', 'W', 'Bi', 'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'O']

def get_Structure_Template(template_path):

    return Poscar.from_file(template_path).structure

def get_Dummies_and_Elements(struct):
    dummies = []
    species = []
    for specie in struct.types_of_specie:
        if type(specie) == DummySpecie:
            dummies.append(specie)
        elif type(specie) == Element:
            species.append(specie)
        elif type(specie) == Specie:
            species.append(specie)
        else:
            continue
    return dummies, species

def get_Species_Substitution_Order(structure, dummies, species, to_ignore):

    els_removed = species.copy()
    for element in to_ignore:
        els_removed.remove(Element(element))

    subs = [list(p) for p in permutations(els_removed)]
    diff_coords = []
    struct_copies = []
    for sub in subs:
        copy = structure.copy()
        for dummy_ind in range(len(dummies)):
            copy[dummies[dummy_ind].symbol] = sub[dummy_ind]
        struct_copies.append(copy)
        coordination_numbers = []
        CN = CrystalNN(weighted_cn=True)
        for element_ind in range(len(copy.species)):
            cn = CN.get_cn(copy, element_ind, use_weights=True)
            coordination_numbers.append((copy.species[element_ind], cn))
        diff_coords.append(coordination_numbers)

    unique_cn_els = []
    for cn in diff_coords:
        cns = []
        for i in range(len(cn)):
            if cn[i] not in cns:
                cns.append(cn[i])
        unique_cn_els.append(cns)

    substitution_ind = None
    check_len = 300 # arbitrarily high number to start, used to get substitution scheme with lowest number of unique sites
    for unique_cn_el_ind in range(len(unique_cn_els)):
        if len(unique_cn_els[unique_cn_el_ind]) < check_len:
            substitution_ind = unique_cn_el_ind
            check_len = len(unique_cn_els[unique_cn_el_ind])
        else:
            continue

    ox_transform = AutoOxiStateDecorationTransformation()
    ox_species = ox_transform.apply_transformation(struct_copies[substitution_ind]).types_of_specie
    for specie in ox_species:
        for element in to_ignore:
            if specie.symbol == Element(element).symbol:
                ox_species.remove(specie)

    return subs[substitution_ind], ox_species

def get_Probable_Substitutions(species, elements_to_include, threshold):

    Sub = Substitutor(threshold=threshold)
    subs_dict = {}

    for specie in species:
        subs = Sub.pred_from_list([specie])
        try:
            subs.sort(key = lambda x: x['probability'], reverse = True)
            subs_dict_key = list(subs[0]['substitutions'].keys())[0]
            subs_dict[subs_dict_key] = []

            for i in range(len(subs)):
                if list(subs[i]['substitutions'].values())[0].symbol in elements_to_include:
                    subs_dict[subs_dict_key].append(list(subs[i]['substitutions'].values())[0])
        except:
            print('No probable substitutions at %s threshold for %s' % (threshold, specie))
            continue

    return subs_dict

def probable_Substitution_Structures(template_structure, dummies, ordered_subs, probable_substitutions):

    combos = list(product(*list(probable_substitutions.values())))

    probable_structures = []
    for combo in combos:
        copy = template_structure.copy()
        for dummy_ind in range(len(dummies)):
            copy[dummies[dummy_ind].symbol] = combo[dummy_ind].symbol

        if len(copy.composition.oxi_state_guesses()) > 0:
            probable_structures.append(copy)
        else:
            continue

    return probable_structures

def get_Structures(template_path, elements_to_ignore, elements_to_include=elements_to_include, threshold=0.038):

    structure = get_Structure_Template(template_path)
    dummies, species = get_Dummies_and_Elements(structure)
    print(dummies, species)
    try:
        ordered_subs, ox_species = get_Species_Substitution_Order(structure, dummies, species, elements_to_ignore)
        print(ordered_subs, ox_species)
        probable_substitutions = get_Probable_Substitutions(ox_species, elements_to_include, threshold)
        probable_structures = probable_Substitution_Structures(structure, dummies, ordered_subs, probable_substitutions)
        return probable_structures

    except:
        print('No probable substitutions at %s threshold for %s' % (threshold, structure.composition))
        return None
