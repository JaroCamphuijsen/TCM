import sys
import numpy 
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from statistics import mean
from omuse.ext.spherical_geometry import distance
from omuse.units import units

filename = sys.argv[1]  #  input file
start_line = int(sys.argv[2]) # line to start reading cyclones
multiple_basins = False
effective_distance = 1500.0  
time_offset = 2*8 #  8 is one day
pre_selection = False
Ncyclones = 0
order = 0
radius= 6371 
cyclones=dict()

class Cyclone(object):
  def __init__(self, yr, index):
    self.yr = yr  # nr
    self.month = 0
    self.index = index  # int, yearly index
    self.start_time = 1e20
    self.status = -1  # -1-not in use, 0-running, 1-finished, 2-offset, 3-removed 
    self.category = 0
    self.basin = 0 # basin N   
    self.landfall = 0
    self.times = [] #  [hours]
    self.lats = [] #  [lats in deg]
    self.lons = [] #  [lons in deg]
    self.radii = [] #  [radii in km]
    self.ws = [] #  [wind speed in m/s]
    self.pressure = [] # [minimum pressure in hPa]
    self.ld = []    # distance to the land
    self.distance = []  # [min distance to another cyclones in km]
    self.connection = []  # 0 - cyclones can not be placed together, 1 - can 
    self.shift = []  # if > 0: shift(each step is 3 h)  at which cyclones can be placed together
    self.order = 0

  def set_times(self, times):
    self.times.append(times)

  def set_lats(self, lats):
    self.lats.append(lats)

  def set_lons(self, lons):
    self.lons.append(lons)

  def set_radii(self, radii):
    self.radii.append(radii)

  def set_ws(self, ws):
    self.ws.append(ws)

  def set_ld(self,ld):
    self.ld.append(ld)

  def set_pressure(self, pressure):
    self.pressure.append(pressure)


def read_data(filename, cyclones, multiple_basins,pre_selection):
  inp_file = open(filename) 
  index_global = -1
  index_old = -1
  n_unactive = 0
  line_number = 0

  for line in inp_file:
    line_number += 1

    if line_number >= start_line:
      fields = line.strip().split(',')
      yr = int(float(fields[0]))
      index = int(float(fields[2]))
    
      if index != index_old:
        index_global += 1
        cyclones[index_global]=Cyclone(yr,index)
        cyclones[index_global].basin = int(float(fields[4]))
        cyclones[index_global].month = int(float(fields[1]))

      # Exclude cyclones without landfall, 
        if pre_selection == True:
          if index_global  > 0:
            if cyclones[index_global-1].landfall == 0:
              cyclones[index_global-1].status = 3
              n_unactive += 1
            if len(cyclones[index_global-1].times) == 0:
              cyclones[index_global-1].status = 3
              n_unactive += 1
      index_old = index

      if pre_selection == True:
        shore_distance = 1000.0
      else:
        shore_distance = 1e6

      if(float(fields[12]) < shore_distance or len(cyclones[index_global].times) != 0):
        cyclones[index_global].set_times(int(float(fields[3])))
        cyclones[index_global].set_lats(float(fields[5]))
        cyclones[index_global].set_lons(float(fields[6]))
        cyclones[index_global].set_pressure(float(fields[7]))
        cyclones[index_global].set_ws(float(fields[8]))
        cyclones[index_global].set_radii(float(fields[9]))
        cyclones[index_global].set_ld(float(fields[12]))

        if int(float(fields[10])) > cyclones[index_global].category:
          cyclones[index_global].category = int(float(fields[10])) 
        if pre_selection == True:
          if int(float(fields[11])) > cyclones[index_global].landfall:
            cyclones[index_global].landfall = int(float(fields[11])) 

      # Stop counting and print line number for next iteration  
      if (index_global - n_unactive) == 300:
        break

  Ncyclones = index_global
  print("N of cyclones in the input file", Ncyclones)
  print("N of cyclones which fit criteria", Ncyclones - n_unactive)
  print("Line number for next iteration", line_number)


  if multiple_basins == True:
    tot_cyclones = numpy.zeros(6)
    tot_tsteps = numpy.zeros(6)

    # Counting N of cyclones per each set of active cyclones per basin
    for i in range(0, Ncyclones):
      if cyclones[i].status == -1:
        for bas in range(0,6):
          if cyclones[i].basin == bas:
            tot_cyclones[bas] += 1
            tot_tsteps[bas] +=  max(cyclones[i].times)

  return Ncyclones


