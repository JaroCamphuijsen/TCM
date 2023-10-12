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

## OMUSE model configurations

The following model configurations, which use OMUSE to model specific combinations of model/data coupling and benchmarking/optimization efforts can be found in this repository in the corresponding directories.

### gtsm-era5

Model configuration that uses OMUSE to couple ERA5 forcing data (wind and pressure) downloaded through OMUSE with the GTSM model (Delft3D).

### gtsm-era5ext

GTSM configuration files to execute GTSM with ERA5 forcing. ERA5 forcing files are downloaded and preprocessed beforehand and are specified in the external forcings file (.ext) of GTSM. - OMUSE is not used. GTSM is ran directly from Delft3d.

### gtsm-holland

Model configuration uses OMUSE to run the Holland model and couple it with the GTSM model (Delft3D).

### gtsm-holland_era5ext

GTSM configuration files to execute GTSM with Holland model output (spiderweb file) and ERA5 forcing in the background. Holland model output and ERA5 forcing files are prepared beforehand and are specified in the external forcings file (.ext) of GTSM. - OMUSE is not used. GTSM is ran directly from Delft3d. The spiderweb file includes a spw_merge_frac parameter to specify the fraction of the spiderweb radius where the merging with ERA5 starts.

### delftfm_benchmark

Benchmarking the Delft3DFM implementation. For more information about this scenario see delftfm_benchmark/README.md

### TC_optimization

Spatio-temporal optimization algorithm can be run with a command `python script.py $Name_of_input_database $Starting_line_number_in_input`
