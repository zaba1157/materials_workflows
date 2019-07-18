#!/usr/bin/env python
# A general catch all function that runs VASP with just one command.  Automatically determines number of nodes to run on,
# based on NPAR and KPAR what type (NEB,Dimer,Standard) to run and sets up a submission script and runs it

from jinja2 import Environment, FileSystemLoader
from Classes_Pymatgen import *
from pymatgen.io.vasp.outputs import *
from Helpers import *
import sys
import os
import shutil
import fnmatch
import cfg
import socket
import random
import argparse
import subprocess

def get_instructions_for_backup(jobtype, incar='INCAR'):
    """
    Args:
        jobtype:
        incar:
    Returns: A dictionary that contains lists to backup, move, and execute in a shell
    """
    instructions = {}
    instructions["commands"] = ['rm *.sh *.err STOPCAR *.e[0-9][0-9][0-9]* *.o[0-9][0-9][0-9]* &> /dev/null']
    instructions['backup'] = []
    instructions['move'] = []
    if jobtype == 'Standard':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS']
        instructions['move'] = [('CONTCAR', 'POSCAR')]
    elif jobtype == 'NEB':
        if os.path.isfile(incar):
            incar = Incar.from_file(incar)
            instructions['commands'].extend(['nebmovie.pl', 'nebbarrier.pl', 'nebef.pl > nebef.dat'])
            instructions['backup'] = ['INCAR', 'KPOINTS', 'neb.dat', 'nebef.dat', 'movie.xyz']
            for i in range(1, int(incar["IMAGES"]) + 1):
                instructions['move'].append((os.path.join(str(i).zfill(2), 'CONTCAR'),
                                           os.path.join(str(i).zfill(2), 'POSCAR')))
                for f in ['OUTCAR', 'POSCAR']:
                    instructions['backup'].append(os.path.join(str(i).zfill(2), f))
        else:
            raise Exception('Need valid INCAR')
    elif jobtype == 'Dimer':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS', 'MODECAR', 'DIMCAR']
        instructions['move'] = [('CENTCAR', 'POSCAR'), ('NEWMODECAR', 'MODECAR')]
    elif jobtype == 'GSM' or jobtype == 'SSM':
        instructions['backup'] = ['stringfile.xyz0000', 'inpfileq', 'scratch/initial0000.xyz', 'scratch/paragsm0000',
                                  'INCAR']
        instructions['move'] = [('stringfile.xyz0000', 'restart.xyz0000')]
        if jobtype == 'SSM':
            instructions['backup'].append('scratch/ISOMERS0000')
    elif jobtype == 'DynMat':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS']
        instructions['move'] = [('CONTCAR', 'POSCAR')]
    else:
        raise Exception('Jobtype Not recognized:  ' + jobtype)
    return instructions

def backup_vasp(dir, backup_dir='backup'):
    """
    Do backup of given directory
    Args:
        dir: VASP directory to backup
        backup_dir: directory files will be backed up to
    Returns: None
    """
    jobtype = getJobType(dir)

    if os.path.isdir(backup_dir):  # Find what directory to backup to
        last_run = -1
        backups = os.listdir(backup_dir)
        for backup in backups:
            try:
                if int(backup) > last_run:
                        last_run = int(backup)
            except:
                pass
        this_run = last_run+1
    else:
        this_run = 0
    backup_dir = os.path.join(backup_dir, str(this_run))

    instructions = get_instructions_for_backup(jobtype, os.path.join(dir, 'INCAR'))
    for command in instructions["commands"]:
        try:
            os.system(command)
        except:
            print('Could not execute command:  ' + command)
    for original_file in instructions["backup"]:
        try:
            backup_file = os.path.join(backup_dir, original_file)
            if not os.path.exists(os.path.dirname(backup_file)):
                os.makedirs(os.path.dirname(backup_file))
            shutil.copy(original_file, backup_file)
        except:
            print('Could not backup file at:  ' + original_file)

    return

def restart_vasp(dir):
    """
    Args:
        dir:
    Returns:
    """
    jobtype = getJobType(dir)
    instructions = get_instructions_for_backup(jobtype, os.path.join(dir, 'INCAR'))
    for (old_file, new_file) in instructions["move"]:
        try:
            if os.path.getsize(old_file) > 0:
                shutil.copy(old_file, new_file)
                print('Moved ' + old_file + ' to ' + new_file)
            else:
                raise Exception()
        except:
            print('Unable to move ' + old_file + ' to ' + new_file)
    if jobtype == 'SSM':
        raise Exception('Make SSM run into GSM run')
    elif jobtype == 'GSM' and os.path.exists('restart.xyz0000'):
        with open('inpfileq') as inpfileq:
            lines = inpfileq.readlines()
            gsm_settings = list(map(lambda x: (x + ' 1').split()[0], lines))
        if 'RESTART' not in gsm_settings:
            lines.insert(len(lines)-1,'RESTART                 1\n')
            with open('inpfileq', 'w') as inpfileq:
                inpfileq.writelines(lines)
            print('RESTART added to inpfileq')

