# VAG Premium Color dashboard image decoder
# https://github.com/skypiece/vagdash
#
# python decode.py filename enctype width(optional) height(optional)
# python decode.py 0506-0305.bin cbch 46
# python decode.py 1104-0775.bin rbrhv 240
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import os
import codecs
from math import ceil

# PNG support by PIL (if installed)
try:
    from PIL import Image
    PIL = True
except ImportError:
    PIL = False
    print("WARN: Python Imaging Library not found! Only BMP output will supported")


def decode(encoded, enclen):
    pos = 0
    decoded = []
    while pos < enclen:
        num = encoded[pos]
        if type(num) is str: num = int(codecs.encode(num, 'hex'), 16) # binary to int on Python 2
        pos+=1
        if num == 0 or pos >= enclen: # unexpected
            break
        else:
            # RLE
            if num > 127: # or 8th bit is set to High
                # need to N repeats of folowing pixel
                cnt = 1
                rpt = num & ~(1<<7) # remove 8 bit
            else:         # or 8th bit is set to Low
                # need to copy N follow pixels as is
                cnt = num
                rpt = 1
            # reading of folowing pixel(s)
            for c in range(cnt):
                pixel = (encoded[pos+3], encoded[pos+2], encoded[pos+1], encoded[pos]) # ABGR to RGBA
                pos+=4
                if pos > enclen: print("ERROR: unexpected eof at", pos); break
                for r in range(rpt):
                    decoded.append(pixel)
    return decoded

def transposition(decoded, declen, width, height, enctype):
    pxdict = {}
    # enctype
    rbr = False; cbc = False
    if enctype.find("rbr") >= 0: rbr = True
    elif enctype.find("cbc") >= 0: cbc = True
    else: print("unknown enctype =", enctype)
    ver = False; hor = False
    if enctype.find("h") >= 0: hor = True
    if enctype.find("v") >= 0: ver = True
    #
    if hor:
        wstep = -1
        wbeg = width - 1
    else:
        wstep = 1
        wbeg = 0
    if ver:
        hstep = -1
        hbeg = height - 1
    else:
        hstep = 1
        hbeg = 0
    w = wbeg
    h = hbeg
    #
    for px in range(declen):
        pxdict[w, h] = decoded[px]
        if rbr: w+=wstep
        if cbc: h+=hstep
        if w >= width or w < 0: w = wbeg; h+=hstep
        if h >= height or h < 0: h = 0; w+=wstep
    return pxdict

def saveimage(filename, bitmap, width, height):
    if PIL:
        img = Image.new('RGBA', (width, height)) # Create a new empty image
        pixels = img.load() # Create the pixel map
        for x in range(width):
            for y in range(height):
                pixels[x,y] = bitmap[x,y]
        img.save(filename + ".png")
    else:
        with open(filename + ".bmp", "wb") as fo:
            # BMP header
            header = bytearray()
            for i in range(54): header.append(0x00)
            header[0] = 0x42
            header[1] = 0x4D
            #TODO size
            header[10] = 0x36 # BMoffset
            header[14] = 0x28
            #TODO more than 1-byte size support
            header[18] = width
            header[22] = height
            header[26] = 0x01
            header[28] = 0x20 # 32 bits
            fo.write(header)
            # data
            pixels = bytearray()
            # pictures stored from last line
            for y in range(height-1, -1, -1):
                for x in range(width):
                    pixels.append(bitmap[x,y][2])
                    pixels.append(bitmap[x,y][1])
                    pixels.append(bitmap[x,y][0])
                    pixels.append(bitmap[x,y][3])
            fo.write(pixels)


def main(filename, enctype, width, height):
    with open(filename, "rb") as fi:
        # read encoded file
        filesize = os.path.getsize(filename)
        enclen = 262144 # 256KB block
        if enclen > filesize : enclen = filesize
        encoded = fi.read(enclen)

        # decode data
        decoded = decode(encoded, enclen)
        declen = len(decoded)

        # guess unknown width or height
        if declen > 0:
            if height == 0:
                if declen > 65536: print("ERROR: image can not be bigger than 256x256")
                print("WARN: height not specified! let me guess it for px_len =", declen)
                if width == 0:
                    # begin search from 10px
                    for w in range(10, 240):
                        width = w
                        height = declen / width
                        if declen % width == 0 and width < 255 and height > 0 and height < 255: break
                else:
                    height = declen / width
                if height % 1 == 0: height = int(height)
                if width * ceil(height) > declen: print ("WARN: cannot find proper width and height!"); width = 255; height = 255
                print("width =", width, "height =", height)

        # transform decoded data to pixels dictionary
        bitmap = transposition(decoded, declen, width, height, enctype)

        # remove extension
        point = filename.rfind('.')
        if len(filename) - point < 8: filename_out = filename[:point]
        else: filename_out = filename

        # save into popular graphical format
        saveimage(filename_out, bitmap, width, height)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        print("ERROR: filename must be specified")
        sys.exit()

    if len(sys.argv) > 2:
        enctype = str(sys.argv[2])
    else:
        print("ERROR: coding type must be specified! Posible values rbr (row by row) and cbc (column by column)")
        sys.exit()

    if len(sys.argv) > 3:
        width = int(sys.argv[3])
    else:
        width = 0

    if len(sys.argv) > 4:
        height = int(sys.argv[4])
    else:
        height = 0

    main(filename, enctype, width, height)
