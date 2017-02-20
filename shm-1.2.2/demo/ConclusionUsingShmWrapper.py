#!/usr/bin/env python

# Python modules
import sys
import time
import md5
import os

# 3rd party modules
import shm_wrapper

# Modules for this project
import DemoConstants

# Note that when using shm_wrapper instead of shm, I don't have to call attach and detach when
# reading and writing.
def WriteToMemory(MemoryHandle, s):
    say("writing %s " % s)
    MemoryHandle.write(s + (MemoryHandle.size - len(s)) * ' ')

def ReadFromMemory(MemoryHandle):
    s = MemoryHandle.read(MemoryHandle.size).strip()
    say("read %s" % s)
    return s

def say(s):
    print "conclusion@%1.6f: %s" % (time.time(), s)

if len(sys.argv) != 3:
    print "Please supply Mrs. Premise's keys on the command line."
    sys.exit(-1)

MemoryHandle = shm_wrapper.SharedMemoryHandle(int(sys.argv[1]))
SemaphoreHandle = shm_wrapper.SemaphoreHandle(int(sys.argv[2]))

WhatIWrote = ""
s = ""

for i in xrange(0, DemoConstants.ITERATIONS):
    say("i = %d" % i)
    if DemoConstants.USE_SEMAPHORE:
        # Wait for Mrs. Premise to free up the semaphore.
        say("waiting for semaphore")
        SemaphoreHandle.P()

    s = ReadFromMemory(MemoryHandle)

    while s == WhatIWrote:
        if DemoConstants.USE_SEMAPHORE:
            # Relinquish the semaphore...
            say("relinquishing the semaphore")
            SemaphoreHandle.V()
            # ...and wait for it to become available again.
            say("waiting for the semaphore")
            SemaphoreHandle.P()

        s = ReadFromMemory(MemoryHandle)

    if WhatIWrote:
        try:
            assert(s == md5.new(WhatIWrote).hexdigest())
        except:
            raise AssertionError, "Shared memory corruption after %d iterations." % i

    WhatIWrote = md5.new(s).hexdigest()

    WriteToMemory(MemoryHandle, WhatIWrote)

    if DemoConstants.USE_SEMAPHORE:
        say("relinquishing the semaphore")
        SemaphoreHandle.V()
