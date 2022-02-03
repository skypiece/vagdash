# VAG Premium Color dashboard image extractor
# https://github.com/skypiece/vagdash
#
# python extract.py filename PIT_offset enctype save_binaries(optional)
# python extract.py 0506.bin 0x48E89C cbch 1
# python extract.py 0611.bin 0xCA0C18 rbrhv
# python extract.py 1104.bin 0xCA2F30 rbrhv
# python extract.py 2030.bin 0xCA305C rbrhv
#
# cbch  bitmaps stored column by column with horizontal flip
# rbrhv bitmaps stored row by row with horizontal and vertical flip
import sys
import codecs
from decode import decode, transposition, saveimage


def main(filename, offset, enctype, save_bin):
    print("Trying to decode", filename, "at PIT offset =", offset, "with enctype =", enctype)
    with open(filename, "rb") as fi:
        PIT = []
        pos = 0

        #TODO need to improve i/o for slow devices by reading blocks
        meta = fi.read(1) # just read something
        fi.seek(offset) # goto PIT
        while meta:
            pit_loc = fi.tell()
            mb = int(codecs.encode(fi.read(1), 'hex'), 16) # binary to int
            if mb == 11:    # 0x0B
                size_len = 1
            elif mb == 12:  # 0x0C
                size_len = 2
            else:
                print("WARN: unexpected value mb =", mb, "at", fi.tell(), "; PIT ended?"); break

            loc = int(codecs.encode(fi.read(3)[::-1], 'hex'), 16)
            lenght = int(codecs.encode(fi.read(size_len + 1)[::-1], 'hex'), 16)
            width = int(codecs.encode(fi.read(size_len)[::-1], 'hex'), 16)
            height = int(codecs.encode(fi.read(size_len)[::-1], 'hex'), 16)
            meta = fi.read(5) # what means this bytes?
            PIT.append({"pos": pos, "width": width, "height": height, "pit_loc": pit_loc, "loc": loc, "len": lenght})
            pos+=1

        # remove extension
        point = filename.rfind('.')
        if len(filename) - point < 8: filename_out = filename[:point]
        else: filename_out = filename

        # PIT processing
        with open(filename_out + ".txt", "w") as foi:
            foi.write("### locations in a PIT need to shift by +8 in real dump\n")
            for pic in PIT:
                info = "pos = "+str(pic["pos"])+"\twidth = "+str(pic["width"])+"\theight = "+str(pic["height"])+"\tpit_location = "+str(pic["pit_loc"])+"\tlocation = "+str(pic["loc"])+"\tlength = "+str(pic["len"])
                print(info)
                foi.write(info+"\n")
                foname = filename_out + "-" + str(pic["pos"]).zfill(4)
                # read encoded data
                fi.seek(pic["loc"]+8)
                encoded = fi.read(pic["len"])
                # save to another bin file
                if save_bin == 1:
                    with open(foname + ".bin", "wb") as fo:
                        fo.write(encoded)
                # decode data
                decoded = decode(encoded, pic["len"])
                declen = len(decoded)
                # transform decoded data to pixels dictionary
                bitmap = transposition(decoded, declen, pic["width"], pic["height"], enctype)
                # save into popular graphical format
                saveimage(foname, bitmap, pic["width"], pic["height"])

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
        print("ERROR: PIT search not supported yet")
        sys.exit()

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
