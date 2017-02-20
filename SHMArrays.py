from __future__ import print_function, division
import os.path
import struct
import pickle
from collections import namedtuple, OrderedDict
import numpy as np
import shm_wrapper
import time
import pdb

mem_objs = namedtuple('mem_objs',('memory_handle','semaphore_handle'))
mem_keys = namedtuple('mem_keys',('memory_key','semaphore_key'))
var_spec = namedtuple('var_spec',('size','shape','dtype'))
def get_var_spec(var):
  return var_spec(var.size,var.shape,var.dtype)

class SHMArrays():
  def __init__(self,param_dict,keys=None,store_dtype=None):
    if store_dtype is None:
      store_dtype = param_dict.values()[0].dtype
    self.total_size = sum([v.size*store_dtype.itemsize for v in param_dict.values()])
    self.store_dtype = store_dtype
    
    self.specs = OrderedDict()
    for k,v in param_dict.items():
      self.specs[k] = get_var_spec(v)
    
    self.partitioning = partition_sizes(np.array([np.prod(spec.shape) for spec in self.specs.values()]))
    
    if keys is None:
      init = True
    else:
      init = False
      self.keys = keys
    
    if init:
      shm_nbytes = [int(sum([self.specs.values()[i].size for i in p.tolist()])*self.store_dtype.itemsize) for p in self.partitioning]
      MemoryHandles = [shm_wrapper.create_memory(nbytes) for nbytes in shm_nbytes]
      SemaphoreHandles = [shm_wrapper.create_semaphore() for l in range(len(self.partitioning))]
      
      self.mmappings = [mem_objs(MH,SH) for MH,SH in zip(MemoryHandles, SemaphoreHandles)]
      self.keys = [mem_keys(MH.key,SH.key) for MH,SH in zip(MemoryHandles, SemaphoreHandles)]
      self.write_arrays(param_dict)
    
    else:
      MemoryHandles = [shm_wrapper.SharedMemoryHandle(k.memory_key) for k in self.keys]
      SemaphoreHandles = [shm_wrapper.SemaphoreHandle(k.semaphore_key) for k in self.keys]
      self.mmappings = [mem_objs(MH,SH) for MH,SH in zip(MemoryHandles,SemaphoreHandles)]

  def get_keys(self):
    return self.keys

  def write_arrays(self,param_dict):
    param_parts = split_dicts(param_dict,self.partitioning)
    for mmapping, param_part in zip(self.mmappings, param_parts):
      MemoryHandle, SemaphoreHandle = mmapping
      SemaphoreHandle.P()
      MemoryHandle.write(self.arrays_to_bytes(param_part))
      SemaphoreHandle.V()

  def read_arrays(self):
    output = OrderedDict([(k,None) for k in self.specs.keys()])
    spec_parts = split_dicts(self.specs,self.partitioning)
    for mmapping,spec_part in zip(self.mmappings,spec_parts):
      MemoryHandle, SemaphoreHandle = mmapping
      
      SemaphoreHandle.P()
      param_part = self.bytes_to_arrays(MemoryHandle.read(MemoryHandle.size),spec_part)
      SemaphoreHandle.V()
      
      for k in param_part.keys():
        output[k] = param_part[k]
    
    return output

  def add_updates(self,diff_dict):
    return self.update_arrays(diff_dict,update_func=lambda new,old: new + old)

  def update_arrays(self,new_val_dict,update_func=lambda new,old: 0.1*new + 0.9*old):
    # Skip func can be used to pick which updates to apply - can be random with some probabilty to improve performance
    val_parts = split_dicts(new_val_dict,self.partitioning)
    
    # Init to ensure order
    output = OrderedDict([(k,None) for k in self.specs.keys()])
    for mmapping, val_part in zip(self.mmappings, val_parts):
      MemoryHandle, SemaphoreHandle = mmapping
      
      SemaphoreHandle.P()
      param_part = self.bytes_to_arrays(MemoryHandle.read(MemoryHandle.size),val_part)
      for p,val in param_part.items():
        param_part[p] = update_func(val_part[p],val).astype(val.dtype)
      write_bytes = self.arrays_to_bytes(param_part)
      MemoryHandle.write(write_bytes)
      SemaphoreHandle.V()
      
      for k in param_part.keys():
        output[k] = param_part[k]
    
    return output 

  def bytes_to_arrays(self,bytes,specs):
    result = OrderedDict(zip(specs.keys(),[None]*len(specs.keys())))
    index = 0
    for k,spec in specs.items():
      result[k] = np.frombuffer(bytes,dtype=self.store_dtype,offset=index,count=spec.size).astype(spec.dtype).reshape(spec.shape)
      index = index + spec.size*self.store_dtype.itemsize
    return result

  def arrays_to_bytes(self,dict):
    result = b''
    for k,v in dict.items():
      result = result + v.astype(self.store_dtype).tobytes()
    return result

def partition_sizes(sizes,min_size=20000):
  # Return partitioning of sizes (list of ind arrays) such that the total sum of each subset is smaller than the largest singlet
  # Must be deterministic - using mergesort since it's stable, in case input order changes
  sort_order = np.argsort(sizes,kind='mergesort')[::-1]
  max_size = sizes[sort_order[0]]
  if max_size < min_size:
    return [sort_order]
  
  result = []
  while sort_order.size > 0:
    cumsum = np.cumsum(sizes[sort_order])
    if np.all(cumsum<=max_size):
      result.append(sort_order)
      break
    
    last_ind = np.max([np.argmax(cumsum>max_size),1])
    result.append(sort_order[:last_ind])
    sort_order = sort_order[last_ind:]
     
  return result

def split_dicts(ordered_dict,partitioning):
  return [OrderedDict([(k,v) for k,v in [ordered_dict.items()[i] for i in p]]) for p in partitioning]
