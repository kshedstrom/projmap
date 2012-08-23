import ConfigParser
import json
import os

import numpy as np
import pylab as pl
from mpl_toolkits.basemap import Basemap

class Projmap(Basemap):
    def __init__(self,region, **kwargs):
        """Init basemap instance using data from config files"""
        self.basedir =  os.path.dirname(os.path.abspath(__file__))
        self.region = region
        self.inkwargs = kwargs
        self.read_configfile()
        for k,v in self.inkwargs.iteritems():
            self.__dict__[k] = v 
        Basemap.__init__(self, **self.base_kwargs)

    def read_configfile(self):
        """Read and parse the config file"""
        cfg = ConfigParser.ConfigParser()

        def openfile(fname):
            self.map_regions_file = fname
            cfg.read(fname)

        openfile(os.curdir + "/map_regions.cfg")
        if not self.region in cfg.sections():
            openfile(os.path.expanduser("~") + "/.map_regions.cfg")
            if not self.region in cfg.sections():
                openfile(self.basedir + "/map_regions.cfg")
                if not self.region in cfg.sections():
                    raise NameError('Region not included in config file')

        self.base_kwargs = {}
        def splitkey(key, val):
            if "base." in key:
                basekey = key[5:]
                if basekey in self.inkwargs.keys():
                    self.base_kwargs[basekey] = self.inkwargs[basekey]
                    del self.inkwargs[basekey]
                else:
                    self.base_kwargs[basekey] = val
            elif "proj." in key:
                selfkey = key[5:]
                if selfkey in self.inkwargs.keys():
                    self.__dict__[selfkey] = self.inkwargs[selfkey]
                    del self.inkwargs[selfkey]
                else:
                    self.__dict__[selfkey] = val
            else:
                print "Unknown option: " + key
                print "Remember to prefix options with base or self"

        for key,val in cfg.items(self.region):
            try:
                splitkey(key, json.loads(val))
            except ValueError:
                splitkey(key, val)



    def nice(self,latlabels=True,lonlabels=True):
        """ Draw land, parallells and meridians on a map"""
        if latlabels == True:
            latlabels = [1,0,0,0]
        elif latlabels == False:
            latlabels = [0,0,0,0]
            
        self.fillcontinents(color=[0.6,0.6,0.6],
                            lake_color=[0.9,0.9,0.9])
        if len(self.merid)>0:
            self.drawmeridians(self.merid,
                               color='k',
                               fontsize=20,linewidth=2,
                               labels=[0,0,0,0],
                               dashes=[1,5],zorder=1)
        if len(self.paral)>0:
            self.drawparallels(self.paral,
                               color='k',
                               fontsize=20,linewidth=2,
                               labels=latlabels,
                               labelstyle="+/-",
                               dashes=[1,5],zorder=1)
        if hasattr(self,'scale_lon'):
            self.drawmapscale(-69.6,43.35,-69.6,43.35,25)

    def rectangle(self,lon1,lat1,lon2,lat2,c='0.3',shading=None, step=100):
        """Draw a rectangle on the map and respect the projection.""" 
        class pos:
            x = np.array([])
            y = np.array([])

        def line(lons, lats):
            x,y = self(lons, lats)
            self.plot(x,y,c=c)
            pos.x = np.hstack((pos.x,x))
            pos.y = np.hstack((pos.y,y))

        line([lon1]*step, np.linspace(lat1,lat2,step))
        line(np.linspace(lon1,lon2,step), [lat1]*step)
        line([lon2]*step, np.linspace(lat2,lat1,step))
        line(np.linspace(lon2,lon1,step), [lat2]*step)
        if shading:
            p = pl.Polygon(zip(pos.x, pos.y),facecolor=shading, edgecolor=c,
                           alpha=0.5,linewidth=1)
            pl.gca().add_patch(p)

    def fronts(self,lglon=36, dlon=5, ax=None):
        """Plot fronts in the Southern Ocean """
        frontdir = self.basedir + "/data/"
        
        def plotfront(frontFile,fname, lon):
            frmat = np.genfromtxt(frontFile)
            mask = frmat[:,0] < -180 + self.merid_offset  
            frmat[mask, 0] = frmat[mask, 0] + 360 
            mask = ~(frmat[:,0] < np.nanmax(frmat[:,0]))
            x,y = self(frmat[:,0],frmat[:,1])
            x[mask] = np.nan
            y[mask] = np.nan
            self.plot(x, y, color=self.frontcolor, lw=self.frontwidth,zorder=2)

            latpos = np.nonzero(frmat[:,0] > lon)[0].min()
            xp,yp = self(lon,frmat[latpos,1])
            if ax:
                ax.text(xp,yp,fname,va='top',size='medium',
                        bbox=dict(facecolor='w', alpha=0.7,lw=0))
                ax.text(xp,yp,fname,va='top',size='medium')
            else:
                pl.text(xp,yp,fname,va='top',size='medium',
                        bbox=dict(facecolor='w', alpha=0.7,lw=0))
                pl.text(xp,yp,fname,va='top',size='medium',)
                
        plotfront(frontdir + 'saf.txt','saf', lglon)
        plotfront(frontdir + 'stf.txt','stf', lglon+dlon)
        #plotfront(frontdir + 'saccf.txt','saccf')
        plotfront(frontdir + 'pf.txt','pf', lglon+2*dlon)
        #plotfront(frontdir + 'sbdy.txt','sbdy')

    def text(self, lon, lat, text, **kwargs):
        x,y = self(lon,lat)
        pl.text(x ,y, text, **kwargs)
  
    def hrzbar(self):
        pl.colorbar(orientation='horizontal',pad=0, aspect=40,
                 fraction=0.0244)
