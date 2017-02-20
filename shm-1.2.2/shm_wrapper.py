# shm_wrapper - A wrapper for the shm module which provides access
# to System V shared memory and semaphores on *nix systems.
#
# Copyright (c) 2007 by Philip Semanchuk
# Contact info at http://NikitaTheSpider.com/
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Python modules
import random
import sys

# Other modules
import shm
# See the __del__ method for why I'm doing this odd import.
from shm import error as ShmError

"""shm_wrapper - A wrapper for the shm module which provides access
to System V shared memory and semaphores on *nix systems.

The module shm is a Python wrapper around system functions like shmget. This
module in turn offers higher-level, more Pythonic access to shared memory and
semaphores.

Full documentation is online at http://NikitaTheSpider.com/python/shm/

"""

def create_memory(size, permissions = 0666, InitCharacter = ' '):
    """ Creates a new shared memory segment. One can destroy it either by calling the
    module-level method remove_memory() or by calling the .remove() method of a handle to
    said memory.
    """
    memory = None

    # I create the memory using a randomly-generated key. I keep trying until I find one
    # that works or until I hit an error.
    while not memory:
        key = random.randint(1, sys.maxint - 1)
        try:
            memory = shm.create_memory(key, size, permissions)
        except shm.error, ExtraData:
            if shm.memory_haskey(key):
                # Oops, bad luck, the key exists. I'll try another. I can't call
                # memory_haskey() before calling create_memory() because that would create
                # a race condition where I could verify a key is not used but then another
                # process could call create_memory() with that key before I got a chance to
                # do so.
                pass
            else:
                # Uh-oh, something fundamental is wrong.
                raise shm.error, ExtraData

    # Here I implicitly discard the memory handle object returned to me by shm and instead
    # return my own handle to the shared memory segment.
    memory = SharedMemoryHandle(key)

    memory.write(InitCharacter[0] * memory.size)

    return memory


def remove_memory(key):
    # Destroys the shared memory segment. Raises KeyError if the key doesn't exist.
    shm.remove_memory(shm.getshmid(key))


class SharedMemoryHandle(object):
    def __init__(self, key):
        self._MemoryHandle = None

        # getshmid will raise a KeyError if there's no memory segment with this key.
        shmid = shm.getshmid(key)
        self._MemoryHandle = shm.memory(shmid)


    def __del__(self):
        if self._MemoryHandle:
            # This will raise an error if the memory has been destroyed.
            try:
                if self._MemoryHandle.attached:
                    self._MemoryHandle.detach()
            # ShmError is the same as shm.error. I'd rather refer to the latter directly, but
            # when this __del__ method is invoked, shm might not be available anymore. In that
            # case, accessing shm.error just raises another error whereas ShmError does not.
            except ShmError:
                pass


    def remove(self):
        if self._MemoryHandle:
            if self._MemoryHandle.attached:
                self._MemoryHandle.detach()

            shm.remove_memory(self._MemoryHandle.shmid)
            self._MemoryHandle = None


    def read(self, NumberOfBytes = 0, offset = 0):
        if not self._MemoryHandle.attached:
            self._MemoryHandle.attach()

        if not NumberOfBytes:
            NumberOfBytes = self._MemoryHandle.size - offset

        return self._MemoryHandle.read(NumberOfBytes, offset)


    def write(self, s, offset = 0):
        if not self._MemoryHandle.attached:
            self._MemoryHandle.attach()

        self._MemoryHandle.write(s, offset)


    # Properties start here ================================================================

    # key
    def __get_key(self): return self._MemoryHandle.key
    def __set_key(self, foo): raise AttributeError
    key = property(__get_key, __set_key)

    # size of segment
    def __get_size(self): return self._MemoryHandle.size
    def __set_size(self, foo): raise AttributeError
    size = property(__get_size, __set_size)

    # permissions
    def __get_permissions(self): return self._MemoryHandle.perm
    def __set_permissions(self, permissions): self._MemoryHandle.setperm(permissions)
    permissions = property(__get_permissions, __set_permissions)

    # The number of processes currently attached to this memory segment.
    def __get_number_attached(self): return self._MemoryHandle.nattch
    def __set_number_attached(self, foo): raise AttributeError
    number_attached = property(__get_number_attached, __set_number_attached)

    # segment's uid
    def __get_uid(self): return self._MemoryHandle.uid
    def __set_uid(self, uid): self._MemoryHandle.setuid(uid)
    uid = property(__get_uid, __set_uid)

    # segment's gid
    def __get_gid(self): return self._MemoryHandle.gid
    def __set_gid(self, gid): self._MemoryHandle.setgid(gid)
    gid = property(__get_gid, __set_gid)

    # Creator uid (read-only)
    def __get_creator_uid(self): return self._MemoryHandle.cuid
    def __set_creator_uid(self, foo): raise AttributeError
    creator_uid = property(__get_creator_uid, __set_creator_uid)

    # Creator gid (read-only)
    def __get_creator_gid(self): return self._MemoryHandle.cgid
    def __set_creator_gid(self, foo): raise AttributeError
    creator_gid = property(__get_creator_gid, __set_creator_gid)

    # Creator pid (read-only)
    def __get_creator_pid(self): return self._MemoryHandle.cpid
    def __set_creator_pid(self, foo): raise AttributeError
    creator_pid = property(__get_creator_pid, __set_creator_pid)

    # pid of last process to operate on this segment (read-only)
    def __get_last_pid(self): return self._MemoryHandle.lpid
    def __set_last_pid(self, foo): raise AttributeError
    last_pid = property(__get_last_pid, __set_last_pid)



