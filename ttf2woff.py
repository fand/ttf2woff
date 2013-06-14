import os
import sys
import struct
import zlib
from collections import OrderedDict

# import ttf classes
from table import Table
from header import Header
from tools import *

#for debug
import binascii


class TTF:

    def __init__(self, path):

        with open(path, "rb") as f:
            self.src = f.read()

        self.header = Header(self.src)
        
        self.offsetData = 12 + 16 * self.header.numTables

        
        self.tables = OrderedDict()
        for i in range(self.header.numTables):
            idx = 12 + 16 * i
            t = Table(self.src, idx)
            self.tables[t.tag] = t
            
            if t.tag == "loca":
                print binascii.b2a_hex(t.data[-3])
                

        # sort tables with offset
#        self.tables.sort(key=lambda x: x.offset)

        # get global properties
        head = self.tables["head"]
        self.checkSumAdjustment = struct.unpack("!L", head.data[8:12])[0]
        head.data = head.data[:8] + "\0\0\0\0" + head.data[12:]
        
        # byte length of loca values
        loca = self.tables["loca"]
        if (ord(head.data[-1]) & 0xFF) >> 4 == 0:
            loca_format = "H"
            loca_size = 2
        else:
            loca_format = "L"
            loca_size = 4

        self.numGlyphs = struct.unpack("!H", self.tables["maxp"].data[4:6])[0]

        print "loca_format: ", loca_format
        print "len(self.loca.data): ", len(loca.data)
        print "numGlyphs: ", self.numGlyphs
        glyf_offsets = struct.unpack("!" + str(self.numGlyphs + 1) + loca_format, loca.data)
        print "len(glyf_offsets): ", len(glyf_offsets)

        
    # check checksum for all table
    def checkTables(self):
        for k,t in self.tables.items():
            tmp = t.data
            if k == "head":
                tmp = tmp[:8] + "\0\0\0\0" + tmp[12:]
            if t.checkSum == calcSum(tmp):
                print k, ": ok"
            else:
                print k, ": ng"

        

    # dump table for debug
    def dumpTable(self, name):
        if not(name in self.tables):
            return
        with open(name + "_data", "wb") as f:
            f.write(self.tables[k].data)
                

            
    def outputTTF(self):

        ttf_header = ""
        ttf_table = ""
        ttf_data = ""        

        # make sure tables are sorted by offset
#        self.tables.sort(key=lambda x: x.offset)

        # compute offsets for data
        offset_new = 0

        # offset for ttf_data = len(ttf_header + ttf_table)
        offset_data = 12 + (16 * self.header.numTables)

        # for checkSumAdj
        offset_csa = 0
        totalSum = 0

        
        # FIRST: generate ttf_data, and calculate offset
        offsets = {}

        for k, t in sorted(self.tables.items(), key=lambda x: x[1].offset):
            offsets[k] = offset_new
            ttf_data += t.data

            # insert paddings
            if t.length % 4 != 0:
                ttf_data += "\0" * (4 - (t.length % 4))

            # check the data with src
            left = offset_data + offset_new
            if (self.src[left : left + t.length] == t.data and 
                ttf_data[offset_new : offset_new + t.length] == t.data):
                print k, ": same"
            else:
                print k, ": different"

            # for checkSumAdjustment.
            totalSum += t.checkSum
                
            # update offset, including paddings
            offset_new += (t.length + 3) & 0xFFFFFFFC

            
        
        # SECOND: generate ttf_table
        for k,t in self.tables.items():
            t.offset = offsets[k] + offset_data
            ttf_table += t.outputTTF()


        # THIRD: generate ttf_header
        ttf_header = self.header.outputTTF()


        # now we gotta calculate checkSumAdjustment in head table.
        offset_csa = offsets["head"] + 8
        if ttf_data[offset_csa:offset_csa+4] == "\0\0\0\0":
            print "csa is \\0\\0\\0\\0, it's ok!"

        num_int32 = (12 + (16 * self.header.numTables)) / 4
        totalSum += sum(struct.unpack("!" + str(num_int32) + "L", ttf_header + ttf_table))

        csa_old = self.src[offset_data + offset_csa : offset_data + offset_csa + 4]
        csa = (0xB1B0AFBA - totalSum) & 0xFFFFFFFF
        print "old csa: ", binascii.b2a_hex(csa_old)
        print "new csa: ", binascii.b2a_hex(struct.pack("!L", csa))
        
        ttf_data = ttf_data[:offset_csa] + struct.pack("!L", csa) + ttf_data[(offset_csa+4):]


        head = self.tables["head"]
        left = head.offset + offset_data
        if self.src[left : left + head.length] == head.data:
            print "head: same"
        else:
            print "head: different"
            

        # check values with self.src
        if ttf_header == self.src[:12]:
            print "header: same"
        else:
            print "header: different"

        if ttf_table == self.src[12:12+(16*self.header.numTables)]:
            print "table: same"
        else:
            print "table: different"

        if ttf_data == self.src[12+(16*self.header.numTables):]:
            print "data: same"
        else:
            print "data: different"
            
        s = (ttf_header + ttf_table + ttf_data)        
        if s == self.src:
            print "all same!!!"
        else:
            print "all differ..."
        
        return s


    def glitch(self):
        pass

    
    
        
if __name__=='__main__':
    if len(sys.argv) != 3:
        print "args error!"
        exit()
        
    ttf = TTF(sys.argv[1])

#    ttf.dumpTable("head")
#    ttf.checkTables()
#    ttf.glitch()
    
    with open("tmp.ttf", "wb") as f:
        f.write(ttf.outputTTF())

    os.system("woff-code-latest/sfnt2woff tmp.ttf")

    with open("tmp.woff", "rb") as f:
        out = f.read()

    with open(sys.argv[2], "wb") as f:
        f.write(out)

        

        

