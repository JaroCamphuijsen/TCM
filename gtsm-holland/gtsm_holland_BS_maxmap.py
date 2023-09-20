from datetime import datetime, timedelta

from omuse.community.delft3d.interface import DFlowFM
from omuse.ext.hurricane_models import HollandHurricane

from omuse.units import units
from matplotlib import pyplot

import sys
import os
import numpy as np
import pandas as pd
from netCDF4 import num2date, Dataset, date2num

print(units.__file__)

# inputs
start_date=sys.argv[1]
start_datetime=datetime.strptime(start_date,"%Y%m%d")
# tend=9. | units.day                                        # end period, I should do 9 afterwards!
tend=3. | units.hour                                        # end period, I should do 9 afterwards!
dt=(1.| units.hour)                                        # timesteps
# input file for the TC track:
tc_track = sys.argv[3]
# create a file to save outputs in map format
try:
  os.mkdir('output')
except FileExistsError:
  print('Output directory already exists')
dest=Dataset(r'output/gtsm_map.nc', 'w', format='NETCDF4')  
# bbox to save files to [lon min, lon max, lat min, lat max]
#coordinates=[-84., -78., 23., 34.]                                                                                                     
coordinates=sys.argv[2].split(',')                                         

def my_plot(x,y,var,var_min,var_max,name):
    pyplot.scatter(x,y,c=var, cmap="jet", s=1., vmin=var_min, vmax=var_max)
    pyplot.xlim(-82.5, -79.5) 
    pyplot.ylim(29.5,32.5)
    #pyplot.xlim(-110, -35)
    #pyplot.ylim(0,75)
    pyplot.xlabel("lon (deg)")
    pyplot.ylabel("lat (deg)")
    pyplot.colorbar()
    #pyplot.title(d.model_time)
    pyplot.savefig(name,format='png')
    pyplot.clf()

# create an array of dates
dates = np.arange(start_datetime + timedelta(days=2) + timedelta(hours=dt.value_in(units.hour)), start_datetime + timedelta(days=6), timedelta(hours=dt.value_in(units.hour)))

#d=DFlowFM( ini_file="gtsm_coarse.mdu", coordinates="spherical", redirection="none",channel_type="sockets") I commented this line because it was giving an error. I added the line below instead
d=DFlowFM(number_of_workers=32, ini_file="/gpfs/home2/jcamphuijsen/input/model_template/gtsm_fine.mdu", coordinates="spherical")
print(d.parameter_set_names())

#Use internal omuse forcings
d.parameters.use_interface_wind=True
d.parameters.use_interface_patm=True
d.ini_time.RefDate=start_date
d.ini_physics.TidalForcing=1
d.ini_output.MapInterval=0.
d.ini_output.HisInterval="3600.  172800.  777600."

d.ini_external_forcing.ExtForceFile="/gpfs/home2/jcamphuijsen/input/model_template/gtsm_fine.ext"
d.ini_geometry.PartitionFile="/gpfs/home2/jcamphuijsen/input/model_template/step11_global_part.pol"
d.ini_numerics.Icgsolver=6

#Prescribe wind speed and pressure with omuse HollandHurricane model
tc_pres=HollandHurricane(d.flow_nodes,actf_file=tc_track,tstart=start_datetime)
tc_vel=HollandHurricane(d.flow_links,actf_file=tc_track,tstart=start_datetime)

pyplot.ion()
pyplot.show()
i=0

# prepare forcings
channel1=tc_vel.nodes.new_channel_to(d.flow_links_forcing)
channel2=tc_pres.nodes.new_channel_to(d.flow_nodes_forcing)
print('---preparing forcings---')

# --------------------------------------------------------------------------------------------------------------------------
#%% create map file
# --------------------------------------------------------------------------------------------------------------------------

