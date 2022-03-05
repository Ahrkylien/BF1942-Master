from random import randint


# A translated and fixed version of Luigi's enctype2 C code
# read ServerListReadList() in the linux server binary for extra info

def crypt_encrypt(tbuff: list, tbuffp: int, len: int):
    t2 = tbuff[304]
    t1 = tbuff[305]
    t3 = tbuff[306]
    t5 = tbuff[307]
    t4 = 0
    for i in range(len):
        p = t2 + 272
        while t5 < 65536:
            t1 += t5
            t1 &= 0xFFFFFFFF
            p += 1
            t3 += t1
            t3 &= 0xFFFFFFFF
            t1 += t3
            t1 &= 0xFFFFFFFF
            tbuff[p-17] = t1
            tbuff[p-1] = t3
            tbuff[p+15] = t5
            t4 = ((t3 << 24) | (t3 >> 8)) & 0xFFFFFFFF
            t5 <<= 1
            t5 &= 0xFFFFFFFF
            t2 += 1
            t2 &= 0xFFFFFFFF
            t1 ^= tbuff[t1 & 0xff]
            t4 ^= tbuff[t4 & 0xff]
            t3 = ((t4 << 24) | (t4 >> 8)) & 0xFFFFFFFF
            t4 = ((t1 >> 24) | (t1 << 8)) & 0xFFFFFFFF
            t4 ^= tbuff[t4 & 0xff]
            t3 ^= tbuff[t3 & 0xff]
            t1 = ((t4 >> 24) | (t4 << 8)) & 0xFFFFFFFF
        t3 ^= t1
        m=tbuffp%4
        mask2 = 2**(8*(4-m))-1
        mask1 = 0xFFFFFFFF-mask2
        tbuff[tbuffp//4+i] = (tbuff[tbuffp//4+i]&mask1) | (t3>>8*m)
        tbuff[tbuffp//4+1+i] = (tbuff[tbuffp//4+1+i]&mask2) | ((t3<<8*(4-m))&0xFFFFFFFF)
        if t2 == 0:
            t2 = 0xFFFFFFFF
        else:
            t2 -= 1
        t1 = tbuff[t2 + 256]
        t5 = tbuff[t2 + 272]
        t1 = ~t1
        t1 &= 0xFFFFFFFF
        t3 = ((t1 << 24) | (t1 >> 8)) & 0xFFFFFFFF
        t3 ^= tbuff[t3 & 0xff]
        t5 ^= tbuff[t5 & 0xff]
        t1 = ((t3 << 24) | (t3 >> 8)) & 0xFFFFFFFF
        t4 = ((t5 >> 24) | (t5 << 8)) & 0xFFFFFFFF
        t1 ^= tbuff[t1 & 0xff]
        t4 ^= tbuff[t4 & 0xff]
        t3 = ((t4 >> 24) | (t4 << 8)) & 0xFFFFFFFF
        t5 = ((tbuff[t2 + 288] << 1) + 1) & 0xFFFFFFFF
        
    tbuff[304] = t2
    tbuff[305] = t1
    tbuff[306] = t3
    tbuff[307] = t5

def crypt_docrypt(tbuff: list, data, datap, len: int):
    s = 309*4
    p = 309*4
    crypt_encrypt(tbuff,p,16)
    for i in range(len):
        if p - s == 63:
            p = s
            crypt_encrypt(tbuff, p, 16)
        tbuff_byte = (tbuff[p//4]>>((p%4)*8))&255 #not int
        data[datap+i] ^= tbuff_byte
        p += 1
    
def crypt_seek(data, n1: int, n2: int):
    t2 = n1
    t1 = 0
    t4 = 1
    data[304] = 0
    i = 32768
    while i != 0:
        t2 += t4
        t2 &= 0xFFFFFFFF
        t1 += t2
        t1 &= 0xFFFFFFFF
        t2 += t1
        t2 &= 0xFFFFFFFF
        if n2 & i:
            t2 = (~t2) & 0xFFFFFFFF
            t4 = ((t4 << 1) + 1) & 0xFFFFFFFF
            t3 = ((t2 << 24) | (t2 >> 8)) & 0xFFFFFFFF
            t3 ^= data[t3 & 0xff]
            t1 ^= data[t1 & 0xff]
            t2 = ((t3 << 24) | (t3 >> 8)) & 0xFFFFFFFF
            t3 = ((t1 >> 24) | (t1 << 8)) & 0xFFFFFFFF
            t2 ^= data[t2 & 0xff]
            t3 ^= data[t3 & 0xff]
            t1 = ((t3 >> 24) | (t3 << 8)) & 0xFFFFFFFF
        else:
            data[data[304] + 256] = t2
            data[data[304] + 272] = t1
            data[data[304] + 288] = t4
            data[304] += 1
            t3 = ((t1 << 24) | (t1 >> 8)) & 0xFFFFFFFF
            t2 ^= data[t2 & 0xff]
            t3 ^= data[t3 & 0xff]
            t1 = ((t3 << 24) | (t3 >> 8)) & 0xFFFFFFFF
            t3 = ((t2 >> 24) | (t2 << 8)) & 0xFFFFFFFF
            t3 ^= data[t3 & 0xff]
            t1 ^= data[t1 & 0xff]
            t2 = ((t3 >> 24) | (t3 << 8)) & 0xFFFFFFFF
            t4 <<= 1
            t4 &= 0xFFFFFFFF
        i >>= 1
    data[305] = t2
    data[306] = t1
    data[307] = t4
    data[308] = n1

def init_crypt_key(src, dest):
    size = len(src)
    for i in range(256):
        dest[i] = 0
    for y in range(4):
        for i in range(256):
           dest[i] = (dest[i] << 8) + i
        pos = y
        for x in range(2):
            for i in range(256):
                tmp = dest[i]
                pos += tmp + src[(i % size)]
                pos &= 255 #unsigned byte
                dest[i] = dest[pos]
                dest[pos] = tmp
    for i in range(256):
        dest[i] ^= i
    crypt_seek(dest, 0, 0)

def enctype2_decoder(key: str, data):
    size = len(data)
    seed = [0] * 326
    
    #xor headerSize byte
    data[0] ^= 0xec
    header_size = data[0]
    #point to start of header:
    datap = 1
    
    #xor the header with the key:
    for i in range(len(key)):
        data[datap+i] ^= ord(key[i])
    
    #fill seed based on header:
    if header_size > 0:
        init_crypt_key(data[1:1+header_size], seed)
    
    #point to start of data:
    datap += header_size
    #substract headerSize + 1:
    size -= header_size + 1
    
    #safety check:
    if header_size < 6:
        header_size = 0
        return(data)
    
    #use seed to fill datap:
    crypt_docrypt(seed, data, datap, size)
    
    size -= 7
    
    return(data[datap:datap+size])

#eventual data looks like: <headerSize (1 byte)><header (6 bytes)><data (size bytes)><'\final\' (7 bytes)>
def enctype2_encoder(key,dataIn):
    dataIn_size = len(dataIn)
    
    header_size = randint(6, 14) #ssks headersize is in the range 6,14
    header = [randint(0, 255) for i in range(header_size)]
    footer = list("\\final\\".encode())
    
    data = [header_size] + header + dataIn + footer
    
    #point to start of header:
    datap = 1
    
    #fill seed based on header:
    seed = [0] * 326
    init_crypt_key(data[1:1+header_size], seed)
    #re-fill data based on seed:
    crypt_docrypt(seed, data, datap + header_size, dataIn_size + 7)
    
    #xor the header with the key:
    for i in range(len(key)):
       data[datap+i] ^= ord(key[i])
    
    #xor headerSize byte:
    data[0] ^= 0xec
    return(data)