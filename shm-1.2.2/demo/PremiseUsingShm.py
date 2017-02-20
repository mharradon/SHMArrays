#!/usr/bin/env python

# Python modules
import time
import md5
import os

# 3rd party modules
import shm

# Modules for this project
import DemoConstants


def say(s):
    print "premise@%1.6f: %s" % (time.time(), s)

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


key = os.getpid()

# Create the semaphore & shared memory. I read somewhere that semaphores and shared memory
# have separate key spaces, so one can safely use the same key for each. This seems to be
# true in my experience.

# For purposes of simplicity, this demo code makes no allowance for the failure of
# create_memory() or create_semaphore(). This is unrealistic because one can never predict
# whether or not a given key will be available, so your code must *always* be prepared for
# these functions to fail. This is one of the advantages to using shm_wrapper -- it handles
# key generation for you so you can assume that all failures are catastrophic (e.g.
# no shared memory available on the system).

SemaphoreHandle = shm.create_semaphore(key, 0)

MemoryHandle = shm.create_memory(key, 1024)

# I seed the shared memory with a random value which is the current time turned into a string.
WhatIWrote = str(time.time())
s = WhatIWrote

WriteToMemory(MemoryHandle, WhatIWrote)

say("OK, I'm ready. Start Mrs. Conclusion with the parameter %d and then hit Enter to make me continue." % key)

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

        # Once the call to .P() completes, I own the semaphore and I'm free to write to
        # the memory.
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
shm.remove_memory(MemoryHandle.shmid)
shm.remove_semaphore(SemaphoreHandle.semid)
