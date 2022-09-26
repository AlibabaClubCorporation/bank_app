from django.apps import AppConfig


class BankControllerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_controller'

    def ready(self) -> None:
        import bank_controller.signals

        return super().ready()
