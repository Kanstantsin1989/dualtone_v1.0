# DualTone v1.1

This is a simple app with as user-friendly as possible interface that adds a color filter to your image and changes its brightness and contrast. It does not require any Photoshop or programming skills. Of course, it is not a replacement of professional graphic editors, but if you need to quickly add a color filter to your image, it is very easy to do with this app. Unlike online services, there are no paid plans, no water marks, no file size restrictions. This app supports such image formats as png, bmp, tif, tiff, ppm, pgm, pbm, pcx, tga, ico, jpg, jpeg, jfif, and webp. In addition, you can process transparent png, webp and ico images, and you can convert your image into CMYK color gamma.

## Installation

If you need its sourse code, just download it as a zip file, or clone it with command:

```git clone https://github.com/Kanstantsin1989/dualtone_v1.0.git```

This app was written on Python 3.10, so you must install Python on your PC.
Next you must install required libraries if you don't have them:

```pip install Pillow```

```pip install numpy```

```pip install keyboard```

If you use Windows Power Shell as terminal, perhaps you will have to enter these commands so:

```(path to your Python exe file) -m pip install (library name)```

Standalone version for Windows is available [here](https://kanstantsin.itch.io/dualtone)

## Graphic User Interface

All app functionality is located in the toolbar on the top of window. The statusbar on the bottom shows you image path, its resolution and size.

_1. Open File button (Hot keys CTRL+O)_

Click this button to chose a file you need to process in the dialod window. This app automatically checks if you image has transparency.

_2. Save File button (Hot keys CTRL+S)_

Click this button to save your image with a new filter and/or changed gamma in any of suggested formats. It automatically saves non-transparent images in RGB or L color modes. Transparent images will be saved in RGBA or P color modes. Such specific image formats as YPbPr, HSV, 1, I, F etc are not available for saving.

_3. Convert Image to CMYK button (Hot keys CTRL+Shift+S)_

Click this button to save your image as CMYK if you need it for printing. CMYKA color mode is not supported. If you save transparent images as CMYK, their transparency will be lost.

_4. Info buton (Hot key F1)_

Shows you information about this app.

_5. Image filter combobox_

Combobox that let you apply you one color filter. If you process an image with resolution more than 1920x1200, processing of your image will last for few seconds. Here are all available color filters:

    1. Mirror: it reflects your image horizontally;
    2. Black and white: makes your image color black and white like an old photograph. Not available for transparent 
    images, use 2-colored RGB filters with black and white colors instead;
    3. Sepia: adds sepia effect and makes you image like an even older photograph;
    4. Red: ads to your image a reddish hue to look like an old color photograph;
    NOTE: the next three color filters may cause loss of quality in "jpg", "jpeg", "jfif", and "webp" formats because 
    these file formats compress your image. If you need to use vivid colors for RGB color filters such as green (0, 128, 
    0), red (255, 0, 0), blue (0, 0, 255), dark blue (0, 0, 160) etc, you should save your picture as png, bmp, tif, tiff, 
    ppm, pgm, pbm, pcx, or tga formats, or convert into CMYK;
    5. Overall Tint RGB Filter: tints all image with one RGB color you chose;
    6. 2-Colored RGB (Bicubic): uses bicubic interpolarion to convert yout image into two-tone color scheme from two RGB 
    colors you chose. If you switch two RGB colors, it inverts colors in your image;
    7. 2-Colored RGB (Linear): uses linear interpolarion to convert yout image into two-tone color scheme from two RGB 
    colors you chose, your image will be look different from bicubic interpolarion. If you switch two RGB colors, it will 
    not invert colors in your image;
    8. Blur: blurs your image;
    9. Smooth: makes your image smoother;
    10. Sharpen: sharpens your image;
    11. Detail: also sharpens your image, but in a little bit different way;
    12. Edge Enhance: with it you will get the sharpest image;
    13. Emboss: your image will look like an embossed relief. Not available for transparent images;
    14. Contour #1: converts your image to black contour lines on a white background. Not available for transparent 
    images;
    15. Contour #2: converts your image to white contour lines on a black background. Not available for transparent 
    images;
    16. Invert: inverts your image colors;
    17. Posterize 1, 2, 3, or 4 bit: displays your image using only a small number of different tones. Not available 
    for transparent images.

_6. Brightness and contrast spinboxes_

Two spinboxes that let you increase or decrease brightness and contrast. Use them to experiment and make you image look better! 

_7. Overall Tint RGB filter_

Click the Color widget to set a color to tint your image.

_8. 2-Colored RGB filters_

Set two RGB colors to invert your image to 2-colored image both for bicubic and interpolation color filters. Chose needed colors and compare these two modes! You can easily switch them with the button, but only for bicubic interpolation.

_9. Right button menu_

Menu that duplicates "Open File" and "Save File" buttons and combobox with color filters.

## License

Copyright 2024 Kanstantsin Mironau

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Another Information

Icons by [Icons 8](https://icons8.com)

If you like this app, you can donate the author:

Bitcoin: bc1qchcz4nmcsa7v5xz7pwngwkk2jcqya3r5qmdx7r

Etherum: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B

Polygon: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B

Polkadot: 16Pf7GjVpgb8nfMujFExkaWtCu5NyeR6oksC7AKkTtPvfuUw

BNB Smart Chain: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B

Rootstock: 0xbEBC82f17Efdf78839364974f64c9c8665da5b7b

Optimism: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B

Paypal: 7524440@gmail.com

Payoneer: 7524440@gmail.com

E-mail to contact the author: 7524440@gmail.com
