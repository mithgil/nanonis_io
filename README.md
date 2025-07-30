# nanonis_io.py: An easy nanonis sxm parser

A simple script that parses Nanonis sxm files as NumPy array with metadata

## Dependencies

This script is tested under ubuntu 24 with numpy 1.26.4

## Usage

Just copy the `nanonis.py` script to the path around your main script.

Assuming the `nanonis.py` and `main.py` is structured as 

```bash

nanonis
├── nanonis.py
├──viewer
├──── main.py

```

Then your main.py should do
```
import sys
sys.path.append("..")  # in notebook
from nanonis_io import SpmImage
```

so main.py can find `nanonis_io.py` to parse data

```python
import os

path = "/home/yourname/path/to/data" 
filename = "dataname.sxm"
pathfile = os.path.join(path, filename)

image = SpmImage(pathfile).load(verbose=True)
print(f"scan pixels {image.scanpixels}")
print(f"scansize {image.scansize}")
```

will output something like

```bash

Reading header from /home/yourname/path/to/data/dataname.sxm

--- Available Header Keys ---
NANONIS_VERSION   | ACQ_TIME          | SCAN_OFFSET       | COMMENT          
SCANIT_TYPE       | SCAN_PIXELS       | SCAN_ANGLE        | DATA_INFO        
REC_DATE          | SCAN_FILE         | SCAN_DIR          |                  
REC_TIME          | SCAN_TIME         | BIAS              |                  
REC_TEMP          | SCAN_RANGE        | Z-CONTROLLER      |                  
-----------------------------


--- DATA_INFO ---
Channel | Name      | Unit | Direction | Calibration | Offset   
----------------------------------------------------------------
30      | Z         | m    | both      | -2.500E-7   | -2.500E-6
2       | Input_3   | V    | both      | 1.000E+0    | 0.000E+0 
3       | Input_4   | V    | both      | 1.000E+0    | 0.000E+0 
4       | Input_5   | V    | both      | 1.000E+0    | 0.000E+0 
24      | Bias      | V    | both      | 1.000E+0    | 0.000E+0 
0       | Current   | A    | both      | 1.000E-6    | -4.156E-7
95      | Counter_2 | Hz   | both      | 6.000E+6    | 0.000E+0 
-----------------

Reading body from /home/yourname/path/to/data/dataname.sxm
scan pixels [256, 256]
scansize [1.5e-06, 1.5e-06]

```
This printed results will show you almost all crucial metadata you need.

## Visualization
Take `Current` channel as an example:

```python
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

import matplotlib as mpl

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial']
import numpy as np


fig, ax = plt.subplots(1,1,figsize = (7,7))

scale_factor = 1e6
data_show = image.data['Current']['forward'] * scale_factor

hmp = ax.imshow(data_show,
                cmap='viridis',
                origin = 'lower')

ax.set_xticks([])
ax.set_yticks([])

cbar = fig.colorbar(hmp, ax=ax, orientation='vertical',
                    pad=0,
                    aspect = 8,
                    shrink=0.3,
                    anchor=(0.5, 0.2)
                   )

cbar.ax.set_title(r'$\mu\text{A}$', fontsize=16)
cbar.ax.tick_params(labelsize=16)

pixel_size_in_nanometers = image.scansize[0]/image.scanpixels[0] * 1e9

scalebar = ScaleBar(pixel_size_in_nanometers, 'nm',
                    length_fraction=0.25, 
                    height_fraction=0.02, 
                    location='upper right', # Position (e.g., 'lower right', 'upper left')
                    box_color='white', 
                    box_alpha=0, 
                    color='white', 
                    font_properties={'size': 16}) 

ax.set_aspect(1)

ax.add_artist(scalebar)

output_filename = pathfile[0:-3] + "_matplot.png"

plt.savefig(output_filename, dpi=500, bbox_inches = 'tight')

plt.show()
```



## License

MIT License.
