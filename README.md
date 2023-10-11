# Tropical Cyclone Modeling (TCM)

Various scenarios of tropical cyclones modelling

## Installation instructions

### Dependencies

|                |                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------ |
| amuse          | https://github.com/amusecode/amuse                                                         |
| omuse          | https://github.com/omuse-geoscience/omuse.                                                 |

### Installation

* Install amuse framework with `pip install amuse-framework`
* Install omuse:\
  go to omuse directory and run `pip install -e .`

## Usage

In general the scenarios can be run by calling the relevant python script from a scenario directory:

```bash
python path/to/script.py
```

To use MPI to run OMUSE in parallel and take advantage of OMUSE capabilities:

```bash
mpirun --report-bindings -v -np 1 python path/to/script.py
```

On snellius one should submit a batch job, an example can be found in job.sh

## OMUSE scenarios descriptions

The following scenarios which use OMUSE to model specific combinations of model/data coupling and benchmarking/optimization efforts can be found in this repository in the corresponding directories.

### gtsm-era5

This scenario couples the Delft3D gtsm model to era5 forcing using the era5 interface in omuse.

### gtsm-era5ext

Running GTSM with ERA5 forcing, but with the forcing files specified in the .ext file of Delft3DFM.

### delftfm_benchmark

Benchmarking the Delft3DFM implementation. For more information about this scenario see delftfm_benchmark/README.md

### TC_optimization

Spatio-temporal optimization algorithm can be run with a command `python script.py $Name_of_input_database $Starting_line_number_in_input`
