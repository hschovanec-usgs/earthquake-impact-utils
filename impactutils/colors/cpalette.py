from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

MMI = {'z0':np.arange(0,10),
       'z1':np.arange(1,11),
       'rgb0':[(255,255,255),
               (255,255,255),
               (191,204,255),
               (160,230,255),
               (128,255,255),
               (122,255,147),
               (255,255,0),
               (255,200,0),
               (255,145,0),
               (255,0,0)],
       'rgb1':[(255,255,255),
               (191,204,255),
               (160,230,255),
               (128,255,255),
               (122,255,147),
               (255,255,0),
               (255,200,0),
               (255,145,0),
               (255,0,0),
               (200,0,0)],
        'nan_color':(0,0,0,0)}

POP = {'z0':[0,5,50,100,500,1000,5000,10000],
       'z1':[5,50,100,500,1000,5000,10000,50000],
       'rgb0':[(255,255,255),
               (191,191,191),
               (159,159,159),
               (127,127,127),
               (95,95,95),
               (63,63,63),
               (31,31,31),
               (0,0,0)],
       'rgb1':[(255,255,255),
               (191,191,191),
               (159,159,159),
               (127,127,127),
               (95,95,95),
               (63,63,63),
               (31,31,31),
               (0,0,0)],
       'nan_color':(0,0,0,0)}

PALETTES = {'mmi':MMI,
            'pop':POP}

