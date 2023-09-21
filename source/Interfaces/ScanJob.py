import os
from abc import abstractmethod
from context.context_creator import create_db_context


class ScanJob:

    @abstractmethod
    def __init__(self, object_id_list):
        pass

    @abstractmethod
    def start_scan(self):
        pass




