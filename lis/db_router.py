class LISRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'lis':
            return 'lis'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'lis':
            return None  # Prevent writes
        return None
