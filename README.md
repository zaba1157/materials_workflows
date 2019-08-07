# materials_workflows

Currently only works on Summit and Eagle (SLURM), assuming you already have all dependencies installed...

#TODO dependencies

1) Download package with: git clone https://github.com/zaba1157/materials_workflows.git
2) Append Install-Directory/materials_workflows to both $PATH and $PYTHONPATH.
3) Run: python Install-Directory/materials_workflows/setup.py

# running workflows

All commands for the workflow are specified in a WORKFLOW_COMMANDS file. 
These files are specified in:

/materials_workflows/workflows/*******.WORKFLOW_COMMANDS

Copy above file as WORKFLOW_COMMANDS (without the name extention) to a run directory that contains a bulk POSCAR file.
Run workflow_rerun.py in the directory with WORKFLOW_COMMANDS, or in any root directory that contains a number of WORKFLOW_COMMANDS files and POSCARs in the subdirectories. You should be able to run workflow_rerun.py at any time to resubmit jobs to the queue and check status of jobs already in the queue. Just keep running workflow_rerun.py until all jobs have converged.

For the scripts with mp in their names (vasp_mp_o_vacancies.py) have a list of Materials Project ids in a document titled 'MPIDS' in the top-level directory where jobs are being submitted (same location as WORKFLOW_COMMANDS.) This will allow different 'batches' of calculations on structures queried from the Materials Project to run concurrently. 
  
  
  
