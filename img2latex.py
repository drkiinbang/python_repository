from PIL import Image
from pix2tex.cli import LatexOCR


if __name__ == "__main__":

    img = Image.open('math_expression.png')
    model = LatexOCR()
    print(model(img))
