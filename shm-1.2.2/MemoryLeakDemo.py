#!/usr/bin/env python

# Demonstrates memory leak when creating/destroying large numbers of memory objects.
# Reading/writing to the memory didn't affect the outcome during my testing. One can
# write a similar test with semaphores and see a similar leak.

# Run this in one window and top in another and watch this process eat memory.

import shm
import os
import gc

PERFORM_READ_WRITE = False
ITERATIONS = 100000
SEGMENT_LENGTH = 4096

# Set the garbage collector to be verbose and only run when I ask it to do so.
gc.set_debug(gc.DEBUG_STATS)
gc.disable()

key = os.getpid()

raw_input("Press Enter when you're ready to start.")

for i in xrange(0, ITERATIONS):
    if i % 100 == 0:
        print "iteration %d" % i
        gc.collect()

    memory = shm.create_memory(key, SEGMENT_LENGTH)

    if PERFORM_READ_WRITE:
        memory.attach()
        memory.write(' ')
        memory.detach()

    shm.remove_memory(memory.shmid)

print "Completed %d iterations" % ITERATIONS

raw_input("Press Enter to run garbage collection.")

gc.collect()

print "Leftover garbage:\n:"
print gc.garbage


for o in gc.get_objects():
   print type(o)


raw_input("Press Enter to end program.")