def get_queue(computer, jobtype, time, nodes):
    if computer == "janus":
        if time <= 24:
            return 'janus'
        elif time > 24:
            return 'janus-long'
    elif computer == "summit":
        if time <= 1:
            return 'debug'
        elif time <= 24:
            return 'normal'
        elif time > 24:
            return 'long'
    elif computer == "peregrine":
        if time <= 1 and nodes <= 4 and False:
            return 'debug'
        elif time <= 4 and nodes <= 8:
            return 'short'
        elif time <= 48 and nodes <= 296:
            return 'batch-h'
        elif time > 48 and time <= 240 and nodes <= 120:
            return'long'
        else:
            raise Exception('Peregrine Queue Configuration not Valid: ' + time + ' hours ' + nodes + ' nodes ')
    elif computer == "eagle":
        return ''
    elif computer == "psiops":
        if nodes <= 1:
            return 'gb'
        else:
            return 'ib'
    elif computer == "rapunzel":
        return 'batch'
    else:
        raise Exception('Unrecognized Computer')

def get_template(computer, jobtype, special=None):
    if special == 'multi':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.multistep.jinja2.py')
    if special == 'encut':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.encut.sh.jinja2')
    if special == 'kpoints':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.kpoints.sh.jinja2')
    if special == 'diffusion':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.diffusion.jinja2.py')
    if special == 'pc':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.plane_constrained.jinja2.py')
    if special == 'hse_ts':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.hse.sh.jinja2')
    if special == 'find_max':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.find_max.py.jinja2')
    if jobtype == 'GSM' or jobtype == 'SSM':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.gsm.sh.jinja2')
    else:
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.standard.sh.jinja2')

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--time', help='walltime for run (integer number of hours)',
                    type=int, default=0)
parser.add_argument('-o', '--nodes', help='nodes per run (default : KPAR*NPAR)',
                    type=int, default=0)
parser.add_argument('-c', '--cores', help='cores per run (default : max allowed per system)',
                    type=int)
parser.add_argument('-q', '--queue', help='manually specify queue instead of auto determining')
parser.add_argument('-b', '--backup', help='backup files, but don\'t execute vasp ',
                    action='store_true')
parser.add_argument('-s', '--silent', help='display less information',
                    action='store_true')
parser.add_argument('-i', '--inplace', help='Run VASP without moving files to continue run',
                    action='store_true')
parser.add_argument('-f', '--finish_convergence', help='Only run vasp if run has not converged.  Can supply numbers to only uprgrade from specified stages',
                    type=int, nargs='*')
parser.add_argument('-n', '--name', help='name of run (Default is SYSTEM_Jobtype')
parser.add_argument('-g', '--gamma', help='force a gamma point run',
                    action='store_true')
parser.add_argument('-m', '--multi-step', help='Vasp will execute multipe runs based on specified CONVERGENCE file',
                    type=str)
parser.add_argument('--init', help='Vasp will initialize multipe runs based on specified CONVERGENCE file',
                    action='store_true')
parser.add_argument('-e', '--encut', help='find ENCUT that will converge to within specified eV/atom for 50 ENCUT',
                    type=float)
parser.add_argument('-k', '--kpoints', help='find Kpoints that will converge to within specified eV/atom',
                    type=float)
parser.add_argument('--ts', help='find ts along path specified in MEP.xml (from vasprun.xml)',
                    action='store_true')
parser.add_argument('--find_max', help='find max from POSCAR.1 to POSCAR.2',
                    type=float)
parser.add_argument('--diffusion', help='Do diffusion optimized run',
                    action='store_true')
parser.add_argument('--pc', help='Do plane constrained run',
                    action='store_true')
parser.add_argument('--frozen', help='Monitors jobs which constantlyfreeze',
                    action='store_true')

args = parser.parse_args()

