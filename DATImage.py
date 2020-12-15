# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 15:33:38 2020
Image module for Elmitec .dat format image file 
from MAXPEEM of MAX IV Laboratory

Author: Lin Zhu
Email: lin.zhu@maxiv.lu.se
"""

import struct
import numpy as np
import scipy.ndimage
import sys
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import xarray as xr

class DATImage:
    """Import Elmitec dat format file containning image and metadata.
    Return an intance of DATImage class.

    Attributes:
        data(np.array): 2D np.array saves the image.
        metadata(dict): A dictionary saves the all metadata.

    Methods:
        filterInelasticBkg(self, sigma=15): Filter inelastic background.
        display_image(self): Display the image.
        image2xarray(self): convert image and metadata to xarray.
            
    Example:
        im = DATImage('../testfiles/LEEM.dat')
        im.data # show the 2D np.array image.
        im.metadata # show the metadata in form of dictionary.
    """

    def __init__(self, filename, *args, **key_args):

        self.filename = filename
        self.metadata = {}
        logging.info('---------------------------------------------------')
        logging.info('FILE:\t{}'.format(self.filename))
        logging.info('---------------------------------------------------')
        self._load_file() # open file and read the metadata.
        logging.info('---------------------------------------------------')

    def _load_file(self):
        """Read metadata and image data from file.
        """

        def convert_ad_timestamp(timestamp):
            """Convert date and time value to datetime object.
            
            Args:
                timestamp(int): date and time value of this image.
                this value represents the number of 100-nanosecond units since
                the beginning of January 1, 1601.
                
            Returns:
                datetime: timestamp in form of datetime type.
            """
            epoch_start = datetime(year=1601, month=1, day=1)
            seconds_since_epoch = timestamp/10**7
            return epoch_start + timedelta(seconds=seconds_since_epoch)

        def read_field(header, current_position):
            """Read data fields formatted by
            "address-name(str)-unit(ASCII digit)-0-value(float)".
            
            Args: 
                header(Byte): Image header contains metadata
                current_position(int): Number of position for the metadata's 
                    name.
                    
            returns:
                tuple: (name, units_dict[unit_tag], val, offset) 
            """
            units_dict = ('', 'V', 'mA', 'A', '°C', ' K', 'mV', 'pA', 'nA', 
                          '\xb5A')
            temp = header[current_position+1:].split(b'\x00')[0]
            name = temp[:-1].decode('cp1252')
            if sys.version_info[0] > 2:
                unit_tag = int(chr(temp[-1]))
            else:
                unit_tag = int(temp[-1])
            val = struct.unpack('<f', header[position + len(temp)
                                + 2:position + len(temp) + 6])[0]
            offset = len(temp) + 5  # length of entire field
            return name, units_dict[unit_tag], val, offset

        def read_varian(header, current_position):
            """
            Read data fields for varian vacuum pressure gauges and return the 
            metadata.
            
            Args: 
                header(Byte): Image header contains metadata
                current_position(int): Number of position for the metadata's 
                    name.                
            """
            temp_1 = header[current_position+1:].split(b'\x00')[0]
            temp_2 = header[current_position+1:].split(b'\x00')[1]
            str_1 = temp_1.decode('cp1252')  # Name
            str_2 = temp_2.decode('cp1252')  # Unit
            val = struct.unpack('<f', header[position+len(temp_1)+len(temp_2)
                                + 3:position+len(temp_1)+len(temp_2)+7])[0]
            offset = len(temp_1)+len(temp_2)+6  # length of entire field
            logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(header[current_position],
                         str_1+':', val, str_2))
            return str_1, str_2, val, offset

        # open file and read header contents
        with open(self.filename, 'rb') as f:

            self.metadata['id'] = f.read(20).split(b'\x00')[0]
            self.metadata['size'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['version'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['bitsperpix'] = struct.unpack('<h', f.read(2))[0]

            f.seek(6,1)  # for alignment
            f.seek(8,1)  # spare

            self.metadata['width'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['height'] = struct.unpack('<h', f.read(2))[0]
            logging.info('\tDimensions:\t {} x {}'.format(
                self.metadata['width'], self.metadata['height']))
            self.noimg = struct.unpack('<h', f.read(2))[0]
            attachedRecipeSize = struct.unpack('<h', f.read(2))[0]
            self.metadata['attachedRecipeSize'] = attachedRecipeSize

            f.seek(56,1)  # spare

            # read recipe if there is one
            if attachedRecipeSize:
                self.metadata['recipe'] = f.read(attachedRecipeSize)
                f.seek(128-attachedRecipeSize, 1)

            # read first block of image header
            self.metadata['isize'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['iversion'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['colorscale_low'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['colorscale_high'] = struct.unpack('<h', f.read(2))[0]

            self.metadata['timestamp'] = convert_ad_timestamp(struct.unpack('<Q', f.read(8))[0])
            logging.info('\tTime Stamp:\t{}'.format(
                  self.metadata['timestamp'].strftime("%Y-%m-%d %H:%M:%S")))
            self.metadata['mask_xshift'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['mask_yshift'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['usemask'] = f.read(1)

            f.seek(1,1)  # spare

            self.metadata['att_markupsize'] = struct.unpack('<h', f.read(2))[0]
            self.metadata['spin'] = struct.unpack('<h', f.read(2))[0]
            self.versleemdata = struct.unpack('<h', f.read(2))[0]

            logging.info('\tCOLLECTING META DATA:\t')
            # read second block of image header into byte sequence
            #      -     usually block of 256 bytes
            #     -     if too many metadata are stored, 388 empty bytes
            #        followed by number given in versleemdata
            if self.versleemdata == 2:
                img_header = f.read(256)
            else:
                f.seek(388,1)
                img_header = f.read(self.versleemdata)
                
            position = 0
            
            #### DEBUG ####
            logging.debug('type(img_header) = {}'.format(type(img_header)))
            ###############
            b_iter = iter(img_header)
            # data_fields with standard format in MAXPEEM 
            known_tags = [210,203,185,208,215,184,169,222,136,137,133,134,138,
                          135,132,143,144,206,172,147,171,145,146,148,168,130,
                          131,158,159,128,129,161,162,211,163,149,187,177,178,
                          180,181,202,190,191,194,195,196,214,198,199,182,179,
                          200,201,176,197,192,213,209,183,186,212,164,165,140,
                          141,11,160,150,151,153,154,156,157,152,155,173,174,
                          205,204,188,189,175,162,170,142,207,219,39,38]

            # 235: COL, 236:Gauge 3, 237:PCH, 106:MCH
            gauge_tags = [106, 235, 236, 237] 
            for b in b_iter:
                if sys.version_info[0] < 3:
                    b = ord(b)
                #### DEBUG ####
                logging.debug('b = {}'.format(b))
                ###############
                
                # stop when reaching end of header
                if b == 255:
                    break
                    
                # Data fields with standard format
                elif b in known_tags:
                    [fieldname, unit, value, offset] = read_field(img_header, position)
                    self.metadata[fieldname] = [value, unit]
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        b, fieldname+':', value, unit))
                        
                # Camera Exposure and average images
                # Average Images = 0 : No Averaging
                # Average Images = 255 : Sliding Averaging
                elif b == 104:
                    self.metadata['Camera Exposure'] = [struct.unpack('<f', img_header[position+1:position+5])[0], 's']
                    self.metadata['Average Images'] = img_header[position+5]
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        b, 'Camera Exposure:',
                        self.metadata['Camera Exposure'][0],
                        self.metadata['Camera Exposure'][1]))
                    
                    if self.metadata['Average Images'] == 0:
                        logging.info('\t{:>3}\t{:<18}\t{:d} {}'.format(
                            '', 'Average Images:',
                            self.metadata['Average Images'],
                            '\t=> No Averaging'))
                        
                    elif self.metadata['Average Images'] == 255:
                        logging.info('\t{:>3}\t{:<18}\t{:d} {}'.format(
                            '', 'Average Images:',
                            self.metadata['Average Images'],
                            '\t=> Sliding Average'))
                    else:
                        if sys.version_info[0] > 2:
                            logging.info('\t{:>3}\t{:<18}\t{:g}'.format(
                                '', 'Average Images:',
                                self.metadata['Average Images']))
                        else:
                            logging.info('\t{:>3}\t{:<18}\t{:g}'.format(
                                         '', 'Average Images:',
                                         ord(self.metadata['Average Images'])))
                    offset = 6
                    
                # Pressure Gauges
                elif b in gauge_tags:
                    [pressure_gauge, unit, pressure, offset] = \
                        read_varian(img_header, position)
                    self.metadata[pressure_gauge] = [pressure, unit]
                    
                # Image Title
                elif b == 233:
                    temp = img_header[position+1:].split(b'\x00')[0]
                    self.metadata['Image Title'] = temp.decode('cp1252')
                    logging.info('\t{:>3}\t{:<18}\t{}'.format(
                        b, 'Image Title:', self.metadata['Image Title']))
                    offset = len(temp) + 1
                    
                # MCP screen    
                elif b == 243:
                    self.metadata['MCPscreen'] = [struct.unpack('<f', img_header[position+1:position+5])[0], 'V']
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        b, 'MCPscreen:', self.metadata['MCPscreen'][0], self.metadata['MCPscreen'][1]))
                    offset = 4
                    
                # MCP channel plate
                elif b == 244:
                    self.metadata['MCPchannelplate'] = [struct.unpack('<f', img_header[position+1:position+5])[0], 'V']
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        b, 'MCPchannelplate:', self.metadata['MCPchannelplate'][0],
                        self.metadata['MCPchannelplate'][1]))
                    offset = 4
                    
                # Micrometers(x,y)
                elif b == 100:
                    self.metadata['Mitutoyo X'] = \
                        [struct.unpack('<f', img_header[position+1:position+5])[0], 'mm']
                    self.metadata['Mitutoyo Y'] = \
                        [struct.unpack('<f', img_header[position+5:position+9])[0], 'mm']
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        b, 'Mitutoyo X:', self.metadata['Mitutoyo X'][0],
                        self.metadata['Mitutoyo X'][1]))
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        '', 'Mitutoyo Y:', self.metadata['Mitutoyo Y'][0],
                        self.metadata['Mitutoyo Y'][1]))
                    offset = 8 
                    
                # Mirror state    
                elif b == 242:
                    self.metadata['MirrorState'] = img_header[position+1]
                    logging.info('\t{:>3}\t{:<18}\t{:g}'.format(b, 'MirrorState:', self.metadata['MirrorState']))
                    offset = 2
                    
                # FOV
                elif b == 110:
                    temp = img_header[position+1:].split(b'\x00')[0]
                    fov_str = temp.decode('cp1252')
                    self.metadata['FOV cal. factor'] = \
                        float(struct.unpack('<f', img_header[position+len(temp)+2:position+len(temp)+6])[0])
                        
                    # for LEED images
                    if fov_str[0:4] == 'LEED':
                        self.metadata['LEED'] = True
                        self.metadata['FOV'] = None
                        logging.info('\t{:>3}\t{:<18}\t{}'.format(
                            b, 'Field Of View:', 'LEED'))
                            
                    # for normal images
                    elif fov_str[0:4] == 'none':
                        self.metadata['FOV'] = None
                        logging.info('\t{:>3}\t{:<18}\t{}'.format(
                            b, 'Field Of View:', 'None'))
                    # for PES images
                    elif fov_str[0:8] == 'disp.pl.':
                        self.metadata['FOV'] = None
                        self.metadata['disp_plane'] = True
                        logging.info('\t{:>3}\t{:<18}\t{}'.format(
                            b, 'Field Of View:', 'disp.pl.'))                        
                    else:
                        self.metadata['LEED'] = False
                        try:
                            self.metadata['FOV'] = [float(fov_str.split('\xb5m')[0]), '\xb5m']
                            logging.info('\t{:>3}\t{:<18}\t{} {}'.format(
                                b, 'Field Of View:',
                                self.metadata['FOV'][0],
                                self.metadata['FOV'][1]))
                        except ValueError:
                            logging.error('FOV field tag: not known string detected: {}'.format(fov_str))
                    logging.info('\t{:>3}\t{:<18}\t{}'.format('','FOV cal. factor:',self.metadata['FOV cal. factor']))
                    offset = len(temp)+5
                    
                # FOV rotation from LEEM presets
                elif b == 113:
                    self.metadata['Rotation'] = \
                        [struct.unpack('<f', img_header[position+1:position+5])[0], 'degree']
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        b, 'Rotation:', self.metadata['Rotation'][0], self.metadata['Rotation'][1]))
                    offset = 4
                # Spin up or down    
                elif b == 240:
                    self.metadata['Spin up_down'] = img_header[position+1]
                    logging.info('\t{:>3}\t{:<18}\t{:g}'.format(b, 'Spin up_down:', self.metadata['Spin up_down']))
                    offset = 2
                
                # Theta and Phi
                elif b == 239:
                    self.metadata['Theta'] = \
                        [struct.unpack('<f', img_header[position+1:position+5])[0], 'degree']
                    self.metadata['Phi'] = \
                        [struct.unpack('<f', img_header[position+5:position+9])[0], 'degree']
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        b, 'Theta:', self.metadata['Theta'][0],
                        self.metadata['Theta'][1]))
                    logging.info('\t{:>3}\t{:<18}\t{:g} {}'.format(
                        '', 'Phi:', self.metadata['Phi'][0],
                        self.metadata['Phi'][1]))
                    offset = 8 
                    
                else:
                    logging.error('ERROR: Unknown field tag {0} at '\
                            'position {1}. This and following data fields might '\
                            'be misinterpreted!'.format(b, position))                    
                # skip byte number given by offset - depending on length of
                # read data field, update position counter
                [next(b_iter) for x in range(offset)]
                position += offset + 1
                
            # Now read image data
            f.seek(-2*self.metadata['height']*self.metadata['width'], 2)
            self.data = np.fromfile(f, dtype=np.uint16, sep='')
            self.data = self.data.reshape(
                [self.metadata['height'], self.metadata['width']])
            # Flip image to get the original orientation
            self.data = np.flipud(self.data)
            
    def filterInelasticBkg(self, sigma=15):
        """Experimental function to remove the inelastic background in
        LEED images. Works like a high-pass filter by subtracting the
        gaussian filtered image.
        
        Args:
            sigma(optional): GaussFilter parameter. Default is 15.
        
        Returns:
            ndarray: Filtered 2D np.ndarray.
        """
        self.data = np.divide(self.data, self.data.max())
        dataGaussFiltered = scipy.ndimage.gaussian_filter(self.data, sigma)
        return self.data - dataGaussFiltered
    
    def display_image(self):
        """
        Display the image using matplotlib.
        
        Returns:
            tuple(fig,ax)
        """
        fig = plt.figure(frameon=False, 
        figsize=(3, 3*self.metadata['height']/self.metadata['width']),
                     dpi=self.metadata['width']/3)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(self.data, cmap='gray',
                  clim=(np.amin(self.data),
                        np.amax(self.data)),
                        aspect='auto')
        plt.show()
        return fig, ax

    def image2xarray(self):
        """Convert image and metadata to xarray and return xarray. The image 
        in the xrarray 'values' attribute. Metadata is in the 'attrs' attribute.
        
        
        """
        
        im_dataarray = xr.DataArray(self.data, 
                                  coords={'height': range(self.metadata['height']),
                                          'width': range(self.metadata['width']),
                                          'time': self.metadata['timestamp']},
                                  dims=['height', 'width'],
                                  name = "Intensity",
                                  attrs = self.metadata
                                  )
        im_dataarray.attrs['unit'] = 'pixel'
        
        return im_dataarray

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
#    logging.basicConfig(level=logging.WARNING)
    
    # for test the 'DATImage' class with different types of .dat files
    im = DATImage('../testfiles/LEEM.dat')
#    im = DATImage('../testfiles/LEED.dat')
#    im = DATImage('../testfiles/PES.dat')
#    im = DATImage('../testfiles/PED.dat')  
    
    # test the 'filterInelasticBkg()' function
#    filtred_im = im.filterInelasticBkg()
    
    # test the 'display_image()' function    
#    (fig, ax) = im.display_image()


