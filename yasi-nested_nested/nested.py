from functools import partial
from datetime import datetime

from omuse.community.delft3d.interface import DFlowFM
from omuse.community.era5.interface import ERA5

from amuse.ext.grid_remappers import bilinear_2D_remapper, nearest_2D_remapper

from omuse.units import units
from matplotlib import pyplot

from time import perf_counter

start_date="20110128"


tend=12. | units.day
dt=(1.| units.hour)

d=DFlowFM( ini_file="RF.mdu", coordinates="spherical", redirection="none",channel_type="sockets")

print(d.parameter_set_names())

# set parameters
d.parameters.use_interface_wind=False
d.parameters.use_interface_patm=False
d.ini_time.RefDate=start_date

d.ini_external_forcing.ExtForceFile="RF.ext"

print(d.flow_nodes)

while d.model_time < tend-dt/2:

    # evolve
    d.evolve_model(d.model_time+dt)
    z=d.flow_nodes.water_level
    
    print(d.model_time, tend-dt/2)
    print(d.model_time, z.min(),z.max())

# prepare plot
x=d.flow_nodes.lon.value_in(units.deg)
y=d.flow_nodes.lat.value_in(units.deg)
z=d.flow_nodes.water_level.value_in(units.m)

f=pyplot.figure()

pyplot.scatter(x,y,c=z, cmap="jet", s=1., vmin=-2.5, vmax=2.5)
pyplot.xlabel("lon (deg)")
pyplot.ylabel("lat (deg)")
pyplot.show()

    
d.stop()
  
