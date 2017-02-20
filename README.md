# SHMArrays
Read and write numpy arrays with multiple processes stored as shared memory

Init the object with an OrderedDict with key-> numpy array pairs:
  
```python
from SHMArrays import SHMArrays
from collections import OrderedDict

array_dict = OrderedDict([(k,np.random.randn(10,10)) for k in range(10)])
shm_array = SHMArrays(array_dict)
keys = shm_array.get_keys()
```

Run another process and initialize with the given keys and an equivalent array:

```python

shm_array2 = SHMArrays(array_dict,keys=keys)
```

Now you can read and write to the variables from multiple processes, as well as update them with a given new variable and update function:

```python
read_vals = shm_array2.read_arrays(new_arrays)
results = shm_array2.update_arrays(new_arrays,lambda new,old: 0.1*new + 0.9*old)
```

Useful if you'd like to run a distributed numerical algorithm and you can't use normal threading. For example, if you need different environments for different processes, e.g. Theano with multiple gpus.

Built using the SHM module written by Vladimir Marangozov: http://nikitathespider.com/python/shm/
Install that first by running 'sudo setup.py' in shm-1.2.2
