import os
import numpy

from datetime import datetime

from omuse.community.delft3d.interface import DFlowFM, Partitioner

from omuse.units import units
from matplotlib import pyplot

start_date="20110130"
start_datetime=datetime.strptime(start_date,"%Y%m%d")
tend=4.5 | units.day
dt=(1.| units.hour)

def init_global(start_date):
    # partition
    #p=Partitioner(redirection="none")
    #p.parameters.generate_polygon_file=1
    #p.parameters.number_of_subdomains=2
    #print(p.parameters)
    #p.parameters.filename="/projects/0/einf2224/TCM/nested-gtsm_partitioned_coarse/global/step11_global_net.nc"
    #p.do_partition()

    # initiate GTSM model
    d=DFlowFM(number_of_workers=2, ini_file="gtsm_coarse.mdu", coordinates="spherical", redirection="none", workdir="/projects/0/einf2224/TCM/nested-gtsm_partitioned_coarse/global")
    
    # set parameters
    d.parameters.use_interface_wind=False
    d.parameters.use_interface_patm=False
    d.ini_time.RefDate=start_date
    
    d.ini_external_forcing.ExtForceFile="gtsm_coarse.ext"
    d.ini_geometry.PartitionFile="step11_global_part.pol"
    d.ini_numerics.Icgsolver=6

    return d

def init_nested(start_date):
    # partition
    p=Partitioner(redirection="none")
    p.parameters.generate_polygon_file=1
    p.parameters.number_of_subdomains=2
    p.parameters.filename="/projects/0/einf2224/TCM/nested-gtsm_partitioned_coarse/local/test_net.nc"
    p.do_partition()
    
    # initiate GTSM model
    d=DFlowFM(number_of_workers=2, ini_file="RF.mdu", coordinates="spherical", redirection="none", workdir="/projects/0/einf2224/TCM/nested-gtsm_partitioned_coarse/local")
 
    # set parameters
    #~ d.parameters.use_interface_wind=False
    #~ d.parameters.use_interface_patm=False
    d.parameters.use_interface_waterlevel_boundary=True

    d.ini_time.RefDate=start_date
    d.ini_external_forcing.ExtForceFile="RF.ext"
    d.ini_geometry.PartitionFile="test_part.pol"
    d.ini_numerics.Icgsolver=6

    return d

def evolve_single(d, tend,dt):
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
        print("evolved to" +str(d.model_time.in_(units.day)))
        
        # update plot
        f.clf()
        z=d.flow_nodes.water_level.value_in(units.m)
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
            
def plot_waterlevel(nodes, n, label="", title=""):
    x=nodes.lon.value_in(units.deg)
    y=nodes.lat.value_in(units.deg)
    f=pyplot.figure()
            
    z=nodes.water_level.value_in(units.m)
    p=pyplot.scatter(x,y,c=z, cmap="jet", s=1., vmin=-.5, vmax=.5)
    pyplot.xlim(110, 170)
    pyplot.ylim(-50,0)
    pyplot.xlabel("lon (deg)")
    pyplot.ylabel("lat (deg)")
    pyplot.title(title)
    f.colorbar(p)    
    pyplot.savefig(label+"waterlevel-%6.6i.png"%n)

def plot_compare(nodes1, nodes2, n, title=""):
    f=pyplot.figure()
            
    z1=nodes1.water_level.value_in(units.m)
    z2=nodes2.water_level.value_in(units.m)
    p=pyplot.plot(z1,z2, 'r+')
    pyplot.xlim(-2,2)
    pyplot.ylim(-2,2)
    pyplot.xlabel("waterlevel 1 (m)")
    pyplot.ylabel("waterlevel 2 (m)")
    pyplot.title(title)
    pyplot.savefig("compare_waterlevel-%6.6i.png"%n)

def allplots(nodes1, nodes2, nodes1b, n, title=""):
    f,axs=pyplot.subplots(1,3, figsize=(12,4))
            
    x1=nodes1.lon.value_in(units.deg)
    y1=nodes1.lat.value_in(units.deg)
    z1=nodes1.water_level.value_in(units.m)

    x2=nodes2.lon.value_in(units.deg)
    y2=nodes2.lat.value_in(units.deg)
    z2=nodes2.water_level.value_in(units.m)
    
    z1b=nodes1b.water_level.value_in(units.m)

    im1=axs[0].scatter(x1,y1,c=z1, cmap="jet", s=1., vmin=-.5, vmax=.5)
    axs[0].set_xlim(110, 170)
    axs[0].set_ylim(-50,0)
    axs[0].set_xlabel("lon (deg)")
    axs[0].set_ylabel("lat (deg)")
    axs[0].set_title(title)
    f.colorbar(im1, ax=axs[0])    

    im2=axs[1].scatter(x2,y2,c=z2, cmap="jet", s=1., vmin=-.5, vmax=.5)
    axs[1].set_xlim(110, 170)
    axs[1].set_ylim(-50,0)
    axs[1].set_xlabel("lon (deg)")
    axs[1].set_ylabel("lat (deg)")
    f.colorbar(im2, ax=axs[1])    

    axs[2].plot(z1b,z2, 'r+')
    axs[2].set_xlim(-2,2)
    axs[2].set_ylim(-2,2)
    axs[2].set_xlabel("waterlevel global (m)")
    axs[2].set_ylabel("waterlevel nested (m)")

    pyplot.tight_layout()

    pyplot.savefig("combined-%6.6i.png"%n)

    pyplot.close(f)



