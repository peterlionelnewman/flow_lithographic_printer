# <p>  <b>Flow lithographic printer custom software </b> </p>
Supporting printer code for the flow lithographic printer in Newman et al

We recommend reviewing instruction with supporting images available in the manuscript supporting information, currently in preprint: https://www.biorxiv.org/content/10.1101/2021.02.10.430691v3

Github code and supporting materials can be found at the repository: https://github.com/peterlionelnewman/flow_lithographic_printer 
Software, installation, and use:

This software has been written for use with the controllers and hardware listed in the table at bottom. Some of the SDK and python packages are supplied by component manufacturers – however, where possible all code has been provided.

  •	We recommend creating a fresh conda environment for this (ie.)
  
    o	conda create --name fl_printer python=3.8 pip
  
    o	conda activate fl_printer
    
  •	Dependencies will have to be installed (also note non-standard packages for clean installation folder)
  
    o	pip/conda install ‘dependancy’
    
  •	The printer software can then be run from command/terminal using python.
  
    o	python fl_printer_app.py


When run a loading screen will be shown:
<img src="https://github.com/peterlionelnewman/flow_lithographic_printer/blob/main/instruction_images/img_1.png" width="500" title="img_1" align="center" vspace = "50">
During successful startup terminal will print connection and initialization confirmation for all controllers:
<img src="https://github.com/peterlionelnewman/flow_lithographic_printer/blob/main/instruction_images/img_2.png" width="500" title="img_2" align="center" vspace = "50">
And the GUI will show with ‘camera tab’ view as default:
<img src="https://github.com/peterlionelnewman/flow_lithographic_printer/blob/main/instruction_images/img_3.png" width="500" title="img_3" align="center" vspace = "50">
gcode can then be uploaded for printing via the ‘printer’ tab:
 
