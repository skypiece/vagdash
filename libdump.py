# VAG Premium Color dashboard dump lib
# https://github.com/skypiece/vagdash

import codecs
from math import ceil


def readdump(filename):
    with open(filename, "rb") as fi:
        return bytearray(fi.read())


def findpit(dump):
    return findpit_shift(dump, 0)


def findpit_shift(dump, shift):
    offset = -1
    mb1 = bytearray.fromhex("0001000409")  # "".join(map(chr, mb))
    mb2 = bytearray.fromhex("0001010408")
    mb3 = bytearray.fromhex("000100040B")
    tmp = [dump.find(mb1, shift), dump.find(mb2, shift), dump.find(mb3, shift)]
    pos = min(filter(lambda score: score >= 1, tmp))
    if dump[pos-10] == 0x0C:
        offset = pos-10
    elif dump[pos-8] == 0x0B:
        offset = pos-8
    print("PicturesInformationTable found at offset="+str(offset))
    return offset


def findpb(dump, adr):
    offset = 0
    dumplen = len(dump)
    if dumplen > adr:
        if dump[adr + 3] == 0x9f and dump[adr] > 0x00:  # 0x9f virtual address for bitmaps
            if dumplen <= 8388608:
                #64 Mbit dumps : remove 8 bit from +2 byte
                offset = ((dump[adr + 2] & ~(1 << 7)) <<
                          16) | (dump[adr + 1] << 8) | dump[adr]
            else:
                offset = ((dump[adr + 2]) <<
                          16) | (dump[adr + 1] << 8) | dump[adr]
                #int(codecs.encode(dump[adr+4 : adr+4+3][::-1], 'hex'), 16)
            print("PicturesBinary found at offset="+str(offset))
            if offset > len(dump):
                offset = 0  # something going wrong
        else:
            offset = findpb(dump, adr + 4)  # recoursive search here
    return offset


def loadpit(dump, offset):
    pit = {}
    pics = []
    pos = offset
    cnt = 0
    while True:
        pit_loc = pos
        mb = dump[pos]
        if mb == 11:    # 0x0B
            size_len = 1
        elif mb == 12:  # 0x0C
            size_len = 2
        else:
            #print("WARN: unexpected value mb =", mb, "at", pos, "; PIT ended?")
            break
        pos += 1

        loc = int(codecs.encode(dump[pos : pos+3][::-1], 'hex'), 16); pos+=3
        lenght = int(codecs.encode(dump[pos : pos+size_len+1][::-1], 'hex'), 16); pos+=size_len+1
        width = int(codecs.encode(dump[pos : pos+size_len][::-1], 'hex'), 16); pos+=size_len
        height = int(codecs.encode(dump[pos : pos+size_len][::-1], 'hex'), 16); pos+=size_len
        meta = dump[pos : pos+5]; pos+=5 # what means these bytes?
        pics.append({"pos": cnt, "width": width, "height": height, "pit_loc": pit_loc, "loc": loc, "len": lenght, "meta": meta})
        cnt+=1
    pit.update({"pics": pics})
    # read bitmap offset from following bytes
    adr = int(4 * ceil(float(pos)/4))  # round end of PIT
    pb_offset = findpb(dump, adr+4)
    pit.update({"pb_adr_offset": adr})
    pit.update({"pb_offset": pb_offset})
    return pit
