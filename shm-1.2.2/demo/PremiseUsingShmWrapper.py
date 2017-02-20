#!/usr/bin/env python

# Python modules
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
    print "premise@%1.6f: %s" % (time.time(), s)

MemoryHandle = shm_wrapper.create_memory(4096)
SemaphoreHandle = shm_wrapper.create_semaphore(0)

# I seed the shared memory with a random value which is the current time turned into a string.
WhatIWrote = str(time.time())
s = WhatIWrote

WriteToMemory(MemoryHandle, WhatIWrote)

say("OK, I'm ready. Start Mrs. Conclusion with the parameters %d and %d and then hit Enter to make me continue." % (MemoryHandle.key, SemaphoreHandle.key))

raw_input("")

for i in xrange(0, DemoConstants.ITERATIONS):
    say("iteration %d" % i)
    if DemoConstants.USE_SEMAPHORE:
        # Relinquish the semaphore...
        say("relinquishing the semaphore")
        SemaphoreHandle.V()
        # ...and wait for it to become available again. In real code it'd be wise to sleep
        # briefly before calling .P() in order to be polite and give other processes an
        # opportunity to grab the semaphore while it is free. But this code is meant to be a
        # stress test that maximizes the opportunity for shared memory corruption and
        # politeness is not helpful for that.
        say("waiting for the semaphore")
        SemaphoreHandle.P()

    s = ReadFromMemory(MemoryHandle)

    # I keep checking the shared memory until something new has been written.
    while s == WhatIWrote:
        if DemoConstants.USE_SEMAPHORE:
            say("forfeiting semaphore")
            SemaphoreHandle.V()
            say("waiting for semaphore")
            SemaphoreHandle.P()

        s = ReadFromMemory(MemoryHandle)

    # What I read must be the md5 of what I wrote or something's gone wrong.
    try:
        assert(s == md5.new(WhatIWrote).hexdigest())
    except:
        raise AssertionError, "Shared memory corruption after %d iterations." % i

    WhatIWrote = md5.new(s).hexdigest()
    WriteToMemory(MemoryHandle, WhatIWrote)


# Announce for one last time that the semaphore is free again so that Mrs. Conclusion can exit.
if DemoConstants.USE_SEMAPHORE:
    say("Final forfeit of semaphore")
    SemaphoreHandle.V()
    time.sleep(5)
    # ...before beginning to wait until it is free again.
    say("Final wait for semaphore")
    SemaphoreHandle.P()

say("Destroying semaphore and shared memory.")
MemoryHandle.remove()
SemaphoreHandle.remove()
