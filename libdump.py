# VAG Premium Color dashboard dump lib
# https://github.com/skypiece/vagdash

import codecs

def readdump(filename):
    with open(filename, "rb") as fi:
        return fi.read()

def findpit(dump):
    offset = -1
    pos = dump.find(bytearray.fromhex("0001000409"))
    if dump[pos-10] == 0x0C: offset = pos-10
    elif dump[pos-8] == 0x0B: offset = pos-8
    return offset

def loadpit(dump, offset):
    pit = []
    pos = offset
    cnt = 0
    while True:
        pit_loc = pos
        mb = int(codecs.encode(dump[pos : pos+1], 'hex'), 16) # binary to int
        if mb == 11:    # 0x0B
            size_len = 1
        elif mb == 12:  # 0x0C
            size_len = 2
        else:
            #print("WARN: unexpected value mb =", mb, "at", pos, "; PIT ended?")
            break
        pos+=1

        loc = int(codecs.encode(dump[pos : pos+3][::-1], 'hex'), 16); pos+=3
        lenght = int(codecs.encode(dump[pos : pos+size_len+1][::-1], 'hex'), 16); pos+=size_len+1
        width = int(codecs.encode(dump[pos : pos+size_len][::-1], 'hex'), 16); pos+=size_len
        height = int(codecs.encode(dump[pos : pos+size_len][::-1], 'hex'), 16); pos+=size_len
        meta = dump[pos : pos+5]; pos+=5 # what means these bytes?
        pit.append({"pos": cnt, "width": width, "height": height, "pit_loc": pit_loc, "loc": loc, "len": lenght})
        cnt+=1
    return pit