# create map file
x_n= np.where((d.flow_nodes.lon.value_in(units.deg)>float(coordinates[0])) & (d.flow_nodes.lon.value_in(units.deg)<float(coordinates[1])) & (d.flow_nodes.lat.value_in(units.deg)<float(coordinates[3])) & (d.flow_nodes.lat.value_in(units.deg)>float(coordinates[2])), d.flow_nodes.lon.value_in(units.deg), np.nan)          # cropping lon,lat
x_n=x_n[~np.isnan(x_n)]
y_n= np.where((d.flow_nodes.lon.value_in(units.deg)>float(coordinates[0]))& (d.flow_nodes.lon.value_in(units.deg)<float(coordinates[1])) & (d.flow_nodes.lat.value_in(units.deg)<float(coordinates[3])) & (d.flow_nodes.lat.value_in(units.deg)>float(coordinates[2])), d.flow_nodes.lat.value_in(units.deg), np.nan)
y_n=y_n[~np.isnan(y_n)]
dest.createDimension('station',len(x_n))
#dest.createDimension('time', None)
lon=dest.createVariable('longitude',d.flow_nodes.lon.value_in(units.deg).dtype.str,('station',)) 
lon.units='degrees_east'
lon.standard_name='longitude'
lon[:]=x_n
#lat=dest.createVariable('latitude',d.flow_nodes.lat.value_in(units.deg).dtype.str,('latitude')) 
lat=dest.createVariable('latitude',d.flow_nodes.lat.value_in(units.deg).dtype.str,('station',)) 
lat.units='degrees_north'
lat.standard_name='latitude'
lat[:]=y_n
'''
time=dest.createVariable('time', np.float64, ('time',))
time.units = '%s since %s'%('seconds', start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
time.standard_name='time'
time[:]=(dates - np.datetime64(start_datetime)) / np.timedelta64(1, 's')                                            # make time to the reference time
#print('time:', time[:])
'''
wl=dest.createVariable('waterlevel', np.float64,('station'))
#wl=dest.createVariable('waterlevel', np.float64,('time','station'))
wl.coordinates= 'longitude latitude'
wl.units='m'
wl.standard_name='sea_surface_height'

wl_ini=dest.createVariable('waterlevel_ini', np.float64,('station'))
#wl=dest.createVariable('waterlevel', np.float64,('time','station'))
wl_ini.coordinates= 'longitude latitude'
wl_ini.units='m'
wl_ini.standard_name='initial_sea_surface_height'


