


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
