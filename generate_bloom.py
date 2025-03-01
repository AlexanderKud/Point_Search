import secp256k1
from datetime import datetime
import os
import sys
import multiprocessing as mp
#============================================================================== 
f_list = ['settings1.txt', 'settings2.txt', 'bloom1.bf', 'bloom2.bf']
arr = os.listdir()
for f in arr:
    if f in f_list:
        os.remove(f)
#==============================================================================
P_table = []
pk = 1;
for i in range(256):
    P_table.append(secp256k1.scalar_multiplication(pk))
    pk *= 2
    
S_table = []
pk = 1
for k in range(256): 
    S_table.append(pk) 
    pk *= 2

print(f"[{datetime.now().strftime("%H:%M:%S")}] S_table and P_table generated")
#==============================================================================
start_range = 44
end_range   = 45
block_width = 22
        
start_point = P_table[start_range]
end_point   = P_table[end_range]
point_05 = secp256k1.scalar_multiplication(57896044618658097711785492504343953926418782139537452191302581570759080747169)

search_pub = '032401b3ea929068ef8d5839b4634edaf0c45f9b4dcface9f1ba1fd44cea064c36'
puzzle_point = secp256k1.pub2upub(search_pub)

puzzle_point_05 = secp256k1.point_addition(puzzle_point, point_05)

puzzle_point_divide2 = secp256k1.point_multiplication(puzzle_point, 57896044618658097711785492504343953926418782139537452191302581570759080747169)

first_point  = P_table[start_range - 1]
second_point = P_table[start_range - 2]

P1 = secp256k1.point_subtraction(puzzle_point_divide2, first_point)
P2 = secp256k1.point_subtraction(puzzle_point_divide2, second_point)
Q1 = secp256k1.point_addition(P1, P2)
Q2 = secp256k1.point_addition(puzzle_point_divide2, Q1)

starting_point = Q2
stride_sum = 0

settingsFile1 = 'settings1.txt'
settingsFile2 = 'settings2.txt'
f1 = open(settingsFile1, "w")
f1.write(f"{secp256k1.point_to_cpub(starting_point)}\n")
f1.write(f"{stride_sum}\n")
f1.close()
f2 = open(settingsFile2, "w")
f2.write(f"{secp256k1.point_to_cpub(starting_point)}\n")
f2.write(f"{stride_sum}\n")
f2.close()
print(f"[{datetime.now().strftime("%H:%M:%S")}] Settings written to file")
#==============================================================================
def bloom_create1():
    bloomfile1 = 'bloom1.bf'
    G = secp256k1.scalar_multiplication(1)
    _elem = (2 * (2**block_width))
    _fp = 0.000001
    _bits, _hashes = secp256k1.bloom_para(_elem, _fp)
    _bf = (b'\x00') * (_bits//8)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Creating bloomfile1')
    P = puzzle_point
    for i in range(2**block_width):
        P = secp256k1.point_addition(P, G)
        secp256k1.add_to_bloom(secp256k1.point_to_cpub(P), _bits, _hashes, _bf)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Writing Bloomfilter to {bloomfile1}')
    secp256k1.dump_bloom_file(bloomfile1, _bits, _hashes, _bf, _fp, _elem)

def bloom_create2():
    bloomfile2 = 'bloom2.bf'
    G = secp256k1.scalar_multiplication(1)
    _elem = (2 * (2**block_width))
    _fp = 0.000001
    _bits, _hashes = secp256k1.bloom_para(_elem, _fp)
    _bf = (b'\x00') * (_bits//8)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Creating bloomfile2')
    P = puzzle_point_05
    for i in range(2**block_width):
        P = secp256k1.point_addition(P, G)
        secp256k1.add_to_bloom(secp256k1.point_to_cpub(P), _bits, _hashes, _bf)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Writing Bloomfilter to {bloomfile2}')
    secp256k1.dump_bloom_file(bloomfile2, _bits, _hashes, _bf, _fp, _elem)

def main():
    p1 = mp.Process(target=bloom_create1)
    p2 = mp.Process(target=bloom_create2)
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    out()
    
def out():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Done. Press <ENTER> to exit...')
    input()
#==============================================================================
if __name__ == '__main__':
    main()
