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
            print('Rerunning '+job_name+' stage '+str(current_stage_number)+' of '+str(max_stage_number))
            rerun = 'multi'               
            
        else:
            rerun = 'single'
   
    return rerun
    
    
def is_converged(path):
    job_name = get_job_name(path)
    rerun = False
    if not_in_queue(path) == True:  # Continue if job is not in queue  
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
                print('Rerunning '+job_name+' stage '+str(current_stage_number)+' of '+str(max_stage_number))
            elif current_stage_number == max_stage_number:
                Vr = Vasprun(os.path.join(path, 'vasprun.xml'))
                if Vr.converged != True:        #Job not converge
                    if Vr.converged_electronic != True:
                        replace_incar_tags(path,'NELM',500) #increase number of electronic steps
                        print('Increased NELM to 500 max steps for electronic convergence.')
                        rerun = 'multi'  #RERUN JOB
                    elif Vr.converged_ionic != True and int(get_incar_value(path, 'NSW')) == 0:
                        print(job_name + ' Assuming you do not want to resubmit job! Single point energy calculation: converged_electronic = TRUE, converged_ionic = FALSE')
                        rerun = 'converged'
                    else:
                        print('Rerunning '+job_name+' stage '+str(current_stage_number)+' of '+str(max_stage_number))
                        rerun = 'multi'  #RERUN JOB    Catch-all for all other errors
                   
                else:
                    print(job_name + ' Complete and ready for post processing.') #Job has completed #post processing bader lobster bandstructure defects adsorbates ect...
                    rerun = 'converged'
                    
    
        elif 'IMAGES' in open(os.path.join(path,'INCAR')).read():
            print('DOES NOT HANDLE NEB YET')
            
        else:                               #Single Relax not NEB job
            Vr = Vasprun(os.path.join(path, 'vasprun.xml'))
            if Vr.converged != True:        #Job not converge
                if Vr.converged_electronic != True:
                    replace_incar_tags(path,'NELM',500) #increase number of electronic steps
                    print('Increased NELM to 500 max steps for electronic convergence.')
                    rerun = 'single'  #RERUN JOB
                elif Vr.converged_ionic != True and int(get_incar_value(path, 'NSW')) == 0:
                    print(job_name + ' Assuming you do not want to resubmit job!! Single point energy calculation: converged_electronic = TRUE, converged_ionic = FALSE')
                    rerun = 'converged'
                else:
                    rerun = 'single'  #RERUN JOB    Catch-all for all other errors
               
            else:
                print(job_name + ' Complete and ready for post processing.') #Job has completed #post processing bader lobster bandstructure ect...
                rerun = 'converged'

        return rerun
    
def check_vasp_input(path):
    if os.path.exists(os.path.join(path,'INCAR')) and os.path.exists(os.path.join(path,'KPOINTS')) and os.path.exists(os.path.join(path,'POSCAR')):
        return True
    else:
        return False
    
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

def default_workflow_nameing(pwd, workflow_stage_name):
    for rt, ds, fs in os.walk(pwd):
        for fle in fs:
            if fle == 'POTCAR' and check_vasp_input(rt) == True:
                    struct = Poscar.from_file(os.path.join(rt,'POSCAR')).structure
                    formula = struct.composition.reduced_formula
                    directories = rt.split(os.sep)
                    if workflow_stage_name != directories[-2]: 
                        if workflow_stage_name != directories[-1]:
                            name =  str(formula+'-'+directories[-1]+'-'+directories[-2]+'-'+workflow_stage_name)
                        
                    elif workflow_stage_name == directories[-2]:                 
                        name =  str(formula+'-'+directories[-1]+'-'+workflow_stage_name)
                    elif workflow_stage_name == directories[-1]:
                        name = str(formula+'-'+workflow_stage_name)
                    replace_incar_tags(rt,'SYSTEM', name)

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

