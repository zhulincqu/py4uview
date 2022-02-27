# Py4Uview: Tools for Uview images 

## Introduction
__Py4Uview__ provides a set of tools for images saved by Uivew, which is used by SPEELEEM in MAXPEEM to save the user's data in format of .dat file. It contains one class: [UviewImage]. One instance of [UviewImage] is for one image, which have two attribure: [UviewImage.image] and [UviewImage.metadata].
 
## Method
 __Py4Uview__ have two core data structures, which inherit from two core data structure ([DataArray](http://xarray.pydata.org/en/stable/generated/xarray.DataArray.html#xarray.DataArray) and [Dataset](http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html#xarray.Dataset) ) from [Xarray](https://xarray.pydata.org/). The images are saved in the [xarray](https://xarray.pydata.org/) -- A multi-dimensions arrays. One single image is save as [DataArray](http://xarray.pydata.org/en/stable/generated/xarray.DataArray.html#xarray.DataArray), while a series of images, e.g. XAS-PEEM, XPS_PEEM, are saved as [Dataset](http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html#xarray.Dataset). The Dataset is a dict-like container of DataArray objects aligned along any number of shared dimensions.