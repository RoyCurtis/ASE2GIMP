#!/usr/bin/env python
# Author: Chris Mohler, Roy Curtis
# Copyright 2008 Chris Mohler
# License: GPL v3
# Portions of this code were taken from easyrgb.com
# GIMP plugin to convert Adobe Swatch Exchange (ASE) palettes to GIMP (GPL) palettes
# Updated for GIMP 2.8.x and later ASE format by Roy Curtis

# ASE file format references:
# * http://carl.camera/default.aspx?id=109
# * http://www.selapa.net/swatches/colors/fileformats.php#adobe_ase
# * https://bazaar.launchpad.net/~olivier-berten/swatchbooker/trunk/view/head:/src/swatchbook/codecs/adobe_ase.py
# 
# ... and their archives, if they become lost to history:
#
# * http://archive.is/C2Fe6
# * http://archive.is/jFiTU
# * http://archive.is/AEB9m

from gimpfu import *
from struct import unpack_from, unpack

import os, traceback
import StringIO

# For debugging; uncomment this and all print lines where necessary
# import sys
# sys.stderr = open('gimpstderr.txt', 'w')
# sys.stdout = open('gimpstdout.txt', 'w')

# Constants
PAL_START = "\xC0\x01"
PAL_ENTRY = "\x00\x01"
PAL_END   = "\xC0\x02"
STR_TERM  = "\x00\x00"

# Get GIMP and palette directories
gimp_dir = gimp.directory
pal_dir  = os.path.join(gimp_dir, "palettes")
# print "GIMP dir:",    gimp_dir
# print "Palette Dir:", pal_dir

def ase_converter(p, ase_path):
    # Plugin's entry point
    # print "ASE file: " + ase_path
    gimp.progress_init()
    
    # Strip of the "file:///" prefix - if called by nautilus, etc
    if ase_path.startswith('file:///'):
        ase_path = ase_path.replace('file:///', '/')
        
    try:
        # Needs to be in read-binary mode, else Windows will break reading.
        # Auto-closes file on finish or exception because of "with"
        with open(ase_path, 'rb') as ase_file:
            do_convert(ase_file)

    except Exception as ex:
        #  Something went wrong - bailing out!
        pdb.gimp_message(
            'Error: %s\n' % traceback.format_exc() +
            "Try starting GIMP from a console to see what went wrong."
        )

        if isinstance(ex, SystemExit): 
            raise # take the exit

