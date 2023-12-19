#!/bin/bash
#Set job requirements
#SBATCH --nodes=1
#SBATCH --ntasks=64
#SBATCH --cpus-per-task=1
#SBATCH --partition=thin
#SBATCH --time=00:20:00
#SBATCH -o log.%j.o
#SBATCH -e log.%j.e



# modules!
source /gpfs/work2/0/einf2224/code/setdev

mpirun --report-bindings -np 1 python coupled-global-local.py 
 
