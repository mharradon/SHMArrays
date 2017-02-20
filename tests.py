from SHMArrays import SHMArrays
import numpy as np
import pdb
from collections import OrderedDict

n_params = 20
sizes = [int(1e5*np.random.rand()) for i in range(n_params)]
arrays = OrderedDict([('id'+str(i),np.random.randn(size)) for i,size in zip(range(n_params),sizes)])
arrays2 = OrderedDict([('id'+str(i),np.random.randn(size)) for i,size in zip(range(n_params),sizes)])

shm_array = SHMArrays(arrays)
keys = shm_array.get_keys()

# Check that partitioning is valid
assert((np.sort(np.concatenate(shm_array.partitioning))==np.arange(0,n_params)).all())

# Check that shm is read properly (init values are ignored when keys are specified)
shm_array2 = SHMArrays(arrays2,keys=keys)
read_vals = shm_array2.read_arrays()

for array,read_array in zip(arrays.values(),read_vals.values()):
  assert((array==read_array).all())

# Check that shm is writing properly (init values are ignored when keys are specified)
shm_array2.write_arrays(arrays2)
read_vals = shm_array.read_arrays()

for array,read_array in zip(arrays2.values(),read_vals.values()):
  assert((array==read_array).all())

# Check that update function is applied properly 
shm_array2.update_arrays(arrays,lambda new,old: new + old)
read_vals = shm_array.read_arrays()

for array,array2,read_array in zip(arrays.values(),arrays2.values(),read_vals.values()):
  assert((array+array2==read_array).all())

print('All passed')
