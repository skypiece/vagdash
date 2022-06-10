# VAG Premium Color dashboard image injector
# https://github.com/skypiece/vagdash
#
# python inject.py filename
#         optional arguments --offset, --enctype, --picdir
# python inject.py 0506.bin --offset 0x48E89C --enctype cbch
# python inject.py 0611.bin --offset 0xCA0C18 --enctype rbrhv
# python inject.py 1104.bin
# python inject.py 2030.bin
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import os
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


def main(filename, offset, enctype, picdir):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Trying to build " + filename + " with enctype = " + enctype)
    
    # process existing dump
    dump = readdump(filename)
    if offset < 0: offset = findpit(dump)
    pit_loc = offset
    pit_old = loadpit(dump, offset)

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
    # new dump
    filename_new = filename_out + datetime.datetime.now().strftime("-%Y%m%d%H%M%S") + ".bin"

    # process new dump
    with open(filename_new, "wb") as fo:
        # copy old data
        fo.write(dump)

        pics = []
        pb = bytearray()
        pib = bytearray()
        pos = 0
        loc = 0
        for filename in os.listdir(picdir_pic):
            if filename.lower().endswith(".png") or filename.lower().endswith(".bmp"):
                # load from popular graphical format
                bitmap, width, height = loadimage(os.path.join(picdir_pic, filename))

                # transform pixels dictionary to decoded data
                decoded = transposition(bitmap, width, height, enctype)

                # encode data
                encoded = encode(decoded)
                enclen = len(encoded)
                
                # modulo / 8 must be 0
                extlen = int(8 * ceil(float(enclen)/8) - enclen)
                for i in range(extlen):
                    encoded.append(0x00)
                
                # append to pics
                pics.append({"pos": pos, "width": width, "height": height, "pit_loc": pit_loc, "loc": loc, "len": enclen})
                info = "pos = "+str(pos)+"\twidth = "+str(width)+"\theight = "+str(height)+"\tlocation = "+str(loc)+"\tlength = "+str(enclen)
                print(info)

                # append to PIB
                if enclen > 65536:
                    mb = 0x0C
                    size_len = 2
                else:
                    mb = 0x0B
                    size_len = 1
                #TODO move PIB from PIT creation to function
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
        # some checks
        # TODO need to cover more cases
        if pics[-1]["pit_loc"] > pit_old["pics"][0][-1]["pit_loc"]: print("ERROR: new PIT bigger than old one! Reduce picture sizes"); sys.exit()
        if pics[-1]["loc"]+pics[-1]["len"] > pit_old["pics"][0][-1]["loc"]+pit_old["pics"][0][-1]["len"]: print("WARN: new PB bigger than old one! Check free space on a dump manually")
        # write PIB
        fo.seek(offset)
        fo.write(pib)
        # write PB
        fo.seek(pit_old["pb_offset"])
        fo.write(pb)

    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Complete")


if __name__ == '__main__':
    # defaults
    offset = -1
    enctype = "rbrhv"
    picdir = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            if sys.argv[i] == "--offset": offset = int(sys.argv[i+1], base=16); i+=1
            if sys.argv[i] == "--enctype": enctype = sys.argv[i+1]; i+=1
            if sys.argv[i] == "--picdir": picdir = sys.argv[i+1]; i+=1
        i+=1

    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        filename = sys.argv[1]
    else:
        print("ERROR: filename must be specified")
        sys.exit()

    main(filename, offset, enctype, picdir)