def set_distances(Ncyclones, cyclones):
  lat_set={}
  lon_set={}

  #   cyclone[1]:
  #               lat(1)   lon(1)
  #		  lat(2)   lon(2)
  #	 	  ...
  #	          lat(len(cyclones[1].lat))   lon(len(cyclones[1].lat))  
  #   cyclone[2]:
  #		  lat(1)   lon(1)
  #		  lat(2)   lon(2)
  #	 	  ...
  #	          lat(len(cyclones[2].lat))   lon(len(cyclones[2].lat))  
  #   ...
  #   cyclone[last]:
  #               lat(1)  lon(1)
  #		  lat(2)   lon(2)
  #	 	  ...
  #	          lat(len(cyclones[last].lat))   lon(len(cyclones[last].lat))  
  
  for i in range(0, Ncyclones):
    lat_set[i] = numpy.array(cyclones[i].lats) 
    lon_set[i] = numpy.array(cyclones[i].lons) 
  for i in range(0, Ncyclones): 
    for j in range(0, Ncyclones):
      dist = 0. 
      dist_iter = []
      k = 0
      shift = -1
      connection = 0
      track_length = 0
      if cyclones[j].basin == cyclones[i].basin:      
        if i != j and cyclones[i].status == -1 and cyclones[j].status == -1:

          for lat1, lon1 in zip(lat_set[i], lon_set[i]):
            dist_single = []
            lat2 = lat_set[j]
            lon2 = lon_set[j] 

            if len(lat_set[j]) >= len(lat_set[i]) - track_length:
              npoints = len(lat_set[i]) - track_length
            else:
              npoints = len(lat_set[j])

            for m in range(0, npoints):
              dist_single.append(distance(lat1, lon1, lat2[m], lon2[m],  \
                                 R=radius))

            dist_iter.append(min(dist_single))
            k = k + 1
            track_length += 1 

          if max(dist_iter) < effective_distance: 
            dist = min(dist_iter)
            shift = -1
            connection = 0
          else:
            l = 0

            for l in reversed(range(0, k-1)):
              dist_temp=min(dist_iter[l:k-1]) 
              if (dist_temp) >= effective_distance:
                dist = dist_temp 
                shift = l
                connection = 1
              if shift > 0 and dist_temp <= effective_distance:
                break

        else:
          connection = 0
          shift = -1
          dist = 0.0 

      else:
        dist = 1e5 
        shift = 0
        connection = 1

      cyclones[i].connection.append(connection)
      cyclones[i].shift.append(shift)
      cyclones[i].distance.append(dist)

# Select from the list all events which do not intersect at time 0
def place_events_initial(Ncyclones, effective_distance, cyclones):
  global order
  first_cyclone = True

  for i in range(0, Ncyclones):
    if cyclones[i].status == -1:
      if first_cyclone == True:
        cyclones[i].status = 0
        cyclones[i].start_time = 0
        first_cyclone = False

  for i in range(0, Ncyclones):
    min_distance = []

    if cyclones[i].status == -1:

      for j in range(0, Ncyclones):
        if cyclones[j].status == 0 and cyclones[i].connection[j] == 1 \
           and cyclones[i].shift[j] == 0:
          min_distance.append(cyclones[i].distance[j])
        elif cyclones[j].status == 0 and (cyclones[i].connection[j] != 1 \
           or cyclones[i].shift[j] != 0):
          min_distance.append(0)

      if len(min_distance) > 0 and min(min_distance) > effective_distance:
        cyclones[i].status = 0
        cyclones[i].start_time = 0
        order += 1
        cyclones[i].order = order

