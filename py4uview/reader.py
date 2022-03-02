"""
Module contains tools for processing one Uview dat file.
"""
import logging
import struct
import sys
import numpy as np
from datetime import datetime, timedelta


def read_uv_dat(filepath):
    """Read image and medata from .dat file saved by Uview.

    Parameters
    ----------
    filepath : path(string)
        date and time value of this image.
        this value represents the number of 100-nanosecond units since
        the beginning of January 1, 1601.

    Returns:
    -------
    Instance: FileReader
        A instance of FileReader class.
    """
    return FileReader(filepath)


# data_fields with standard format in MAXPEEM
KNOWN_TAGS = [
    210,
    203,
    185,
    208,
    215,
    184,
    169,
    222,
    136,
    137,
    133,
    134,
    138,
    135,
    132,
    143,
    144,
    206,
    172,
    147,
    171,
    145,
    146,
    148,
    168,
    130,
    131,
    158,
    159,
    128,
    129,
    161,
    162,
    211,
    163,
    149,
    187,
    177,
    178,
    180,
    181,
    202,
    190,
    191,
    194,
    195,
    196,
    214,
    198,
    199,
    182,
    179,
    200,
    201,
    176,
    197,
    192,
    213,
    209,
    183,
    186,
    212,
    164,
    165,
    140,
    141,
    11,
    160,
    150,
    151,
    153,
    154,
    156,
    157,
    152,
    155,
    173,
    174,
    205,
    204,
    188,
    189,
    175,
    162,
    170,
    142,
    207,
    219,
    39,
    38,
]
UNIT_DICT = ("", "V", "mA", "A", "°C", " K", "mV", "pA", "nA", "\xb5A")
# 235: COL, 236:Gauge 3, 237:PCH, 106:MCH
GAUGE_TAGS = [106, 235, 236, 237]

_EPOCH_START = datetime(year=1601, month=1, day=1)


def _convert_ad_timestamp(timestamp):
    """Convert date and time value to datetime object.

    Parameters
    ----------
    timestamp : int
        date and time value of this image.
        this value represents the number of 100-nanosecond units since
        the beginning of January 1, 1601.

    Returns:
    -------
    datetime: timestamp
        time in form of datetime type.
    """
    seconds_since_epoch = timestamp / 10**7
    return _EPOCH_START + timedelta(seconds=seconds_since_epoch)