def find_matching_subgrid(grid, sub, names=["lon","lat"]):
    indices=[]
    for s in sub:
      d=(getattr(s, names[0])-grid.lon)**2+(getattr(s, names[1])-grid.lat)**2
      indices.append(numpy.argmin(d.number))
    indices=numpy.array(indices)
    return grid[indices]

def evolve_gtsm_nested(gtsm, nested, tend, dt):

    # fix loose ends on the state model
    print("global flow_nodes:", gtsm.flow_nodes)
    print("local flow_nodes:", nested.flow_nodes)

    # generate subset of the nested grid
    # 
    # boundary_nodes = get_boundary_nodes_subgrid(nested.flow_nodes, bbox)
    # print(boundary_nodes)

    #~ gtsm_boundary_nodes=find_matching_subgrid(gtsm.flow_nodes, nested.boundary_links_forcing, names=["lon_bndz", "lat_bndz"])
    print("local boundary_nodes:", nested.boundary_nodes)
    print("local boundary_nodes latvalues:", nested.boundary_nodes.lat)
    print("local boundary_nodes lonvalues:", nested.boundary_nodes.lon)

    # Select the nodes in the global model that correspond to the boundary of the local model (defined by the forcing files of the deflt3d model)
    gtsm_boundary_nodes=find_matching_subgrid(gtsm.flow_nodes, nested.boundary_nodes)
    
    # Select the nodes in the local model that are at the boundary (defined by the forcing files of the deflt3d model)
    nested_boundary_links_forcing=find_matching_subgrid(nested.flow_links_forcing, nested.boundary_nodes)
    print("global gtsm_boundary_nodes:", gtsm_boundary_nodes)
    print("local nested_boundary_nodes:", nested_boundary_links_forcing)

    # Select the nodes in the global model that are covered by the local model
    gtsm_nested_nodes=find_matching_subgrid(gtsm.flow_nodes, nested.flow_nodes)

    print("global local_flow_nodes:", gtsm_nested_nodes)

    channel=gtsm_boundary_nodes.new_channel_to(nested.boundary_links_forcing)

    # channel=gtsm_boundary_nodes.new_channel_to(nested_boundary_nodes) # testing the local linking with a subgrid of nested.flow_nodes

    print("nested boundary_links_forcing:", nested.boundary_links_forcing)

    n=0
    while gtsm.model_time < tend-dt/2:
        n+=1

        gtsm.evolve_model(gtsm.model_time+dt/2)

        # copy boundary conditions
        channel.copy_attributes(["water_level"])

        nested.evolve_model(nested.model_time+dt)

        gtsm.evolve_model(gtsm.model_time+dt/2)

        print("evolved to " +str(gtsm.model_time.in_(units.day)))

        #~ print(gtsm_boundary_nodes.water_level)
        #~ print(nested.boundary_links_forcing.water_level)
        #~ print(nested.boundary_nodes.water_level)
        #~ input()
        
        assert gtsm.model_time==nested.model_time
        
        time="{0:5.3f} days".format(gtsm.model_time.value_in(units.day))
        #~ plot_waterlevel(gtsm.flow_nodes, n, label="gtsm_", title="gtsm at "+time)
        #~ plot_waterlevel(nested.flow_nodes, n, label="nested_", title="nested at "+time)
        #~ plot_compare(gtsm_nested_nodes, nested.flow_nodes, n, title="gtsm vs nested region, "+time) 
        allplots(gtsm.flow_nodes,nested.flow_nodes, gtsm_nested_nodes,n, title=time)
        
if __name__=="__main__":

    gtsm=init_global(start_date)
    nested=init_nested(start_date)
    
        
    evolve_gtsm_nested(gtsm, nested, tend,dt)
    #evolve_single(gtsm, tend, dt)
    
    nested.stop()
    gtsm.stop()
  