# Place cyclone to replace finished  
def place_event(Ncyclones, effective_distance, cyclones, current_time,time_offset):
  global order
  week = 56

  placed_cyclone = False
  for i in range(0, Ncyclones):
    min_distance = []

    if cyclones[i].status == -1:
      active_cyclone = False
      coun = 0
      for j in range(0, Ncyclones):
        if cyclones[j].status == 0:  
          active_cyclone = True
          coun += 1
          if (cyclones[j].connection[i] == 1 and       \
              cyclones[j].start_time <= current_time):
 
            if (cyclones[j].shift[i] == (current_time - cyclones[j].start_time) \
                and cyclones[j].start_time < current_time):
                min_distance.append(cyclones[j].distance[i])
            elif cyclones[j].shift[i] == 0:
              min_distance.append(cyclones[j].distance[i])
            else:            
              min_distance.append(0)

          else:            
             min_distance.append(0)
      # At the end we always have a N of large cyclones which can only be placed alone 
      if not active_cyclone:
        cyclones[i].status = 0
        cyclones[i].start_time = current_time + time_offset
        order += 1
        cyclones[i].order = order
        placed_cyclone = True       
    if placed_cyclone == True:
      break    
    else:
      if len(min_distance) > 0 and min(min_distance) > effective_distance:
        cyclones[i].status = 0
        order += 1
        cyclones[i].order = order
     
        # Added custom made offset (time_offset2)
        # time_offset is regular one
        dist_min = []
        dist_min.append(effective_distance)

        for j in range(0, Ncyclones):
          if (current_time-8 <= cyclones[j].start_time+max(cyclones[j].times) <= current_time):
            lat2 = cyclones[j].lats[len(cyclones[j].lats)-1] 
            lon2 = cyclones[j].lons[len(cyclones[j].lons)-1] 
            dist_min.append(distance(cyclones[i].lats[0],cyclones[i].lons[0], \
                            lat2, lon2, R=radius))  

        if min(dist_min) >= effective_distance:
          time_offset2 = time_offset
        else:
          time_offset2 = int(8*(1-min(dist_min)/effective_distance))
          
        cyclones[i].start_time = current_time + time_offset2
        #cyclones[i].start_time = current_time + time_offset
        placed_cyclone = True


# Plotting and writing data
def tstepping(Ncyclones, cyclones):
  week = 56
  yr = 52 * week
  ax = plt.axes(projection=ccrs.PlateCarree())
  ax.stock_img()

  # To plot data for single basin
  #ax.set_extent([-160,0,-10,70])
  
  cyclones_in_use = []
  #--------START TIMESTEPPING-----------
  for current_time in range(0, 1000*week):

    # First check whether we have any cyclone left to be run
    active_cyclones = 0
    cycl_count = 0
    for j in range(0, Ncyclones):
      if cyclones[j].status == -1 or cyclones[j].status == 0:
        active_cyclones += 1
    if active_cyclones == 0:
      print('timing_parallel', current_time)
      break 

    # Estimate average N of cyclones which we run simultaneously
    for j in range(0,Ncyclones):
      if cyclones[j].status ==0:
        cycl_count  += 1
    cyclones_in_use.append(cycl_count)

    # Go over cyclones for plotting and checking status
    for i in range(0, Ncyclones):

      if cyclones[i].status == 0 and (cyclones[i].start_time +  \
         max(cyclones[i].times)) == current_time:
        cyclones[i].status = 2 # start of spinup(time between cyclones)

      if cyclones[i].status == 2 and (cyclones[i].start_time +  \
         max(cyclones[i].times) + time_offset == current_time):
        cyclones[i].status = 1
    
      if current_time % 24 ==0:  
        if cyclones[i].status == 0 and (cyclones[i].start_time + \
             min(cyclones[i].times))<=current_time:  
          if cyclones[i].category == 0:
             line_col = "green"
          if cyclones[i].category == 1:
            line_col = "yellow"
          if cyclones[i].category == 2:
            line_col = "orange"
          if cyclones[i].category == 3:
            line_col = "red"
          if cyclones[i].category == 4:
            line_col = "black"
          if cyclones[i].category == 5:
            line_col = "purple"
          plt.plot(cyclones[i].lons, cyclones[i].lats, transform=ccrs.PlateCarree(), \
                 color=line_col)
          plt.text(mean(cyclones[i].lons)+1, mean(cyclones[i].lats),     \
                   cyclones[i].start_time, transform=ccrs.PlateCarree(), \
                   color=line_col)

    # 1 output in 3 days 
    if current_time % 24 ==0:  
      count = int(current_time/24)
      name = "test_"+str(count)+".png"
      plt.savefig(name, format='png')

      plt.pause(0.002)
      plt.clf()
      ax = plt.axes(projection=ccrs.PlateCarree())
      ax.stock_img()

    #------ FIND NEW CYCLONE------
    place_event(Ncyclones, effective_distance, cyclones, current_time, time_offset)

  plt.show()  

      
if __name__=="__main__":
  Ncyclones = read_data(filename, cyclones, multiple_basins, pre_selection)
  Ncyclones = 50
  set_distances(Ncyclones, cyclones) 
  place_events_initial(Ncyclones, effective_distance, cyclones)
  tstepping(Ncyclones, cyclones)
