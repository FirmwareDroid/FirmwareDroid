from model import AndroidFirmware


def firmware_id_exists(firmware_id_list):
    existing_firmware_ids = set(AndroidFirmware.objects.filter(pk__in=firmware_id_list).values_list('pk', flat=True))
    missing_firmware_ids = set(firmware_id_list) - existing_firmware_ids
    if missing_firmware_ids:
        raise ValueError(f"The following firmware IDs do not exist in the database: {missing_firmware_ids}")