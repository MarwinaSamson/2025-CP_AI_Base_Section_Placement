from django.apps import AppConfig


class EnrollmentAppConfig(AppConfig):
    name = "enrollment_app"
    
    def ready(self):
        """Import signals when app is ready"""
        import enrollment_app.signals  # noqa
