# VAG Premium Color dashboard image extractor
# https://github.com/skypiece/vagdash
#
# python extract.py filename
#         optional arguments --offset, --enctype, --picdir, --savebin
# python extract.py 0506.bin --offset 0x48E89C --enctype cbch --savebin 1
# python extract.py 0611.bin --offset 0xCA0C18 --enctype rbrhv
# python extract.py 1104.bin
# python extract.py 2030.bin
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import os
import datetime
from decode import decode, transposition, saveimage
from libdump import readdump, findpit, loadpit

# PNG support by PIL (if installed)
try:
    from PIL import Image
    PIL = True
except ImportError:
    PIL = False
    print("WARN: Python Imaging Library not found! Only BMP output will supported")


def main(filename, offset, enctype, save_bin, picdir):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Trying to decode " + filename + " with enctype = " + enctype)

    dump = readdump(filename)

    if offset < 0: offset = findpit(dump)

    pit = loadpit(dump, offset)

    # remove extension
    point = filename.rfind('.')
    if len(filename) - point < 8: filename_out = filename[:point]
    else: filename_out = filename

    # directories management
    if not picdir: picdir = os.path.dirname(filename)
    # for pictures output
    if PIL: picdir_pic = os.path.join(picdir, "png")
    else: picdir_pic = os.path.join(picdir, "bmp")
    if not os.path.exists(picdir_pic): os.makedirs(picdir_pic)
    if save_bin == 1:
        picdir_bin = os.path.join(picdir, "bin")
        if not os.path.exists(picdir_bin): os.makedirs(picdir_bin)

    # PIT processing
    with open(filename_out + ".txt", "w") as foi:
        foi.write("### picture location need shift by +8 in real dump\n### rest of location/8 (Modulo) must be 0\n")
        for pic in pit:
            info = "pos = "+str(pic["pos"])+"\twidth = "+str(pic["width"])+"\theight = "+str(pic["height"])+"\tpit_location = "+str(pic["pit_loc"])+"\tlocation = "+str(pic["loc"])+"\tlength = "+str(pic["len"])
            print(info)
            foi.write(info+"\n")
            # read encoded data
            encoded = dump[pic["loc"]+8 : pic["loc"]+pic["len"]+8]
            # save to another bin file
            if save_bin == 1:
                with open(os.path.join(picdir_bin, str(pic["pos"]).zfill(4) + ".bin"), "wb") as fo:
                    fo.write(encoded)
            # decode data
            decoded = decode(encoded, pic["len"])
            declen = len(decoded)
            # transform decoded data to pixels dictionary
            bitmap = transposition(decoded, declen, pic["width"], pic["height"], enctype)
            # save into popular graphical format
            saveimage(os.path.join(picdir_pic, str(pic["pos"]).zfill(4)), bitmap, pic["width"], pic["height"])

    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Complete")


if __name__ == '__main__':
    # defaults
    offset = -1
    enctype = "rbrhv"
    savebin = 0
    picdir = ""

    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            if sys.argv[i] == "--offset": offset = int(sys.argv[i+1], base=16); i+=1
            if sys.argv[i] == "--enctype": enctype = sys.argv[i+1]; i+=1
            if sys.argv[i] == "--picdir": picdir = sys.argv[i+1]; i+=1
            if sys.argv[i] == "--savebin": savebin = sys.argv[i+1]; i+=1
        i+=1

    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        filename = sys.argv[1]
    else:
        print("ERROR: filename must be specified")
        sys.exit()

    main(filename, offset, enctype, savebin, picdir)
