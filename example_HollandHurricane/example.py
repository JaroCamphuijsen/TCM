from datetime import datetime

from omuse.community.delft3d.interface import DFlowFM
from omuse.ext.hurricane_models import HollandHurricane

from omuse.units import units
from matplotlib import pyplot

import sys
import numpy

def my_plot(x,y,var,var_min,var_max,name):
    pyplot.scatter(x,y,c=var, cmap="jet", s=1., vmin=var_min, vmax=var_max)
    pyplot.xlim(-110, -50)
    pyplot.ylim(0,50)
    pyplot.xlabel("lon (deg)")
    pyplot.ylabel("lat (deg)")
    pyplot.colorbar()
    pyplot.savefig(name,format='png')
    pyplot.clf()


start_date="20080101"
start_datetime=datetime.strptime(start_date,"%Y%m%d")
tend=30. | units.day
dt=(3.| units.hour)

d=DFlowFM( ini_file="gtsm_coarse.mdu", coordinates="spherical", redirection="none",channel_type="sockets")
print(d.parameter_set_names())

#Use internal omuse forcings
d.parameters.use_interface_wind=True
d.parameters.use_interface_patm=True
d.ini_time.RefDate=start_date
input()

print("flow links",d.flow_nodes.shape)
print("flow links",d.flow_links.shape)

#Prescribe wind speed and pressure with omuse HollandHurricane model
tc_pres=HollandHurricane(d.flow_nodes,storm_file="syntheticTC.txt")
tc_vel=HollandHurricane(d.flow_links,storm_file="syntheticTC.txt")

pyplot.ion()
pyplot.show()
i=0

# prepare forcings
channel1=tc_vel.nodes.new_channel_to(d.flow_links_forcing)
channel2=tc_pres.nodes.new_channel_to(d.flow_nodes_forcing)

while d.model_time < tend-dt/2:
    i+=1
    # evolve model and apply forcings
    channel1.copy_attributes(["vx","vy"],target_names=["wind_vx","wind_vy"])
    channel2.copy_attributes(["pressure"],target_names=["atmospheric_pressure"])

    d.evolve_model(d.model_time+dt)

    tc_vel.evolve_model(d.model_time+dt) 
    tc_pres.evolve_model(d.model_time+dt) 


    #Plotting waterlevels
    x_n=d.flow_nodes.lon.value_in(units.deg)
    y_n=d.flow_nodes.lat.value_in(units.deg)

    z=d.flow_nodes.water_level.value_in(units.m)
    name = "waterlevel" + str(i) + ".png"
    my_plot(x_n,y_n,z,-0.3,0.3,name)

    #Plotting wind speed
    x_l=d.flow_links.lon.value_in(units.deg)
    y_l=d.flow_links.lat.value_in(units.deg)

    vel=(d.flow_links_forcing.wind_vx.value_in(units.m/units.s)**2+ \
            d.flow_links_forcing.wind_vy.value_in(units.m/units.s)**2)**0.5
    name = "velocity" + str(i) + ".png"
    my_plot(x_l,y_l,vel,vel.min(),vel.max(),name)


 
d.stop()
  
