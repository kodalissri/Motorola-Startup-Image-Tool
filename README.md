# Motorola-Startup-Image-Tool
converts images to use with Mototrbo radios as Wecome images

MOTOTRBO Startup Image Converter
=================================
Author: Shri Kodali

Converts any image (PNG, JPG, BMP, WebP) into the correct BMP format
for Motorola MOTOTRBO radio startup/welcome screens.


SUPPORTED RADIOS
-----------------
  Model                      Size        Format
  ---------------------------------------------------------------
  XPR 5550 / 5550e           160x72      8-bit (256 color)
  XPR 7550 / 7550e           132x90      8-bit (256 color)
  XPR 7350e                  132x72      1-bit (monochrome)
  Handheld Control Head       132x90      8-bit (256 color)
  SL7550 / SL300             320x240     16-bit (RGB565)
  MOTOTRBO R7                240x320     16-bit (RGB565)


FILES IN THIS FOLDER
---------------------
  moto_startup.html   - Web UI (open in any browser, no install needed)
  moto_startup.exe    - Standalone command-line tool (no install needed)
  moto_startup.py     - Python source (requires Python + Pillow)


=========================================================================
OPTION 1: HTML (Recommended for most users)
=========================================================================

  Just double-click moto_startup.html to open in your browser.

  1. Drag & drop your image or click Browse
  2. Select the radio model(s) you need
  3. Click Convert & Download
  4. Save the BMP file(s)

  No internet, no installs, no server required.


=========================================================================
OPTION 2: Command Line (.exe)
=========================================================================

  Open Command Prompt or PowerShell in this folder.

  LIST ALL SUPPORTED MODELS:
    .\moto_startup.exe --list

  CONVERT FOR A SINGLE MODEL:
    .\moto_startup.exe logo.png xpr7550
    .\moto_startup.exe logo.png r7
    .\moto_startup.exe logo.png xpr5550
    .\moto_startup.exe logo.png hch

  CONVERT FOR ALL MODELS AT ONCE:
    .\moto_startup.exe logo.png all

  SPECIFY OUTPUT FILE NAME:
    .\moto_startup.exe logo.png xpr7550 -o my_custom_splash.bmp

  PREVIEW THE RESULT:
    .\moto_startup.exe logo.png r7 --preview

  USE MODEL ALIASES:
    .\moto_startup.exe logo.png xpr7550e
    .\moto_startup.exe logo.png dp4800
    .\moto_startup.exe logo.png sl300

  NOTE: Replace logo.png with your actual image file name.
        The image must be in the same folder as the .exe file.
        Output files are saved in the same folder as the input image.


=========================================================================
OPTION 3: Python Script (for developers)
=========================================================================

  Requires: Python 3.x and Pillow
    pip install Pillow

  USAGE (same as .exe):
    python moto_startup.py logo.png xpr7550
    python moto_startup.py logo.png all
    python moto_startup.py logo.png r7 -o splash.bmp
    python moto_startup.py --list

  USE IN YOUR OWN SCRIPTS:
    from moto_startup import convert_image

    # Convert for a single model
    convert_image("logo.png", "xpr7550")

    # Convert with custom output path
    convert_image("logo.png", "r7", output_path="r7_splash.bmp")


=========================================================================
LOADING INTO RADIO (via CPS)
=========================================================================

  1. Connect the radio to PC via USB
  2. Open MOTOTRBO CPS (Customer Programming Software)
  3. Read the codeplug from the radio
  4. Go to General Settings > Welcome Image
  5. Click Select and choose the converted BMP file
  6. Write the codeplug back to the radio
