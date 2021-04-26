import sys
import numpy 
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from statistics import mean
from geopy.distance import distance
#Dont forget to swith back to variable time offset

filename = "STORM_DATA_IBTRACS_NA_1000_YEARS_0.txt"  #  input file
start_line = 0 # line to start reading cyclones
multiple_basins = False
effective_distance = 1500.0  
time_offset = 16 #  8 is one day
Nfiles = 5
basin_name = "WP_"
pre_selection = False
Ncyclones = 0
order = 0
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
      if (index_global - n_unactive) == 100:
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
  radius= 6371 
  effective_distance = 1500.0
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
              dist_single.append(distance((lat1,lon1),(lat2[m],lon2[m])).km)
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
          dist = 0. 

      else:
        dist = 1e5 
        shift = 0
        connection = 1

      cyclones[i].connection.append(connection)
      cyclones[i].shift.append(shift)
      cyclones[i].distance.append(dist)


def place_event(Ncyclones, effective_distance, cyclones, current_time,time_offset):
  global order
  week = 56
  effective_distance = 1500.0
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
                and cyclones[j].start_time <= current_time):
                min_distance.append(cyclones[j].distance[i])
            elif cyclones[j].shift[i] == 0:
              min_distance.append(cyclones[j].distance[i])
            else:            
              min_distance.append(0)

          else:            
            min_distance.append(0)
          if cyclones[j].start_time > current_time:
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
     
        # Add custom made offset (time_offset2)
        # to remove it move time_offset2 to time_offset and comment for loop
        # 8 is 24 hours
        dist_min = []
        dist_min.append(effective_distance)

        for j in range(0, Ncyclones):
          if (current_time-8 <= cyclones[j].start_time+max(cyclones[j].times) <= current_time):
            lat2 = cyclones[j].lats[len(cyclones[j].lats)-1] 
            lon2 = cyclones[j].lons[len(cyclones[j].lons)-1] 
            dist_min.append(distance((cyclones[i].lats[0],cyclones[i].lons[0]), (lat2,lon2)).km)  

        if min(dist_min) >= effective_distance:
          time_offset2 = time_offset
        else:
          time_offset2 = int(8*(1-min(dist_min)/effective_distance))
          
        cyclones[i].start_time = current_time + time_offset2
        placed_cyclone = True


def tstepping(Ncyclones, cyclones, Nfiles):
  week = 56
  yr = 52 * week

  for current_time in range(0, 1000*week):
    n = 0
    # First check whether we have any cyclone left to be run
    active_cyclones = 0
    for j in range(0, Ncyclones):
      if cyclones[j].status == -1 or cyclones[j].status == 0:
        active_cyclones += 1
    if active_cyclones == 0:
      print('timing_parallel', current_time)
      break

    # Go over cyclones for checking status
    for i in range(0, Ncyclones):

      if cyclones[i].status == 0 and (cyclones[i].start_time +  \
         max(cyclones[i].times)) == current_time:
        # Wait for offset time before changing to finished
        cyclones[i].status = 2 # start of spinup

      if cyclones[i].status == 2 and (cyclones[i].start_time +  \
         max(cyclones[i].times) + time_offset == current_time):
        cyclones[i].status = 1
      if cyclones[i].status == 0 or cyclones[i].status == 2:
        n += 1
    print(n)
    #------ FIND NEW CYCLONE------
    if n < Nfiles:
      place_event(Ncyclones, effective_distance, cyclones, current_time,time_offset)


def write_new_database(Ncyclones, cyclones, basin_name):

   filename = dict()
   out_file = dict()
   counter = numpy.zeros(Nfiles,dtype=int)
   time_list=open("data/starting_times.txt","w+")
   for k in range(0, Nfiles):
     filename[k] = basin_name + str(k) + ".txt"
     out_file[k] = open(filename[k], "w+")

   for i in range(0, Ncyclones):
     for j in range(0, Ncyclones):
       if (cyclones[j].order == i):
         if (cyclones[j].status == 1):
           # Write filenames based on the start time in hours 
           filename2 = "data/cyclone_" + str(cyclones[j].start_time) + ".txt"
           single_out_file = open(filename2, "w+")

           for l in range(0, Nfiles):
             if counter[l] <= cyclones[j].start_time:
               counter[l] = cyclones[j].start_time + max(cyclones[j].times)
               print ('file number', l,'cyclone N',j,'starting time',    \
                      cyclones[j].start_time, 'starting time for next cyclone',counter[l])      
               str_time=str(cyclones[j].start_time)+', '+str(cyclones[j].start_time + len(cyclones[j].times))
               time_list.write(str_time + '\n')
               break

         for k in range(0, len(cyclones[j].times)):

             strn = '2008.0, 1.0, ' + str(j) + ', ' + str(cyclones[j].start_time + \
                    cyclones[j].times[k]) + ', ' + str(cyclones[j].basin) + ', ' + \
                    str(cyclones[j].lats[k]) + ', ' + str(cyclones[j].lons[k]) +   \
                    ', ' + str(cyclones[j].pressure[k]) + ', ' + str(cyclones[j].ws[k]) + \
                    ', ' + str(cyclones[j].radii[k]) + ', ' + str(cyclones[j].category) + \
                    ', ' + str(cyclones[j].landfall) + ', ' + str(cyclones[j].ld[k])

             single_out_file.write(strn + '\n')
             out_file[l].write(strn + '\n')

         single_out_file.close()

   time_list.close()
   for k in range(0,Nfiles):
     out_file[k].close()


#if __name__=="__main__":

def optimization():

  Ncyclones = read_data(filename, cyclones,multiple_basins, pre_selection)
  Ncyclones = 20 # for fast check
  set_distances(Ncyclones, cyclones)
  order = 0

  for i in range(0, Ncyclones):
    if cyclones[i].status == -1:
        cyclones[i].status = 0
        cyclones[i].start_time = 0
        cyclones[i].order = 0
        order += 1
        break

  tstepping(Ncyclones, cyclones, Nfiles)
  write_new_database(Ncyclones, cyclones, basin_name)
  check_distance(Ncyclones, cyclones, basin_name)



