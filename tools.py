# global function
# calcSum algorithm for ttf
def calcSum(data):
    s = 0
    for i in range(len(data)):
        s += ord(data[i]) << (8 * (3 - (i % 4)))
    return s & 0xFFFFFFFF

