# VAG Premium Color dashboard image encoder
# https://github.com/skypiece/vagdash
#
# python encode.py filename enctype
# python encode.py 0506-0305.bmp cbch
# python encode.py 1104-0775.png rbrhv
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import codecs

# PNG support by PIL (if installed)
try:
    from PIL import Image
    PIL = True
except ImportError:
    PIL = False
    print("WARN: Python Imaging Library not found! Only BMP input will supported")


def encode(decoded):
    pos = 0
    rpt = 0
    cnt = 0
    encoded = bytearray()
    pixels = bytearray()
    pixel_prev = None

    for pixel in decoded+[(-1,-1,-1,-1)]: # wrong pixel just for careful processing of last elements
        if pixel_prev is None:
            pixel_prev = pixel
        elif pixel == pixel_prev:
            if cnt > 0:
                # save collected not repeated
                encoded.append(cnt)
                encoded+=pixels
                pixels = bytearray()
                cnt = 0
            rpt+=1
            if rpt == 127: # rpt cannot be more than 127
                # save repeated
                encoded.append(rpt | 1<<7) # set bit 8 to high
                encoded.append(pixel_prev[3]); encoded.append(pixel_prev[2]); encoded.append(pixel_prev[1]); encoded.append(pixel_prev[0]) # RGBA to ABGR
                rpt = 0
                pixel_prev = pixel
        elif pixel != pixel_prev:
            if rpt > 0:
                rpt+=1
                # save repeated
                encoded.append(rpt | 1<<7) # set bit 8 to high
                encoded.append(pixel_prev[3]); encoded.append(pixel_prev[2]); encoded.append(pixel_prev[1]); encoded.append(pixel_prev[0]) # RGBA to ABGR
                rpt = 0
            else:
                pixels.append(pixel_prev[3]); pixels.append(pixel_prev[2]); pixels.append(pixel_prev[1]); pixels.append(pixel_prev[0]) # RGBA to ABGR
                cnt+=1
            if cnt == 127: # cnt cannot be more than 127
                # save collected not repeated
                encoded.append(cnt)
                encoded+=pixels
                cnt = 0
                pixels = bytearray()
            pixel_prev = pixel
    # process final data
    if rpt > 0:
        rpt+=1
        # save repeated
        encoded.append(rpt | 1<<7) # set bit 8 to high
        encoded.append(pixel_prev[3]); encoded.append(pixel_prev[2]); encoded.append(pixel_prev[1]); encoded.append(pixel_prev[0]) # RGBA to ABGR
    elif cnt > 0:
        # save collected not repeated
        encoded.append(cnt)
        encoded+=pixels
    return encoded

def transposition(pxdict, width, height, enctype):
    decoded = []
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
    for px in range(width*height):
        decoded.append( (pxdict[w, h][0], pxdict[w, h][1], pxdict[w, h][2], pxdict[w, h][3]) )
        if rbr: w+=wstep
        if cbc: h+=hstep
        if w >= width or w < 0: w = wbeg; h+=hstep
        if h >= height or h < 0: h = 0; w+=wstep
    return decoded

def loadimage(filename):
    pxdict = {}
    width = 0
    height = 0
    if PIL:
        img = Image.open(filename)
        pixels = img.load()
        for x in range(img.width):
            for y in range(img.height):
                pxdict[x,y] = pixels[x,y]
        width = img.width
        height = img.height
    else:
        with open(filename, "rb") as fi:
            header = fi.read(54)
            if header[0] != b'\x42' or header[1] != b'\x4D': print("ERROR: not a BMP file!"); sys.exit()
            width = int(codecs.encode(header[18 : 20][::-1], 'hex'), 16)
            height = int(codecs.encode(header[22 : 24][::-1], 'hex'), 16)
            if header[28] != b'\x20': print("ERROR: only 32 bit BMP supported!"); sys.exit() # 32 bits
            bitmap = fi.read()
            pos = 0
            for y in range(height-1, -1, -1):
                for x in range(width):
                    pxdict[x,y] = ( (bitmap[pos+2 : pos+3], bitmap[pos+1 : pos+2], bitmap[pos : pos+1], bitmap[pos+3 : pos+4]) )
                    pos+=4

    return pxdict, width, height


def main(filename, enctype):
    # load from popular graphical format
    bitmap, width, height = loadimage(filename)

    # transform pixels dictionary to decoded data
    decoded = transposition(bitmap, width, height, enctype)

    # encode data
    encoded = encode(decoded)

    # remove extension
    point = filename.rfind('.')
    if len(filename) - point < 8: filename_out = filename[:point]
    else: filename_out = filename

    with open(filename_out + ".bin", "wb") as fo:
        fo.write(encoded)


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

    main(filename, enctype)
