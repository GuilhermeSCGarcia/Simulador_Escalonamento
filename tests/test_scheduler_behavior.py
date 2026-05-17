import random
import tempfile
import unittest

from Escalonadores import EscalonadorPRIOP, EscalonadorSRTF
from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from SimuladorEngine import SimuladorEngine
from TCB import TCB


def _write_temp_config(text: str) -> str:
    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt")
    tmp.write(text)
    tmp.flush()
    tmp.close()
    return tmp.name


def _make_engine(cfg_text: str) -> SimuladorEngine:
    path = _write_temp_config(cfg_text)
    config = SimuladorConfig(path)
    estado = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
    return SimuladorEngine(config, estado)


def _task_ids_in_cpus(estado) -> set[int]:
    ids: set[int] = set()
    for cpu in getattr(estado, "cpus", []):
        if cpu.atualTarefa is not None:
            ids.add(cpu.atualTarefa.id)
    return ids


class TestSchedulerBehavior(unittest.TestCase):
    def setUp(self):
        random.seed(0)

    def test_srtf_one_cpu_picks_shortest(self):
        cfg_text = (
            "SRTF;1;1\n"
            "1;FF6B6B;0;9;1;[]\n"
            "2;4ECDC4;0;2;1;[]\n"
            "3;45B7D1;0;4;1;[]\n"
        )
        engine = _make_engine(cfg_text)
        cpu_ids = _task_ids_in_cpus(engine.estado_atual)

        self.assertEqual(cpu_ids, {2})

    def test_srtf_two_cpus_pick_two_shortest(self):
        cfg_text = (
            "SRTF;1;2\n"
            "1;FF6B6B;0;8;1;[]\n"
            "2;4ECDC4;0;3;1;[]\n"
            "3;45B7D1;0;5;1;[]\n"
        )
        engine = _make_engine(cfg_text)
        cpu_ids = _task_ids_in_cpus(engine.estado_atual)

        self.assertEqual(cpu_ids, {2, 3})

    def test_priop_two_cpus_pick_highest_priorities(self):
        cfg_text = (
            "PRIOP;1;2\n"
            "1;FF6B6B;0;5;1;[]\n"
            "2;4ECDC4;0;5;5;[]\n"
            "3;45B7D1;0;5;3;[]\n"
        )
        engine = _make_engine(cfg_text)
        cpu_ids = _task_ids_in_cpus(engine.estado_atual)

        self.assertEqual(cpu_ids, {2, 3})

    def test_priop_three_cpus_pick_top_three_priorities(self):
        cfg_text = (
            "PRIOP;1;3\n"
            "1;FF6B6B;0;5;1;[]\n"
            "2;4ECDC4;0;5;2;[]\n"
            "3;45B7D1;0;5;10;[]\n"
            "4;F7B801;0;5;7;[]\n"
            "5;A29BFE;0;5;4;[]\n"
        )
        engine = _make_engine(cfg_text)
        cpu_ids = _task_ids_in_cpus(engine.estado_atual)

        self.assertEqual(cpu_ids, {3, 4, 5})

    def test_srtf_tiebreak_prefers_running_task(self):
        escalonador = EscalonadorSRTF()
        t1 = TCB(tempoDeIngresso=0, tempoTotal=5, tempoCorrido=3, prioridadeEstatica=1, id=1)
        t2 = TCB(tempoDeIngresso=0, tempoTotal=5, tempoCorrido=3, prioridadeEstatica=1, id=2)
        t2.estavaRodando = True

        chosen = escalonador.ordenar_candidatos([t1, t2])
        self.assertEqual(chosen.id, 2)

    def test_srtf_tiebreak_prefers_earlier_ingresso(self):
        escalonador = EscalonadorSRTF()
        t1 = TCB(tempoDeIngresso=1, tempoTotal=5, tempoCorrido=3, prioridadeEstatica=1, id=1)
        t2 = TCB(tempoDeIngresso=0, tempoTotal=5, tempoCorrido=3, prioridadeEstatica=1, id=2)

        chosen = escalonador.ordenar_candidatos([t1, t2])
        self.assertEqual(chosen.id, 2)

    def test_priop_tiebreak_prefers_running_task(self):
        escalonador = EscalonadorPRIOP()
        t1 = TCB(tempoDeIngresso=0, tempoTotal=5, tempoCorrido=5, prioridadeEstatica=3, id=1)
        t2 = TCB(tempoDeIngresso=0, tempoTotal=5, tempoCorrido=5, prioridadeEstatica=3, id=2)
        t1.estavaRodando = True

        chosen = escalonador.ordenar_candidatos([t1, t2])
        self.assertEqual(chosen.id, 1)

    def test_priop_tiebreak_prefers_earlier_ingresso(self):
        escalonador = EscalonadorPRIOP()
        t1 = TCB(tempoDeIngresso=2, tempoTotal=5, tempoCorrido=5, prioridadeEstatica=3, id=1)
        t2 = TCB(tempoDeIngresso=1, tempoTotal=5, tempoCorrido=5, prioridadeEstatica=3, id=2)

        chosen = escalonador.ordenar_candidatos([t1, t2])
        self.assertEqual(chosen.id, 2)


if __name__ == "__main__":
    unittest.main()
