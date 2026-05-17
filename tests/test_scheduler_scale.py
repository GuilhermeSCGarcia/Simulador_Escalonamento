import tempfile
import unittest

from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from SimuladorEngine import SimuladorEngine


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


class TestSchedulerScale(unittest.TestCase):
    def test_large_cpus_and_tasks_cpu_time_matches_work(self):
        cpus = 30
        tasks = 50
        quantum = 3

        durations = [(i % 5) + 1 for i in range(tasks)]
        total_work = sum(durations)

        lines = [f"SRTF;{quantum};{cpus}"]
        for i, dur in enumerate(durations, start=1):
            lines.append(f"{i};FF6B6B;0;{dur};1;[]")
        cfg_text = "\n".join(lines) + "\n"

        engine = _make_engine(cfg_text)
        engine.executar_tudo()

        self.assertGreater(engine.estado_atual.relogio_global, 0)
        self.assertEqual(engine.estado_atual.relogio_global, len(engine.historico_estados) - 1)
        self.assertEqual(engine.estado_atual.relogio_de_processo, engine.estado_atual.relogio_global)

        total_cpu_time = sum(cpu.tempoAtivo for cpu in engine.estado_atual.cpus)
        self.assertEqual(total_cpu_time, total_work)
        self.assertLessEqual(engine.estado_atual.relogio_global, total_work)


if __name__ == "__main__":
    unittest.main()
