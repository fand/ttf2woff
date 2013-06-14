import struct
import zlib
from tools import *

class Header:
    
    def __init__(self, src):
        l = struct.unpack("!LHHHH", src[:12])            
        self.scaler_type = l[0]
        self.numTables = l[1]
        self.searchRange = l[2]
        self.entrySelector = l[3]
        self.rangeShift = l[4]



    def outputTTF(self):
        return struct.pack("!LHHHH", self.scaler_type,
                           self.numTables, self.searchRange,
                           self.entrySelector, self.rangeShift)

    
        
    # requires totalSfntSize... header can't calculate it by himself.
    def outputWOFF(self, totalSfntSize, totalWoffSize):

        s = struct.pack("!4sLLHHLHHLLLLL",
                        "wOFF",             # signature
                        self.scaler_type,   # flavor
                        totalWoffSize,      # length : Total size of WOFF file
                        self.numTables,     # numTables
                        0,                  # reserved : always 0
                        totalSfntSize,      # totalSfntSize : total size of raw data
                        1,                  # majorVersion
                        0,                  # minorVersion
                        0, 0, 0, 0, 0)      # meta / priv data
        return s        
        