def create_semaphore(InitialValue = 1, permissions = 0666):
    """ Creates a new semaphore. One can destroy it either by calling the
    module-level method remove_semaphore() or by calling the .remove() method of a
    handle to said semaphore.
    """
    semaphore = None

    # I create the semaphore using a randomly-generated key. I keep trying until I find one
    # that works or until I hit an error.
    while not semaphore:
        key = random.randint(1, sys.maxint - 1)
        try:
            semaphore = shm.create_semaphore(key, InitialValue, permissions)
        except shm.error, ExtraData:
            if shm.semaphore_haskey(key):
                # Oops, bad luck, the key exists. I'll try another. I can't call
                # memory_haskey() before calling create_semaphore() because that would create
                # a race condition where I could verify a key is not used but then another
                # process could call create_semaphore() with that key before I got a chance to
                # do so.
                pass
            else:
                # Uh-oh, something fundamental is wrong.
                raise ExtraData

    # Here I implicitly discard the semaphore object returned to me by shm and instead
    # return my own handle to the semaphore.
    return SemaphoreHandle(key)


def remove_semaphore(key):
    # Destroys the semaphore. Raises KeyError if the key doesn't exist.
    shm.remove_semaphore(shm.getsemid(key))


class SemaphoreHandle(object):
    def __init__(self, key):
        # getsemid will raise a KeyError if appropriate.
        self._SemaphoreHandle = shm.semaphore(shm.getsemid(key))


    def remove(self):
        shm.remove_semaphore(self._SemaphoreHandle.semid)
        self._SemaphoreHandle = None


    def P(self):
        # P = prolaag = probeer te verlagen (try to decrease)
        self._SemaphoreHandle.P()


    def V(self):
        # V = verhoog (increase)
        self._SemaphoreHandle.V()


    def Z(self):
        # Z = block until Zee semaphore is Zero
        self._SemaphoreHandle.Z()


    # Properties start here ================================================================
    def __get_key(self): return self._SemaphoreHandle.key
    def __set_key(self, foo): raise AttributeError
    key = property(__get_key, __set_key)


    def __get_value(self): return self._SemaphoreHandle.val
    def __set_value(self, value): self._semaphore.setval(value)
    value = property(__get_value, __set_value)


    def __get_WaitingForZero(self): return self._SemaphoreHandle.zcnt
    def __set_WaitingForZero(self, foo): raise AttributeError
    WaitingForZero = property(__get_WaitingForZero, __set_WaitingForZero)


    def __get_WaitingForNonZero(self): return self._SemaphoreHandle.ncnt
    def __set_WaitingForNonZero(self, foo): raise AttributeError
    WaitingForNonZero = property(__get_WaitingForNonZero, __set_WaitingForNonZero)


    def __get_blocking(self): return self._SemaphoreHandle.blocking
    def __set_blocking(self, block): self._SemaphoreHandle.setblocking(block)
    blocking = property(__get_blocking, __set_blocking)


    def __get_undo(self): raise AttributeError
    def __set_undo(self, undo): self._SemaphoreHandle.setundo(undo)
    undo = property(__get_undo, __set_undo)


    # segment's uid
    def __get_uid(self): return self._SemaphoreHandle.uid
    def __set_uid(self, uid): self._SemaphoreHandle.setuid(uid)
    uid = property(__get_uid, __set_uid)


    # segment's gid
    def __get_gid(self): return self._SemaphoreHandle.gid
    def __set_gid(self, gid): self._SemaphoreHandle.setgid(gid)
    gid = property(__get_gid, __set_gid)


    # Creator uid (read-only)
    def __get_creator_uid(self): return self._SemaphoreHandle.cuid
    def __set_creator_uid(self, foo): raise AttributeError
    creator_uid = property(__get_creator_uid, __set_creator_uid)


    # Creator gid (read-only)
    def __get_creator_gid(self): return self._SemaphoreHandle.cgid
    def __set_creator_gid(self, foo): raise AttributeError
    creator_gid = property(__get_creator_gid, __set_creator_gid)


    # Creator pid -- since semaphores have a lot of the same properties as memory
    # objects, one would expect creator PID to be exposed here, but it isn't
    # made available by the system (true AFAICT for BSDs, OS X and Solaris).


    # pid of last process to operate on this segment (read-only)
    def __get_last_pid(self): return self._SemaphoreHandle.lpid
    def __set_last_pid(self, foo): raise AttributeError
    last_pid = property(__get_last_pid, __set_last_pid)
