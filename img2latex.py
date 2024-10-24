from PIL import Image
from pix2tex.cli import LatexOCR
from tkinter import Tk, filedialog


if __name__ == "__main__":
    filename = filedialog.askopenfilename(title="Select the image file", filetypes=[("png files", "*.png"), ("All files", "*.*")])
    img = Image.open(filename)
    model = LatexOCR()
    print(model(img))
