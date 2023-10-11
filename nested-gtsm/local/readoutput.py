from netCDF4 import Dataset

from matplotlib import pyplot

d=Dataset("output/omuse_map.nc")

print(d)




print(d.variables)

x=d["FlowElem_xcc"][:]
y=d["FlowElem_ycc"][:]
z=d["s1"][19,:]

print(x.shape)

print(z.shape)


f=pyplot.figure()

pyplot.scatter(x,y,c=z, cmap="jet", s=1., vmin=-2.5, vmax=2.5)
pyplot.xlabel("lon (deg)")
pyplot.ylabel("lat (deg)")
pyplot.show()

    
d.stop()
