import os
import numpy as np

import dfm_tools as dfmt  # this requires numpy >= 1.22, which requires the 2022 software stack on snellius
import hydrolib.core.dflowfm as hcdfm
import xarray as xr

from datetime import datetime

from omuse.community.delft3d.interface import DFlowFM

from omuse.units import units
from matplotlib import pyplot

start_date="20110130"
start_datetime=datetime.strptime(start_date,"%Y%m%d")
local_bbox = [] # lon_min, lon_max, lat_min, lat_max
tend=4.5 | units.day
dt=(1.| units.hour)

def init_global(start_date):
    d=DFlowFM(ini_file="gtsm_coarse.mdu", coordinates="spherical", redirection="none", workdir="global")
 
    # set parameters
    d.parameters.use_interface_wind=False
    d.parameters.use_interface_patm=False
    d.ini_time.RefDate=start_date
    
    d.ini_external_forcing.ExtForceFile="gtsm_coarse.ext"

    return d


def create_forcing_files(model_name, bbox, course_res, fine_res, bath_file = None, crs = 'EPSG:4326'):
    """
    model_name: str,
    bbox: list, [lon_min, lon_max, lat_min, lat_max]
    course_res: float, course resolution of the grid in degrees 
    fine_res: float, minimal edge length of the refined grid in meters
    bath_file: str, path to the bathymetry file, default: None 
    crs: str, coordinate reference system identifier, default: 'EPSG:4326'
    """
    ## use workdir as model_name and create directories
    dir_output = os.path.abspath(f'./{model_name}')
    os.makedirs(dir_output, exist_ok=True)


    ## from bounding box define the grid extent
    lon_min, lon_max, lat_min, lat_max = bbox
    mk_object = dfmt.make_basegrid(lon_min, lon_max, lat_min, lat_max, dx=course_res, dy=course_res, crs=crs)
    bnd_gdf = dfmt.generate_bndpli_cutland(mk=mk_object, res='h', buffer=0.01)
    bnd_gdf['name'] = f'{model_name}_bnd'
    bnd_gdf_interp = dfmt.interpolate_bndpli(bnd_gdf, res=0.03)
    
    pli_polyfile = dfmt.geodataframe_to_PolyFile(bnd_gdf_interp)
    pli_polyfile.save(os.path.join(dir_output, f'{model_name}.pli'))

    # connect to a coarse version of the GEBCO_2022 dataset on OPeNDAP
    if not bath_file:
        bath_file = f'https://opendap.deltares.nl/thredds/dodsC/opendap/deltares/Delft3D/netcdf_example_files/GEBCO_2022/GEBCO_2022_coarsefac08.nc'
    data_bathy_sel = xr.open_dataset(bath_file).sel(lon=slice(lon_min-1,lon_max+1),lat=slice(lat_min-1,lat_max+1))

    # refine grid and remove land with GSHHS coastlines
    dfmt.refine_basegrid(mk=mk_object, data_bathy_sel=data_bathy_sel, min_edge_size=fine_res)
    dfmt.meshkernel_delete_withcoastlines(mk=mk_object, res='h')

    # convert to xugrid
    xu_grid_uds = dfmt.meshkernel_to_UgridDataset(mk=mk_object, crs=crs)
    # interpolate bathymetry onto the grid
    data_bathy_interp = data_bathy_sel.interp(lon=xu_grid_uds.obj.mesh2d_node_x, lat=xu_grid_uds.obj.mesh2d_node_y).reset_coords(['lat','lon'])
    xu_grid_uds['mesh2d_node_z'] = data_bathy_interp.elevation.clip(max=10)

    # write xugrid grid to netcdf
    xu_grid_uds.ugrid.to_netcdf(os.path.join(dir_output, f'{model_name}_net.nc'))

    # TODO create the .cmp files from template
    cmp_file = os.path.join(dir_output, f'{model_name}_0001.cmp')
    with open(cmp_file, "w") as f:
        f.write(
            """* COLUMNN=3\n
            * COLUMN1=Period (min) or Astronomical Componentname\n
            * COLUMN2=Amplitude (ISO)\n
            * COLUMN3=Phase (deg)\n
            0.0  0.  0.0\n 
            745.0  .0  0.0"""
        )
    return ext_forcing_file

def init_nested(start_date, bbox):
    model_name = "local"
    bbox = [] # lon_min, lon_max, lat_min, lat_max
    d=DFlowFM(ini_file="RF.mdu", coordinates="spherical", redirection="none", workdir="local")

    ext_forcing_file = create_forcing_files(model_name, bbox, 0.05, 300)
    # set parameters
    #~ d.parameters.use_interface_wind=False
    #~ d.parameters.use_interface_patm=False
    d.parameters.use_interface_waterlevel_boundary=True

    d.ini_time.RefDate=start_date
    d.ini_external_forcing.ExtForceFile="RF.ext"

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

def get_bounding_subgrid(grid, bbox=None):
    if bbox:
        lon_min, lon_max, lat_min, lat_max = bbox
    else: 
        lon_min = grid.lon.min()


    return grid[indices]

def get_subgrid_from_pli(grid, pli_file):
    pass


def find_matching_subgrid(grid, sub, names=["lon","lat"]):
    indices=[]
    for s in sub:
      d=(getattr(s, names[0])-grid.lon)**2+(getattr(s, names[1])-grid.lat)**2
      indices.append(np.argmin(d.number))
    indices=np.array(indices)
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
    
    nested.stop()
    gtsm.stop()
  