if __name__ == '__main__':
    if args.finish_convergence != None:
        run = Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False, parse_potcar_file=False)
        if run.converged:
            exit('Run is already converged')
        elif args.finish_convergence != []:
            stage = Incar.from_file('INCAR')['STAGE_NUMBER']
            if stage not in args.finish_convergence:
                exit('Not correct stage')
    jobtype = getJobType('.')
    incar = Incar.from_file('INCAR')
    computer = getComputerName()
    print('Running vasp.py for ' + jobtype +' on ' + computer)
    print('Backing up previous run')
    backup_vasp('.')
    if args.backup:
        exit(0)
    if not args.inplace:
        print('Setting up next run')
        restart_vasp('.')
    print('Determining settings for run')

    # What kind of run.  load correct template
    additional_keywords = {}
    special = None
    if args.multi_step != None:
        additional_keywords['CONVERGENCE'] = args.multi_step
        if args.init:
            subprocess.call(['Upgrade_Run.py', '-i', args.multi_step])
            incar = Incar.from_file('INCAR')
        special = 'multi'
    elif args.encut:
        additional_keywords['target'] = args.encut
        special = 'encut'
    elif args.kpoints:
        additional_keywords['target'] = args.kpoints
        special = 'kpoints'
    elif args.ts:
        additional_keywords['target'] = args.ts
        special = 'hse_ts'
    elif args.diffusion:
        special = 'diffusion'
    elif args.pc:
        special = 'pc'
    elif args.find_max:
        special = 'find_max'
        additional_keywords['target'] = args.find_max

    # Set Time
    if args.time == 0:
        if 'AUTO_TIME' in incar:
            time = int(incar["AUTO_TIME"])
        elif 'VASP_DEFAULT_TIME' in os.environ:
            time = int(os.environ['VASP_DEFAULT_TIME'])
        else:
            time = 20
    else:
        time = args.time

    # Find number of Nodes
    if args.nodes == 0:
        if 'AUTO_NODES' in incar:
            nodes = incar['AUTO_NODES']
        elif 'NPAR' in incar:
            nodes = int(incar['NPAR']) * int(incar['KPAR']) if 'KPAR' in incar else int(incar['NPAR'])
            if jobtype == 'NEB':
                nodes = nodes * int(incar["IMAGES"])
        else:
            raise Exception('No Nodes specifying need 1 of the following (in order of decreasing priority): \n-o option, AUTO_NODES in INCAR, or NPAR in INCAR')
    else:
        nodes = args.nodes

    # Set Name
    if args.name:
        name = args.name
    elif 'SYSTEM' in incar:
        name = incar['SYSTEM'].strip().replace(' ', '_')
    elif 'System' in incar:
        name = incar['System'].strip().replace(' ', '_')
    elif 'system' in incar:
        name = incar['system'].strip().replace(' ', '_')

    # Set Memory
    if 'AUTO_MEM' in incar:
        mem = incar['AUTO_MEM']
    else:
        mem = 0

    # What version of VASP to run
    if args.gamma:
        vasp_kpts = os.environ["VASP_GAMMA"]
    elif 'AUTO_GAMMA' in incar and incar['AUTO_GAMMA']:
        vasp_kpts = os.environ["VASP_GAMMA"]
    elif 'AUTO_GAMMA' in incar and not incar['AUTO_GAMMA']:
        vasp_kpts = os.environ["VASP_KPTS"]
    else:
        vasp_kpts = os.environ["VASP_KPTS"]

    # Get number of cores
    if args.cores:
        cores = args.cores
    elif 'AUTO_CORES' in incar:
        cores = int(incar['AUTO_CORES'])
    elif 'VASP_MPI_PROCS' in os.environ:
        cores = int(os.environ["VASP_MPI_PROCS"])
    else:
        cores = int(os.environ["VASP_NCORE"])

    # Set Allocation
    if 'AUTO_ALLOCATION' in incar:
        account = incar['AUTO_ALLOCATION']
    elif 'VASP_DEFAULT_ALLOCATION' in os.environ:
        account = os.environ['VASP_DEFAULT_ALLOCATION']
    else:
        account = ''

    if 'VASP_OMP_NUM_THREADS' in os.environ:
        openmp = int(os.environ['VASP_OMP_NUM_THREADS'])
    else:
        openmp = 1

    if computer == 'janus' or computer == 'rapunzel'  or computer=='eagle':
        queue_type = 'slurm'
        submit = 'sbatch'
    elif computer=='summit':
        queue_type = 'slurm'
        submit = 'sbatch --export=NONE'
    else:
        queue_type = 'pbs'
        submit = 'qsub'

    if args.queue:
        queue = args.queue
    elif 'AUTO_QUEUE' in incar:
        queue = incar['AUTO_QUEUE'].lower()
    elif 'VASP_DEFAULT_QUEUE' in os.environ:
        queue = os.environ['VASP_DEFAULT_QUEUE']
    else:
        queue = get_queue(computer, jobtype, time, nodes)


    if args.frozen:
        jobtype = jobtype + '-Halting'

    (template_dir, template) = get_template(computer, jobtype, special)
    script = 'vasp_standard.sh'

    keywords = {'queue_type'    : queue_type,
                'queue'         : queue,
                'nodes'         : nodes,
                'computer'      : computer,
                'time'          : time,
                'nodes'         : nodes,
                'name'          : name,
                'ppn'           : cores,
                'cores'         : cores,
                'logname'       : name + '.log',
                'mem'           : mem,
                'account'       : account,
                'mpi'           : os.environ["VASP_MPI"],
                'vasp_kpts'     : os.environ["VASP_KPTS"],
                'vasp_gamma'    : os.environ["VASP_GAMMA"],
                'vasp_bashrc'   : os.environ['VASP_BASHRC'] if 'VASP_BASHRC' in os.environ else '~/.bashrc_vasp',
                'jobtype'       : jobtype,
                'tasks'         : int(nodes*cores),
                'openmp'        : openmp}
    keywords.update(additional_keywords)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template)
    with open(script, 'w+') as f:
        f.write(template.render(keywords))
    os.system(submit+script)
    #subprocess.call([submit, script])
    print('Submitted ' + name + ' to ' + queue)
