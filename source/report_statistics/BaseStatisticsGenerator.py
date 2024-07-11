class BaseStatisticsGenerator:
    def __init__(self, reports, attribute_names=None):
        self.reports = reports
        self.attribute_names = attribute_names or self._discover_attributes()

    def _discover_attributes(self):
        """
        Auto-discover attributes from the first report object that are relevant for statistics.
        This example assumes all reports have a similar structure.
        """
        if not self.reports:
            return []
        first_report = self.reports[0]
        # Example: Discover DictField attributes
        return [attr for attr, value in first_report._data.items() if isinstance(value, dict)]

    def count_attribute_occurrences(self, attribute_name):
        """
        Counts occurrences of a specific attribute across all reports.
        """
        attribute_counts = {}
        for report in self.reports:
            attribute_value = getattr(report, attribute_name, None)
            if attribute_value:
                for key, value in attribute_value.items():
                    attribute_counts[key] = attribute_counts.get(key, 0) + value
        return attribute_counts

    def generate_statistics(self):
        """
        Generate statistics for predefined or discovered attributes.
        """
        statistics = {}
        for attribute_name in self.attribute_names:
            statistics[attribute_name] = self.count_attribute_occurrences(attribute_name)
        return statistics
