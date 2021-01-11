from omuse.ext.hurricane_models import HollandHurricane
from omuse.units import units


class List_Forcings:
    ambient_pressure=1013 | units.mbar
    def __init__(self,nodes,links):
        self.internal_list={}  # should be changed to list of classes
        self.nodes=nodes.copy()
        self.links=links.copy()
        self.Nforcings=0 
        self.nodes.pressure=  self.ambient_pressure
        self.links.vx=0 | units.m/units.s
        self.links.vy=0 | units.m/units.s
 
    def add_elements(self):
        order=0
        time_list=open("data/starting_times.txt")

        for line in time_list:
            fields=line.strip().split(',')
            start_time=float(fields[0])*3600 | units.s
            end_time=float(fields[1])*3600 | units.s
            filename="data/cyclone_"+str(int(float(fields[0])))+".txt"
            self.internal_list[order]=TC_forcing(self.nodes,self.links,   \
                                      start_time,end_time,filename)
            self.internal_list[order].filename=filename
            order+=1
        self.Nforcings=order-1


    def evolve(self,tend):
        #Set all values to 
        Nactive=0
        self.nodes.pressure=  self.ambient_pressure
        self.links.vx=0 | units.m/units.s
        self.links.vy=0 | units.m/units.s
        for i in range(0,self.Nforcings):
            self.internal_list[i].evolve_model(tend)
        #Here we should go over all forcings and make a summation
            if self.internal_list[i].active==True:
               self.nodes.pressure+=self.internal_list[i].nodes.pressure
               self.links.vx+=self.internal_list[i].links.vx
               self.links.vy+=self.internal_list[i].links.vy
               Nactive+=1
            self.nodes.pressure=self.nodes.pressure-Nactive*self.ambient_pressure


class TC_forcing(object):
    def __init__(self, nodes, links, tstart, tend, filename):
        self._vmodel=HollandHurricane(links, storm_file=filename)
        self._pmodel=HollandHurricane(nodes, storm_file=filename)
        self.links=self._vmodel.nodes
        self.nodes=self._pmodel.nodes
        self._tstart=tstart
        self._tend=tend
        self.active=True
        self.filename=filename

    def evolve_model(self,tend):
        self.tmodel = tend
        if (self.tmodel < self._tstart or self.tmodel > self._tend):
            self.nodes=None
            self.links=None
            self.active=False
        else:
            self.links=self._vmodel.nodes
            self.nodes=self._pmodel.nodes
            self.active=True

        self._vmodel.evolve_model(tend) 
        self._pmodel.evolve_model(tend) 
