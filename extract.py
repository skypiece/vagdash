# VAG Premium Color dashboard image extractor
# https://github.com/skypiece/vagdash
#
# python extract.py filename PIT_offset enctype
# python extract.py 0506dump.bin 0x48E89C cbch
# python extract.py 1104dump.bin 0xCA2F30 rbrhv
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import os
import codecs


if len(sys.argv) > 1:
    filename = sys.argv[1]
    # remove extension
    point = filename.rfind('.')
    if len(filename) - point < 8: filename_out = filename[:point]
    else: filename_out = filename
else:
    print("ERROR: filename must be specified")
    sys.exit()

if len(sys.argv) > 2:
    offset = int(sys.argv[2], base=16)
else:
    print("ERROR: PIT search not supported yet")
    sys.exit()

if len(sys.argv) > 3:
    enctype = sys.argv[3]
else:
    print("ERROR: autodetection of bitmap orientation is not supported yet")
    sys.exit()


print("Trying to decode", filename, "at PIT offset =", offset, "with enctype =", enctype)
with open(filename, "rb") as fi:
    PIT = []
    pos = 0

    #TODO need to improve i/o for slow devices by reading blocks
    meta = fi.read(1) # just read something
    fi.seek(offset) # goto PIT
    while meta:
        mb = int(codecs.encode(fi.read(1), 'hex'), 16) # binary to int
        if mb == 11:    # 0x0B
            size_len = 1
        elif mb == 12:  # 0x0C
            size_len = 2
        else:
            print("WARN: unexpected value mb =", mb, "at", fi.tell(), "; PIT ended?"); break

        loc = int(codecs.encode(fi.read(3)[::-1], 'hex'), 16)
        len = int(codecs.encode(fi.read(size_len + 1)[::-1], 'hex'), 16)
        width = int(codecs.encode(fi.read(size_len)[::-1], 'hex'), 16)
        height = int(codecs.encode(fi.read(size_len)[::-1], 'hex'), 16)
        meta = fi.read(5) # what means this bytes?
        PIT.append({"pos": pos, "width": width, "height": height, "loc": loc, "len": len})
        pos+=1


    foi = open(filename_out + ".txt", "w")
    for pic in PIT:
        info = "pos = "+str(pic["pos"])+"\twidth = "+str(pic["width"])+"\theight = "+str(pic["height"])+"\tlocation = "+str(pic["loc"])+"\tlength = "+str(pic["len"])
        print(info)
        foi.write(info+"\n")
        #TODO need to remove create small bins; functions?!
        # save to another file
        foname = filename_out + "-" + str(pic["pos"]).zfill(4) + ".bin"
        with open(foname, "wb") as fo:
            pos_cur = fi.tell()
            fi.seek(pic["loc"]+8)
            buf = fi.read(pic["len"])
            fi.seek(pos_cur)

            fo.write(buf)
        fo.close()
        # decode to popular graphical format
        os.system("python decode.py \"" + foname + "\" " + enctype + " " + str(pic["width"]) + " " + str(pic["height"]))
    foi.close()

print("Complete")
#input()
