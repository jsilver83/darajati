from django.apps import AppConfig


class AttendancesAndGradesConfig(AppConfig):
    name = 'attendances_and_grades'

    def ready(self):
        import attendances_and_grades.signals