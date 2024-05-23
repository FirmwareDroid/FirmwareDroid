from context.context_creator import create_db_context
from model.AecsJob import AecsJob


@create_db_context
def update_or_create_aecs_job(firmware_id_list):
    """
    Updates or creates the aecs-job in the database.

    :param firmware_id_list: list(str) - list of firmware ids.

    """
    if firmware_id_list and len(firmware_id_list) > 0:
        aecs_job = AecsJob.objects().first()
        if aecs_job:
            aecs_job.firmware_id_list = firmware_id_list
            aecs_job.save()
        else:
            AecsJob(firmware_id_list=firmware_id_list).save()
    else:
        raise ValueError("No firmware ids found.")