class ColorPalette(object):
    def __init__(self,name,z0,z1,rgb0,rgb1,nan_color=None):
        """Construct a DataColorMap from input Z values and RGB specs.

        :param name:
          Name of colormap.
        :param z0:
          Sequence of z0 values.
        :param z1:
          Sequence of z1 values.
        :param rgb0:
          Sequence of RGB triplets (values between 0-255).
        :param rgb1:
          Sequence of RGB triplets (values between 0-255).
        :param nan_color:
          Either None or RGBA quadruplet (A is for Alpha, where 
        """
        #validate that lengths are all identical
        if len(z0) != len(z1) != len(rgb0) != len(rgb1):
            raise Exception('Lengths of input sequences to ColorPalette() must be identical.')
        
        z0 = np.array(z0)
        z1 = np.array(z1)
        self._vmin = z0.min()
        self._vmax = z1.max()
        self.nan_color = nan_color

        #change the z values to be between 0 and 1
        adj_z0 = (z0 - self._vmin) / (self._vmax-self._vmin) #should this be z0 - vmin?
        adj_z1 = (z1 - self._vmin) / (self._vmax-self._vmin)

        #loop over the sequences, and construct a dictionary of red, green, blue tuples
        B = -.999*255 #this will mark the y0 value in the first row (isn't used)
        E = .999*255 #this will mark the y1 value in the last row (isn't used)

        #if we add dummy rows to our rgb sequences, we can do one simple loop through.
        rgb0_t = rgb0.copy()
        rgb1_t = rgb1.copy()
        rgb0_t.append((E,E,E)) #append a dummy row to the end of RGB0
        rgb1_t.insert(0,(B,B,B)) #prepend a dummy row to the beginning of RGB1
        x = np.append(adj_z0,adj_z1[-1])#Make the column of x values have the same length as the rgb sequences
        
        cdict = {'red':[],
                 'green':[],
                 'blue':[]}
        
        for i in range(0,len(x)):
            red0 = rgb1_t[i][0]/255.0
            red1 = rgb0_t[i][0]/255.0
            green0 = rgb1_t[i][1]/255.0
            green1 = rgb0_t[i][1]/255.0
            blue0 = rgb1_t[i][2]/255.0
            blue1 = rgb0_t[i][2]/255.0
            cdict['red'].append((x[i],red0,red1))
            cdict['green'].append((x[i],green0,green1))
            cdict['blue'].append((x[i],blue0,blue1))

        self._cdict = cdict.copy()
        self._cmap = LinearSegmentedColormap(name,cdict)
        self._cmap.set_bad(self.nan_color)

    @classmethod
    def fromPreset(cls,preset):
        """Construct a ColorPalette from one of several preset color maps.

        :param preset:
          String to represent one of the preset color maps (see getPresets()).
        :returns:
          ColorPalette object.
        """
        if preset not in PALETTES:
            raise Exception('Preset %s not in list of supported presets.' % preset)
        z0 = PALETTES[preset]['z0'].copy()
        z1 = PALETTES[preset]['z1'].copy()
        rgb0 = PALETTES[preset]['rgb0'].copy()
        rgb1 = PALETTES[preset]['rgb1'].copy()
        nan_color = PALETTES[preset]['nan_color']
        return cls(preset,z0=z0,z1=z1,rgb0=rgb0,rgb1=rgb1,nan_color=nan_color)

    @classmethod
    def getPresets(cls):
        """Get list of preset color palettes.

        :returns:
          List of strings which can be used with fromPreset() to create a ColorPalette.
        """
        return PALETTES.keys()

    @classmethod
    def fromFile(cls,filename):
        """Load a ColorPalette from a file.

        ColorPalette files should be formatted as below:
        --------------------------------------------
        #This file is a test file for ColorPalette.
        #Lines beginning with pound signs are comments.
        #Lines beginning with pound signs followed by a "$" are variable definition lines.
        #For example, the following line defines a variable called nan_color.
        #$nan_color: 0,0,0,0
        #$name: test
        Z0 R0  G0  B0  Z1  R1  G1  B1
        0   0   0   0   1  85  85  85
        1  85  85  85   2 170 170 170
        2 170 170 170   3 255 255 255 
        --------------------------------------------

        These files contain all the information needed to assign colors to any data value.
        The data values are in the Z0/Z1 columns, the colors (0-255) are in the RX/GX/BX columns.
        In the sample file above, a data value of 0.5 would be assigned the color (42.5/255,42.5/255,42.5/255).
        
        :param filename:
          String file name pointing to a file formatted as above.
        :returns:
          ColorPalette object.
        """
        nan_color = (0,0,0,0)
        name = 'generic'
        f = open(filename,'rt')
        for line in f.readlines():
            if line.startswith('#$nan_color'):
                parts = line[2:].split(':')
                value = parts[1].split(',')
                colortuple = tuple([int(xpi) for xpi in value])
                nan_color = colortuple
            elif line.startswith('#$nan_color'):
                parts = line[2:].split(':')
                name = parts[1].strip()
        f.close()
        df = pd.read_table(filename,comment='#',sep='\s+',header=0)
        rgb0 = list(zip(df.R0,df.G0,df.B0))
        rgb1 = list(zip(df.R1,df.G1,df.B1))
        return cls(name=name,z0=df.Z0,z1=df.Z1,rgb0=rgb0,rgb1=rgb1,nan_color=nan_color)

    @property
    def vmin(self):
        """Property accessor for vmin.

        :returns:
          Minimum data value for ColorPalette.
        """
        return self._vmin

    @vmin.setter
    def vmin(self, value):
        """Property setter for vmin.

        :param value:
          Float data value to which vmin should be set.
        """
        self._vmin = value

    @property
    def vmax(self):
        """Property accessor for vmax.

        :returns:
          Maximum data value for ColorPalette.
        """
        return self._vmax

    @vmax.setter
    def vmax(self, value):
        """Property setter for vmax.

        :param value:
          Float data value to which vmax should be set.
        """
        self._vmax = value

    @property
    def cmap(self):
        """Property accessor for the Matplotlib colormap contained within the ColorPalette object.

        :returns:
          Matplotlib colormap object.
        """
        return self._cmap

    def getDataColor(self,value):
        """Get the RGB color associated with a given data value.

        :param value:
          Data value for which color should be retrieved.
        :returns:
          The color value associated with the input data value.
        """
        normvalue = (value - self.vmin) / (self.vmax - self.vmin)
        return self.cmap(normvalue)

        
        