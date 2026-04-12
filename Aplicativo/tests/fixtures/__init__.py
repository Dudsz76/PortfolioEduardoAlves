"""
Fixtures (dados de teste) reutilizáveis
"""
from .dados_teste import (
    tarefa_exemplo,
    lista_tarefas,
    dados_json_validos
)
from .mock_objects import (
    criar_tarefa_mock,
    criar_app_mock
)

__all__ = [
    'tarefa_exemplo',
    'lista_tarefas', 
    'dados_json_validos',
    'criar_tarefa_mock',
    'criar_app_mock'
]