import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog

def read_image(file_path):
    # Reads an image file and returns it as a PIL Image object.
    image = Image.open(file_path)
    return image

def read_dem(file_path, metadata_path):
    # Reads DEM data from a binary file with width and height specified in a separate txt file.
    # Read width and height from the metadata file
    with open(metadata_path, 'r') as f:
        width = int(f.readline().strip())
        height = int(f.readline().strip())
        
def read_hdr(hdr_path):
    # Reads a text file containing two integers, one float, and two double numbers in sequence.
    with open(hdr_path, 'r') as file:
        # Read lines from the file and parse the values
        lines = file.readlines()
        
        # Ensure the file has the expected number of values
        if len(lines) < 5:
            raise ValueError("The file does not contain the expected number of lines.")
        
        # Parse the values in the expected order
        width = int(lines[0].strip())
        height = int(lines[1].strip())
        resolution = float(lines[2].strip())
        startX = float(lines[3].strip())
        startY = float(lines[4].strip())
        
    return width, height, resolution, startX, startY

def get_pixel_value(image, x, y):
    # Retrieves the pixel value at specified (x, y) coordinates from an image.
    return image.getpixel((x, y))

def set_pixel_value(image, x, y, value):
    # Sets the pixel value at specified (x, y) coordinates in an image.
    image.putpixel((x, y), value)

def create_blank_image(width, height, color=(0, 0, 0)):
    # Creates a blank image of specified width and height, filled with the given color.
    return Image.new("RGB", (width, height), color)

def main():
    # Tkinter hides the root window
    root = tk.Tk()
    root.withdraw()

    # Select an image file using the file dialog
    img_path = filedialog.askopenfilename(title="Select an image file", 
                                          filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")])
    if not img_path:
        print("An image file was not selected.")
        return
    
    # Select a dem file using the file dialog
    dem_path = filedialog.askopenfilename(title="Select a dem file", 
                                          filetypes=[("DEM Files", "*.bin;*.dem")])
    
    # Select a dem header file using the file dialog
    demhdr_path = filedialog.askopenfilename(title="Select a dem header file", 
                                          filetypes=[("DEM HDR Files", "*.txt;*.hdr")])
    
    # Read dem hdr file
    width, height, resolution, startX, startY = read_hdr(demhdr_path)
    
    # Load an source image
    srcImg = read_image(img_path)
            
    # Create an empty ortho image
    orthoImg = create_blank_image(srcImg.width, srcImg.height)

if __name__ == "__main__":
    main()