class FileReader:
    __slots__ = (
        "metadata",
        "data",
        "markups",
        "recipe",
        "_position",
        "_markups",
        "_leemheader",
    )

    def __init__(self, filepath):
        self._position = 0
        self.metadata = {}
        self._read(filepath)

    def _read_field(self):
        """Read data fields formatted by
        "address-name(str)-unit(ASCII digit)-0-value(float)".

        Args:
            current_position(int): Number of position for the metadata's
                name.

        returns:
            tuple: (name, units_dict[unit_tag], val, offset)
        """
        # UNIT_DICT = ('', 'V', 'mA', 'A', '°C', ' K', 'mV', 'pA', 'nA', '\xb5A')

        temp = self._leemheader[self._position + 1 :].split(b"\x00")[0]
        name = temp[:-1].decode("cp1252")
        if sys.version_info[0] > 2:
            unit_tag = int(chr(temp[-1]))
        else:
            unit_tag = int(temp[-1])
        val = struct.unpack(
            "<f",
            self._leemheader[
                self._position + len(temp) + 2 : self._position + len(temp) + 6
            ],
        )[0]
        offset = len(temp) + 5  # length of entire field
        return name, UNIT_DICT[unit_tag], val, offset

    def _read_leemheader(self):

        b_iter = iter(self._leemheader)

        # 235: COL, 236:Gauge 3, 237:PCH, 106:MCH
        # GAUGE_TAGS = [106, 235, 236, 237]
        for b in b_iter:
            if sys.version_info[0] < 3:
                b = ord(b)
            #### DEBUG ####
            logging.debug("b = {}".format(b))
            ###############

            # stop when reaching end of header
            if b == 255:
                break

            # Data fields with standard format
            elif b in KNOWN_TAGS:
                [fieldname, unit, value, offset] = self._read_field()
                self.metadata[fieldname] = [value, unit]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(b, fieldname + ":", value, unit)
                )

            # Camera Exposure and average images
            # Average Images = 0 : No Averaging
            # Average Images = 255 : Sliding Averaging
            elif b == 104:
                self.metadata["Camera Exposure"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 1 : self._position + 5]
                    )[0],
                    "s",
                ]
                self.metadata["Average Images"] = self._leemheader[self._position + 5]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        b,
                        "Camera Exposure:",
                        self.metadata["Camera Exposure"][0],
                        self.metadata["Camera Exposure"][1],
                    )
                )

                if self.metadata["Average Images"] == 0:
                    logging.info(
                        "\t{:>3}\t{:<18}\t{:d} {}".format(
                            "",
                            "Average Images:",
                            self.metadata["Average Images"],
                            "\t=> No Averaging",
                        )
                    )

                elif self.metadata["Average Images"] == 255:
                    logging.info(
                        "\t{:>3}\t{:<18}\t{:d} {}".format(
                            "",
                            "Average Images:",
                            self.metadata["Average Images"],
                            "\t=> Sliding Average",
                        )
                    )
                else:
                    if sys.version_info[0] > 2:
                        logging.info(
                            "\t{:>3}\t{:<18}\t{:g}".format(
                                "", "Average Images:", self.metadata["Average Images"]
                            )
                        )
                    else:
                        logging.info(
                            "\t{:>3}\t{:<18}\t{:g}".format(
                                "",
                                "Average Images:",
                                ord(self.metadata["Average Images"]),
                            )
                        )
                offset = 6

            # Pressure Gauges
            elif b in GAUGE_TAGS:
                [pressure_gauge, unit, pressure, offset] = self._read_varian()
                self.metadata[pressure_gauge] = [pressure, unit]

            # Image Title
            elif b == 233:
                temp = self._leemheader[self._position + 1 :].split(b"\x00")[0]
                self.metadata["Image Title"] = temp.decode("cp1252")
                logging.info(
                    "\t{:>3}\t{:<18}\t{}".format(
                        b, "Image Title:", self.metadata["Image Title"]
                    )
                )
                offset = len(temp) + 1

            # MCP screen
            elif b == 243:
                self.metadata["MCPscreen"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 1 : self._position + 5]
                    )[0],
                    "V",
                ]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        b,
                        "MCPscreen:",
                        self.metadata["MCPscreen"][0],
                        self.metadata["MCPscreen"][1],
                    )
                )
                offset = 4

            # MCP channel plate
            elif b == 244:
                self.metadata["MCPchannelplate"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 1 : self._position + 5]
                    )[0],
                    "V",
                ]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        b,
                        "MCPchannelplate:",
                        self.metadata["MCPchannelplate"][0],
                        self.metadata["MCPchannelplate"][1],
                    )
                )
                offset = 4

            # Micrometers(x,y)
            elif b == 100:
                self.metadata["Mitutoyo X"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 1 : self._position + 5]
                    )[0],
                    "mm",
                ]
                self.metadata["Mitutoyo Y"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 5 : self._position + 9]
                    )[0],
                    "mm",
                ]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        b,
                        "Mitutoyo X:",
                        self.metadata["Mitutoyo X"][0],
                        self.metadata["Mitutoyo X"][1],
                    )
                )
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        "",
                        "Mitutoyo Y:",
                        self.metadata["Mitutoyo Y"][0],
                        self.metadata["Mitutoyo Y"][1],
                    )
                )
                offset = 8

                # Mirror state
            elif b == 242:
                self.metadata["MirrorState"] = self._leemheader[self._position + 1]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g}".format(
                        b, "MirrorState:", self.metadata["MirrorState"]
                    )
                )
                offset = 2

            # FOV
            elif b == 110:
                temp = self._leemheader[self._position + 1 :].split(b"\x00")[0]
                fov_str = temp.decode("cp1252")
                self.metadata["FOV cal. factor"] = float(
                    struct.unpack(
                        "<f",
                        self._leemheader[
                            self._position
                            + len(temp)
                            + 2 : self._position
                            + len(temp)
                            + 6
                        ],
                    )[0]
                )

                # for LEED images
                if fov_str[0:4] == "LEED":
                    self.metadata["LEED"] = True
                    self.metadata["FOV"] = None
                    logging.info(
                        "\t{:>3}\t{:<18}\t{}".format(b, "Field Of View:", "LEED")
                    )

                # for normal images
                elif fov_str[0:4] == "none":
                    self.metadata["FOV"] = None
                    logging.info(
                        "\t{:>3}\t{:<18}\t{}".format(b, "Field Of View:", "None")
                    )
                # for PES images
                elif fov_str[0:8] == "disp.pl.":
                    self.metadata["FOV"] = None
                    self.metadata["disp_plane"] = True
                    logging.info(
                        "\t{:>3}\t{:<18}\t{}".format(b, "Field Of View:", "disp.pl.")
                    )
                else:
                    self.metadata["LEED"] = False
                    try:
                        self.metadata["FOV"] = [
                            float(fov_str.split("\xb5m")[0]),
                            "\xb5m",
                        ]
                        logging.info(
                            "\t{:>3}\t{:<18}\t{} {}".format(
                                b,
                                "Field Of View:",
                                self.metadata["FOV"][0],
                                self.metadata["FOV"][1],
                            )
                        )
                    except ValueError:
                        logging.error(
                            "FOV field tag: not known string detected: {}".format(
                                fov_str
                            )
                        )
                logging.info(
                    "\t{:>3}\t{:<18}\t{}".format(
                        "", "FOV cal. factor:", self.metadata["FOV cal. factor"]
                    )
                )
                offset = len(temp) + 5

            # FOV rotation from LEEM presets
            elif b == 113:
                self.metadata["Rotation"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 1 : self._position + 5]
                    )[0],
                    "degree",
                ]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        b,
                        "Rotation:",
                        self.metadata["Rotation"][0],
                        self.metadata["Rotation"][1],
                    )
                )
                offset = 4
            # Spin up or down
            elif b == 240:
                self.metadata["Spin up_down"] = self._leemheader[self._position + 1]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g}".format(
                        b, "Spin up_down:", self.metadata["Spin up_down"]
                    )
                )
                offset = 2

            # Theta and Phi
            elif b == 239:
                self.metadata["Theta"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 1 : self._position + 5]
                    )[0],
                    "degree",
                ]
                self.metadata["Phi"] = [
                    struct.unpack(
                        "<f", self._leemheader[self._position + 5 : self._position + 9]
                    )[0],
                    "degree",
                ]
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        b,
                        "Theta:",
                        self.metadata["Theta"][0],
                        self.metadata["Theta"][1],
                    )
                )
                logging.info(
                    "\t{:>3}\t{:<18}\t{:g} {}".format(
                        "", "Phi:", self.metadata["Phi"][0], self.metadata["Phi"][1]
                    )
                )
                offset = 8

            else:
                logging.error(
                    "ERROR: Unknown field tag {0} at "
                    "position {1}. This and following data fields might "
                    "be misinterpreted!".format(b, self._position)
                )
                # skip byte number given by offset - depending on length of
            # read data field, update position counter
            [next(b_iter) for x in range(offset)]
            self._position += offset + 1

    def _read_varian(self):
        """
        Read data fields for varian vacuum pressure gauges and return the
        metadata.

        Args:
            header(Byte): Image header contains metadata
            current_position(int): Number of position for the metadata's
                name.
        """
        temp_1 = self._leemheader[self._position + 1 :].split(b"\x00")[0]
        temp_2 = self._leemheader[self._position + 1 :].split(b"\x00")[1]
        str_1 = temp_1.decode("cp1252")  # Name
        str_2 = temp_2.decode("cp1252")  # Unit
        val = struct.unpack(
            "<f",
            self._leemheader[
                self._position
                + len(temp_1)
                + len(temp_2)
                + 3 : self._position
                + len(temp_1)
                + len(temp_2)
                + 7
            ],
        )[0]
        offset = len(temp_1) + len(temp_2) + 6  # length of entire field
        logging.info(
            "\t{:>3}\t{:<18}\t{:g} {}".format(
                self._leemheader[self._position], str_1 + ":", val, str_2
            )
        )
        return str_1, str_2, val, offset

    def _read_markups(self):
        """read out the markups"""
        MARKER_LENGTH = {  # byte
            "marker": 24,
            "horizontal": 0,
            "vertical": 0,
            "arbitrary": 14,
            "label": 0,
        }
        self.markups = {}
        i = 4
        type_marker = struct.unpack("<H", self._markups[i : i + 2])[0]
        while type_marker:
            if type_marker == 6:  # markers
                mytype = "marker"
                length_byte = MARKER_LENGTH[mytype]
                raw_markup = self._markups[i : i + length_byte]
                unpack_format = "<" + str(length_byte // 2) + "H"
                markup = struct.unpack(unpack_format, raw_markup)
                mark_val = {
                    "x": markup[1],
                    "y": markup[2],
                    "radius": markup[3],
                }
                if mytype in self.markups.keys():
                    self.markups[mytype].append(mark_val)
                else:
                    self.markups[mytype] = list()
                    self.markups[mytype].append(mark_val)
                i += MARKER_LENGTH[mytype]
            elif type_marker == 3:  # arbitrary cross section
                mytype = "arbitrary"
                length_byte = MARKER_LENGTH[mytype]
                raw_markup = self._markups[i : i + length_byte]
                unpack_format = "<" + str(length_byte // 2) + "H"
                markup = struct.unpack(unpack_format, raw_markup)
                mark_val = {
                    "x0_y0": (markup[1], markup[2]),
                    "x1_y1": (markup[3], markup[4]),
                }
                if mytype in self.markups.keys():
                    self.markups[mytype].append(mark_val)
                else:
                    self.markups[mytype] = list()
                    self.markups[mytype].append(mark_val)
                i += MARKER_LENGTH[mytype]
            else:
                print("Unknown marker")
                break
            type_marker = struct.unpack("<H", self._markups[i : i + 2])[0]

    def _read(self, filepath):
        """Generic reader of UView .dat files."""
        # data_fields with standard format in MAXPEEM
        # KNOWN_TAGS = [210, 203, 185, 208, 215, 184, 169, 222, 136, 137, 133, 134, 138,
        #               135, 132, 143, 144, 206, 172, 147, 171, 145, 146, 148, 168, 130,
        #               131, 158, 159, 128, 129, 161, 162, 211, 163, 149, 187, 177, 178,
        #               180, 181, 202, 190, 191, 194, 195, 196, 214, 198, 199, 182, 179,
        #               200, 201, 176, 197, 192, 213, 209, 183, 186, 212, 164, 165, 140,
        #               141, 11, 160, 150, 151, 153, 154, 156, 157, 152, 155, 173, 174,
        #               205, 204, 188, 189, 175, 162, 170, 142, 207, 219, 39, 38]
        with open(filepath, "rb") as f:
            self.metadata["id"] = f.read(20).split(b"\x00")[0]
            self.metadata["size"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["version"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["bitsperpix"] = struct.unpack("<h", f.read(2))[0]

            f.seek(6, 1)  # for alignment
            f.seek(8, 1)  # spare

            self.metadata["width"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["height"] = struct.unpack("<h", f.read(2))[0]
            logging.info(
                "\tDimensions:\t {} x {}".format(
                    self.metadata["width"], self.metadata["height"]
                )
            )
            # ‘<h’ Byte order: little-endian; C Type: short
            self.metadata["noimg"] = struct.unpack("<h", f.read(2))[0]
            attachedRecipeSize = struct.unpack("<h", f.read(2))[0]
            self.metadata["attachedRecipeSize"] = attachedRecipeSize

            f.seek(56, 1)  # spare

            # read recipe (fixed 128 bytes) if there is one
            if attachedRecipeSize:
                self._recipe = f.read(attachedRecipeSize)
                f.seek(128 - attachedRecipeSize, 1)

            # read first block of image header (fixed size 288bytes)
            self.metadata["isize"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["iversion"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["colorscale_low"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["colorscale_high"] = struct.unpack("<h", f.read(2))[0]

            self.metadata["timestamp"] = _convert_ad_timestamp(
                struct.unpack("<Q", f.read(8))[0]
            )
            logging.info(
                "\tTime Stamp:\t{}".format(
                    self.metadata["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            self.metadata["mask_xshift"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["mask_yshift"] = struct.unpack("<h", f.read(2))[0]
            self.metadata["usemask"] = f.read(1)

            f.seek(1, 1)  # spare

            att_markupsize = struct.unpack("<h", f.read(2))[0]
            self.metadata["att_markupsize"] = att_markupsize
            self.metadata["spin"] = struct.unpack("<h", f.read(2))[0]
            versleemdata = struct.unpack("<h", f.read(2))[0]  # 28 bytes
            # self.metadata["versleemdata"] = versleemdata

            logging.info("\tCOLLECTING META DATA:\t")
            # read second block of image header into byte sequence
            #      -     usually block of 288(fixed size) - 28(read already) bytes
            #     -     if too many metadata are stored, 388 empty bytes
            #        followed by number given in versleemdata
            if versleemdata <= 2:
                leemheader = f.read(240)  # 240 bytes leemdata.
                f.seek(20, 1)  # spare
            else:
                f.seek(260, 1)
                if att_markupsize > 0:
                    self._markups = f.read(128 * (att_markupsize // 128 + 1))
                    self._read_markups()
                leemheader = f.read(versleemdata)

            #### DEBUG ####
            logging.debug("type(img_leemheader) = {}".format(type(leemheader)))
            ###############
            self._leemheader = leemheader
            self._read_leemheader()

            # Now read image data
            # Seek relative to the file's end (2)
            f.seek(-2 * self.metadata["height"] * self.metadata["width"], 2)
            self.data = np.fromfile(f, dtype=np.uint16, sep="")
            self.data = self.data.reshape(
                [self.metadata["height"], self.metadata["width"]]
            )
            # Flip image to get the original orientation
            self.data = np.flipud(self.data)
