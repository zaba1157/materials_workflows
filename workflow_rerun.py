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
    name = formula+'-'+directories[-2]+'-'+directories[-1]
    name.replace("(",'')
    name.replace(")",'')
    return name


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
                    if workflow_stage_name != directories[-2] and workflow_stage_name != directories[-1]: 
                        name =  str(formula+'-'+directories[-1]+'-'+directories[-2]+'-'+workflow_stage_name)                      
                    elif workflow_stage_name == directories[-2]:                 
                        name =  str(formula+'-'+directories[-1]+'-'+workflow_stage_name)
                    elif workflow_stage_name == directories[-1]:
                        name = str(formula+'-'+workflow_stage_name)
                    name.replace("(",'')
                    name.replace(")",'')
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

def parse_wf_cmds(path):
    with open(os.path.join(path,'WORKFLOW_COMMANDS')) as fd:
        lines = [line.split(',') for line in fd]

        wf_input_cmds = {line[4].rstrip():line[1] for line in lines if len(line) == 5 and line[0].isdigit()}
        wf_conv_cmds = {line[4].rstrip():line[2] for line in lines if len(line) == 5 and line[0].isdigit()}
        wf_rerun_cmds = {line[4].rstrip():line[3] for line in lines if len(line) == 5 and line[0].isdigit()}
        wf_stgnum_cmds = {line[4].rstrip():line[0] for line in lines if len(line) == 5 and line[0].isdigit()}
        fd.close()
        
    return wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds  


    
    
def check_wf_cmds_for_nonVASP_cals(path):
    other_calcs = None
    wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds = parse_wf_cmds(path)
    for task_name in wf_input_cmds:
        if str(wf_rerun_cmds[task_name]) != 'vasp_run':                                   
            other_calcs = True
    return other_calcs

def initialize_workflow(path):
    wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds = parse_wf_cmds(path)
    with open(os.path.join(path,'WORKFLOW_STAGE'),'w') as f:
        f.write('WORKFLOW_STAGE_NUMBER = 0')
        f.close()

    for task_name in wf_input_cmds:
        workflow_path = os.path.join(path,task_name)
        task_stage_number, task_input_command, task_rerun_command, task_convergence_command = get_task_info(path, task_name)
        if task_stage_number == 0:
            os.system(task_input_command)
            default_workflow_nameing(workflow_path, task_name)
            if str(task_rerun_command) != 'vasp_run':                                   
                os.system(task_rerun_command)

def get_workflow_stage_number(path):
    workflow_stage = Incar().from_file(os.path.join(path,'WORKFLOW_STAGE'))
    current_workflow_stage_number = workflow_stage['WORKFLOW_STAGE_NUMBER']
    
    return current_workflow_stage_number

def get_max_workflow_stage_number(path):
    max_workflow_stage_number = 0
    wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds = parse_wf_cmds(path)
    for task_name in wf_input_cmds:
        task_stage_number = int(wf_stgnum_cmds[task_name])
        if task_stage_number > max_workflow_stage_number:
            max_workflow_stage_number = task_stage_number
            
    return max_workflow_stage_number

def get_task_info(path, task_name):
    wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds = parse_wf_cmds(path)
    task_stage_number = int(wf_stgnum_cmds[task_name])
    task_input_command = wf_input_cmds[task_name]
    task_rerun_command = wf_rerun_cmds[task_name]
    task_convergence_command = wf_conv_cmds[task_name]
    
    return task_stage_number, task_input_command, task_rerun_command, task_convergence_command

