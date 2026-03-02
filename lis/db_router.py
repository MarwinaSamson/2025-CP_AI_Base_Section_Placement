from django.conf import settings


class LISRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'lis':
            # Only route to 'lis' DB if it's actually configured (local dev)
            # In production (Railway), fall back to default DB
            if 'lis' in settings.DATABASES:
                return 'lis'
            return None
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'lis':
            return None  # Prevent writes
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Allow lis migrations only on the appropriate database."""
        if app_label == 'lis':
            # If 'lis' DB exists, only migrate there; otherwise use default
            if 'lis' in settings.DATABASES:
                return db == 'lis'
            return db == 'default'
        return None
