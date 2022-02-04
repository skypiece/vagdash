# VAG Premium Color dashboard image extractor
# https://github.com/skypiece/vagdash
#
# python extract.py filename PIT_offset enctype save_binaries(optional)
# python extract.py 0506.bin 0x48E89C cbch  1
# python extract.py 0611.bin 0xCA0C18 rbrhv
# python extract.py 1104.bin 0xCA2F30 rbrhv
# python extract.py 2030.bin 0xCA305C rbrhv
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import os
from decode import decode, transposition, saveimage
from libdump import readdump, findpit, loadpit

# PNG support by PIL (if installed)
try:
    from PIL import Image
    PIL = True
except ImportError:
    PIL = False
    print("WARN: Python Imaging Library not found! Only BMP output will supported")


def main(filename, offset, enctype, save_bin):
    print("Trying to decode " + filename + " at PIT offset = " + str(offset) + " with enctype = " + enctype)

    dump = readdump(filename)

    if offset < 0: offset = findpit(dump)

    pit = loadpit(dump, offset)

    # remove extension
    point = filename.rfind('.')
    if len(filename) - point < 8: filename_out = filename[:point]
    else: filename_out = filename

    # directories management
    filedir = os.path.dirname(filename)
    if save_bin == 1:
        filedir_bin = os.path.join(filedir, "bin")
        if not os.path.exists(filedir_bin): os.makedirs(filedir_bin)
    # for pictures output
    if PIL: filedir_pic = os.path.join(filedir, "png")
    else: filedir_pic = os.path.join(filedir, "bmp")
    if not os.path.exists(filedir_pic): os.makedirs(filedir_pic)

    # PIT processing
    with open(filename_out + ".txt", "w") as foi:
        foi.write("### locations in a PIT need to shift by +8 in real dump\n### rest of location/8 (Modulo) must be 0\n")
        for pic in pit:
            info = "pos = "+str(pic["pos"])+"\twidth = "+str(pic["width"])+"\theight = "+str(pic["height"])+"\tpit_location = "+str(pic["pit_loc"])+"\tlocation = "+str(pic["loc"])+"\tlength = "+str(pic["len"])
            print(info)
            foi.write(info+"\n")
            # read encoded data
            encoded = dump[pic["loc"]+8 : pic["loc"]+8+pic["len"]]
            # save to another bin file
            if save_bin == 1:
                with open(os.path.join(filedir_bin, str(pic["pos"]).zfill(4) + ".bin"), "wb") as fo:
                    fo.write(encoded)
            # decode data
            decoded = decode(encoded, pic["len"])
            declen = len(decoded)
            # transform decoded data to pixels dictionary
            bitmap = transposition(decoded, declen, pic["width"], pic["height"], enctype)
            # save into popular graphical format
            saveimage(os.path.join(filedir_pic, str(pic["pos"]).zfill(4)), bitmap, pic["width"], pic["height"])

    print("Complete")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        print("ERROR: filename must be specified")
        sys.exit()

    if len(sys.argv) > 2:
        offset = int(sys.argv[2], base=16)
    else:
        offset = -1

    if len(sys.argv) > 3:
        enctype = sys.argv[3]
    else:
        print("ERROR: autodetection of bitmap orientation is not supported yet")
        sys.exit()

    if len(sys.argv) > 4:
        save_bin = int(sys.argv[4])
    else:
        save_bin = 0

    main(filename, offset, enctype, save_bin)
