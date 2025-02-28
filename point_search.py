from datetime import datetime
import secp256k1 #https://github.com/iceland2k14/secp256k1
import sys
import time
import math
import cursor    # pip install cursor
import multiprocessing as mp

cursor.hide()
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
block_width = 20
stride_status = 2**block_width
first_scalar  = S_table[start_range - 1]
second_scalar = S_table[start_range - 2]
pre_calc_sum = first_scalar + second_scalar

search_pub = '0307cc34433cb76bf50ee2b2a5227ac06ba3019ee52c6ee0dffdcc8818c627c8e4'
puzzle_point = secp256k1.pub2upub(search_pub)
point_05 = secp256k1.scalar_multiplication(57896044618658097711785492504343953926418782139537452191302581570759080747169)
puzzle_point_05 = secp256k1.point_addition(puzzle_point, point_05)

bloomfile1 = 'bloom1.bf'
print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading bloomfilter {bloomfile1}')
_bits1, _hashes1, _bf1, _fp1, _elem1 = secp256k1.read_bloom_file(bloomfile1)
bloomfile2 = 'bloom2.bf'
print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading bloomfilter {bloomfile2}')
_bits2, _hashes2, _bf2, _fp2, _elem2 = secp256k1.read_bloom_file(bloomfile2)
print(f'[{datetime.now().strftime("%H:%M:%S")}] Each BloomFilter size: 2^{block_width} ({S_table[block_width]})')
print(f'[{datetime.now().strftime("%H:%M:%S")}] Stride size: 2^{int(math.log2(stride_status))} ({stride_status})') 
print(f'[{datetime.now().strftime("%H:%M:%S")}] Search Range: 2^{start_range} .. 2^{end_range} [{S_table[start_range]}-{S_table[end_range]}]')
#==============================================================================
queue = mp.Queue()
G = secp256k1.scalar_multiplication(1)
starttime = time.time()

def addition_search():
    save_counter = 0
    settingsFile = 'settings1.txt'
    settings = open(settingsFile, 'r')
    starting_point = secp256k1.pub2upub(settings.readline().strip())
    stride_sum = int(settings.readline().strip())
    settings.close()
    stride = 2**block_width
    stride_point = secp256k1.scalar_multiplication(stride)
    
    while True:
        cpub = secp256k1.point_to_cpub(starting_point)
        if secp256k1.check_in_bloom(cpub, _bits1, _hashes1, _bf1):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile1} (Even Point) [Lower Range Half]')
            steps = 0
            P = starting_point
            for i in range(2**block_width):
                P = secp256k1.point_subtraction(P, G)
                steps += 1
                if P == puzzle_point:
                    privkey = pre_calc_sum - (stride_sum - steps)
                    privkey *= 2
                    f = open("found_key.txt", "a")
                    f.write(f"{privkey}\n")
                    f.close()
                    queue.put_nowait(privkey)
                    return
            print(f'[{datetime.now().strftime("%H:%M:%S")}] False Positive')
                
            
        if secp256k1.check_in_bloom(cpub, _bits2, _hashes2, _bf2):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile2} (Odd Point) [Lower Range Half]')
            steps = 0
            P = starting_point
            for i in range(2**block_width):
                P = secp256k1.point_subtraction(P, G)
                steps += 1
                if P == puzzle_point_05:
                    privkey = pre_calc_sum - (stride_sum - steps)
                    privkey = (privkey * 2) + 1
                    f = open("found_key.txt", "a")
                    f.write(f"{privkey}\n")
                    f.close()
                    queue.put_nowait(privkey)
                    return
            print(f'[{datetime.now().strftime("%H:%M:%S")}] False Positive')
                
        starting_point = secp256k1.point_addition(starting_point, stride_point)
        stride_sum += stride
        save_counter += 1
        if save_counter % 18000000 == 0:
            cpub = secp256k1.point_to_cpub(starting_point)
            f = open(settingsFile, "w")
            f.write(f"{cpub}\n")
            f.write(f"{stride_sum}\n")
            f.close()
            save_counter = 0
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Save Data written to {settingsFile}')
            
def subtraction_search():
    save_counter = 0
    settingsFile = 'settings2.txt'
    settings = open(settingsFile, 'r')
    starting_point = secp256k1.pub2upub(settings.readline().strip())
    stride_sum = int(settings.readline().strip())
    settings.close()
    stride = 2**block_width
    stride_point = secp256k1.scalar_multiplication(stride)
    
    while True:
        cpub = secp256k1.point_to_cpub(starting_point)
        if secp256k1.check_in_bloom(cpub, _bits1, _hashes1, _bf1):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile1} (Even Point) [Higher Range Half]')
            steps = 0
            P = starting_point
            for i in range(2**block_width):
                P = secp256k1.point_subtraction(P, G)
                steps += 1
                if P == puzzle_point:
                    privkey = pre_calc_sum + (stride_sum + steps)
                    privkey *= 2
                    f = open("found_key.txt", "a")
                    f.write(f"{privkey}\n")
                    f.close()
                    queue.put_nowait(privkey)
                    return
            print(f'[{datetime.now().strftime("%H:%M:%S")}] False Positive')
            
        if secp256k1.check_in_bloom(cpub, _bits2, _hashes2, _bf2):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile2} (Odd Point) [Higher Range Half]')
            steps = 0
            P = starting_point
            for i in range(2**block_width):
                P = secp256k1.point_subtraction(P, G)
                steps += 1
                if P == puzzle_point_05:
                    privkey = pre_calc_sum + (stride_sum + steps)
                    privkey = (privkey * 2) + 1
                    f = open("found_key.txt", "a")
                    f.write(f"{privkey}\n")
                    f.close()
                    queue.put_nowait(privkey)
                    return
            print(f'[{datetime.now().strftime("%H:%M:%S")}] False Positive')
                
        starting_point = secp256k1.point_subtraction(starting_point, stride_point)
        stride_sum += stride
        save_counter += 1
        if save_counter % 18000000 == 0:
            cpub = secp256k1.point_to_cpub(starting_point)
            f = open(settingsFile, "w")
            f.write(f"{cpub}\n")
            f.write(f"{stride_sum}\n")
            f.close()
            save_counter = 0
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Save Data written to {settingsFile}')

def main():    
    p1 = mp.Process(target=addition_search)
    p2 = mp.Process(target=subtraction_search)
    p1.start()
    p2.start()
    data = queue.get()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Privatekey: {data}')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Time taken : %.2f sec' % (time.time()-starttime))
    active = mp.active_children()
    for child in active:
        child.kill()
    out()

def out():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Press <ENTER> to exit')
    input()
    sys.exit()
#============================================================================== 
if __name__ == '__main__':
    main()
