import unittest
from unittest.mock import Mock

import pandas as pd

from autorh247.core.processor import AbonoProcessor


class ProcessorTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock()
        self.processor = AbonoProcessor(self.service)

    def test_processa_inclusao_de_uma_linha(self):
        self.service.buscar_funcionario.return_value = [{"id": 42}]
        frame = pd.DataFrame(
            [{
                "Status": "",
                "Nome Completo": "Joao",
                "Data Inicial": "01/08/2026",
                "Data Final": "02/08/2026",
                "Descrição": "Atestado",
            }]
        )

        self.processor._processar_linha(frame, 0, frame.iloc[0], 1)

        self.assertEqual(frame.at[0, "Status"], "OK")
        self.service.enviar_abono.assert_called_once_with(
            42, "01/08/2026", "02/08/2026", "Atestado"
        )

    def test_processa_remocao_de_todos_os_dias_do_intervalo(self):
        self.service.buscar_funcionario.return_value = [{"fv_alteracao_escala_main": 42}]
        frame = pd.DataFrame(
            [{
                "Status": "DELETE",
                "Nome Completo": "Joao",
                "Data Inicial": "01/08/2026",
                "Data Final": "03/08/2026",
                "Descrição": "",
            }]
        )

        self.processor._processar_linha(frame, 0, frame.iloc[0], 1)

        self.assertEqual(frame.at[0, "Status"], "DELETED")
        self.assertEqual(self.service.remover_abono_dia.call_count, 3)
        self.assertEqual(
            [call.kwargs["data_iso"] for call in self.service.remover_abono_dia.call_args_list],
            ["2026-08-01", "2026-08-02", "2026-08-03"],
        )


if __name__ == "__main__":
    unittest.main()
