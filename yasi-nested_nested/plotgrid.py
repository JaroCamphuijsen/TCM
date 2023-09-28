import numpy

from omuse.community.delft3d.interface import DFlowFM
from omuse.units import units

from matplotlib import pyplot
from matplotlib import tri

from netCDF4 import Dataset

kwargs=dict(redirection="none", ini_file="RF.mdu", channel_type="sockets")
#~ kwargs=dict(redirection="none", ini_file="westerscheldt.mdu", channel_type="sockets", debugger="gdb" )
#~ kwargs=dict(ini_file="westerscheldt.mdu", )

def read_pli(filename):
  f=open(filename, "r")
  
  tag =f.readline()
  npoints,ndim=f.readline().split()

  coords=[]  
  for i in range(int(npoints)):
    coords.append([float(x) for x in f.readline().split()])
  
  return numpy.array(coords)

def read_nc(filename):
  d=Dataset(filename,'r')
  x=d["NetNode_x"][:]
  y=d["NetNode_y"][:]
  return x,y

def plot_points_and_net():

  d=DFlowFM(**kwargs)
  
  print(d.data_store_names())
  boundary=read_pli("forcing/testbc.pli")
  xb=boundary[:,0]
  yb=boundary[:,1]

  x=d.flow_nodes.x.number
  y=d.flow_nodes.y.number
  pyplot.plot(x,y,'ro')
  
  x=d.boundary_nodes.x.number
  y=d.boundary_nodes.y.number
  pyplot.plot(x,y,'bp')

  x=d.net_nodes.x
  y=d.net_nodes.y
  pyplot.plot(x,y,'k.')

  x,y=read_nc("test.nc")
  pyplot.plot(x,y,'k+')


  pyplot.plot(xb,yb,'y', lw=2)

      
  pyplot.show()

if __name__=="__main__":
    #~ plot_evolve()
    plot_points_and_net()
    #~ plot_points()
