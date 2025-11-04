"""
Конфигурация pytest
"""

import pytest
import logging

# Отключаем логирование во время тестов
@pytest.fixture(autouse=True)
def disable_logging():
    """Отключить логирование во время тестов"""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)

