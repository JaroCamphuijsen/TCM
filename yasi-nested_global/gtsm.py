from functools import partial
from datetime import datetime

from omuse.community.delft3d.interface import DFlowFM
from omuse.community.era5.interface import ERA5

from amuse.ext.grid_remappers import bilinear_2D_remapper, nearest_2D_remapper

from omuse.units import units
from matplotlib import pyplot

from time import perf_counter

start_date="20110130"
start_datetime=datetime.strptime(start_date,"%Y%m%d")
tend=4.5 | units.day
dt=(6.| units.hour)

d=DFlowFM( ini_file="gtsm_coarse.mdu", coordinates="spherical", redirection="none")

print(d.parameter_set_names())

# set parameters
d.parameters.use_interface_wind=False
d.parameters.use_interface_patm=False
d.ini_time.RefDate=start_date

d.ini_external_forcing.ExtForceFile="gtsm_coarse.ext"

# prepare plot
x=d.flow_nodes.lon.value_in(units.deg)
y=d.flow_nodes.lat.value_in(units.deg)
pyplot.ion()
f=pyplot.figure()
pyplot.show()

n=0
while d.model_time < tend-dt/2:
    n+=1
    # evolve
    d.evolve_model(d.model_time+dt)
    
    # update plot
    f.clf()
    z=d.flow_nodes.water_level.value_in(units.m)
    print(d.model_time, z.min(),z.max())
    p=pyplot.scatter(x,y,c=z, cmap="jet", s=1., vmin=-.5, vmax=.5)
    pyplot.xlim(110, 170)
    pyplot.ylim(-50,0)
    pyplot.xlabel("lon (deg)")
    pyplot.ylabel("lat (deg)")
    pyplot.title(str(d.model_time.in_(units.day)))
    f.colorbar(p)
    
    f.canvas.draw()
    f.canvas.flush_events()
    pyplot.savefig("waterlevel-%6.6i.png"%n)
    
    
d.stop()
  