'''
# only necessary when plotting veloticies:
x_l= np.where((d.flow_links.lon.value_in(units.deg)>float(coordinates[0]))& (d.flow_links.lon.value_in(units.deg)<float(coordinates[1])) & (d.flow_links.lat.value_in(units.deg)<float(coordinates[3])) & (d.flow_links.lat.value_in(units.deg)> float(coordinates[2])), d.flow_links.lon.value_in(units.deg), np.nan)          # cropping lon,lat
x_l=x_l[~np.isnan(x_l)]
y_l= np.where((d.flow_links.lon.value_in(units.deg)>float(coordinates[0]))& (d.flow_links.lon.value_in(units.deg)<float(coordinates[1])) & (d.flow_links.lat.value_in(units.deg)<float(coordinates[3])) & (d.flow_links.lat.value_in(units.deg)> float(coordinates[2])), d.flow_links.lat.value_in(units.deg), np.nan)
y_l=y_l[~np.isnan(y_l)]
'''                                                                                                 # set initial water level to 0. Would this also work if you have tides?
# --------------------------------------------------------------------------------------------------------------------------
#%% execute model
# --------------------------------------------------------------------------------------------------------------------------
# evolve the model in OMUSE
while d.model_time < tend-dt/2:
    i+=1
    # evolve model and apply forcings
    channel1.copy_attributes(["vx","vy"],target_names=["wind_vx","wind_vy"])
    channel2.copy_attributes(["pressure"],target_names=["atmospheric_pressure"])

    d.evolve_model(d.model_time+dt)
    print(d.model_time)
    tc_vel.evolve_model(d.model_time+dt) 
    tc_pres.evolve_model(d.model_time+dt) 
    
    # -----------------------------------------------------------------------------------------------------------------------
    #%% save data to map file
    # -----------------------------------------------------------------------------------------------------------------------
    #Plotting waterlevels
    z=d.flow_nodes.water_level.value_in(units.m)
    z_bbox= np.where((d.flow_nodes.lon.value_in(units.deg)>float(coordinates[0])) & (d.flow_nodes.lon.value_in(units.deg)<float(coordinates[1])) & (d.flow_nodes.lat.value_in(units.deg)<float(coordinates[3])) & (d.flow_nodes.lat.value_in(units.deg)>float(coordinates[2])), z, np.nan)
    z_bbox=z_bbox[~np.isnan(z_bbox)]
    #print('z_bbox', z_bbox)

    name = "waterlevel" + str(i) + ".png"
    
        
    if d.model_time.value_in(units.s) == 3600.: 
        wl_ini[:]=z_bbox
        wl[:]=wl_ini[:]
        #print('wl_ini[:]', wl_ini[:])
        my_plot(x_n,y_n,z_bbox,0,2,name)

       
    # if 172800. < d.model_time.value_in(units.s) <= 518400. - dt.value_in(units.s):
    #wl[:]=z_bbox
    wl[:]=np.where(z_bbox>wl[:], z_bbox, wl[:])
    #print('wl[:]', wl[:])
    my_plot(x_n,y_n,z_bbox,0,2,name)

    
    '''
    #if d.model_time <= tend-dt:
    if 172800. < d.model_time.value_in(units.s) <= 518400. - dt.value_in(units.s):
        datei = num2date(d.model_time.number,units=time.units)#,calendar=time.calendar)
        #datei = num2date(d.model_time.number,units=time.units,calendar=time.calendar)
        #print('timestep2:',timestep2)
        #print('dates:', dates)
        #print('waterlevel:', d.model_time, z_bbox.min(),z_bbox.max())
        #print('datei:', np.datetime64(datei))
        tid_fileout = list(dates).index(datei)
        #print('tid_fileout:', tid_fileout)
        #time[:]=d.model_time.number
        #print('dest.variables[time][:]', dest.variables['time'][:])
        #
        #dest.variables['waterlevel'][n,:,:]=z
        wl[tid_fileout-1,:]=z_bbox # not sure if this should be -1 or not! lets check out the results later on..
        #wl[d.model_time,:,:]=z    
    '''    

    # #Plotting waterlevels
    # z=d.flow_nodes.water_level.value_in(units.m)
    # z_bbox= np.where((d.flow_nodes.lon.value_in(units.deg)>float(coordinates[0]))& (d.flow_nodes.lon.value_in(units.deg)<float(coordinates[1])) & (d.flow_nodes.lat.value_in(units.deg)<float(coordinates[3])) & (d.flow_nodes.lat.value_in(units.deg)> float(coordinates[2])), z, np.nan)
    # z_bbox=z_bbox[~np.isnan(z_bbox)]
    # print('waterlevel:', d.model_time, z_bbox.min(),z_bbox.max())
    # name = "waterlevel" + str(i) + ".png"
    # my_plot(x_n,y_n,z_bbox,-2.,2.,name)
    
    # #Plotting wind speed    
    vel=(d.flow_links_forcing.wind_vx.value_in(units.m/units.s)**2+ \
            d.flow_links_forcing.wind_vy.value_in(units.m/units.s)**2)**0.5
    # vel_bbox= np.where((d.flow_links.lon.value_in(units.deg)>float(coordinates[0])) & (d.flow_links.lon.value_in(units.deg)<float(coordinates[1])) & (d.flow_links.lat.value_in(units.deg)<float(coordinates[3])) & (d.flow_links.lat.value_in(units.deg)> float(coordinates[2])), vel, np.nan)
    # vel_bbox=vel_bbox[~np.isnan(vel_bbox)]
    print('velocity:', d.model_time, vel.min(),vel.max())
    # print('max_velocity location:', d.model_time, d.datetime)
    # name = "velocity" + str(i) + ".png"
    # my_plot(x_l,y_l,vel_bbox,0.,40.,name)

d.stop()
  
