# SHMArrays
Read and write numpy arrays with multiple processes stored as shared memory. See http://man7.org/linux/man-pages/man7/shm_overview.7.html 

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

SHMArrays was designed to enable performant pipelining over the values of the data dictionaries by partitioning into multiple shm entries so multiple processes can update the data structure simultaneously. Valid updates are guaranteed via semaphores. Useful if you'd like to run a distributed numerical algorithm and you can't use normal threading. For example, if you need different environments for different processes, e.g. Theano with multiple gpus.

Built using the SHM module written by Vladimir Marangozov: http://nikitathespider.com/python/shm/. Install that first by running 'sudo setup.py' in shm-1.2.2

# Example Distributed Gradient Descent Use Case

Say you have an algorithm that performs gradient descent on a function:

```python
for i in range(iters):
  gradient = grad(state)
  state = state - alpha*gradient
```

Now you can distribute it across multiple cores or GPUs on a single machine using SHM:

```python
state_shm = SHMArrays(state,keys=keys)
for i in range(iters):
  gradient = grad(state)
  state = state_shm.update_arrays(gradient,lambda grad,state: state - alpha*grad)
```
  
Then you just need to spawn multiple processes running this code to get multithreaded performance, or specify different GPUs to parallelize across GPUs, etc. SHMArrays takes care of all of the os interaction as well as proper locking, enabling the processes to pipeline naturally. This is useful if, for example, different parts of the iteration tax different parts of the machine e.g. reading training data from SSD.
  
#Author
Feel free to email me at mharradon@gmail.com. I also have a small website up at www.highdimensionality.com
