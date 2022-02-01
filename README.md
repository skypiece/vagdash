# vagdash
VAG dashboards tools

Use decode.py for decoding of image binaries.
Use extract.py to extract and decode images from LCD's nand dump.
- run examples can be found in file header

Python both versions are supported. For PNG output you need to install PIL (for Python 3 use "pip3 install pillow").
Windows' built-in picture viewers not a good tools for watching BMP with alphachannel. Use PNG format instead or another tools, like XnView (https://www.xnview.com).

How to find valid offset for Picture Information Table:
- open your dump and find HEX values "0001000409"
- look up 8 or 11 bytes earlier for byte 0x0B or 0x0C
- there is a your offset, catch it!)
