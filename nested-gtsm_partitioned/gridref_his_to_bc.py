import os
import xarray as xr
from pathlib import Path
import pandas as pd
from scipy.spatial import KDTree
import numpy as np
import matplotlib.pyplot as plt
plt.close('all')
import contextily as ctx
import dfm_tools as dfmt
import hydrolib.core.dflowfm as hcdfm
import sys

model_name = sys.argv[1]

file_pli_list = [Path(f'/projects/0/einf2224/TCM/nested-gtsm_partitioned/local_{model_name}/{model_name}.pli'),]
                 #Path(r'p:\i1000668-tcoms\03_newModel\01_input\02_bnd\pli\PacificOcean.pli'),
                 #Path(r'p:\i1000668-tcoms\03_newModel\01_input\02_bnd\pli\SeaOfJapan.pli'),
                 #Path(r'p:\i1000668-tcoms\03_newModel\01_input\02_bnd\pli\TorresStrait.pli'),]
                 
#NESTING PART 2
for file_pli in file_pli_list:
    kdtree_k = 4
    file_his = f'/projects/0/einf2224/TCM/nested-gtsm_partitioned/global_{model_name}/output/omuse_0000_his.nc'
    #file_his = f'/projects/0/einf2224/paper1/scripts/case_studies/{model_name}/no_omuse/holland_GR/global_{model_name}/output/gtsm_fine_0000_his.nc'
    data_xr_his = xr.open_mfdataset(file_his,preprocess=dfmt.preprocess_hisnc)
    data_xr_his_selvars = data_xr_his[['waterlevel']]#,'velocity_magnitude']]
    
    data_interp = dfmt.interp_hisnc_to_plipoints(data_xr_his=data_xr_his_selvars,file_pli=file_pli,kdtree_k=kdtree_k)
    #fig,ax = plt.subplots()
    #data_interp.waterlevel.drop_vars('plipoints').T.plot(ax=ax) 
    
    rename_dict = {'waterlevel':'waterlevelbnd'}#,
    data_interp=data_interp.rename(rename_dict)
    
    #make all waterlevels to 0
    data_interp['waterlevelbnd'][:] = 0
    
    ForcingModel_object = dfmt.plipointsDataset_to_ForcingModel(plipointsDataset=data_interp)
    file_bc_out=f'/projects/0/einf2224/TCM/nested-gtsm_partitioned/local_{model_name}/{model_name}_waterlevel_global.bc'
    
    print('saving bc file')
    ForcingModel_object.save(filepath=file_bc_out) #TODO REPORT: writing itself is fast, but takes quite a while to start writing (probably because of conversion)
    print('done')
