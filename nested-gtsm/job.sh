#!/bin/bash
#Set job requirements
#SBATCH --nodes=1
#SBATCH --ntasks=64
#SBATCH --cpus-per-task=1
#SBATCH --partition=thin
#SBATCH --time=03:00:00
#SBATCH -o log.%j.o
#SBATCH -e log.%j.e

# note the ntasks=64 above is too much and should be maybe set to 32

echo $OMP_NUM_THREADS

# modules!
source /gpfs/work2/0/einf2224/code/setdev

start_date="20170906"            # Default 7 days before landfall. Results are saved from 2 days before landfall until 5 days after. Changes of these settings can be made in the gtsm_template.py script
bbox_gtsm=-82.5,-79.5,29.5,32.5

# maybe by default now I would do that I have a certain period for which I run tides, and also for which I save data. To make it simple.

mpirun --report-bindings -v -np 1 python /gpfs/work2/0/einf2224/TCM/nested-gtsm/coupled-global-local.py "$start_date" "$bbox_gtsm"
 

