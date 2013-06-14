import zlib
import struct
from tools import *

class Table:

    def __init__(self, src, offset):
        l = struct.unpack("!4sLLL", src[offset : offset + 16])
        self.tag = l[0]
        self.checkSum = l[1]
        self.offset = l[2]
        self.length = l[3]
        self.data = src[self.offset : self.offset + self.length]
        self.compdata = zlib.compress(self.data)


    def update(self):
        self.length = len(self.data) & 0xFFFFFFFF
        self.compdata = zlib.compress(self.data)
        d = self.data
        if self.tag == "head":
            d = d[:8] + "\0\0\0\0" + d[12:]
        self.checkSum = calcSum(d)

        
    def outputTTF(self):
        self.update()
        return struct.pack("!4sLLL", self.tag, self.checkSum, self.offset, self.length)


        
    def outputWoff(self):
        self.update()
        s = struct.pack("!4sLLLL", self.tag, self.offset,
                        len(self.compdata), self.length, self.checkSum)
        return s


                    
    def checkSum(self):
        d = self.data
        if self.tag == "head":
            d = d[:8] + "\0\0\0\0" + d[12:]
        return self.checkSum == calcSum(d)

