# VAG Premium Color dashboard image decoder
# https://github.com/skypiece/vagdash
# python decode.py filename width(optional) height(optional)
# python decode.py image.bin 82 46
# python decode.py 0506-2266920.bin 82
# python decode.py dump.bin
import sys
import os
import codecs
from math import ceil


if len(sys.argv) > 1:
    filename = sys.argv[1]
    filesize = os.path.getsize(filename)
else:
    print("ERROR: filename must be specified")
    sys.exit()

if len(sys.argv) > 2:
    width = int(sys.argv[2])
else:
    width = 0

if len(sys.argv) > 3:
    height = int(sys.argv[3])
else:
    height = 0


with open(filename,"rb") as fi:
    pos = -1
    pos_beg = None          # stores position of first byte
    encmap = bytearray()    # stores original encoded binary
    bitmap = bytearray()    # stores decoded bitmap

    #TODO need to improve i/o for slow devices by reading blocks
    byte = fi.read(1)
    while byte:
        pos+=1
        if pos_beg == None: pos_beg = pos
        num = int(codecs.encode(byte, 'hex'), 16) # binary to int
        encmap.append(num)

        # unexpected
        if num == 0:
            # detecting end of encoded bitmap
            # multiple bitmaps in a one file are supported, but
            # 0x00 not exists every time between bitmaps, because
            # bitmap's length rounded by 0x00 to 4 bytes when it is really needed
            print("0 found at", pos, "; previous image finished and another one begins?")
            # save decoded bitmap of previous image
            bitmap_len = len(bitmap)
            print()
            if bitmap_len > 0:
                if height == 0:
                    bitmap_len_4 = bitmap_len / 4
                    if bitmap_len_4 > 65536: print("ERROR: image can not be bigger than 256x256; is it properly dump?"); break
                    print("WARN: height not specified; trying to calculate it for bitmap_len_4=", bitmap_len_4)
                    if width == 0:
                        # begin search from 10px
                        for w in range(10, 240):
                            width = w
                            height = bitmap_len_4 / width
                            if bitmap_len_4 % width == 0 and width < 255 and height > 0 and height < 255: break
                    else:
                        height = bitmap_len_4 / width
                    if height % 1 == 0: height = int(height)
                    if width * ceil(height) > bitmap_len_4: print ("WARN: cannot find working width and height"); width = 255; height = 255
                print("width =", width, "height =", height)

                # do not save same binary
                if filesize != len(encmap):
                    with open(filename+"-" + str(pos_beg) + ".bin", "wb") as fo:
                        fo.write(encmap)
                    fo.close()
                with open(filename+"-" + str(pos_beg) + ".bmp", "wb") as fo:
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
                    #TODO lines need to be flipped some cases?
                    #TODO R U sure that images coded by horizontal lines?!
                    fo.write(bitmap)
                fo.close()
            # reset
            width = 0
            height = 0
            encmap = bytearray()
            bitmap = bytearray()
            pos_beg = None
        else:
            # RLE
            if num > 127:   # or 8th bit is set to High
                # need to N repeats of folowing pixel
                cnt = 1
                rpt = num & ~(1<<7) # remove 8 bit
            else:
                # need to copy N follow pixels as is
                cnt = num
                rpt = 1
            # reading of folowing pixel(s)
            for c in range(cnt):
                pixel = fi.read(4)
                pos+=4
                encmap.append(pixel[0])
                encmap.append(pixel[1])
                encmap.append(pixel[2])
                encmap.append(pixel[3])
                if len(pixel) < 4: print("ERROR: unexpected eof at", pos); break
                for r in range(rpt):
                    bitmap.append(pixel[1])
                    bitmap.append(pixel[2])
                    bitmap.append(pixel[3])
                    bitmap.append(pixel[0])
        byte = fi.read(1)

print("Complete")
input()
