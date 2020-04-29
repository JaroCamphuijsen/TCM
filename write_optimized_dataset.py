import sys
import numpy
from omuse.units import units
from visualisation import read_data,set_distances
from visualisation import place_events_initial, place_event

filename = sys.argv[1]  # input file with list of cyclones
start_line = int(sys.argv[2]) # line to start reading cyclones
multiple_basins = False
effective_distance = 1500 | units.km
time_offset = 2*8 #  8 is one day
Nfiles = 4

Ncyclones = 0
cyclones=dict()

def write_new_database(Ncyclones, cyclones):

   filename = dict()
   out_file = dict()
   counter = numpy.zeros(4,dtype=int)

   for k in range(0, Nfiles):
     filename[k] = "WP_" + str(k) + ".txt"
     out_file[k] = open(filename[k], "w+")

   for i in range(0, Ncyclones):

     if (cyclones[i].status == 1):

       # Write filenames based on the start time in hours 
       filename2 = "cyclone_" + str(cyclones[i].start_time*3) + ".txt"
       single_out_file = open(filename2, "w+")
       
       for k in range(0, Nfiles):
         if counter[k] <= cyclones[i].start_time*3:
           counter[k] = cyclones[i].start_time*3 + max(cyclones[i].times)*3
           print (k,counter[k])
           break

       for j in range(0, len(cyclones[i].times)):
 
         strn = str(cyclones[i].yr) + ', ' + str(cyclones[i].month) + ', ' +    \
                str(i) + ', ' + str(cyclones[i].start_time + cyclones[i].times[j]) + ', ' +  \
                str(cyclones[i].basin) + ', ' + str(cyclones[i].lats[j]) + ', ' + \
                str(cyclones[i].lons[j]) + ', ' + str(cyclones[i].pressure[j]) + ', ' + \
                str(cyclones[i].ws[j]) + ', ' + str(cyclones[i].category) + ', ' + \
                str(cyclones[i].landfall) + ', ' + str(cyclones[i].ld[j])

         single_out_file.write(strn + '\n')
         out_file[k].write(strn + '\n')

       single_out_file.close()


   for k in range(0,Nfiles):
     out_file[k].close()


def tstepping(Ncyclones, cyclones):
  week = 56
  yr = 52 * week

  for current_time in range(0, 1000*week):
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
    #------ FIND NEW CYCLONE------
    place_event(Ncyclones, effective_distance, cyclones, current_time)



if __name__=="__main__":
  Ncyclones = read_data(filename, cyclones,multiple_basins)
  Ncyclones = 50 # for fast check
  set_distances(Ncyclones, cyclones)
  place_events_initial(Ncyclones, effective_distance, cyclones)
  tstepping(Ncyclones, cyclones)
  write_new_database(Ncyclones, cyclones)
