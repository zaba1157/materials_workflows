#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 21:11:04 2019

@author: Zach Bare
"""

import os
import json
from pymatgen.io.vasp.outputs import Vasprun
from tempfile import mkstemp
from shutil import move
from os import remove
import subprocess
from pymatgen.io.vasp.inputs import Poscar, Incar

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
    formula = str(struct.composition.reduced_formula)
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
            with open('CONVERGENCE') as fd:
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
                if file == 'POTCAR' and if check_vasp_input(root) == True:                  
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
    if False not in workflow_converged_list:
        return True
    else:
        return Fasle
    
def write_workflow_convergence_file(pwd, value):
    convergence_file = os.path.join(pwd,'WORKFLOW_CONVERGENCE')
    with open(convergence_file, 'w') as f:
        f.write('WORKFLOW_CONVERGED = '+str(value))
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
                if file == 'POTCAR' and if check_vasp_input(root) == True:                  
                    Vr = Vasprun(os.path.join(root, 'vasprun.xml'))
                    if Vr.final_energy < min_energy:
                        min_energy = Vr.final_energy
                        job_path = root
    return root                    
    
def get_workflow_stage_number(pwd):
    workflow_stage = Incar().from_file(os.path.join(root,'WORKFLOW_STAGE'))
    current_workflow_stage_number = workflow_stage['WORKFLOW_STAGE_NUMBER']
    
    return current_workflow_stage_number
    
    
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

def workflow_progress(pwd):
    other_calculators_in_workflow = False
    for root, dirs, files in os.walk(pwd):
        for file in files:
            if file == 'WORKFLOW_COMMANDS':                
                with open(os.path.join(root,'WORKFLOW_COMMANDS')) as fd:
                    pairs = (line.split(None) for line in fd)
                    workflow_commands_dict   = {pair[1]:int(pair[0]) for pair in pairs if len(pair) == 5 and pair[0].isdigit()}  
                    workflow_convergence_command_dict = {pair[1]:pair[2] for pair in pairs if len(pair) == 5 and pair[0].isdigit()}
                    workflow_run_directory_dict = {pair[1]:pair[3] for pair in pairs if len(pair) == 5 and pair[0].isdigit()} 
                    workflow_rerun_command_dict = {pair[1]:pair[4] for pair in pairs if len(pair) == 5 and pair[0].isdigit()} 
                    fd.close()
                    
                if os.path.exists(os.path.join(root,'WORKFLOW_STAGE')):
                        workflow_stage = Incar().from_file(os.path.join(root,'WORKFLOW_STAGE'))
                        current_workflow_stage_number = workflow_stage['WORKFLOW_STAGE_NUMBER']
                        max_workflow_stage_number = 0
                        rerun_command = None
                        upgrade_workflow_list = []
                        for workflow_command in workflow_commands_dict:
                            if workflow_commands_dict[workflow_command] > max_workflow_stage_number:
                                max_workflow_stage_number = workflow_commands_dict[workflow_command]
                            if workflow_commands_dict[workflow_command] == int(current_workflow_stage_number):
                                workflow_path = os.path.join(root,str(workflow_run_directory_dict[workflow_command]))
                                os.chdir(workflow_path)
                                convergence_file = os.path.join(workflow_path,'WORKFLOW_CONVERGENCE')
                                if os.path.exists(convergence_file):
                                    workflow_convergence = Incar().from_file(convergence_file)
                                    if workflow_convergence['WORKFLOW_CONVERGED'] == True:
                                        upgrade_workflow_list.append(True)
                                    else:
                                        os.system(str(workflow_convergence_command_dict[workflow_command]))
                                        if workflow_convergence['WORKFLOW_CONVERGED'] == True:
                                                upgrade_workflow_list.append(True) 
                                        else:       
                                            upgrade_workflow_list.append(False)                                        
                                            rerun_command = str(workflow_rerun_command_dict[workflow_command])        

                                else:
                                    os.system(str(workflow_convergence_command_dict[workflow_command]))
                                    if workflow_convergence['WORKFLOW_CONVERGED'] == True:
                                            upgrade_workflow_list.append(True) 
                                    else:       
                                        upgrade_workflow_list.append(False)                                        
                                        rerun_command = str(workflow_rerun_command_dict[workflow_command])
                                        
                            if rerun_command != None:
                                if rerun_command != 'vasp_run' or 'vasp' or 'Vasp':                                    
                                    os.system(rerun_command)
                                    other_calculators_in_workflow = True    
                        if False not in upgrade_workflow_list:
                            if current_workflow_stage_number < max_workflow_stage_number:                                
                                replace(os.path.join(root,'WORKFLOW_STAGE'), str(current_workflow_stage_number), str(current_workflow_stage_number+1))
                                current_workflow_stage_number+=1
                                for workflow_command in workflow_commands_dict:
                                    if workflow_commands_dict[workflow_command] == int(current_workflow_stage_number):
                                        workflow_path = os.path.join(root,str(workflow_run_directory_dict[workflow_command]))
                                        os.chdir(workflow_path)
                                        os.system(workflow_command)
                                        rerun_command = str(workflow_rerun_command_dict[workflow_command])
                                        if rerun_command != 'vasp_run' or 'vasp' or 'Vasp':                                 
                                            os.system(rerun_command)
                                            other_calculators_in_workflow = True
                            elif current_workflow_stage_number == max_workflow_stage_number:
                                #name = str(workflow_run_directory_dict[workflow_command])
                                print('\n'+root+': WORKFLOW COMPLETE \n')
                else:
                    with open(os.path.join(root,'WORKFLOW_STAGE'),'w') as f:
                        f.write('WORKFLOW_STAGE_NUMBER = 0')
                        f.close()
                    current_workflow_stage_number=0
                    for workflow_command in workflow_commands_dict:
                        if workflow_commands_dict[workflow_command] == int(current_workflow_stage_number):
                            workflow_path = os.path.join(root,str(workflow_run_directory_dict[workflow_command]))
                            os.chdir(workflow_path)
                            os.system(workflow_command)
                            rerun_command = str(workflow_rerun_command_dict[workflow_command])
                            if rerun_command != 'vasp_run' or 'vasp' or 'Vasp':                                   
                                os.system(rerun_command)
                                other_calculators_in_workflow = True
                                
                return other_calculators_in_workflow

def driver():
    pwd = os.getcwd()
    other_calculators_in_workflow = workflow_progress(pwd)
        
    num_jobs_in_workflow = check_num_jobs_in_workflow(pwd)  #only checks for vasp jobs
        
    if num_jobs_in_workflow > 1 or other_calculators_in_workflow == True:
        if os.path.exists(os.path.join(pwd,'WORKFLOW_NAME')):
            workflow_file = Incar().from_file(os.path.join(pwd,'WORKFLOW_NAME'))
            workflow_name = workflow_file['NAME']
    
        else:
                
            workflow_name = input("Please enter a name for this workflow: ")
            with open(os.path.join(pwd,'WORKFLOW_NAME'),'w') as f:
                writeline = 'NAME = '+str(workflow_name)
                f.write(writeline)
                f.close()        
            
        computed_entries = vasp_run_main(pwd)
                
    else:
        workflow_name = get_single_job_name(pwd)    
        computed_entries = vasp_run_main(pwd)
        
    if not computed_entries:
        pass
    else:        
        with open(os.path.join(pwd,str(workflow_name) +'_converged.json'),'w') as f:
            json.dump(computed_entries, f)    
        