def do_convert(ase_file):
    # If we've given a warning about using LAB or CMYK colors
    inaccuracy_warning = False

    ase_header = ase_file.read(4) # first 4 bytes
    # print "ASE Header:", ase_header

    # first 4 bytes should be "ASEF" if this is an ASE file
    if ase_header != "ASEF": 
        raise Exception("\"" + ase_file.name  + "\" is not an ASE file.")

    ase_version_major = unpack( '>H', ase_file.read(2) )[0]
    ase_version_minor = unpack( '>H', ase_file.read(2) )[0]
    # print "ASE version:", ase_version_major, ".", ase_version_minor

    if ase_version_major != 1:
        raise Exception("Major version of given file is not 1; not compatiable with script.")

    if ase_version_minor != 0:
        pdb.gimp_message("Warning: Minor version of given file is not 0; might not work with this script.")

    ase_nbblocks = unpack( '>I', ase_file.read(4) )[0]
    # print "ASE number of blocks:", ase_nbblocks

    if ase_nbblocks == 0:
        raise Exception("Given ASE file has no blocks")

    # Predefined for later use
    pal_title = ""
    pal_gpl   = ""
    pal_ncols = 0

    # Iterate through each block, creating GIMP palette files along the way
    for block in range(ase_nbblocks):
        block_type = ase_file.read(2)
        block_len  = unpack( '>I', ase_file.read(4) )[0]
        block_data = StringIO.StringIO( ase_file.read(block_len) )
        # print "Block #", block, "type:", block_type, "length:", block_len
    
        ######################
        # Creating a palette #
        ######################
        if block_type == PAL_START:

            # We must not be in the middle of creating a palette...
            if pal_gpl != "":
                raise Exception("Unexpected beginning of palette")

            # start GPL (GIMP Palette) file
            pal_gpl   = "GIMP Palette\nName: "
            pal_title = read_ase_string(block_data)

            if pal_title == "":
                pal_title = "Untitled"

            # print "  Palette title:", pal_title

            # Finish GPL header info
            # FIXME: If we're importing a multi-palette ASE, this is a little janky because ase_nbblocks is not equal to
            # length of individual palettes. But it's a safe assumption to make that we're just dealing with one.
            if ase_nbblocks <= 12:
                pal_gpl += pal_title + "\nColumns: 1\n#\n"
            else:
                pal_gpl += pal_title + "\n#\n"

        ###########################
        # Parsing a palette color #
        ###########################
        elif block_type == PAL_ENTRY:
            
            # We must have at least started the palette...
            if pal_gpl == "":
                raise Exception("Unexpected palette entry before palette start")

            col_name  = read_ase_string(block_data)
            col_model = block_data.read(4)
            # print "  Color name:", col_name, "model:", col_model

            # From testing, and I assume because of the funky conversion code below, converting some LAB colors results
            # in some RGB colors being off-by-one than what Kuler reports...
            if col_model == "LAB " or col_model == "CMYK":
                if not inaccuracy_warning:
                    pdb.gimp_message("Warning: Converting from LAB or CMYK colors is inaccurate and may result in "
                                     "slightly-off RGB values")
                    inaccuracy_warning = True

            if col_model == "RGB ":
                red   = unpack_from( '>f',  block_data.read(4) ) #read 4 bytes, unpack to float - little endian
                green = unpack_from( '>f',  block_data.read(4) ) #next 4 bytes
                blue  = unpack_from( '>f',  block_data.read(4) ) #next 4 bytes
                red   = (red[0] * 255) # multiply float by 255
                red   = int(round(red,  0)) # round to int
                green = (green[0] * 255)
                green = int(round(green,  0))
                blue  = (blue[0] * 255)
                blue  = int(round(blue,  0))
                # print "  RGB:", red,  green , blue

                # Add swatch RGB values to the GPL file
                pal_ncols += 1
                pal_gpl   += str(red) + "\t" + str(green) + "\t" + str(blue)

                if col_name != "":
                    pal_gpl += "\t" + col_name + "\n"
                else:
                    pal_gpl += "\n"

            elif col_model == "LAB ":
                lab_L = unpack_from( '>f',  block_data.read(4) ) #read 4 bytes, unpack to float - little endian
                lab_A = unpack_from( '>f',  block_data.read(4) ) #next 4 bytes
                lab_B = unpack_from( '>f',  block_data.read(4) ) #next 4 bytes

                # print "  LAB:", str(lab_L[0]), str(lab_A[0]), str(lab_B[0])

                # Courtesy of EasyRGB.com - convert Lab to XYZ
                lab_L = lab_L[0] * 100 #move dec point
                var_Y = ( lab_L + 16 ) / 116
                var_X = lab_A[0] / 500 + var_Y
                var_Z = var_Y - lab_B[0] / 200

                if var_Y**3 > 0.008856: var_Y = var_Y ** 3
                else:                   var_Y = ( var_Y - 16 / 116 ) / 7.787
                if var_X**3 > 0.008856: var_X = var_X ** 3
                else:                   var_X = ( var_X - 16 / 116 ) / 7.787
                if var_Z**3 > 0.008856: var_Z = var_Z ** 3
                else:                   var_Z = ( var_Z - 16 / 116 ) / 7.787

                # Correct the white point - Observer= 2 deg, Illuminant= D65
                ref_X =  95.047
                ref_Y = 100.000
                ref_Z = 108.883
                X = ref_X * var_X
                Y = ref_Y * var_Y
                Z = ref_Z * var_Z

                # print "  XYZ:", str(X), str(Y), str(Z)

                # Courtesy of EasyRGB.com - convert XYZ to RGB
                var_X = X / 100 #X from 0 to  95.047 (Observer = 2 deg, Illuminant = D65)
                var_Y = Y / 100 #Y from 0 to 100.000
                var_Z = Z / 100 #Z from 0 to 108.883
                var_R = var_X *  3.2406 + var_Y * -1.5372 + var_Z * -0.4986
                var_G = var_X * -0.9689 + var_Y *  1.8758 + var_Z *  0.0415
                var_B = var_X *  0.0557 + var_Y * -0.2040 + var_Z *  1.0570

                if var_R > 0.0031308: var_R = 1.055 * (var_R ** (1 / 2.4)) - 0.055
                else:                 var_R = 12.92 * var_R
                if var_G > 0.0031308: var_G = 1.055 * (var_G ** (1 / 2.4)) - 0.055
                else:                 var_G = 12.92 * var_G
                if var_B > 0.0031308: var_B = 1.055 * (var_B ** (1 / 2.4)) - 0.055
                else:                 var_B = 12.92 * var_B

                R = int(round((var_R * 255),  0))
                G = int(round((var_G * 255),  0))
                B = int(round((var_B * 255),  0))

                # Check for out-of-bounds values - there has to be a prettier way :)
                if R < 0:   R = 0
                if R > 255: R = 255
                if G < 0:   G = 0
                if G > 255: G = 255
                if B < 0:   B = 0
                if B > 255: B = 255
                # print "  RGB:", str(R), str(G), str(B)

                # Add color to GPL swatch file
                pal_ncols += 1
                pal_gpl += str(R) + "\t" + str(G) + "\t" + str(B)

                if col_name != "":
                    pal_gpl += "\t" + col_name + "\n"
                else:
                    pal_gpl += "\n"

            elif col_model == "CMYK":
                cmyk_C = unpack_from( '>f',  block_data.read(4) ) #read 4 bytes, unpack to float - little endian
                cmyk_M = unpack_from( '>f',  block_data.read(4) ) #next 4 bytes
                cmyk_Y = unpack_from( '>f',  block_data.read(4) ) #next 4 bytes
                cmyk_K = unpack_from( '>f',  block_data.read(4) ) #next 4 bytes
                # print "  CMYK:", cmyk_C,  cmyk_M,  cmyk_Y,  cmyk_K

                # Convert CMYK to CMY
                C = (cmyk_C[0] * (1 - cmyk_K[0]) + cmyk_K[0])
                M = (cmyk_M[0] * (1 - cmyk_K[0]) + cmyk_K[0])
                Y = (cmyk_Y[0] * (1 - cmyk_K[0]) + cmyk_K[0])

                # Convert CMY to RGB
                R = ( ( 1 - C ) * 255 )
                G = ( ( 1 - M ) * 255 )
                B = ( ( 1 - Y ) * 255 )
                R = int( round(R, 0) )
                G = int( round(G, 0) )
                B = int( round(B, 0) )

                # Check for out-of-bounds
                if R < 0:   R = 0
                if R > 255: R = 255
                if G < 0:   G = 0
                if G > 255: G = 255
                if B < 0:   B = 0
                if B > 255: B = 255
                # print "  RGB:", R, G, B

                # Add color to GPL swatch file
                pal_ncols += 1
                pal_gpl   += str(R) + "\t" + str(G) + "\t" + str(B)

                if col_name != "":
                    pal_gpl += "\t" + col_name + "\n"
                else:
                    pal_gpl += "\n"

            else:
                pdb.gimp_message("Warning: Unknown color model \"" + col_model + "\", skipped")

        ###############################
        # Writing the palette to file #
        ###############################
        elif block_type == PAL_END:
            
            # We must have at least started the palette...
            if pal_gpl == "":
                raise Exception("Unexpected palette end before palette start")

            if pal_ncols == 0:
                pdb.gimp_message("Warning: Could not import any colors from palette \"" + pal_title + "\"")
            else:
                # Target GPL path and file name
                pal_path = os.path.join( pal_dir,  (pal_title + ".gpl") )
                # print "Final GIMP palette title:", pal_title
                # print "Final GIMP palette color count:", pal_ncols
                # print "Final GIMP palette path:", pal_path

                if os.path.isfile(pal_path):
                    pdb.gimp_message("Warning: Palette \"" + pal_path + "\" already exists; not overwriting.")
                else:
                    pf = open(pal_path, 'w')
                    pf.write(pal_gpl)
                    pf.close()
                    pdb.gimp_palettes_refresh()
                    pdb.gimp_context_set_palette(pal_title)

            # Reset values for next palette
            pal_title = ""
            pal_gpl   = ""
            pal_ncols = 0
        else:
            raise Exception("Error: Unexpected block type " + block_type)

        # Update progress bar
        gimp.progress_update( (1.0 / ase_nbblocks) * block )

# Reads double-byte string from ASE format
def read_ase_string(data):
    # First two bytes are length of string in amount of byte pairs
    length = unpack( '>H', data.read(2) )[0] - 1

    # print "Processing ase string of length:", length

    raw_string = data.read(length * 2)
    terminator = data.read(2)

    if terminator != STR_TERM:
        raise Exception("Expected double-NUL terminated string")

    # FIXME: This doesn't seem right. UTF-16 allows more than two bytes for
    # some characters, but ASE spec apparently says all chars are two bytes...
    return unicode(raw_string, "utf_16_be")

# Needed to get translation string for UI
gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

register(
    "python-fu-convert-ase",
    "Convert ASE palette(s) to GIMP palette(s)",
    "Convert ASE palette(s) from Creative Cloud into a GIMP palette(s).",
    "Chris Mohler, Roy Curtis",
    "Chris Mohler",
    "2008",
    "<Palettes>/Import _ASE palette...",
    "",
    [
        (PF_PALETTE, "palette",  _("Palette"), ""),
        (PF_FILE, "ase_path", "ASE File", ""),
    ],
    [],
    ase_converter, 
    domain=("gimp20-python", gimp.locale_directory)
)

main()