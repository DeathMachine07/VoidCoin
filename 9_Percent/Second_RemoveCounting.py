import struct
import math
from z3 import *

# Observed doubles from Math.random() calls (without clicking system).
# Replace these with the 5 observed doubles you get from the website's developer console.
observed_doubles = [
    0.5368584449767335,
    0.883588766746984,
    0.7895949638905317,
    0.5106241305628436,
    0.49965622623126693
]

# This xorshift128+ step is symbolic. It returns the next state.
def xs128p_sym(s0, s1):
    s1_x = s1 ^ (s1 << 23)
    s1_x = s1_x ^ LShR(s1_x, 17)
    s1_x = s1_x ^ s0
    s1_x = s1_x ^ LShR(s0, 26)
    return s1, s1_x

# Convert state0 to double as Chrome's Math.random() would:
def to_double_from_state(state0):
    bits = (state0 >> 12) | 0x3FF0000000000000
    packed = struct.pack('<Q', bits)
    return struct.unpack('d', packed)[0] - 1.0

def from_double_to_bits(d):
    return struct.unpack('<Q', struct.pack('d', d + 1.0))[0]

def main():
    state0, state1 = BitVecs('state0 state1', 64)
    solver = Solver()
    s0 = state0
    s1 = state1

    # Constrain states based on observed doubles
    for obs in observed_doubles:
        ns0, ns1 = xs128p_sym(s0, s1)
        obs_bits = from_double_to_bits(obs)
        fraction_bits = obs_bits & 0x000FFFFFFFFFFFFF
        calc = LShR(ns0, 12)
        solver.add(calc == fraction_bits)
        s0, s1 = ns0, ns1

    # Solve for the initial state
    if solver.check() == sat:
        model = solver.model()
        rec_s0 = model[state0].as_long()
        rec_s1 = model[state1].as_long()

        # Now that we have the recovered state, we can predict future numbers.
        # We'll generate a set of 'lottery numbers' from 1 to 50 (as an example).
        # For each next call:
        #   Perform the XORShift128+ step, convert to double, then map double to 1..50.
        def xs128p_forward(st0, st1):
            s1 = st0
            s0 = st1
            s1 ^= (s1 << 23) & 0xFFFFFFFFFFFFFFFF
            s1 ^= (s1 >> 17)
            s1 ^= s0
            s1 ^= (s0 >> 26)
            new_s0 = s1 & 0xFFFFFFFFFFFFFFFF
            new_s1 = s0 & 0xFFFFFFFFFFFFFFFF
            return new_s0, new_s1

        cur_s0, cur_s1 = rec_s0, rec_s1

        # Advance beyond the observed sequence:
        for _ in observed_doubles:
            cur_s0, cur_s1 = xs128p_forward(cur_s0, cur_s1)

        # Predict next lottery numbers (example: 5 lottery numbers)
        # Range 1 to 50:
        lottery_numbers = []
        for _ in range(5):
            cur_s0, cur_s1 = xs128p_forward(cur_s0, cur_s1)
            nxt_double = to_double_from_state(cur_s0)
            num = math.floor(nxt_double * ) + 1
            lottery_numbers.append(num)

        print("Predicted lottery numbers:", sorted(lottery_numbers))
    else:
        print("Failed to solve.")

if __name__ == "__main__":
    main()
