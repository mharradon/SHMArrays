#!/usr/bin/env python

import distutils.core
import sys
import popen2
import tempfile
import os

version = "1.2.2"

description = """SHM gives access to System V shared memory and semaphores on *nix systems.
The companion module shm_wrapper offers more Pythonic access. These modules only work on 
platforms that support System V shared objects. Most *nixes do (including OS X) but 
Windows does not."""

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
if sys.version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

classifiers = [ 'Development Status :: 5 - Production/Stable', 
                'Intended Audience :: Developers', 
                'License :: Freely Distributable', 
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Operating System :: MacOS :: MacOS X',
                'Operating System :: POSIX', 
                'Operating System :: Unix', 
                'Programming Language :: Python', 
                'Topic :: Utilities' ]


# shm makes use of the ipc_perm structure defined in include/sys/ipc.h (or include/bits/ipc.h
# on some systems). That structure includes an element called key, _key or __key depending
# on the OS. Here's the variations I've been able to find with OS version numbers where 
# possible. 
#     key: FreeBSD 6, AIX, Solaris, OS X 10.3, OS X 10.4 (conditionally)
#    _key: NetBSD, OS X 10.4 (conditionally)
#   __key: Debian 4 (Etch), Ubuntu 7, RH 3.3 & 3.4

# OS X side note: OS X 10.4's ipc.h (see /Developer/SDKs/MacOSX10.4u.sdk/usr/include/sys/ipc.h) 
# defines structs called __ipc_perm_old (which uses key) and __ipc_perm_new (which uses _key). 
# Use of __ipc_perm_new is inside this:
#     #if defined(__POSIX_C_SOURCE) || defined(kernel) || defined(__LP64__)
# Obviously __ipc_perm_new is the preferred version. This code doesn't use that yet but 
# will probably do so in some future version when compiled on OS X >= 10.4.

# Trying to enumerate all of the variations is a fool's errand so instead I figure it out 
# on the fly using the function CountKeyUnderscores() below.

# Lots of systems use the unadorned "key" so that's the default when I'm forced to guess.
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


MacrosAndDefines = [ ]

# HAVE_UNION_SEMUN needs to be #defined on FreeBSD and OS X and must *not* be #defined
# on Linux. On other systems, I'm not sure. Please let me know if you find that you
# need to make changes for your platform.
if (sys.platform.find("bsd") != -1) or (sys.platform.find("darwin") != -1):
    MacrosAndDefines.append( ('HAVE_UNION_SEMUN', None) )

KeyUnderscores = CountKeyUnderscores()

if KeyUnderscores == 2:
    MacrosAndDefines.append( ('TWO_UNDERSCORE_KEY', None) )
elif KeyUnderscores == 1:
    MacrosAndDefines.append( ('ONE_UNDERSCORE_KEY', None) )
else:
    MacrosAndDefines.append( ('ZERO_UNDERSCORE_KEY', None) )


# fPIC option from dkhchan:
# http://mail.python.org/pipermail/python-list/2000-February/023060.html
ext_modules = [distutils.core.Extension("shm", ["shmmodule.c"],
                                        define_macros=MacrosAndDefines,
                                        extra_compile_args=['-fPIC']
                                       )
              ]
distutils.core.setup(name="shm", 
                     version=version,
                     author="Vladimir Marangozov",
                     maintainer="Philip Semanchuk",
                     url="http://NikitaTheSpider.com/python/shm/",
                     description=description,
                     ext_modules=ext_modules, 
                     py_modules=["shm_wrapper"],
                     classifiers=classifiers)

