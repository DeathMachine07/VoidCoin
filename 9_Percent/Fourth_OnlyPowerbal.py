import struct
import math
from z3 import *

# Insert your 5 observed Math.random() outputs here:
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
    return struct.unpack('d', packed)[0] - 1.0

def from_double_to_bits(d):
    return struct.unpack('<Q', struct.pack('d', d + 1.0))[0]

def main():
    # Symbolic variables for the internal states
    state0, state1 = BitVecs('state0 state1', 64)
    solver = Solver()
    s0 = state0
    s1 = state1

    # Constrain states based on the observed 5 doubles
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

        # Once we have the seed, we generate the next set of doubles.
        # According to the explained process for Powerball:
        # 1. We have a pool of possible numbers from 1 to 49 (for demonstration).
        # 2. We use the next 5 doubles to "select" 5 numbers from the pool (just to follow the process).
        # 3. The 6th double after these 5 is used to generate the Powerball number by:
        #    Powerball = floor(double * 50) + 1.

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

        # Advance one step for each observed double to reach the state after them
        for _ in observed_doubles:
            cur_s0, cur_s1 = xs128p_forward(cur_s0, cur_s1)

        # Prepare the pool for the first 5 numbers as per process (though we won't print them, we just follow the logic)
        poss = list(range(1, 50))

        # Generate 5 doubles and mimic choosing winning numbers
        for _ in range(5):
            cur_s0, cur_s1 = xs128p_forward(cur_s0, cur_s1)
            nxt_double = to_double_from_state(cur_s0)
            index = int(nxt_double * len(poss))
            # Chosen number (not needed to store for output now, just following the process)
            _ = poss[index]
            poss = poss[:index] + poss[index+1:]

        # The 6th double after these 5 chosen numbers is the Powerball double
        cur_s0, cur_s1 = xs128p_forward(cur_s0, cur_s1)
        power_double = to_double_from_state(cur_s0)
        powerball_num = int(math.floor(power_double * 49) + 1)

        print("Predicted Powerball number:", powerball_num)
    else:
        print("Failed to solve.")

if __name__ == "__main__":
    main()
