# Py4Uview: Tools for Uview images

## Introduction
__Py4Uview__ provides a set of tools for images saved by Uivew, which is used by SPEELEEM in MAXPEEM to save the user's data in format of .dat file. Py4Uview can read the image and metadata from the file saved by Uview software.

## Quick start
### Install
```
python -m pip install py4uview
```
### import
``` python
>>> import py4uview
```
### How to use?

1. use `read_uv_dat()` function to read the data and metadata.
``` ipython
In [1]: import py4uview as pu

In [2]: data = pu.read_uv_dat("./testfiles/LEEM.dat")

In [3]: data.metadata
Out[3]:
{'id': b'UKSOFT2001',
 'size': 104,
 'version': 8,
 'bitsperpix': 16,
 'width': 1024,
 'height': 1024,
 'noimg': 1,
 'attachedRecipeSize': 0,
 'isize': 288,
 ......

In [4]: data.data
Out[4]:
array([[3047, 2880, 2652, ..., 2716, 2630, 2562],
       [2789, 2848, 2862, ..., 2549, 2485, 2655],
       [2808, 2840, 2739, ..., 2640, 2602, 2747],
       ...,
       [3054, 2675, 2656, ..., 1926, 2017, 2021],
       [2885, 2949, 2705, ..., 1907, 1886, 1945],
       [2810, 2688, 2807, ..., 2009, 2025, 2641]], dtype=uint16)
 ```

2. Use `Uview` class method `read_dat()` to read the dat file

```ipython
In [1]: import py4uview as pu

In [2]: data = pu.Uview.read_dat("./testfiles/LEEM.dat")

In [3]: data.attrs
Out[3]:
{'id': b'UKSOFT2001',
 'size': 104,
 'version': 8,
 'bitsperpix': 16,
 'width': 1024,
 'height': 1024,
 'noimg': 1,
 'attachedRecipeSize': 0,
 'isize': 288,
 ......

In [4]: data.data
Out[4]:
array([[3047, 2880, 2652, ..., 2716, 2630, 2562],
       [2789, 2848, 2862, ..., 2549, 2485, 2655],
       [2808, 2840, 2739, ..., 2640, 2602, 2747],
       ...,
       [3054, 2675, 2656, ..., 1926, 2017, 2021],
       [2885, 2949, 2705, ..., 1907, 1886, 1945],
       [2810, 2688, 2807, ..., 2009, 2025, 2641]], dtype=uint16)
```
