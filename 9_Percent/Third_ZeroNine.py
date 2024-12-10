import struct
import math
from z3 import *

observed_doubles = [
    0.5368584449767335,
    0.883588766746984,
    0.7895949638905317,
    0.5106241305628436,
    0.49965622623126693
]

def xs128p_sym(s0, s1):
    s1_x = s1 ^ (s1 << 23)
    s1_x = s1_x ^ LShR(s1_x, 17)
    s1_x = s1_x ^ s0
    s1_x = s1_x ^ LShR(s0, 26)
    return s1, s1_x

def to_double_from_state(state0):
    bits = (state0 >> 12) | 0x3FF0000000000000
    packed = struct.pack('<Q', bits)
    double_val = struct.unpack('d', packed)[0] - 1.0
    return double_val

def from_double_to_calc(d):
    bits = struct.unpack('<Q', struct.pack('d', d + 1.0))[0]
    return bits

def main():
    state0, state1 = BitVecs('state0 state1', 64)
    solver = Solver()
    s0 = state0
    s1 = state1

    for obs in observed_doubles:
        ns0, ns1 = xs128p_sym(s0, s1)
        observed_bits = from_double_to_calc(obs)
        fraction_bits = observed_bits & 0x000FFFFFFFFFFFFF
        calc = LShR(ns0, 12)
        solver.add(calc == fraction_bits)
        s0, s1 = ns0, ns1

    if solver.check() == sat:
        model = solver.model()
        rec_s0 = model[state0].as_long()
        rec_s1 = model[state1].as_long()
        cur_s0, cur_s1 = rec_s0, rec_s1
        s1 = cur_s0
        s0 = cur_s1
        s1 ^= (s1 << 23) & 0xFFFFFFFFFFFFFFFF
        s1 ^= (s1 >> 17)
        s1 ^= s0
        s1 ^= (s0 >> 26)
        next_s0 = s1 & 0xFFFFFFFFFFFFFFFF
        next_s1 = s0 & 0xFFFFFFFFFFFFFFFF
        nxt_double = to_double_from_state(next_s0)
        nxt_val = math.floor(nxt_double * 10)
        print("-> :", nxt_val)
    else:
        print("Failed to find a solution.")

if __name__ == "__main__":
    main()
