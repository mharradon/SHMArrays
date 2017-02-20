#!/usr/bin/env python

# Python modules
import sys
import time
import md5
import os

# 3rd party modules
import shm

# Modules for this project
import DemoConstants

def WriteToMemory(MemoryHandle, s):
    MemoryHandle.attach()
    say("writing %s " % s)
    MemoryHandle.write(s + (MemoryHandle.size - len(s)) * ' ')
    MemoryHandle.detach()

def ReadFromMemory(MemoryHandle):
    MemoryHandle.attach()
    s = MemoryHandle.read(MemoryHandle.size).strip()
    say("read %s" % s)
    MemoryHandle.detach()

    return s

def say(s):
    print "conclusion@%1.6f: %s" % (time.time(), s)

if len(sys.argv) != 2:
    print "Please supply Mrs. Premise's integer key on the command line."
    sys.exit(-1)

key = int(sys.argv[1])

SemaphoreHandle = shm.semaphore(shm.getsemid(key))
MemoryHandle = shm.memory(shm.getshmid(key))

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
