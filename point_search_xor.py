from datetime import datetime
import secp256k1
import sys
import time
import math
import cursor
import multiprocessing as mp

cursor.hide()
#==============================================================================
def break_down_to_pow10(num):
    nums = []
    num_len = len(str(num)) - 1
    for pw in reversed(range(num_len)):
        nums.append(pow(10, pw))
    return nums
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
start_range = 57
end_range   = 58
block_width = 28
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
pow10_nums = break_down_to_pow10(2**block_width)
pow10_points = []
for num in pow10_nums:
    pow10_points.append(secp256k1.scalar_multiplication(num))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++    
stride_status = 2**block_width
first_scalar  = S_table[start_range - 1]
second_scalar = S_table[start_range - 2]
pre_calc_sum = first_scalar + second_scalar

search_pub = '028b8715f7c25858790d2207fb84be96567f3d3367122fbcd69221ab063039167c'
puzzle_point = secp256k1.pub2upub(search_pub)
point_05 = secp256k1.scalar_multiplication(57896044618658097711785492504343953926418782139537452191302581570759080747169)
puzzle_point_05 = secp256k1.point_addition(puzzle_point, point_05)

bloomfile1 = 'xor_bloom1.xf'
print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading bloomfilter {bloomfile1}')
_bits1, _hashes1, _xf1, _fp1, _elem1 = secp256k1.read_xor_file(bloomfile1)
bloomfile2 = 'xor_bloom2.xf'
print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading bloomfilter {bloomfile2}')
_bits2, _hashes2, _xf2, _fp2, _elem2 = secp256k1.read_xor_file(bloomfile2)
print(f'[{datetime.now().strftime("%H:%M:%S")}] Each BloomFilter size: 2^{block_width} ({S_table[block_width]})')
print(f'[{datetime.now().strftime("%H:%M:%S")}] Stride size: 2^{int(math.log2(stride_status))} ({stride_status})') 
print(f'[{datetime.now().strftime("%H:%M:%S")}] Search Range: 2^{start_range} .. 2^{end_range} [{S_table[start_range]}-{S_table[end_range]}]')
#==============================================================================
queue = mp.Queue()
G = secp256k1.scalar_multiplication(1)
starttime = time.time()

def addition_search():
    save_counter = 0
    settingsFile = 'x_settings1.txt'
    settings = open(settingsFile, 'r')
    starting_point = secp256k1.pub2upub(settings.readline().strip())
    stride_sum = int(settings.readline().strip())
    settings.close()
    stride = 2**block_width
    stride_point = secp256k1.scalar_multiplication(stride)
    
    while True:
        cpub = secp256k1.point_to_cpub(starting_point)
        if secp256k1.check_in_xor(cpub, _bits1, _hashes1, _xf1):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile1} (Even Point) [Lower Range Half]')            
            P = starting_point
            privkey_num = []
            for i,p in enumerate(pow10_points):
                count = 0
                cpub1 = secp256k1.point_to_cpub(P)
                while secp256k1.check_in_xor(cpub1, _bits1, _hashes1, _xf1):
                    P = secp256k1.point_subtraction(P, p)
                    cpub1 = secp256k1.point_to_cpub(P)
                    count += 1
                privkey_num.append(pow10_nums[i] * (count - 1))
                P = secp256k1.point_addition(P, p)
            steps = 0
            for i in privkey_num:
                steps += i
            privkey = pre_calc_sum - (stride_sum - steps)
            privkey *= 2
            if secp256k1.point_to_cpub(secp256k1.scalar_multiplication(privkey)) == search_pub:
                queue.put_nowait(privkey)
                return
            print(f'[{datetime.now().strftime("%H:%M:%S")}] False Positive')
                
            
        if secp256k1.check_in_xor(cpub, _bits2, _hashes2, _xf2):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile2} (Odd Point) [Lower Range Half]')
            P = starting_point
            privkey_num = []
            for i,p in enumerate(pow10_points):
                count = 0
                cpub2 = secp256k1.point_to_cpub(P)
                while secp256k1.check_in_xor(cpub2, _bits2, _hashes2, _xf2):
                    P = secp256k1.point_subtraction(P, p)
                    cpub2 = secp256k1.point_to_cpub(P)
                    count += 1
                privkey_num.append(pow10_nums[i] * (count - 1))
                P = secp256k1.point_addition(P, p)                
            steps = 0
            for i in privkey_num:
                steps += i
            privkey = pre_calc_sum - (stride_sum - steps)
            privkey = (privkey * 2) + 1            
            if secp256k1.point_to_cpub(secp256k1.scalar_multiplication(privkey)) == search_pub:
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
    settingsFile = 'x_settings2.txt'
    settings = open(settingsFile, 'r')
    starting_point = secp256k1.pub2upub(settings.readline().strip())
    stride_sum = int(settings.readline().strip())
    settings.close()
    stride = 2**block_width
    stride_point = secp256k1.scalar_multiplication(stride)
    
    while True:
        cpub = secp256k1.point_to_cpub(starting_point)
        if secp256k1.check_in_xor(cpub, _bits1, _hashes1, _xf1):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile1} (Even Point) [Higher Range Half]')
            P = starting_point
            privkey_num = []
            for i,p in enumerate(pow10_points):
                count = 0
                cpub1 = secp256k1.point_to_cpub(P)
                while secp256k1.check_in_xor(cpub1, _bits1, _hashes1, _xf1):
                    P = secp256k1.point_subtraction(P, p)
                    cpub1 = secp256k1.point_to_cpub(P)
                    count += 1
                privkey_num.append(pow10_nums[i] * (count - 1))
                P = secp256k1.point_addition(P, p)
            steps = 0
            for i in privkey_num:
                steps += i
            privkey = pre_calc_sum + (stride_sum + steps)
            privkey *= 2
            if secp256k1.point_to_cpub(secp256k1.scalar_multiplication(privkey)) == search_pub:
                queue.put_nowait(privkey)
                return
            print(f'[{datetime.now().strftime("%H:%M:%S")}] False Positive')
 
        if secp256k1.check_in_xor(cpub, _bits2, _hashes2, _xf2):
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] BloomFilter Hit {bloomfile2} (Odd Point) [Higher Range Half]')
            P = starting_point
            privkey_num = []
            for i,p in enumerate(pow10_points):
                count = 0
                cpub2 = secp256k1.point_to_cpub(P)
                while secp256k1.check_in_xor(cpub2, _bits2, _hashes2, _xf2):
                    P = secp256k1.point_subtraction(P, p)
                    cpub2 = secp256k1.point_to_cpub(P)
                    count += 1
                privkey_num.append(pow10_nums[i] * (count - 1))
                P = secp256k1.point_addition(P, p)
            steps = 0
            for i in privkey_num:
                steps += i
            privkey = pre_calc_sum + (stride_sum + steps)
            privkey = (privkey * 2) + 1
            if secp256k1.point_to_cpub(secp256k1.scalar_multiplication(privkey)) == search_pub:
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
    f = open("x_found_key.txt", "a")
    f.write(f"{data}\n")
    f.close()
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
