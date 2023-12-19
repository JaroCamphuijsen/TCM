#!/bin/bash
#Set job requirements
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=thin
#SBATCH --time=00:10:00

source activate dfm_tools_env

event='haiyan' # name of the event

python gridref_his_to_bc.py "$event" 
