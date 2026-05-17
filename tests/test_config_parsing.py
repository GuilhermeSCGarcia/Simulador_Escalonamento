import tempfile
import unittest

from CarregarConfig import CarregarConfig
from SimuladorConfig import SimuladorConfig


def _write_temp_config(text: str) -> str:
    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt")
    tmp.write(text)
    tmp.flush()
    tmp.close()
    return tmp.name


class TestConfigParsing(unittest.TestCase):
    def test_id_parses_t_prefix_and_leading_zeros(self):
        cfg_text = (
            "SRTF;1;1\n"
            "t007;FF6B6B;0;3;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)

        self.assertEqual(len(config.listaTarefasCarregadas), 1)
        self.assertEqual(config.listaTarefasCarregadas[0].id, 7)

    def test_id_parses_non_numeric_prefix(self):
        cfg_text = (
            "SRTF;1;1\n"
            "x-02;4ECDC4;0;3;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)

        self.assertEqual(len(config.listaTarefasCarregadas), 1)
        self.assertEqual(config.listaTarefasCarregadas[0].id, 2)

    def test_empty_fields_receive_defaults(self):
        cfg_text = (
            "SRTF;1;1\n"
            ";;;;;\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)

        self.assertEqual(len(config.listaTarefasCarregadas), 1)
        tarefa = config.listaTarefasCarregadas[0]

        self.assertEqual(tarefa.id, 0)
        self.assertEqual(tarefa.cor, "FF6B6B")
        self.assertEqual(tarefa.tempoDeIngresso, 0)
        self.assertEqual(tarefa.tempoTotal, 10)
        self.assertEqual(tarefa.tempoCorrido, 10)
        self.assertEqual(tarefa.prioridadeEstatica, 5)

    def test_invalid_id_raises_value_error(self):
        loader = CarregarConfig()
        with self.assertRaises(ValueError):
            loader.parsetarefaId("abc")

    def test_duplicate_ids_raise_value_error(self):
        cfg_text = (
            "SRTF;1;1\n"
            "1;FF6B6B;0;3;1;[]\n"
            "1;4ECDC4;0;3;1;[]\n"
        )
        path = _write_temp_config(cfg_text)

        with self.assertRaises(ValueError):
            SimuladorConfig(path)

    def test_empty_config_defaults(self):
        cfg_text = (
            ";;\n"
            "1;FF6B6B;0;3;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)

        self.assertEqual(config.algoritmoEscalomento, "STFR")
        self.assertEqual(config.quantum, 2)
        self.assertEqual(config.qtde_cpus, 2)


if __name__ == "__main__":
    unittest.main()
