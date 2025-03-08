import secp256k1
from datetime import datetime
import time
import os
import sys
import multiprocessing as mp
#============================================================================== 
f_list = ['x_settings1.txt', 'x_settings2.txt', 'xor_bloom1.xf', 'xor_bloom2.xf']
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

print(f"[{datetime.now().strftime("%H:%M:%S")}] P_table generated")
#==============================================================================
start_range = 51
end_range   = 52
block_width = 24
        
start_point = P_table[start_range]
end_point   = P_table[end_range]
point_05 = secp256k1.scalar_multiplication(57896044618658097711785492504343953926418782139537452191302581570759080747169)

search_pub = '03eb708c5acebf58263f5af63b63f9f75b9f7a211d80c833237f37911da350796f'
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

settingsFile1 = 'x_settings1.txt'
settingsFile2 = 'x_settings2.txt'
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
bloom_inc = 1.5
chunk_divisor = int(2**block_width // 1000000)

def bloom_create1():
    bloomfile1 = 'xor_bloom1.xf'
    G = secp256k1.scalar_multiplication(1)
    _elem = int(bloom_inc * (2**block_width))
    _fp = 0.000001
    _bits, _hashes = secp256k1.xor_para(_elem, _fp)
    _xf = (b'\x00') * ((_bits + 7) // 8)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Creating xor_bloom1')
    P = puzzle_point
    points = []
    add_counter = 0
    chunk = 2**block_width // chunk_divisor
    for i in range(2**block_width):
        points.append(secp256k1.point_to_cpub(P))
        P = secp256k1.point_addition(P, G)
        add_counter += 1
        if add_counter % chunk == 0:
            secp256k1.add_list_to_xor(tuple(points), _bits, _hashes, _xf)
            add_counter = 0
            points.clear()
                
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Writing Bloomfilter to {bloomfile1}')
    secp256k1.dump_xor_file(bloomfile1, _bits, _hashes, _xf, _fp, _elem)

def bloom_create2():
    bloomfile2 = 'xor_bloom2.xf'
    G = secp256k1.scalar_multiplication(1)
    _elem = int(bloom_inc * (2**block_width))
    _fp = 0.000001
    _bits, _hashes = secp256k1.xor_para(_elem, _fp)
    _xf = (b'\x00') * ((_bits + 7) // 8)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Creating xor_bloom2')
    P = puzzle_point_05
    points = []
    add_counter = 0
    chunk = 2**block_width // chunk_divisor
    for i in range(2**block_width):
        points.append(secp256k1.point_to_cpub(P))
        P = secp256k1.point_addition(P, G)
        add_counter += 1
        if add_counter % chunk == 0:
            secp256k1.add_list_to_xor(tuple(points), _bits, _hashes, _xf)
            add_counter = 0
            points.clear()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Writing Bloomfilter to {bloomfile2}')
    secp256k1.dump_xor_file(bloomfile2, _bits, _hashes, _xf, _fp, _elem)

def main():
    p1 = mp.Process(target=bloom_create1)
    p2 = mp.Process(target=bloom_create2)
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    out()
    
def out():
    elapsed_time = time.time() - start_time
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Time taken: hours:{int(hours)} minutes:{int(minutes)} seconds:{int(seconds)}')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Done. Press <ENTER> to exit...')
    input()
#==============================================================================
if __name__ == '__main__':
    start_time = time.time()    
    main()
