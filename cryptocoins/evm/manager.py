from kombu import Queue


class EVMHandlerManager:
    def __init__(self):
        self._registry = {}

    def register(self, evm_handler_class, **options):
        self._registry[evm_handler_class.CURRENCY.code] = evm_handler_class
        # print(f'Success register {evm_handler_class}')

    def get_handler(self, currency_code):
        return self._registry[currency_code]

    def register_celery_tasks(self, beat_schedule):
        queues = []
        for currency_code, evm_handler in self._registry.items():
            if not evm_handler.IS_ENABLED:
                continue

            beat_schedule.update({
                f'{currency_code}_process_new_blocks': {
                    'task': 'cryptocoins.tasks.evm.process_new_blocks_task',
                    'schedule': evm_handler.BLOCK_GENERATION_TIME,
                    'args': (currency_code,),
                    'options': {
                        'queue': f'{currency_code}_new_blocks',
                    }
                },
                f'{currency_code}_check_balances': {
                    'task': 'cryptocoins.tasks.evm.check_balances_task',
                    'schedule': evm_handler.ACCUMULATION_PERIOD,
                    'args': (currency_code,),
                    'options': {
                        'expires': 20,
                        'queue': f'{currency_code}_check_balances',
                    }
                },
            })
            queues.extend([
                Queue(f'{currency_code}_new_blocks'),
                Queue(f'{currency_code}_deposits'),
                Queue(f'{currency_code}_payouts'),
                Queue(f'{currency_code}_check_balances'),
                Queue(f'{currency_code}_accumulations'),
                Queue(f'{currency_code}_tokens_accumulations'),
                Queue(f'{currency_code}_send_gas'),
            ])
        return queues


evm_handlers_manager = EVMHandlerManager()


def register_evm_handler(cls):
    evm_handlers_manager.register(cls)
    return cls