def workflow_progress(top_dir):
    other_calculators_in_workflow = False
    workflow_commands_in_workflow = False
    for root, dirs, files in os.walk(top_dir):
        for file in files:
            if file == 'WORKFLOW_COMMANDS':
                workflow_commands_in_workflow = True
                with open(os.path.join(root,'WORKFLOW_COMMANDS')) as fd:
                    lines = [line.split(',') for line in fd]

                    workflow_input_commands_dict = {line[4].rstrip():line[1] for line in lines if len(line) == 5 and line[0].isdigit()}
                    workflow_convergence_commands_dict = {line[4].rstrip():line[2] for line in lines if len(line) == 5 and line[0].isdigit()}
                    workflow_rerun_commands_dict = {line[4].rstrip():line[3] for line in lines if len(line) == 5 and line[0].isdigit()}
                    workflow_stage_numbers_dict = {line[4].rstrip():line[0] for line in lines if len(line) == 5 and line[0].isdigit()}
                    fd.close()
                    
                if os.path.exists(os.path.join(root,'WORKFLOW_STAGE')):
                        workflow_stage = Incar().from_file(os.path.join(root,'WORKFLOW_STAGE'))
                        current_workflow_stage_number = workflow_stage['WORKFLOW_STAGE_NUMBER']
                        max_workflow_stage_number = 0
                        rerun_command = None
                        upgrade_workflow_list = []
                        for task_name in workflow_input_commands_dict:
                            #workflow_stage_name = str(workflow_run_directory_dict[workflow_command])
                            workflow_path = os.path.join(root,task_name)
                            task_stage_number = int(workflow_stage_numbers_dict[task_name])
                            task_input_command = workflow_input_commands_dict[task_name]
                            task_convergence_command = workflow_convergence_commands_dict[task_name]
                            task_rerun_command = workflow_rerun_commands_dict[task_name]
                            
                            if task_stage_number > max_workflow_stage_number:
                                max_workflow_stage_number = task_stage_number
                            if task_stage_number == int(current_workflow_stage_number):
                                
                                os.chdir(workflow_path)
                                convergence_file = os.path.join(workflow_path,'TASK_CONVERGENCE')
                                if os.path.exists(convergence_file):
                                    task_convergence = Incar().from_file(convergence_file)
                                    if task_convergence['TASK_CONVERGED'] == True:
                                        upgrade_workflow_list.append(True)
                                    else:
                                        os.system(task_convergence_command)
                                        if task_convergence['TASK_CONVERGED'] == True:
                                                upgrade_workflow_list.append(True) 
                                        else:       
                                            upgrade_workflow_list.append(False)                                        
                                            rerun_command = task_rerun_command        

                                else:
                                    os.chdir(workflow_path)
                                    os.system(task_convergence_command)
                                    if task_convergence['TASK_CONVERGED'] == True:
                                            upgrade_workflow_list.append(True) 
                                    else:       
                                        upgrade_workflow_list.append(False)                                        
                                        rerun_command = task_rerun_command
                                        
                            if rerun_command != None:
                                os.chdir(workflow_path)
                                if str(rerun_command) != 'vasp_run':                                    
                                    os.system(rerun_command)
                                    other_calculators_in_workflow = True 
                                    
                        if False not in upgrade_workflow_list:
                            if current_workflow_stage_number < max_workflow_stage_number:                                
                                replace(os.path.join(root,'WORKFLOW_STAGE'), str(current_workflow_stage_number), str(current_workflow_stage_number+1))
                                current_workflow_stage_number+=1
                                for task_name in workflow_input_commands_dict:
                                    workflow_path = os.path.join(root,task_name)
                                    task_stage_number = int(workflow_stage_numbers_dict[task_name])
                                    task_input_command = workflow_input_commands_dict[task_name]
                                    task_convergence_command = workflow_convergence_commands_dict[task_name]
                                    task_rerun_command = workflow_rerun_commands_dict[task_name]
                                   # workflow_stage_name = str(workflow_run_directory_dict[workflow_command])
                                    if task_stage_number == int(current_workflow_stage_number):
                                        #workflow_path = os.path.join(root,str(workflow_run_directory_dict[workflow_command])) 
                                        os.chdir(root)
                                        os.system(task_input_command)
                                        os.chdir(workflow_path)
                                        if str(task_rerun_command) != 'vasp_run':                                 
                                            os.system(task_rerun_command)
                                            other_calculators_in_workflow = True
                                        else:
                                            default_workflow_nameing(workflow_path, task_name)
                            elif current_workflow_stage_number == max_workflow_stage_number:
                                #name = str(workflow_run_directory_dict[workflow_command])
                                print('\n'+root+': WORKFLOW COMPLETE \n')
                else:
                    with open(os.path.join(root,'WORKFLOW_STAGE'),'w') as f:
                        f.write('WORKFLOW_STAGE_NUMBER = 0')
                        f.close()
                    current_workflow_stage_number=0
                    for task_name in workflow_input_commands_dict:
                        workflow_path = os.path.join(root,task_name)
                        task_stage_number = int(workflow_stage_numbers_dict[task_name])
                        task_input_command = workflow_input_commands_dict[task_name]
                        task_convergence_command = workflow_convergence_commands_dict[task_name]
                        task_rerun_command = workflow_rerun_commands_dict[task_name]
                        if task_stage_number == int(current_workflow_stage_number):
                            os.chdir(root)
                            os.system(task_input_command)
                            os.chdir(workflow_path)
                            #print(str(task_rerun_command))
                            if str(task_rerun_command) != 'vasp_run':                                   
                                os.system(task_rerun_command)
                                other_calculators_in_workflow = True
                            else:
                                default_workflow_nameing(workflow_path, task_name)
                                            
                                            
                return other_calculators_in_workflow, workflow_commands_in_workflow

def driver():
    pwd = os.getcwd()
    other_calculators_in_workflow, workflow_commands_in_workflow  = workflow_progress(pwd)
        
    num_jobs_in_workflow = check_num_jobs_in_workflow(pwd)  #currently only checks for vasp jobs
    
    
    if num_jobs_in_workflow > 1 or other_calculators_in_workflow == True or workflow_commands_in_workflow == True :
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
    
    
if __name__ == '__main__':
    driver()







