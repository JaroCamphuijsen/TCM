# TCM
Different aspects of tropical cyclones modelling

## Spatio-temporal optimization algorithm and DelftFM benchmark

### Dependencies

|                |                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------ |
| amuse          | https://github.com/amusecode/amuse                                                         |
| omuse          | https://github.com/omuse-geoscience/omuse.                                                 |

### Installation
* Install amuse framework with `pip install amuse-framework`
* Install omuse:
  go to omuse directory and run `pip install -e .`
  
### Running script

#### Spatio-temporal optimization
Optimization algorithm can be run with a command `python script.py Name_of_input_database Starting_line_number_in_input`

#### DelftFM benchmark
* Run with wind velocities and pressure determined on Spiderweb grid.
  input files:
  gtsm_coarse_irma.ext
  gtsm_coarse_irma.mdu
  SPW_irma.spw
* Run with internal omuse calculations of wind velocities and pressure.
  input files:
  gtsm_coarse.ext
  gtsm_coarse.mdu
  irma_data.txt
* Creating movies from output files.
  Movies are created using Online GIF maker and image editor:
  https://ezgif.com/apng-maker

