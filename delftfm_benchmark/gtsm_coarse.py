from datetime import datetime

from omuse.community.delft3d.interface import DFlowFM
from omuse.ext.hurricane_models import HollandHurricane

from amuse.ext.grid_remappers import bilinear_2D_remapper, nearest_2D_remapper

from omuse.units import units
from matplotlib import pyplot

import sys
import numpy

def my_plot(x,y,var,var_min,var_max,name):
    pyplot.scatter(x,y,c=var, cmap="jet", s=1., vmin=var_min, vmax=var_max)
    pyplot.xlim(-110, -25)
    pyplot.ylim(0,65)
    pyplot.xlabel("lon (deg)")
    pyplot.ylabel("lat (deg)")
    pyplot.colorbar()
    pyplot.savefig(name,format='png')
    pyplot.clf()


start_date="20080902"
start_datetime=datetime.strptime(start_date,"%Y%m%d")
tend=20. | units.day
dt=(3.| units.hour)

#internal calculations of TC
d=DFlowFM( ini_file="gtsm_coarse.mdu", coordinates="spherical", redirection="none",channel_type="sockets")
#spiderweb
d_sp=DFlowFM( ini_file="gtsm_coarse_irma.mdu", coordinates="spherical", redirection="none",channel_type="sockets")

print(d.parameter_set_names())

#set parameters for spiderweb
d_sp.parameters.use_interface_wind=False
d_sp.parameters.use_interface_patm=False
d_sp.ini_time.RefDate=start_date
ini_external_forcing=getattr(d_sp, "ini_external forcing")
ini_external_forcing.ExtForceFile="gtsm_coarse_irma.ext"

# set parameters for internal forcing
d.parameters.use_interface_wind=True
d.parameters.use_interface_patm=True
ini_external_forcing=getattr(d, "ini_external forcing")
ini_external_forcing.ExtForceFile="gtsm_coarse.ext"
d.ini_time.RefDate=start_date
input()

print("flow links",d.flow_links.shape)

tc_pres=HollandHurricane(d.flow_nodes,"irma_data.txt")
tc_vel=HollandHurricane(d.flow_links,"irma_data.txt")

print(tc_vel.__dict__.keys())

# prepare plot
pyplot.ion()
pyplot.show()
i=0

# prepare forcings
channel1=tc_vel.nodes.new_channel_to(d.flow_links_forcing)
channel2=tc_pres.nodes.new_channel_to(d.flow_nodes_forcing)

while d.model_time < tend-dt/2:
    i+=1
    # evolve
    channel1.copy_attributes(["vx","vy"],target_names=["wind_vx","wind_vy"])
    channel2.copy_attributes(["pressure"],target_names=["atmospheric_pressure"])

    d_sp.evolve_model(d.model_time+dt)
    d.evolve_model(d.model_time+dt)
    tc_vel.evolve_model(d.model_time+dt) 
    tc_pres.evolve_model(d.model_time+dt) 

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

    vel_sp=(d_sp.flow_links_forcing.wind_vx.value_in(units.m/units.s)**2+ \
            d_sp.flow_links_forcing.wind_vy.value_in(units.m/units.s)**2)**0.5
    name = "vel_spiderweb" + str(i) + ".png"
    my_plot(x_l,y_l,vel_sp,vel_sp.min(),vel_sp.max(),name)
    
    vel_diff=vel_sp-vel_int
    name = "vel_diff" + str(i) + ".png"
    my_plot(x_l,y_l,vel_diff,vel_diff.min(),vel_diff.max(),name)

    z_int=d.flow_nodes.water_level.value_in(units.m)
    #z_int=d.flow_nodes_forcing.atmospheric_pressure.value_in(units.mbar)
    name = "waterlevel_int" + str(i) + ".png"
    #name = "pressure_int" + str(i) + ".png"
    my_plot(x_n,y_n,z_int,-0.5,0.5,name)
    
    z_sp=d_sp.flow_nodes.water_level.value_in(units.m)
    #z_sp=d_sp.flow_nodes_forcing.atmospheric_pressure.value_in(units.mbar)
    name = "waterlevel_sp" + str(i) + ".png"
    #name = "pressure_sp" + str(i) + ".png"
    my_plot(x_n,y_n,z_sp,-0.5,0.5,name)
    pyplot.clf()
 
    z_diff=z_sp-z_int
    name="difference_in_waterlevel" + str(i) + ".png"
    my_plot(x_n,y_n,z_sp,z_diff.min(),z_diff.max(),name)
    
    print(d.model_time, z_diff.min(),z_diff.max())
 
d.stop()
  
