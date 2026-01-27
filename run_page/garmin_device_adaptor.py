import traceback
from io import BytesIO

try:
    from fit_tool.fit_file import FitFile
    from fit_tool.fit_file_builder import FitFileBuilder
    from fit_tool.profile.messages.device_info_message import DeviceInfoMessage
    from fit_tool.profile.messages.record_message import RecordMessage

    FIT_TOOL_AVAILABLE = True
except ImportError:
    FIT_TOOL_AVAILABLE = False

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


def process_garmin_data(origin_file, use_fake_garmin_device):
    if not FIT_TOOL_AVAILABLE:
        print(
            "fit-tool not available, skipping Garmin data processing. "
            "Install fit-tool for Python < 3.13 to use this feature."
        )
        origin_file.seek(0)
        return BytesIO(origin_file.read())

    try:
        origin_file_content = origin_file.read()
        # if origin file is not fit format, skip
        if not is_fit_file(origin_file):
            return BytesIO(origin_file_content)

        return do_process_garmin_data(origin_file_content, use_fake_garmin_device)
    except Exception:
        print("process garmin data failed, will use origin file")
        traceback.print_exc()
        return BytesIO(origin_file.read())


def do_process_garmin_data(file_content, use_fake_garmin_device):
    """
    Process garmin data, fix heart rate data and add fake garmin device info to fit file
    """
    fit_file = FitFile.from_bytes(file_content)
    builder = FitFileBuilder(auto_define=True)

    record_messages = []

    for record in fit_file.records:
        message = record.message
        if use_fake_garmin_device and message.global_id == DeviceInfoMessage.ID:
            # ignore file device info, like WorkoutDoors APP
            continue
        elif not isinstance(message, RecordMessage):
            builder.add(message)
        else:
            record_messages.append(message)

    # Add device info if needed
    if use_fake_garmin_device:
        device_info_message = get_device_info_message()
        builder.add(device_info_message)

    # Process and add heart rate data
    for message in get_processed_heart_rate_message(record_messages):
        builder.add(message)

    modified_file = builder.build()
    print("process garmin data success")
    return modified_file.to_bytes()


def find_valid_heart_rate(messages, current_index):
    """Find the nearest valid heart rate value."""

    for msg in messages[current_index + 1 :]:
        if msg.heart_rate is not None and msg.heart_rate != 255:
            return msg.heart_rate

    for msg in reversed(messages[:current_index]):
        if msg.heart_rate is not None and msg.heart_rate != 255:
            return msg.heart_rate

    return None


def create_new_record_message(old_message, heart_rate):
    """Create a new record message with updated heart rate."""
    new_message = RecordMessage()

    for field in old_message.fields:
        field_name = field.name
        if hasattr(old_message, field_name):
            field_value = getattr(old_message, field_name)
            if field_name == "heart_rate":
                setattr(new_message, field_name, heart_rate)
            elif field_value is not None:
                setattr(new_message, field_name, field_value)

    return new_message


def get_processed_heart_rate_message(record_messages):
    """Process heart rate data, replacing None/255 values with nearby valid values."""
    processed_messages = []

    for i, message in enumerate(record_messages):
        if message.heart_rate is None or message.heart_rate == 255:
            valid_heart_rate = find_valid_heart_rate(record_messages, i)
            if valid_heart_rate is not None:
                processed_messages.append(
                    create_new_record_message(message, valid_heart_rate)
                )
            else:
                processed_messages.append(message)
        else:
            processed_messages.append(message)

    print("process heart rate data success")
    return processed_messages


def get_device_info_message():
    """
    add customized device info to fit file,
    """

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

    print("add garmin device info success")
    return message
