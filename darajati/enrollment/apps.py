from django.apps import AppConfig


class EnrollmentConfig(AppConfig):
    name = 'enrollment'

    def ready(self):
        import enrollment.signals