**ASE2GPL** is a Python-Fu plugin for GIMP 2.8, that imports Adobe Swatch Exchange (ASE)
palette files by converting them into GIMP'S GPL format. The converted palette is
automatically added to the user's GIMP palette library.

[This script was originally written in 2008 by Chris Mohler][ORIGINAL]. It was updated by
Roy Curtis in 2018 [after an issue report on reddit by /u/Adderbox76][REDDIT].

# Installation

Simply save `ASE2GPL.py` into your local GIMP's `plug-ins` folder:

* Windows: `%USERPROFILE%\.gimp-2.8\plug-ins`
* Linux: `$HOME/.gimp-2.8/plug-ins`
* OS X: `$HOME/Library/Application Support/GIMP/2.8/plug-ins/`

You must **restart** GIMP after (un)installing the script, for it to appear.

# Usage

1. [Open the Palettes dock with Windows > Dockable Dialogs > Palettes][1]
2. [Right-click an existing Palette and "Import ASE palette..."][2]
3. [Navigate to the target ASE palette and hit OK][3]
4. [Observe as the palette is imported and auto-selected][4]

Note that if the ASE file has multiple palettes (as is possible, according to the spec),
each palette will be imported as its own new palette file.

# Issues

* Palettes that use CMYK and LAB colors will convert to RGB inaccurately, meaning some of
the colors may be off by one or two values. The plugin will warn you about this.
* Grayscale palettes are not yet supported
* The code is not exactly clean or DRY...

[ORIGINAL]: http://registry.gimp.org/node/10325
[REDDIT]: https://www.reddit.com/r/GIMP/comments/80t574/kuler_palettes_to_gpl/
[1]: https://i.imgur.com/lvaIRTi.jpg
[2]: https://i.imgur.com/BLrLMSo.jpg
[3]: https://i.imgur.com/fbsU3Rx.jpg
[4]: https://i.imgur.com/DgJ62g0.jpg