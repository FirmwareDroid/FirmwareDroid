from abc import abstractmethod


class VulnCheck:
    result = None
    apk_path = None
    rule_name = None
    rule_path = None

    @abstractmethod
    def __init__(self, apk_path, rule_dir_path):
        raise NotImplementedError("Please Implement this method")

    @abstractmethod
    def verify(self):
        raise NotImplementedError("Please Implement this method")
