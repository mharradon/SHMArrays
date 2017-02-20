#!/usr/bin/env python

import popen2
import tempfile
import os

COUNT_KEY_UNDERSCORES_DEFAULT = 0


def CountKeyUnderscores():
    """ Uses trial-and-error with the system's C compiler to figure out the number of 
        underscores preceding key in the ipc_perm structure. Returns 0, 1 or 2. In case of
        error, it makes a guess and hopes for the best.
    """
    UnderscoresCount = COUNT_KEY_UNDERSCORES_DEFAULT
    
    underscores = { }

    # mktemp isn't secure, but I don't care since I use it only for compiling this dummy code.
    # Using mktemp() allows me to keep this code compatible with Python < 2.3.    
    #path = tempfile.mktemp(dir=os.getcwd())
    path = tempfile.mktemp(dir='.')
    os.mkdir(path)
    if path[-1] != "/": path += '/'
    
    # Here I compile three mini-programs with key, _key and __key. Theoretically, 
    # two should fail and one should succeed, and that will tell me how this platform names
    # ipc_perm.key. If the number of successes != 1, something's gone wrong.
    # I use popen2.Popen4() in order to trap (and discard) stderr so that the user doesn't 
    # see the compiler errors I'm deliberately generating here.
    src = """
#include <sys/ipc.h>
int main(void) { struct ipc_perm foo; foo.%skey = 42; }

"""
    for i in range(0, 3):
        # I'd prefer to feed the C source to the compiler via stdin so as to entirely avoid
        # using files and directories, but I had trouble on Ubuntu getting echo to cooperate.
        filename = "%d.c" % i
        file(path + filename, "w").write(src % ('_' * i))
        
        cmd = ["cc", "-c", "-o", "/dev/null", "%s" % path + filename]

        po = popen2.Popen4(cmd)
        if not po.wait(): underscores[i] = True
        
        # Clean up
        os.remove(path + filename)
        
    os.rmdir(path)

    KeyCount = len(underscores.keys())

    if KeyCount == 1:
        UnderscoresCount = underscores.keys()[0]
    else:
        print """
*********************************************************************
* I was unable to detect the structure of ipc_perm on your system.  *
* I'll make my best guess, but compiling might fail anyway. Please  *
* email this message, the error code of %d, and the name of your OS  *
* to the contact at http://NikitaTheSpider.com/python/shm/.         *
*********************************************************************
""" % KeyCount
        
    return UnderscoresCount

print CountKeyUnderscores()