# VAG Premium Color dashboard image injector
# https://github.com/skypiece/vagdash
#
# python inject.py filename PIT_offset enctype
# python inject.py 0506.bin 0x48E89C cbch
# python inject.py 0611.bin 0xCA0C18 rbrhv
# python inject.py 1104.bin 0xCA2F30 rbrhv
# python inject.py 2030.bin 0xCA305C rbrhv
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import os
from shutil import copyfile
import datetime
from math import ceil
from encode import encode, transposition, loadimage
from libdump import readdump, findpit, loadpit

# PNG support by PIL (if installed)
try:
    from PIL import Image
    PIL = True
except ImportError:
    PIL = False
    print("WARN: Python Imaging Library not found! Only BMP input will supported")


def int_to_bytes(val, num_bytes, endian): # int to binary on both Pythons
    if endian == "little":
        return [(val & (0xff << pos*8)) >> pos*8 for pos in range(num_bytes)]
    elif endian == "big":
        return [(val & (0xff << pos*8)) >> pos*8 for pos in reversed(range(num_bytes))]


def main(filename, offset, enctype):
    print("Trying to build " + filename + " at PIT offset = " + str(offset) + " with enctype = " + enctype)
    
    pit = []
    pb = bytearray()
    pib = bytearray()
    pos = 0
    loc = 0

    dump = readdump(filename)
    if offset < 0: offset = findpit(dump)
    pit_loc = offset
    pit_old = loadpit(dump, offset)

    # remove extension
    point = filename.rfind('.')
    if len(filename) - point < 8: filename_out = filename[:point]
    else: filename_out = filename
    
    # directories management
    filedir = os.path.dirname(filename)
    # for pictures
    if PIL: filedir_pic = os.path.join(filedir, "png")
    else: filedir_pic = os.path.join(filedir, "bmp")
    if not os.path.exists(filedir_pic): os.makedirs(filedir_pic)

    # prepare dump for modifications
    filename_new = filename_out + datetime.datetime.now().strftime("-%Y%m%d%H%M%S") + ".bin"
    copyfile(filename, filename_new)
    
    #TODO need to use dump from memory
    with open(filename_new, "r+b") as fo:
        for filename in os.listdir(filedir_pic):
            if filename.lower().endswith(".png") or filename.lower().endswith(".bmp"):
                # load from popular graphical format
                bitmap, width, height = loadimage(os.path.join(filedir_pic, filename))

                # transform pixels dictionary to decoded data
                decoded = transposition(bitmap, width, height, enctype)

                # encode data
                encoded = encode(decoded)
                enclen = len(encoded)
                
                # modulo / 8 must be 0
                extlen = int(8 * ceil(float(enclen)/8) - enclen)
                for i in range(extlen):
                    encoded.append(0x00)
                
                # append to pit
                pit.append({"pos": pos, "width": width, "height": height, "pit_loc": pit_loc, "loc": loc, "len": enclen})
                info = "pos = "+str(pos)+"\twidth = "+str(width)+"\theight = "+str(height)+"\tlocation = "+str(loc)+"\tlength = "+str(enclen)
                print(info)

                # append to PIB
                if enclen > 65536:
                    mb = 0x0C
                    size_len = 2
                else:
                    mb = 0x0B
                    size_len = 1
                pib.append(mb)
                pib+=bytearray(int_to_bytes(loc, 3, "little"))
                pib+=bytearray(int_to_bytes(enclen, size_len+1, "little"))
                pib+=bytearray(int_to_bytes(width, size_len, "little"))
                pib+=bytearray(int_to_bytes(height, size_len, "little"))
                pib+=bytearray.fromhex("0001000409")
                pit_loc+=10+3*size_len
                # append to PB
                pb+=encoded
                
                loc+=enclen + extlen
                pos+=1
        # some cheks
        # TODO need to cover more cases
        if pit[-1]["pit_loc"] > pit_old[-1]["pit_loc"]: print("ERROR: new PIT bigger than old one! Reduce picture sizes"); sys.exit()
        if pit[-1]["loc"]+pit[-1]["len"] > pit_old[-1]["loc"]+pit_old[-1]["len"]: print("WARN: new PB bigger than old one! Check free space on a dump")
        # write PIB
        fo.seek(offset)
        fo.write(pib)
        # write PB
        fo.seek(8)
        fo.write(pb)

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

    main(filename, offset, enctype)
