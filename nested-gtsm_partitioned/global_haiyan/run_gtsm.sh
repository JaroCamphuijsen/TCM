#!/bin/bash
# start this script with sbatch <script name>
#SBATCH --nodes=1
#SBATCH --tasks-per-node=32
#SBATCH --partition=thin
#SBATCH --time=10:00:00

# Usage:
# D-Flow FM computations using a Singularity container,
# either sequential, or parallel computations using one node.
# For parallel using multiple nodes: use submit_singularity.sh.
#
# To start:
# 1. Be sure that a Singularity container is available, 
#    together with an execute_singularity.sh script in the same folder.
# 2. Copy the run_singularity script into your working folder, i.e. the folder containing the dimr config file.
# 3. Modify the run_singularity script, see remarks below.
# 4. Execute the script from the command line.
#    You can feed the script to a queueing system.
#
# "execute_singularity.sh -p 2": Parent level to mount:
# If your working folder does not contain all of the input files, then you must set the -p flag.
# Let's define the "top level" as the folder containing all of the input files.
# The value of -p must be the number of folder levels between the dimr config file and the top level.
# A higher value will not cause any harm, provided that folders exist at the higher levels.
# 


#
#
# --- You will need to change the lines below -----------------------------

#module load intelmpi/21.2.0 #on H6
module load 2021 #on Snellius
module load intel/2021a
 
# Set number of partitions (this script only works for one node)
nPart=32

# Set the path to the folder containing the singularity image
singularitydir=/projects/0/einf2224/dflowfm_2022.04_fix20221108/delft3dfm_2022.04

mdufile=gtsm_fine.mdu


#
#
# --- You shouldn't need to change the lines below ------------------------

# stop after an error occurred:
set -e



#
#
# --- Execution part: modify if needed ------------------------------------

# Parallel computation on one node
#

# First: partitioning 
# (You can re-use a partition if the input files and the number of partitions haven't changed)
# Partitioning is executed by dflowfm, in the folder containing the mdu file
 echo partitioning...
 # "-p": See above. Arguments after "run_dflowfm.sh" are explained in run_dflowfm.sh
 srun -n 1 $singularitydir/execute_singularity_snellius.sh -p 1 run_dflowfm.sh --partition:ndomains=$nPart:icgsolver=6:contiguous=0  $mdufile

# Second: computation
#echo computation...
srun $singularitydir/execute_singularity_snellius.sh -p 1 run_dflowfm.sh $mdufile 
