from datetime import datetime

from omuse.community.delft3d.interface import DFlowFM

from omuse.units import units
from matplotlib import pyplot

import sys
import numpy

from forcing import List_Forcings
from optimization_algorithm import optimization
 
def my_plot(x,y,var,var_min,var_max,name):
    pyplot.scatter(x,y,c=var, cmap="jet", s=1., vmin=var_min, vmax=var_max)
    pyplot.xlim(-110, -15)
    pyplot.ylim(0,65)
    pyplot.xlabel("lon (deg)")
    pyplot.ylabel("lat (deg)")
    pyplot.colorbar()
    pyplot.savefig(name,format='png')
    pyplot.clf()



optimization()

start_date="20080101"
start_datetime=datetime.strptime(start_date,"%Y%m%d")
tend=30. | units.day
dt=(3.| units.hour)

#internal calculations of TC
d=DFlowFM( ini_file="gtsm_coarse.mdu", coordinates="spherical", redirection="none",channel_type="sockets")

print(d.parameter_set_names())

# set parameters for internal forcing
d.parameters.use_interface_wind=True
d.parameters.use_interface_patm=True
ini_external_forcing=getattr(d, "ini_external forcing")
ini_external_forcing.ExtForceFile="gtsm_coarse.ext"
d.ini_time.RefDate=start_date

print("flow nodes",d.flow_nodes.shape)
print("flow links",d.flow_links.shape)

tc_forcings=List_Forcings(d.flow_nodes,d.flow_links)
tc_forcings.add_elements()

# prepare plot
pyplot.ion()
pyplot.show()
i=0
time_count = 0

# prepare forcings
channel1=tc_forcings.links.new_channel_to(d.flow_links_forcing)
channel2=tc_forcings.nodes.new_channel_to(d.flow_nodes_forcing)

while d.model_time < tend-dt/2:
    # evolve
    channel1.copy_attributes(["vx","vy"],target_names=["wind_vx","wind_vy"])
    channel2.copy_attributes(["pressure"],target_names=["atmospheric_pressure"])

    tc_forcings.evolve(d.model_time+dt)
    d.evolve_model(d.model_time+dt)

    i+=1
    time_count += 3

    #Plotting on nodes
    x_n=d.flow_nodes.lon.value_in(units.deg)
    y_n=d.flow_nodes.lat.value_in(units.deg)
    #Plotting on links
    x_l=d.flow_links.lon.value_in(units.deg)
    y_l=d.flow_links.lat.value_in(units.deg)

    pyplot.clf()

    vel_int=(d.flow_links_forcing.wind_vx.value_in(units.m/units.s)**2+ \
            d.flow_links_forcing.wind_vy.value_in(units.m/units.s)**2)**0.5
    name = "vel_internal" + str(i) + ".png"
    my_plot(x_l,y_l,vel_int,vel_int.min(),vel_int.max(),name)

    z_int=d.flow_nodes.water_level.value_in(units.m)
    name = "waterlevel_int" + str(i) + ".png"
    my_plot(x_n,y_n,z_int,-0.3,0.3,name)
    
    print(d.model_time)
 
d.stop()
  
