import numpy as np
import matplotlib.pyplot as plt
import scipy


from xarray.core.dataarray import DataArray
from py4uview.reader import read_uv_dat


class Uview(DataArray):
    """Import Elmitec dat format file containning image and metadata.
    Return an intance of Uview class.

    Attributes:
        data(np.array): 2D np.array saves the image.
        metadata(dict): A dictionary savees the all metadata.

    Methods:
        filterInelasticBkg(self, sigma=15): Filter inelastic background.
        display_image(self): Display the image.
        image2xarray(self): convert image and metadata to xarray.

    Example:
        im = DATImage('../testfiles/LEEM.dat')
        im.data # show the 2D np.array image.
        im.metadata # show the metadata in form of dictionary.
    """

    __slots__ = (
        "markups",
        "leemdata",
    )

    def __init__(self, markups=None, *args, **kargs):
        self.markups = markups
        super().__init__(*args, **kargs)

    @classmethod
    def read_dat(cls, filename):
        f = read_uv_dat(filename)
        return cls(
            f.markups,
            f.data,
            coords={
                "height": range(f.metadata["height"]),
                "width": range(f.metadata["width"]),
                "time": f.metadata["timestamp"],
            },
            dims=["height", "width"],
            name="Intensity",
            attrs=f.metadata,
        )

    def filterInelasticBkg(self, sigma=15):
        """Experimental function to remove the inelastic background in
        LEED images. Works like a high-pass filter by subtracting the
        gaussian filtered image.

        Args:
            sigma(optional): GaussFilter parameter. Default is 15.

        Returns:
            ndarray: Filtered 2D np.ndarray.
        """
        self.data = np.divide(self.data, self.data.max())
        dataGaussFiltered = scipy.ndimage.gaussian_filter(self.data, sigma)
        return self.data - dataGaussFiltered

    def display_image(self):
        """
        Display the image using matplotlib.

        Returns:
            tuple(fig,ax)
        """

        fig = plt.figure(
            frameon=False,
            figsize=(3, 3 * self.attrs["height"] / self.attrs["width"]),
            dpi=self.attrs["width"] / 3,
        )
        ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(
            self.data,
            cmap="gray",
            clim=(np.amin(self.data), np.amax(self.data)),
            aspect="auto",
        )
        plt.show()
        return fig, ax


if __name__ == "__main__":
    pass
#     (fig, ax) = im.display_image()
