import sys
import struct
import zlib



# global function
# calcSum algorithm for ttf
def calcSum(data):
    s = 0
    for i in range(len(data)):
        s += ord(data[i]) << (8 * (3 - (i % 4)))
    return s & 0xFFFFFFFF




class Header:
    
    def __init__(self, src):
        l = struct.unpack("!LHHHH", src[:12])            
        self.scaler_type = l[0]
        self.numTables = l[1]
        self.searchRange = l[2]
        self.entrySelector = l[3]
        self.rangeShift = l[4]


    # requires totalSfntSize... header can't calculate it by himself.
    def outputWoff(self, totalSfntSize):

        s = struct.pack("!4sLLHHLHHLLLLL", "wOFF", self.scaler_type,
                        0, self.numTables, 0, totalSfntSize,
                        1, 0, 0, 0, 0, 0, 0)
        return s        
        
            
    def checkSum(self):
        d = self.data
        if self.tag == "head":
            d = d[:8] + "\0\0\0\0" + d[12:]
        return self.checkSum == calcSum(d)




class Table:

    def __init__(self, src, offset):
        l = struct.unpack("!4sLLL", src[offset : offset + 16])
        self.tag = l[0]
        self.checkSum = l[1]
        self.offset = l[2]
        self.length = l[3]
        self.data = src[self.offset : self.offset + self.length]
        self.compdata = zlib.compress(self.data)

        # store the original length in case of that len(data) will change.
        self.origLength = self.length
        

    def outputWoff(self, diff):
        self.offset += diff
        self.update()
        s = struct.pack("!4sLLLL", self.tag, self.offset,
                        len(self.compdata), self.length, self.checkSum)
        d = (len(self.compdata) - self.origLength)
        return (s, self.compdata, d)    # (out_table, out_data, diff)

        
    def update(self):
        self.length = len(self.data) & 0xFFFFFFFF
        self.compdata = zlib.compress(self.data)
        self.checkSum = calcSum(self.data)



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

        print "before sort############"
        for t in self.tables:
            print t.tag
        print "#####################"
            
        # sort tables with offset
        self.tables.sort(key=lambda x: x.offset)


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


            print t.tag, ": ",
            d = t.data
            if t.tag == "head":
                d = d[:8] + "\0\0\0\0" + d[12:]
            if t.checkSum == calcSum(d):
                print "ok"
            else:
                print "ng"


        with open("loca_data", "wb") as f:
            f.write(self.loca.data)
        with open("glyf_data", "wb") as f:
            f.write(self.glyf.data)
                

        glyf_offsets = struct.unpack("!" + str(self.numGlyphs + 1) + loca_format, self.loca.data)
        print "len(self.loca.data): ", len(self.loca.data)
        print "len(glyf_offsets): ", len(glyf_offsets)
        print "numGlyphs: ", self.numGlyphs

        

    # This converts ttf to woff.
    # woff_header includes totalSfntSize, so generate it after woff_table/woff_data.
    def outputWoff(self):

        woff_header = ""
        woff_table = ""
        woff_data = ""

        offsetDataWoff = 44 + 20 * self.header.numTables
        diff = 0
        
        for t in self.tables:
            o = t.outputWoff(diff)
            woff_table += o[0]
            woff_data += o[1]
            diff += o[2]


        totalSfntSize = 12 + (16 * self.header.numTables)
        
        for t in self.tables:
            t.update()
#            sum_to += t.checkSum
            totalSfntSize += (t.length + 3) & 0xFFFFFFFC

        woff_header = self.header.outputWoff(totalSfntSize)

        
        return (woff_header + woff_table + woff_data)



"""

class Glyf:

    def __init__(self, binary):
        l = struct.unpack("!hhhhh", binary[:10])
        self.numberOfContours = l[0]
        self.xMin = l[1]
        self.yMin = l[2]
        self.xMax = l[3]
        self.yMax = l[4]
        self.data = binary[10:]

        offset = 0
        # for single glyph
        if self.numberOfContours >= 0:
            print "numOfContours: ", self.numberOfContours
            ll = struct.unpack("!" + str(self.numberOfContours + 1) + "H",
                               self.data[:(self.numberOfContours + 1) * 2])
            self.endPtsOfContours = ll[:-1]
            self.instructionLength = ll[-1]
            offset = (self.numberOfContours + 1) * 2
            print "len(data), offset, instlen"
            print len(self.data), offset, self.instructionLength
            self.instructions = \
                struct.unpack("!" + str(self.instructionLength) + "B",
                              self.data[offset : offset + self.instructionLength])

            offset += self.instructionLength

            # read flags
            num_points = 0
            self.flags = []
            xsize_list = []
            ysize_list = []
            xsize = 2
            ysize = 2
            repeat = False
            print "endPts: ", self.endPtsOfContours[-1]
            while num_points <= self.endPtsOfContours[-1]:

                f = self.data[offset]
                print "%4x"%ord(f), 
                
                if repeat:
                    repeat = False
                    num_points += ord(f)
                    xsize_list += [xsize] * ord(f)
                    ysize_list += [ysize] * ord(f)                    
                    
                else:
                    xsize = 1 if (ord(f) & 0x02) == 0x02 else 2
                    ysize = 1 if (ord(f) & 0x04) == 0x04 else 2
                    
                    if (ord(f) & 0x08) == 0x08:
                        repeat = True
                    else:
                        num_points += 1
                        
                    if (ord(f) & 0x02) == 0x02 or (ord(f) & 0x10) != 0x10:
                        print "ax",
                        xsize_list.append(xsize)
                    if (ord(f) & 0x04) == 0x04 or (ord(f) & 0x20) != 0x20:
                        print "ay",
                        ysize_list.append(ysize)

                self.flags.append(f)
                offset += 1
                print ""
                
            print "len(xsize_list): ", len(xsize_list)
            print "len(ysize_list): ", len(ysize_list)
                
            # read coordinates
            self.xCoordinates = []
            for s in xsize_list:
                self.xCoordinates.append(self.data[offset : offset + s])
                offset += s
                
            self.yCoordinates = []
            for s in ysize_list:
                self.yCoordinates.append(self.data[offset : offset + s])
                offset += s


    def output(self):
        header = struct.pack("!Hhhhh", self.xMin, self.yMin, self.xMax, self.yMax)
        return header + self.data



        
        
        


    def update(self):
        oldsum = self.checkSumAdjustment
        
        sum_total = 0
        size_total = 12 + (16 * self.header.numTables)
        
        for t in self.tables:
            t.update()
            sum_total += t.origChecksum
            size_total += (t.origLength + 3) & 0xFFFFFFFC
            
#        sum_total += calcSum(self.src[:44])
            
        self.header.totalSfntSize = size_total
        self.checkSumAdjustment = (0xB1B0AFBA - sum_total) & 0xFFFFFFFF
        print "oldsum: ", oldsum
        print "newsum: ", self.checkSumAdjustment
        
            
    def computeSfntSize(self):
        s = 12
        s += 16 * self.header.numTables
        for t in self.tables:
            s += (t.origLength + 3) & 0xFFFFFFFC
        self.header.totalSfntSize = s
"""

        
if __name__=='__main__':
    if len(sys.argv) != 3:
        print "args error!"
        exit()
    ttf = TTF(sys.argv[1])
    with open(sys.argv[2], "wb") as f:
        f.write(ttf.outputWoff())