def wf_task_is_converged(root):
    current_workflow_stage_number = get_workflow_stage_number(root)
    wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds = parse_wf_cmds(root)
    upgrade_workflow = False                    
    for task_name in wf_input_cmds:
        task_stage_number, task_input_command, task_rerun_command, task_convergence_command = get_task_info(root, task_name)
        workflow_path = os.path.join(root,task_name)
        convergence_file = os.path.join(workflow_path,'TASK_CONVERGENCE')
        
        if task_stage_number == current_workflow_stage_number:
            if os.path.exists(convergence_file):
                task_convergence = Incar().from_file(convergence_file)
                if task_convergence['TASK_CONVERGED'] == True:
                   upgrade_workflow = True
                else:
                    os.system(task_convergence_command)
                    task_convergence = Incar().from_file(convergence_file)
                    if task_convergence['TASK_CONVERGED'] == True:                 
                        upgrade_workflow = True
            else:       
                os.system(task_convergence_command)
                task_convergence = Incar().from_file(convergence_file)
                if task_convergence['TASK_CONVERGED'] == True:                 
                    upgrade_workflow = True
                
    return upgrade_workflow

def get_wf_cmds_path_list(top_dir):
    wf_cmds_pth_lst = []
    for root, dirs, files in os.walk(top_dir):
        for file in files:
            if file == 'WORKFLOW_COMMANDS': 
                wf_cmds_pth_lst.append(root)
    return wf_cmds_pth_lst

def upgrade_current_workflow(root):
    current_workflow_stage_number = get_workflow_stage_number(root)
    max_workflow_stage_number = get_max_workflow_stage_number(root)
    wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds = parse_wf_cmds(root)
    if current_workflow_stage_number == max_workflow_stage_number:
        print('\n'+root+' WORKFLOW COMPLETE \n')
    elif current_workflow_stage_number < max_workflow_stage_number:                                
        replace(os.path.join(root,'WORKFLOW_STAGE'), str(current_workflow_stage_number), str(current_workflow_stage_number+1))
        current_workflow_stage_number+=1
        
        for task_name in wf_input_cmds:
            task_stage_number, task_input_command, task_rerun_command, task_convergence_command = get_task_info(root, task_name) 
            workflow_path = os.path.join(root,task_name)

            if task_stage_number == current_workflow_stage_number:
                os.system(task_input_command)
                default_workflow_nameing(workflow_path, task_name)
                if str(task_rerun_command) != 'vasp_run': 
                    os.system(task_rerun_command)

                
def workflow_progress(top_dir):
    wf_cmds_pth_lst = get_wf_cmds_path_list(top_dir)
    other_calculators_in_workflow = False
    workflow_commands_in_workflow = False
    if len(wf_cmds_pth_lst) > 0: # if WORKFLOW_COMMANDS file in path
        workflow_commands_in_workflow = True
        for root in wf_cmds_pth_lst:
            os.chdir(root)
            wf_input_cmds, wf_conv_cmds, wf_rerun_cmds, wf_stgnum_cmds = parse_wf_cmds(root)
            
            if check_wf_cmds_for_nonVASP_cals(root) == True:
                other_calculators_in_workflow = True
                
            if os.path.exists(os.path.join(root,'WORKFLOW_STAGE')) == False: # workflow Init
                initialize_workflow(root)                                                                     
            
            elif wf_task_is_converged(root) == True:              
                upgrade_current_workflow(root)
                                        
    os.chdir(top_dir) 
                                       
    return other_calculators_in_workflow, workflow_commands_in_workflow

def driver():
    pwd = os.getcwd()
    other_calculators_in_workflow, workflow_commands_in_workflow  = workflow_progress(pwd)
        
    num_jobs_in_workflow = check_num_jobs_in_workflow(pwd)  #currently only checks for vasp jobs
    
    
    if num_jobs_in_workflow > 1 or other_calculators_in_workflow == True or workflow_commands_in_workflow == True:
        if os.path.exists(os.path.join(pwd,'WORKFLOW_NAME')):
            workflow_file = Incar().from_file(os.path.join(pwd,'WORKFLOW_NAME'))
            workflow_name = workflow_file['NAME']
    
        else:         
            print('\n#---------------------------------#\n')
            workflow_name = input("Please enter a name for this workflow: ")
            print('\n#---------------------------------#\n')
                  
            with open(os.path.join(pwd,'WORKFLOW_NAME'),'w') as f:
                writeline = 'NAME = '+str(workflow_name)
                f.write(writeline)
                f.close()
                
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
    
