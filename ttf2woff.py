import sys
import struct
import zlib

from table import Table
from header import Header
from tools import *


class TTF:

    def __init__(self, path):

        with open(path, "rb") as f:
            self.src = f.read()

        self.header = Header(self.src)
        
        self.offsetData = 12 + 16 * self.header.numTables

        
        self.tables = []
        for i in range(self.header.numTables):
            idx = 12 + 16 * i
            self.tables.append(Table(self.src, idx))

        # sort tables with offset
#        self.tables.sort(key=lambda x: x.offset)

        # get global properties
        for t in self.tables:
            if t.tag == "head":
                self.checkSumAdjustment = struct.unpack("!L", t.data[8:12])[0]
                # byte length of loca values
                if ord(t.data[-3]) == 0:
                    loca_format = "H"
                    loca_size = 2
                else:
                    loca_format = "L"
                    loca_size = 4
                    
            elif t.tag == "maxp":
                self.numGlyphs = struct.unpack("!H", t.data[4:6])[0]

            elif t.tag == "loca":
                self.loca = t

            elif t.tag == "glyf":
                self.glyf = t


        glyf_offsets = struct.unpack("!" + str(self.numGlyphs + 1) + loca_format, self.loca.data)
        print "len(self.loca.data): ", len(self.loca.data)
        print "len(glyf_offsets): ", len(glyf_offsets)
        print "numGlyphs: ", self.numGlyphs


        
    # check checksum for all table
    def checkTables(self):
        for t in self.tables:
            print t.tag, ": ",
            d = t.data
            if t.tag == "head":
                d = d[:8] + "\0\0\0\0" + d[12:]
            if t.checkSum == calcSum(d):
                print "ok"
            else:
                print "ng"

        

    # dump table for debug
    def dumpTable(self, name):
        for t in self.tables:
            if t.tag == name:
                with open(t.tag + "_data", "wb") as f:
                    f.write(t.data)
                
        
        
    def outputTTF(self):

        ttf_header = ""
        ttf_table = ""
        ttf_data = ""        

        # make sure tables are sorted by offset
        self.tables.sort(key=lambda x: x.offset)        

        # prepare totalSfntSize for sfnt_header
        offset_new = 12 + (16 * self.header.numTables)


        # FIRST: generate ttf_data, and calculate offset
        offsets = {}
        offset_data = 0
        for t in sorted(self.tables, key=lambda x: x.offset):
            offsets[t.tag] = offset_new
            ttf_data += t.data

            if self.src[offset_new:offset_new+t.length] == t.data and ttf_data[offset_data : offset_data + t.length] == t.data:
                print t.tag, "same"
            else:
                print t.tag, "different"

            # insert paddings
            if t.length % 4 != 0:
                ttf_data += "\0" * (4 - (t.length % 4))

            # update offset, including paddings
            offset_data += (t.length + 3) & 0xFFFFFFFC
            offset_new += (t.length + 3) & 0xFFFFFFFC

        
        # SECOND: generate ttf_table
        for t in self.tables:
            t.offset = offsets[t.tag]
            ttf_table += t.outputTTF()


        # THIRD: generate ttf_header
        ttf_header = self.header.outputTTF()



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


        
        

    # This converts ttf to woff.
    # woff_header includes totalSfntSize,
    # and woff_table and woff_data will be generated simultaneous
    # (coz they're stored in same object: Table)
    # so output must follow next steps:
    # (woff_table + woff_table) -> woff_header
    def outputWOFF(self):

        woff_header = ""
        woff_table = ""
        woff_data = ""

        # make sure tables are sorted by offset
        self.tables.sort(key=lambda x: x.offset)        

        # offset for 1st data is fixed; it depends only on numTables.
        offset_data = 44 + 20 * self.header.numTables

        # prepare totalSfntSize for woff_header
        totalSfntSize = 12 + 16 * self.header.numTables
        
        # generate woff_table and woff_data
        for t in self.tables:
            t.offset = offset_data
            woff_table += t.output()
            woff_data += t.compdata
            offset_data += len(t.compdata)
            if (offset_data % 4 != 0):
                woff_data += "\0" * (4 - (offset_data % 4))
                offset_data += (4 - (offset_data % 4))


            # get len(t.length + padding)
            # t.length is for t.data (not t.compdata)... is this ok?
            totalSfntSize += (t.length + 3) & 0xFFFFFFFC


        # Now, it's time to generate woff_header!
        self.header.totalSfntSize = totalSfntSize
        totalWoffSize = len(woff_table) + len(woff_data) + 44
        woff_header = self.header.outputWoff(totalSfntSize, totalWoffSize)
        
        return (woff_header + woff_table + woff_data)

    
        
if __name__=='__main__':
    if len(sys.argv) != 3:
        print "args error!"
        exit()
    ttf = TTF(sys.argv[1])
    ttf.dumpTable("head")
    ttf.checkTables()
    
    with open(sys.argv[2], "wb") as f:
        f.write(ttf.outputTTF())

