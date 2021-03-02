from model import ApplicationSetting


def get_application_setting():
    """
    Gets the application default settings.
    :return: class:'ApplicationSetting'
    """
    application_setting = ApplicationSetting.objects.first()
    if not application_setting:
        application_setting = create_application_setting()
    return application_setting


def create_application_setting():
    """
    Creates a class:'ApplicationSetting' instance and saves it to the database.
    :return: class:'ApplicationSetting'
    """
    return ApplicationSetting().save()
