# -*- coding:utf-8 -*-
# NOTE: Changes in the global settings might not immediately affect
# the precompiled (and cached) functions in helpers_numba.py!

PACKAGE_NAME = "timezonefinder"

DEFAULT_INPUT_PATH = "combined-with-oceans.json"
DEFAULT_OUTPUT_PATH = "."  # store parsed data in same directory as default

DEBUG = False
# DEBUG = True
DEBUG_POLY_STOP = 20  # parse only some polygons in debugging mode

# no "magic numbers" import all as "constants" from this global settings file
# ATTENTION: Don't change these settings or timezonefinder wont work!
# different setups of shortcuts are not supported, because then addresses in the .bin
# need to be calculated depending on how many shortcuts are being used.
# number of shortcuts per longitude
NR_SHORTCUTS_PER_LNG = 1
# shortcuts per latitude
NR_SHORTCUTS_PER_LAT = 2
NR_LAT_SHORTCUTS = 180 * NR_SHORTCUTS_PER_LAT

OCEAN_TIMEZONE_PREFIX = r"Etc/GMT"

# DATA FILES
# BINARY
BINARY_FILE_ENDING = ".bin"

POLY_ZONE_IDS = "poly_zone_ids"
POLY_COORD_AMOUNT = "poly_coord_amount"
POLY_ADR2DATA = "poly_adr2data"
POLY_MAX_VALUES = "poly_max_values"
POLY_DATA = "poly_data"
POLY_NR2ZONE_ID = "poly_nr2zone_id"

HOLE_COORD_AMOUNT = "hole_coord_amount"
HOLE_ADR2DATA = "hole_adr2data"
HOLE_DATA = "hole_data"

SHORTCUTS_ENTRY_AMOUNT = "shortcuts_entry_amount"
SHORTCUTS_ADR2DATA = "shortcuts_adr2data"
SHORTCUTS_DATA = "shortcuts_data"
SHORTCUTS_UNIQUE_ID = "shortcuts_unique_id"

BINARY_DATA_ATTRIBUTES = [
    POLY_ZONE_IDS,
    POLY_COORD_AMOUNT,
    POLY_ADR2DATA,
    POLY_MAX_VALUES,
    POLY_DATA,
    POLY_NR2ZONE_ID,
    HOLE_COORD_AMOUNT,
    HOLE_ADR2DATA,
    HOLE_DATA,
    SHORTCUTS_ENTRY_AMOUNT,
    SHORTCUTS_ADR2DATA,
    SHORTCUTS_DATA,
    SHORTCUTS_UNIQUE_ID,
]

SHORTCUTS_DIRECT_ID = "shortcuts_direct_id"  # for TimezoneFinderL only

# JSON
JSON_FILE_ENDING = ".json"
TIMEZONE_NAMES = "timezone_names"
HOLE_REGISTRY = "hole_registry"
JSON_DATA_ATTRIBUTES = [TIMEZONE_NAMES]
TIMEZONE_NAMES_FILE = TIMEZONE_NAMES + JSON_FILE_ENDING
HOLE_REGISTRY_FILE = HOLE_REGISTRY + JSON_FILE_ENDING

DATA_ATTRIBUTE_NAMES = BINARY_DATA_ATTRIBUTES + [HOLE_REGISTRY]

# all data files that should be included in the build:
ALL_BINARY_FILES = [
    specifier + BINARY_FILE_ENDING for specifier in BINARY_DATA_ATTRIBUTES
] + [SHORTCUTS_DIRECT_ID + BINARY_FILE_ENDING]
ALL_JSON_FILES = [TIMEZONE_NAMES_FILE, HOLE_REGISTRY_FILE]
PACKAGE_DATA_FILES = ALL_BINARY_FILES + ALL_JSON_FILES

# TODO create variables for used dtype for each type of data (polygon address, coordinate...)
# B = unsigned char (1byte = 8bit Integer)
NR_BYTES_B = 1
DTYPE_FORMAT_B_NUMPY = "<i1"

# H = unsigned short (2 byte integer)
NR_BYTES_H = 2
DTYPE_FORMAT_H = b"<H"
DTYPE_FORMAT_H_NUMPY = "<u2"
THRES_DTYPE_H = 2 ** (NR_BYTES_H * 8)  # = 65536

# value to write for representing an invalid zone (e.g. no shortcut polygon)
# = 65535 = highest possible value with H (2 byte unsigned integer)
INVALID_VALUE_DTYPE_H = THRES_DTYPE_H - 1

# i = signed 4byte integer
NR_BYTES_I = 4
DTYPE_FORMAT_SIGNED_I_NUMPY = "<i4"
DTYPE_FORMAT_SIGNED_I = b"<i"
THRES_DTYPE_SIGNED_I_UPPER = 2 ** ((NR_BYTES_I * 8) - 1)
THRES_DTYPE_SIGNED_I_LOWER = -THRES_DTYPE_SIGNED_I_UPPER

# I = unsigned 4byte integer
DTYPE_FORMAT_I = b"<I"
THRES_DTYPE_I = 2 ** (NR_BYTES_I * 8)

# f = 8byte signed float
DTYPE_FORMAT_F_NUMPY = "<f8"

# IMPORTANT: all values between -180 and 180 degree must fit into the domain of i4!
# is the same as testing if 360 fits into the domain of I4 (unsigned!)
MAX_ALLOWED_COORD_VAL = 2 ** (8 * NR_BYTES_I - 1)

# from math import floor,log10
# DECIMAL_PLACES_SHIFT = floor(log10(MAX_ALLOWED_COORD_VAL/180.0)) # == 7
DECIMAL_PLACES_SHIFT = 7
INT2COORD_FACTOR = 10 ** (-DECIMAL_PLACES_SHIFT)
COORD2INT_FACTOR = 10 ** DECIMAL_PLACES_SHIFT
max_int_val = 180.0 * COORD2INT_FACTOR
assert max_int_val < MAX_ALLOWED_COORD_VAL

# the maximum possible distance is half the perimeter of earth pi * 12743km = 40,054.xxx km
MAX_HAVERSINE_DISTANCE = 40100

# TESTS
DECIMAL_PLACES_ACCURACY = 7
