import unittest
from unittest.mock import Mock, patch

from autorh247.api.services import RH247Service


class ResponseStub:
    content = b"{}"

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data

    def raise_for_status(self):
        pass


class ServicesTests(unittest.TestCase):
    def test_busca_por_nome_usa_params_em_vez_de_concatenar_url(self):
        client = Mock()
        client.get.return_value = ResponseStub([])
        service = RH247Service(client)

        with patch("autorh247.api.services.URL_SEARCH", "https://api.test/search"):
            service.buscar_por_nome("Joao & Silva")

        client.get.assert_called_once_with(
            "https://api.test/search",
            params={"descricao": '{"nome": ["Joao & Silva"]}'},
        )


if __name__ == "__main__":
    unittest.main()
