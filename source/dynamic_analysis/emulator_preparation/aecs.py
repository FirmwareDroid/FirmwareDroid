from context.context_creator import create_db_context
from model.AecsJob import AecsJob


@create_db_context
def update_or_create_aecs_job(firmware_id_list, aces_job_id=None, arch=None):
    """
    Updates or creates the aecs-job in the database.

    :param arch: str - cpu architecture of the firmware.
    :param aces_job_id: str - id of the aecs job.
    :param firmware_id_list: list(str) - list of firmware ids.

    """
    if firmware_id_list and len(firmware_id_list) > 0:
        if aces_job_id:
            aecs_job_list = AecsJob.objects(pk=aces_job_id)
            if len(aecs_job_list) == 0:
                raise ValueError(f"No aecs job found with id: {aces_job_id}")
            for aecs_job in aecs_job_list:
                aecs_job.firmware_id_list = firmware_id_list
                if arch:
                    aecs_job.arch = arch
                aecs_job.save()
        else:
            AecsJob(firmware_id_list=firmware_id_list, arch=arch).save()
    else:
        raise ValueError("No firmware ids found.")
