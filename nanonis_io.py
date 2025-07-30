import re
import numpy as np
from datetime import datetime

class SpmImage:
    def __init__(self, filename):
        self.filename = filename
        self.header = {}
        self.scansize = None
        self.scansize_unit = "m"
        self.center = None
        self.angle = None
        self.scanpixels = None
        self.scan_direction = None
        self.bias = None
        self.z_feedback = None
        self.z_feedback_setpoint = None
        self.z_feedback_setpoint_unit = None
        self.z = None
        self.start_time = None
        self.acquisition_time = None
        self.channel_names = []
        self.channel_units = []
        self.channel_indices_fwd = []
        self.channel_indices_bwd = []
        self.data = None

    def _string_prettify(self, s):
        return s.replace('>', '_').replace(':', '').strip()

    def _parse_header(self, f):
        caption = re.compile(r"^:.*:")
        key = ""
        contents = ""

        for line in f:
            line = line.strip()
            if line == ":SCANIT_END:":
                if key:
                    self.header[key] = contents.strip()
                break

            if caption.match(line):
                if key:
                    self.header[key] = contents.strip()
                key = self._string_prettify(line[1:-1])  # skip leading/trailing ':'
                contents = ""
            else:
                if contents:
                    contents += "\n"
                contents += line

    def print_header_keys_table(self, num_columns=4):
        """
        Prints the available header keys in a formatted tabular form.
        """
        items = list(self.header.keys())
        if not items:
            print("No header keys found.")
            return

        # Determine the maximum width needed for any key
        max_key_len = max(len(key) for key in items) + 2 # +2 for a little padding

        print("\n--- Available Header Keys ---")

        # Calculate the number of rows needed
        num_rows = (len(items) + num_columns - 1) // num_columns

        for r in range(num_rows):
            row_items = []
            for c in range(num_columns):
                idx = r + c * num_rows # Calculate index for column-major order
                if idx < len(items):
                    row_items.append(items[idx])
                else:
                    row_items.append("") # Fill with empty string for alignment

            # Format and print the row
            print(" | ".join(f"{item:<{max_key_len}}" for item in row_items))

        print("-----------------------------\n")

    def _parse_metadata(self):
        self.print_header_keys_table(num_columns=4)
        
        self.scanfile = self.header['SCAN_FILE']
        self.scanpixels = [int(x) for x in self.header['SCAN_PIXELS'].split()]
        self.scansize = [float(x) for x in self.header['SCAN_RANGE'].split()] # in m
        self.center = [float(x) for x in self.header['SCAN_OFFSET'].split()] # in m
        self.angle = float(self.header['SCAN_ANGLE'])
        
        self.scan_direction = "up" if self.header['SCAN_DIR'] == "up" else "down"
        self.bias = float(self.header['BIAS'])

        z_data = self.header['Z-CONTROLLER'].split("\t")
        self.z_feedback = z_data[8] == "1"
        z_setpoint = z_data[9].split()
        self.z_feedback_setpoint = float(z_setpoint[0])
        self.z_feedback_setpoint_unit = z_setpoint[1] if len(z_setpoint) > 1 else ""

        z_key = "Z-CONTROLLER_Z (m)"
        if z_key in self.header:
            self.z = float(self.header[z_key])

        self.start_time = datetime.strptime(
            self.header['REC_DATE'] + " " + self.header['REC_TIME'], "%d.%m.%Y %H:%M:%S"
        )
        self.acquisition_time = float(self.header['ACQ_TIME'])
        self.channel_names, self.channel_units = self._get_channel_names_units()
        self.channel_indices_fwd = list(range(0, len(self.channel_names) * 2, 2))
        self.channel_indices_bwd = list(range(1, len(self.channel_names) * 2, 2))
        
    def _read_binary_data(self, f):
        x_pixels, y_pixels = self.scanpixels
        num_channels_actual = len(self.channel_names) 

        f.read(4) # Skip the 4-byte signature

        total_values = x_pixels * y_pixels * num_channels_actual * 2 # Total for all channels, all directions
        raw = np.fromfile(f, dtype='>f4', count=total_values) # big-endians float32

        reshaped_data = raw.reshape((num_channels_actual, 2, y_pixels, x_pixels)) # this reshaping logic will affect the nested structure 

        self.data = {}
        for i, channel_name in enumerate(self.channel_names):
            self.data[channel_name] = {
                "forward": reshaped_data[i, 0, :, :],
                "backward": reshaped_data[i, 1, :, :]
            }

    def _get_channel_names_units(self):

        lines = self.header['DATA_INFO'].split("\n")
    
        names = []
        units = []

        table_data = []
    
        for (i, line) in enumerate(lines):
            
            entries = line.split()
            table_data.append(entries)
            
            if len(entries) > 1 and i != 0:
                
                names.append(entries[1].replace("_", " "))
                units.append(entries[2])
                if entries[3].lower() != "both":
                    raise NotImplementedError(
                        f"Only one direction recorded. This is not implemented yet. ({entries})"
                    )
                
        # Get column widths (max length of each item in a column)
        # e.g. ('Channel', '30', '2', '3', '4', '24', '0', '95') and find max of the length of a string
        column_widths = [max(len(str(item)) for item in col) for col in zip(*table_data)] 
        
        # Print the table header
        header_line = table_data[0]
        header_str = " | ".join(f"{item:<{width}}" for item, width in zip(header_line, column_widths))
        print("\n" + "--- DATA_INFO ---")
        print(header_str)
        print("-" * len(header_str))
        
        # Print the data rows
        for row in table_data[1:]:
            row_str = " | ".join(f"{item:<{width}}" for item, width in zip(row, column_widths))
            print(row_str)
        print("-----------------\n")

        return names, units

    def load(self, header_only=False, verbose=True):
        if verbose:
            print(f"Reading header from {self.filename}")

        with open(self.filename, 'r', encoding='latin1') as f:
            self._parse_header(f)

        self._parse_metadata()

        if not header_only:
            if verbose:
                print(f"Reading body from {self.filename}")
            
            # Reopen in binary mode for reading the float32 image data
            with open(self.filename, 'rb') as f:
                # Seek to binary section (find :SCANIT_END:)
                while True:
                    line = f.readline()
                    if line.strip() == b':SCANIT_END:':
                        break
                self._read_binary_data(f)

        return self

    def show_data_shapes(self):
        if self.data is None:
            print("No data loaded yet. Call load() first.")
            return

        print("\n--- Data Shapes ---")
        if isinstance(self.data, dict): # Check if it's the nested dict structure
            for channel_name, directions in self.data.items():
                print(f"   {channel_name}")
                if isinstance(directions, dict):
                    for direction, array in directions.items():
                        if isinstance(array, np.ndarray):
                            print(f"  {direction}: {array.shape}")
                        else:
                            print(f"  {direction}: Not a NumPy array (type: {type(array)})")
                else:
                    print(f"  {channel_name}: Unexpected data structure (type: {type(directions)})")
        elif isinstance(self.data, np.ndarray): # If you kept your original (Y, X, interleaved_channels)
            print(f"Main data array shape: {self.data.shape}")
            print("Channels are interleaved along the last axis.")
        else:
            print(f"Unknown data structure for self.data (type: {type(self.data)})")
        print("-------------------\n")

    