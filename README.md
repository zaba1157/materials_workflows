# materials_workflows

Currently only works on Summit and Eagle (SLURM), assuming you already have all dependencies installed...
#TODO dependencies

1) Download package with: git clone https://github.com/zaba1157/materials_workflows.git
2) Append Install-Directory/materials_workflows to both $PATH and $PYTHONPATH.
3) Run: python Install-Directory/materials_workflows/setup.py

# running workflows

All commands for the workflow are specified in a WORKFLOW_COMMANDS file. 
For the only current workflow implemented, this file is:
/materials_workflows/materials_workflows/workflows/vasp_bulk_mag_relax.WORKFLOW_COMMANDS

Copy above file as WORKFLOW_COMMANDS (without the name extention) to a run directory that contains a bulk POSCAR file.
Run workflow_rerun.py in the directory with WORKFLOW_COMMANDS, or in any root directory that contains a number of WORKFLOW_COMMANDS files and POSCARs in the subdirectories. You should be able to run workflow_rerun.py at any time to resubmit jobs to the queue and check status of jobs already in the queue. Just keep running workflow_rerun.py until all jobs have converged.


  
  
  
