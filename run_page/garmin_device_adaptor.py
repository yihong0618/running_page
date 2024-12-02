import traceback

from fit_tool.fit_file import FitFile
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.device_info_message import DeviceInfoMessage
from io import BytesIO

# the device manufacturer and product info can be found in github,
# https://github.com/garmin/fit-python-sdk/blob/main/garmin_fit_sdk/profile.py
MANUFACTURER = 1  # Garmin
GARMIN_DEVICE_PRODUCT_ID = 3415  # Forerunner 245
GARMIN_SOFTWARE_VERSION = 3.58
# The device serial number must be real Garmin will identify device with it
# here the default number:1234567890 Garmin will recognize it as Forerunner 245
GARMIN_DEVICE_SERIAL_NUMBER = 1234567890


def is_fit_file(file):
    file.seek(8)  # Move file pointer to the 9th byte
    header = file.read(4)
    file.seek(0)  # recover file pointer
    return header == b".FIT"


def wrap_device_info(origin_file):
    try:
        return do_wrap_device_info(origin_file)
    except Exception:
        print("wrap garmin device failed, will use origin file")
        traceback.print_exc()
        return BytesIO(origin_file.read())


def do_wrap_device_info(origin_file):
    """
    add customized device info to fit file,
    """
    # if origin file is gpx file, skip
    if not is_fit_file(origin_file):
        return BytesIO(origin_file.read())

    fit_file = FitFile.from_bytes(origin_file.read())
    builder = FitFileBuilder(auto_define=True)

    for record in fit_file.records:
        message = record.message
        if message.global_id == DeviceInfoMessage.ID:
            # ignore file device info, like WorkoutDoors APP
            continue
        builder.add(message)

    # Add custom Device Info
    message = DeviceInfoMessage()
    # the serial number must be real, otherwise Garmin will not identify it
    message.serial_number = GARMIN_DEVICE_SERIAL_NUMBER
    message.manufacturer = MANUFACTURER
    message.garmin_product = GARMIN_DEVICE_PRODUCT_ID
    message.software_version = GARMIN_SOFTWARE_VERSION
    message.device_index = 0
    message.source_type = 5
    message.product = GARMIN_DEVICE_PRODUCT_ID
    builder.add(message)

    modified_file = builder.build()
    print("wrap garmin device info sucess, product id:", GARMIN_DEVICE_PRODUCT_ID)
    return modified_file.to_bytes()
