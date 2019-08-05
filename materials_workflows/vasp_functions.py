#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 21:11:04 2019
@author: Zach Bare
"""

import os
import json
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.core.periodic_table import Element
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.ext.matproj import MPRester
from tempfile import mkstemp
from shutil import move,copy
from os import remove
import subprocess
from pymatgen.io.vasp.inputs import Poscar, Incar
import sys
import numpy as np

def readfile(filename):
    #read a file into a list of strings
    f = open(filename,'r')
    tempfile = f.readlines()
    f.close()
    return tempfile

def read_poscar(path):
    #get elements lists from POSCAR
    pos_tempfile = readfile(path)
    pos_tempfile_read = [x.split() for x in pos_tempfile]

    #get lattice
    lattice = pos_tempfile_read[2:5]
    #assumes lattice in angstroms in poscar
    ang2bohr = 1.88973
    lattice = [[float(y)*ang2bohr for y in x] for x in lattice]
    total = sum([int(float(x)) for x in pos_tempfile_read[6]])
    return total,lattice

def reciprocal_lattice(lattice):
    a = lattice[0]
    b = lattice[1]
    c = lattice[2]
    b1 = np.cross(b,c)/(np.dot(a,np.cross(b,c)))
    b2 = np.cross(c,a)/(np.dot(b,np.cross(c,a)))
    b3 = np.cross(a,b)/(np.dot(c,np.cross(a,b)))
    recip_latt = [list(b1),list(b2),list(b3)]
    return recip_latt

def autokgrid(recip_latt,length):
    #generate kgrid using VASP's auto kgrid method
    b1 = recip_latt[0]
    b2 = recip_latt[1]
    b3 = recip_latt[2]
    N1 = max(1,length*np.linalg.norm(b1)+0.5)
    N2 = max(1,length*np.linalg.norm(b2)+0.5)
    N3 = max(1,length*np.linalg.norm(b3)+0.5)
    return int(N1),int(N2),int(N3)

def get_kpoints(poscar_path, kmin):

    #kmin = sys.argv[1]          #set this as variable or via argparse
    #indir = './'    
    total,lattice = read_poscar(poscar_path)
    kmin = float(kmin)/total
    #generates kpts same as vasp
    recip_latt = reciprocal_lattice(lattice)
    Nk = 0
    L = 5
    kaold = 0
    kbold = 0
    kcold = 0
    while Nk < kmin:
        ka,kb,kc = autokgrid(recip_latt,L)
        Nk = ka*kb*kc
        L += 2
        kaold = ka
        kbold = kb
        kcold = kc
        
    return   str(ka) + ' ' + str(kb) + ' ' + str(kc)

def append_to_incars_and_write_convergence_files(workflow_path, tags_to_append):
    
    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            if file == 'INCAR':
                with open(os.path.join(root, 'INCAR'), "r+") as incar:
                    for tag in tags_to_append:
                        incar.write(tag + '\n')

                    with open(os.path.join(root, 'CONVERGENCE'), 'a') as convergence:
                        convergence.write('0 %s\n\n' % os.path.basename(__file__))
                        for line in incar.readlines():
                            convergence.write(line)
                        for tag in tags_to_append:
                            convergence.write(tag + '\n')

                        convergence.close()
                    incar.close()
    return

def get_mpids_from_file(filename):
     
    try:
        all_entries = []
        pwd = os.getcwd()
        with open(os.path.join(pwd, filename)) as f: # The name of the mpid file in the present working directory
            lines = f.read().splitlines()
        for line in lines:
            all_entries.append(line.split())
    
        flattened_entries = [entry for entries_list in all_entries for entry in entries_list]
        for string in flattened_entries:
            if 'mp-' in string: # mp-id check
                continue
            else:
                flattened_entries.remove(string)
    
        return flattened_entries
    
    except:
        print('No file with mp-ids named %s in present working directory %s' % (filename, pwd))

def get_structures_from_materials_project(mpid_list, mp_key):
    
    m = MPRester(mp_key)
    structures = []
    for mpid in mpid_list:

        try:
            structure = m.get_structures(mpid, final=True)[0]
            structures.append(structure)
        except:
            print('%s not a valid mp-id' % mpid)

    return structures

def get_unique_coordination_environment_indices(structure, env_tolerance=0):

    ''' Identifies the unique coordination environments of atoms in a pymatgen.core.structure.Structure object '''
    ''' env_tolerance sets the tolerance at which sites are considered different: default is 0 '''
    ''' Returns sub_site_dict dictionary of a single unique site: key format '%element_site_%site_number' '''
    ''' Each key has a tuple value of (<enum 'Element'> object from pmg, site index) '''

    structure.add_oxidation_state_by_guess() #adds oxidation guess to a structure
    unique_species = np.unique(structure.species) #returns the unique species in the structure
    coord_envs = np.zeros((len(structure.species), len(unique_species))) #builds array to house coordination envs

    unique_sites = []
    site_counter = np.ones(len(unique_species))
    sites_dict = {} #contains all the equivalent substitution sites in arrays
    sub_site_dict = {} #contains only the first substitution site in the sites_dict array

    cnn = CrystalNN(weighted_cn=True)
    for i in range(len(structure.sites)):
        cnn_structure = cnn.get_nn_info(structure, i)
        for j in range(len(cnn_structure)):
            site = cnn_structure[j]['site']
            for specie in unique_species:
                if site.specie == specie:
                    el_ind = int(np.where(unique_species == specie)[0])
                    coord_envs[i][el_ind] += cnn_structure[j]['weight']

    for i in range(len(coord_envs)):
        duplicate_sites = []
        for j in range(len(coord_envs)):
            if np.linalg.norm(coord_envs[i]-coord_envs[j]) <= env_tolerance:
                duplicate_sites.append(i)
                duplicate_sites.append(j)
        one_unique = list(np.unique(duplicate_sites))
        if one_unique not in [x for x in unique_sites]:
            unique_sites.append(one_unique)

    for i in range(len(unique_sites)):
        species = []
        for j in range(len(unique_sites[i])):
            species.append(structure.species[unique_sites[i][j]])

        if len(np.unique(species)) == 1: #only a single element in the group of coordination environments
            specie = np.unique(species)[0]
            site_index = np.where(unique_species == specie)
            key = '%s_site_%s' % (str(specie.element), int(site_counter[site_index]))
            sites_dict[key] = (specie.element, unique_sites[i])
            sub_site_dict[key] = (specie.element, unique_sites[i][0]) #pick the first equivalent site
            site_counter[site_index] += 1
        else:
            raise Exception('Coordination environments similar w/in tolerance, but species %s are not' % np.unique(species))
            # should be a very rare exception when weighted_cn=True in CrystalNN, unless threshold is high

    return sub_site_dict

def structure_scaler(structure_list):
    
    for structure in structure_list:

        if len(structure.species) <= 16:
            structure.make_supercell([2, 2, 2])
        elif len(structure.species) <= 32:
            structure.make_supercell([2, 2, 1])
        elif len(structure.species) <= 64:
            structure.make_supercell([2, 1, 1])
        else:
            structure.make_supercell([1, 1, 1])
     
    return structure_list

def replace(source_file_path, pattern, substring):
    fh, target_file_path = mkstemp()
    with open(target_file_path, 'w') as target_file:
        with open(source_file_path, 'r') as source_file:
            for line in source_file:
                target_file.write(line.replace(pattern, substring))
    remove(source_file_path)
    move(target_file_path, source_file_path)
    
def replace_incar_tags(path, tag, value):
    incar = Incar().from_file(os.path.join(path,'INCAR'))
    incar.__setitem__(tag,value)
    incar.write_file(os.path.join(path,'INCAR'))

def get_incar_value(path, tag):
    incar = Incar().from_file(os.path.join(path,'INCAR'))
    value = incar[tag]
    return value    

def default_nameing(path):
    struct = Poscar.from_file(os.path.join(path,'POSCAR')).structure
    formula = str(struct.composition.formula).replace(' ', '')
    directories = path.split(os.sep)
  
    return formula+'-'+directories[-2]+'-'+directories[-1]


def jobs_in_queue():
    p = subprocess.Popen(['squeue' ,'-o', '"%Z %T"'],   #can be user specific, add -u username 
                         stdout=subprocess.PIPE)
    jobs_running = []
    line_count = 0
    for line in p.stdout:
        if line_count > 0:
            line = str(line, 'utf-8').replace('"', '').split()
            jobs_running.append((line[0],line[1])) # tuple is (directory, status)
        line_count+=1  
    all_jobs_dict = {job[0]:job[1] for job in jobs_running}    
    return all_jobs_dict
         

def not_in_queue(path):
    all_jobs_dict = jobs_in_queue()
    
    if path not in all_jobs_dict:
        return True
    elif all_jobs_dict[path] == 'COMPLETING' or all_jobs_dict[path] == 'COMPLETED':
        return True
    else:        
        return all_jobs_dict[path]

def get_job_name(path):
    if 'SYSTEM' in open(os.path.join(path,'INCAR')).read():
        name = get_incar_value(path, 'SYSTEM')
        return str(name)
    else:
        name = default_nameing(path)
        replace_incar_tags(path,'SYSTEM', name)
        return str(name)
    
def fizzled_job(path):
    job_name = get_job_name(path)
    rerun = False
    if not_in_queue(path) == True: # Continue if job is not in queue   
        if 'STAGE_NUMBER' in open(os.path.join(path,'INCAR')).read():
            if os.path.exists(os.path.join(path,'CONVERGENCE')):
                with open('CONVERGENCE') as fd:
                    pairs = (line.split(None) for line in fd)
                    res   = {int(pair[0]):pair[1] for pair in pairs if len(pair) == 2 and pair[0].isdigit()}
                    max_stage_number = len(res)-1
                    fd.close()
            else:
                raise Exception('Copy CONVERGENCE file into execution directory to run multistep job. Delete STAGE_NUMBER tag from INCAR for single step job.')
                
            current_stage_number = get_incar_value(path, 'STAGE_NUMBER')
            #print('Rerunning '+job_name+' stage '+str(current_stage_number)+' of '+str(max_stage_number))
            rerun = 'multi'               
            
        else:
            rerun = 'single'
   
    return rerun
    

                        
def is_converged(path):
    rerun = False
    if 'STAGE_NUMBER' in open(os.path.join(path,'INCAR')).read():
        if os.path.exists(os.path.join(path,'CONVERGENCE')):
            with open(os.path.join(path,'CONVERGENCE')) as fd:
                pairs = (line.split(None) for line in fd)
                res   = {int(pair[0]):pair[1] for pair in pairs if len(pair) == 2 and pair[0].isdigit()}
                max_stage_number = len(res)-1
                fd.close()
        else:
            raise Exception('Copy CONVERGENCE file into execution directory to run multistep job. Delete STAGE_NUMBER tag from INCAR for single step job.')

        current_stage_number = get_incar_value(path, 'STAGE_NUMBER')

        if current_stage_number < max_stage_number:
            rerun = 'multi'    #RERUN JOB
        elif current_stage_number == max_stage_number:
            Vr = Vasprun(os.path.join(path, 'vasprun.xml'))
            if Vr.converged != True:        #Job not converge
                pass

            else:
                rerun = 'converged'


    elif 'IMAGES' in open(os.path.join(path,'INCAR')).read():
        print('DOES NOT HANDLE NEB YET')

    else:                               #Single Relax not NEB job
        Vr = Vasprun(os.path.join(path, 'vasprun.xml'))
        if Vr.converged != True:        #Job not converge
            if Vr.converged_electronic != True:
                rerun = 'single'  #RERUN JOB
            elif Vr.converged_ionic != True and int(get_incar_value(path, 'NSW')) == 0:
                rerun = 'converged'
            else:
                rerun = 'single'  #RERUN JOB    Catch-all for all other errors

        else:
            rerun = 'converged'

        return rerun
    
def check_vasp_input(path):
    if os.path.exists(os.path.join(path,'INCAR')) and os.path.exists(os.path.join(path,'KPOINTS')) and os.path.exists(os.path.join(path,'POSCAR')):
        return True
    else:
        return False
    
def workflow_is_converged(pwd):
    workflow_converged_list = []
    for root, dirs, files in os.walk(pwd):
            for file in files:
                if file == 'POTCAR' and check_vasp_input(root) == True:                  
                    if os.path.exists(os.path.join(root,'vasprun.xml')):
                        try: 
                            Vr = Vasprun(os.path.join(root, 'vasprun.xml'))
                            fizzled = False                                
                        except:
                            fizzled = True
                            workflow_converged_list.append(False)
                        if fizzled == False:    
                            job = is_converged(root)
                            if job == 'converged':
                                workflow_converged_list.append(True)
                    else:
                        workflow_converged_list.append(False)
                        
    if False not in workflow_converged_list:
        return True
    else:
        return False
    
def write_workflow_convergence_file(pwd, value):
    convergence_file = os.path.join(pwd,'TASK_CONVERGENCE')
    with open(convergence_file, 'w') as f:
        f.write('TASK_CONVERGED = '+str(value))
        f.close()
def write_vasp_convergence_file(path, writelines):
    with open(os.path.join(path,'CONVERGENCE'),'w') as f:
        for line in writelines:
            f.write("%s\n" % line)
        f.close()
        
  
def get_minimum_energy_job(pwd):
    min_energy = 1000
    for root, dirs, files in os.walk(pwd):
            for file in files:
                if file == 'POTCAR' and check_vasp_input(root) == True:                  
                    Vr = Vasprun(os.path.join(root, 'vasprun.xml'))
                    nsites = len(Vr.final_structure)
                    E_per_atom = Vr.final_energy/nsites
                    if E_per_atom < min_energy:
                        min_energy = E_per_atom
                        job_path = root
    return root                    
    
def get_workflow_stage_number(pwd):
    workflow_stage = Incar().from_file(os.path.join(pwd,'WORKFLOW_STAGE'))
    current_workflow_stage_number = workflow_stage['WORKFLOW_STAGE_NUMBER']
    
    return current_workflow_stage_number

def get_workflow_stage_number_from_name(wf_command_path, workflow_name):
    with open(os.path.join(wf_command_path,'WORKFLOW_COMMANDS')) as fd:
        lines = [line.split(',') for line in fd]

        workflow_input_commands_dict = {line[4].rstrip():line[1] for line in lines if len(line) == 5 and line[0].isdigit()}
        workflow_convergence_commands_dict = {line[4].rstrip():line[2] for line in lines if len(line) == 5 and line[0].isdigit()}
        workflow_rerun_commands_dict = {line[4].rstrip():line[3] for line in lines if len(line) == 5 and line[0].isdigit()}
        workflow_stage_numbers_dict = {line[4].rstrip():line[0] for line in lines if len(line) == 5 and line[0].isdigit()}
        fd.close()
            
        for task_name in workflow_input_commands_dict:
            task_stage_number = int(workflow_stage_numbers_dict[task_name])
            task_input_command = workflow_input_commands_dict[task_name]
            task_convergence_command = workflow_convergence_commands_dict[task_name]
            task_rerun_command = workflow_rerun_commands_dict[task_name]
            if task_name == workflow_name:
                return task_stage_number
            
def get_workflow_name_from_stage_number(wf_command_path, workflow_stage):
    with open(os.path.join(wf_command_path,'WORKFLOW_COMMANDS')) as fd:
        lines = [line.split(',') for line in fd]

        workflow_input_commands_dict = {line[4].rstrip():line[1] for line in lines if len(line) == 5 and line[0].isdigit()}
        workflow_convergence_commands_dict = {line[4].rstrip():line[2] for line in lines if len(line) == 5 and line[0].isdigit()}
        workflow_rerun_commands_dict = {line[4].rstrip():line[3] for line in lines if len(line) == 5 and line[0].isdigit()}
        workflow_stage_numbers_dict = {line[4].rstrip():line[0] for line in lines if len(line) == 5 and line[0].isdigit()}
        fd.close()
            
        for task_name in workflow_input_commands_dict:
            task_stage_number = int(workflow_stage_numbers_dict[task_name])
            task_input_command = workflow_input_commands_dict[task_name]
            task_convergence_command = workflow_convergence_commands_dict[task_name]
            task_rerun_command = workflow_rerun_commands_dict[task_name]
            if task_stage_number == workflow_stage:
                return task_name   
        
def is_init_wf(wf_command_path, wf_name):
    if get_workflow_stage_number_from_name(wf_command_path, wf_name) == 0:
        if os.path.exists(os.path.join(wf_command_path,wf_name)) == False:
            return True
        else:
            return False
    else:
        return False
    
def write_init_wf(wf_command_path, wf_name):
    if is_init_wf(wf_command_path, wf_name) == True:
        wf_init_path = os.path.join(wf_command_path, '0_Init')
        os.mkdir(wf_init_path)
        for root, dirs, files in os.walk(wf_command_path):
            for file in files:
                if 'WORKFLOW' not in file and wf_init_path not in root:
                    move(os.path.join(root,file),wf_init_path)
                    
def get_structure_from_pass_path(pass_path):
    if os.path.exists(os.path.join(pass_path,'CONTCAR')) == True:
        return Poscar.from_file(os.path.join(pass_path,'CONTCAR')).structure
    else:
        return Poscar.from_file(os.path.join(pass_path,'POSCAR')).structure
        
        
def get_previous_pass_path(wf_command_path,wf_name):
    
    init_path = os.path.join(wf_command_path, '0_Init')
    current_stage = get_workflow_stage_number_from_name(wf_command_path, wf_name)
    if is_init_wf(wf_command_path, wf_name) == False and current_stage > 0:
        
        previous_stage = current_stage - 1
        previous_wf_name = get_workflow_name_from_stage_number(wf_command_path, previous_stage)
        pass_path = os.path.join(wf_command_path,str(previous_stage)+'_'+previous_wf_name+'_final')
        return pass_path
    
    elif os.path.exists(init_path) == False:
        write_init_wf(wf_command_path, wf_name)
        return init_path
    else:
        return init_path
    
                         
def move_job_to_pass_path(wf_command_path,final_job_path,wf_name):
    stage_number = get_workflow_stage_number_from_name(wf_command_path, wf_name)
    pass_path = os.path.join(wf_command_path,str(stage_number)+'_'+wf_name+'_final')
    os.mkdir(pass_path)
    wf_path = os.path.join(wf_command_path,wf_name)
    if wf_path != final_job_path:
       copy(os.path.join(wf_path,'TASK_CONVERGENCE'),pass_path)
    for root, dirs, files in os.walk(final_job_path):
        for file in files:
            if file == 'TASK_CONVERGENCE':
                copy(os.path.join(root,file),pass_path)
            elif 'backup' not in root:
                move(os.path.join(root,file),pass_path) 
    
def rerun_job(job_type, job_name):
    if job_type == 'multi':
        os.system('vasp.py -m CONVERGENCE -n '+job_name)
    if job_type == 'single':
        os.system('vasp.py -n '+job_name)
    if job_type == 'multi_inital':
        os.system('vasp.py -m CONVERGENCE --init -n '+job_name)
        
def check_num_jobs_in_workflow(pwd):
    num_jobs = 0
    for root, dirs, files in os.walk(pwd):
        for file in files:
            if file == 'POTCAR' and check_vasp_input(root) == True:
                num_jobs +=1
    return num_jobs

def get_single_job_name(pwd):
    for root, dirs, files in os.walk(pwd):
        for file in files:
            if file == 'POTCAR' and check_vasp_input(root) == True:
                job_name = get_job_name(root)
    return job_name

def store_data(vasprun_obj,job_name):
    
    entry_obj = vasprun_obj.as_dict() 
    entry_obj["complete_dos"] = vasprun_obj.complete_dos.as_dict()
    entry_obj["entry_id"] = job_name
    
    return entry_obj     



def vasp_run_main(pwd):
    completed_jobs, computed_entries = [], []              
    for root, dirs, files in os.walk(pwd):
        for file in files:
            if file == 'POTCAR':
                if check_vasp_input(root) == True:
                    print('#********************************************#\n')
                    job_name = get_job_name(root)
                    if not_in_queue(root) == True:
                            
                        if os.path.exists(os.path.join(root,'vasprun.xml')):
                            try: 
                                Vr = Vasprun(os.path.join(root, 'vasprun.xml'))                                
                                fizzled = False
                                
                            except:
                                print(root, '  Fizzled job, check errors! Attempting to resubmit...')
                                fizzled = True
                                
                            if fizzled == False:    
                                os.chdir(root)
                                job = is_converged(root)
                                rerun_job(job, job_name)
                                if job == 'converged':
                                    completed_jobs.append(str(job_name) + ','+ str(root))
                                    store_dict = store_data(Vr,job_name)
                                    computed_entries.append(store_dict)
                                    #post_processing(root)
                            else:
                                os.chdir(root)
                                job = fizzled_job(root)
                                rerun_job(job, job_name)
                                
                               
                        elif os.path.exists(os.path.join(root,'CONVERGENCE')):
                            print(job_name + ' Initializing multi-step run.')
                            os.chdir(root)
                            rerun_job('multi_inital', job_name)
                        else:
                            print(job_name + ' Initializing run.')
                            os.chdir(root)
                            rerun_job('single', job_name)
                    else:
                        print(job_name + ' Job in queue. Status: ' + not_in_queue(root))
                    print('\n') 
    num_jobs_in_workflow = check_num_jobs_in_workflow(pwd)
    if num_jobs_in_workflow > 1:                  
        if not completed_jobs:
            pass
        else:
            with open(os.path.join(pwd, 'completed_jobs.txt'), 'w') as f:
                for item in completed_jobs:
                    f.write("%s\n" % item)
                f.close()
   
        if len(completed_jobs) == num_jobs_in_workflow:
            print('\n  ALL JOBS HAVE CONVERGED!  \n')
            with open(os.path.join(pwd, 'WORKFLOW_CONVERGENCE'), 'w') as f:
                f.write('WORKFLOW_CONVERGED = True')
                f.close()
    
    return computed_entries                    

  
            
            
from pymatgen.analysis.eos import EOS

def get_number_of_subs(path):
    backup_path = os.path.join(path,'backup')
    max_num_sub = 0
    for root, dirs, files in os.walk(job_path):
        for di in dirs:
            if di.isdigit():
                if int(di) > max_num_sub:
                    max_num_sub = int(di)
    return max_num_sub

def remove_sys_incar(path):
    filepath = os.path.join(path,'INCAR')
    with open(filepath,'r') as f:
        data = f.readlines()
    for line in range(len(data)):
        if data[line].split()[0] == 'SYSTEM':
            data[line] = '\n'
    with open(filepath,'w') as f:
        f.writelines( data )
        
def volume_workflow_is_converged(pwd,max_num_sub,min_num_vols,volume_tolerance):
    workflow_converged_list = []
    E,V = [],[]
    minE = 100
    for root, dirs, files in os.walk(pwd):
            for file in files:
                if file == 'POTCAR' and check_vasp_input(root) == True:                  
                    if os.path.exists(os.path.join(root,'vasprun.xml')):
                        try: 
                            Vr = Vasprun(os.path.join(root, 'vasprun.xml'))
                            fizzled = False                                
                        except:
                            fizzled = True
                            workflow_converged_list.append(False)
                            
                        if fizzled == False:    
                            job = is_converged(root)
                            if job == 'converged':
                                workflow_converged_list.append(True)
                                vol = Poscar.from_file(os.path.join(root,'POSCAR')).structure.volume
                                if Vr.final_energy < minE:
                                    minE = Vr.final_energy
                                    minV = vol
                                    minE_path = root
                                    minE_formula = str(Poscar.from_file(os.path.join(path,'POSCAR')).structure.composition.reduced_formula)
                                E.append(Vr.final_energy)
                                V.append(vol)
                                
                        elif fizzled == True and get_incar_value(path, 'STAGE_NUMBER') == 0: #job is failing on initial relaxation
                            num_sub = get_number_of_subs(root)
                            if num_sub == max_num_sub:
                                os.remove(os.path.join(root,'POTCAR'))
                                #job failed too many times.... just ignore this job for the remainder of the workflow
                    else:
                        workflow_converged_list.append(False)

    num_jobs = check_num_jobs_in_workflow(pwd)
    if num_jobs < min_num_vols and len(E) > 0:
        scale_around_min = [0.98,1.02]   
        for s in scale_around_min:
            write_path = os.path.join(pwd,minE_formula+str(s*minV))
            os.mkdir(write_path)
            structure = Poscar.from_file(os.path.join(minE_path,'POSCAR')).structure
            structure.scale_lattice(s*minV)
            Poscar.write_file(structure,os.path.join(write_path,'POSCAR'))
            files_copy = ['backup/Init/INCAR','CONVERGENCE','KPOINTS','POTCAR']
            for fc in files_copy:
                copy_from_path = os.path.join(minE_path,fc)
                if os.path.exists(copy_from_path):
                    copy(copy_from_path,write_path)
            remove_sys_incar(write_path)
                    
        
        #create new jobs
    if False not in workflow_converged_list:
        if len(E) > min_num_vols-1:
            volumes = V
            energies = E
            eos = EOS(eos_name='murnaghan')
            eos_fit = eos.fit(volumes, energies)
            eos_minV = eos_fit.v0
            if abs(eos_minV - minV) < volume_tolerance: # ang^3 cutoff
                return True
                #eos_fit.plot()
                
            else:
                scale_around_min = [0.99,1,1.01]   
                for s in scale_around_min:
                    write_path = os.path.join(pwd,minE_formula+str(s*eos_minV))
                    os.mkdir(write_path)
                    structure = Poscar.from_file(os.path.join(minE_path,'POSCAR')).structure
                    structure.scale_lattice(s*eos_minV)
                    Poscar.write_file(structure,os.path.join(write_path,'POSCAR'))
                    files_copy = ['backup/Init/INCAR','CONVERGENCE','KPOINTS','POTCAR']
                    for fc in files_copy:
                        copy_from_path = os.path.join(minE_path,fc)
                        if os.path.exists(copy_from_path):
                            copy(copy_from_path,write_path)
                    remove_sys_incar(write_path)
                
                return False
                
        
    else:
        return False
