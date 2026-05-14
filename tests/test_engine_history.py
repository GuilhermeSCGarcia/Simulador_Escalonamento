import random
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


def _find_task_anywhere(estado, task_id: int):
    for t in getattr(estado, "tarefas_futuras", []):
        if t.id == task_id:
            return t
    for t in getattr(estado, "fila_prontos", []):
        if t.id == task_id:
            return t
    for t in getattr(estado, "fila_suspensas", []):
        if t.id == task_id:
            return t
    for t in getattr(estado, "tarefas_finalizadas", []):
        if t.id == task_id:
            return t
    for cpu in getattr(estado, "cpus", []):
        if cpu.atualTarefa is not None and cpu.atualTarefa.id == task_id:
            return cpu.atualTarefa
    return None


def _task_ids_in_prontos(estado) -> set[int]:
    return {t.id for t in getattr(estado, "fila_prontos", [])}


def _task_ids_in_cpus(estado) -> set[int]:
    ids: set[int] = set()
    for cpu in getattr(estado, "cpus", []):
        if cpu.atualTarefa is not None:
            ids.add(cpu.atualTarefa.id)
    return ids


class TestEngineHistoricoSemantica(unittest.TestCase):
    def setUp(self):
        # Deixa desempates determinísticos
        random.seed(0)

    def _make_engine(self, quantum: int = 1, cpus: int = 1):
        # Formato esperado pelo parser:
        # linha 0: algoritmo;quantum;qtde_cpus
        # demais: id;cor;ingresso;tempoTotal;prioridade;listaEvento
        cfg_text = (
            f"SRTF;{quantum};{cpus}\n"
            "1;FF6B6B;0;3;1;[]\n"
            "2;4ECDC4;0;5;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)
        estado = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
        return SimuladorEngine(config, estado)

    def test_estado_inicial_nao_deve_vir_adiantado(self):
        engine = self._make_engine(quantum=2, cpus=1)

        self.assertEqual(engine.estado_atual.relogio_global, 0)
        self.assertEqual(len(engine.historico_estados), 1)
        self.assertEqual(engine.historico_estados[0].relogio_global, 0)

        t1 = _find_task_anywhere(engine.estado_atual, 1)
        t2 = _find_task_anywhere(engine.estado_atual, 2)
        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)

        # tempoCorrido deve iniciar igual ao tempoTotal (parser seta assim)
        self.assertEqual(t1.tempoCorrido, 3)
        self.assertEqual(t2.tempoCorrido, 5)

    def test_retroceder_deve_voltar_exatamente_um_tick(self):
        engine = self._make_engine(quantum=2, cpus=1)

        engine.avancar_tick()
        self.assertEqual(engine.estado_atual.relogio_global, 1)
        self.assertEqual(len(engine.historico_estados), 2)

        engine.retroceder_tick()

        # Esperado: voltar para t=0
        self.assertEqual(engine.estado_atual.relogio_global, 0)
        self.assertEqual(len(engine.historico_estados), 1)

    def test_avancar_apos_retroceder_deve_ser_deterministico(self):
        engine = self._make_engine(quantum=1, cpus=1)

        engine.avancar_tick()
        snap_tick_1 = engine.estado_atual.clonar_estado()

        engine.retroceder_tick()
        self.assertEqual(engine.estado_atual.relogio_global, 0)

        engine.avancar_tick()

        # Se o retrocesso restaurou corretamente, o tick 1 reexecutado deve bater
        self.assertEqual(engine.estado_atual.relogio_global, snap_tick_1.relogio_global)
        self.assertEqual(len(engine.estado_atual.cpus), len(snap_tick_1.cpus))

        cpu_now = engine.estado_atual.cpus[0]
        cpu_prev = snap_tick_1.cpus[0]
        self.assertEqual(cpu_now.quantumProprio, cpu_prev.quantumProprio)

        t1_now = _find_task_anywhere(engine.estado_atual, 1)
        t1_prev = _find_task_anywhere(snap_tick_1, 1)
        self.assertIsNotNone(t1_now)
        self.assertIsNotNone(t1_prev)
        self.assertEqual(t1_now.tempoCorrido, t1_prev.tempoCorrido)

    def test_quantum_cpu_deve_ser_restaurado_no_retrocesso(self):
        engine = self._make_engine(quantum=2, cpus=1)

        # Avança 1 tick para alterar quantumProprio
        engine.avancar_tick()
        self.assertGreaterEqual(engine.estado_atual.cpus[0].quantumProprio, 0)

        engine.retroceder_tick()

        # Esperado: snapshot inicial tem quantumProprio=0
        self.assertEqual(engine.estado_atual.cpus[0].quantumProprio, 0)

    def test_ingresso_no_tick_deve_aparecer_no_estado_do_mesmo_tick(self):
        # Reproduz o sintoma do Gantt: marcador aparece em `tempoDeIngresso`,
        # mas o estado do simulador só reflete a chegada um tick depois.
        cfg_text = (
            "SRTF;1;1\n"
            "1;FF6B6B;0;3;1;[]\n"
            "2;4ECDC4;1;5;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)
        estado = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
        engine = SimuladorEngine(config, estado)

        def esta_em_cpu(estado_atual, task_id: int) -> bool:
            return any(
                cpu.atualTarefa is not None and cpu.atualTarefa.id == task_id
                for cpu in estado_atual.cpus
            )

        def esta_em_prontos(estado_atual, task_id: int) -> bool:
            return any(t.id == task_id for t in estado_atual.fila_prontos)

        def esta_em_futuras(estado_atual, task_id: int) -> bool:
            return any(t.id == task_id for t in estado_atual.tarefas_futuras)

        # t=0: tarefa 1 já ingressou; tarefa 2 ainda é futura
        self.assertTrue(esta_em_prontos(engine.estado_atual, 1) or esta_em_cpu(engine.estado_atual, 1))
        self.assertTrue(esta_em_futuras(engine.estado_atual, 2))
        self.assertFalse(esta_em_prontos(engine.estado_atual, 2) or esta_em_cpu(engine.estado_atual, 2))

        engine.avancar_tick()
        self.assertEqual(engine.estado_atual.relogio_global, 1)

        # Esperado: ao chegar em t=1, a tarefa 2 já deve ter ingressado (saiu de futuras)
        self.assertFalse(esta_em_futuras(engine.estado_atual, 2))
        self.assertTrue(esta_em_prontos(engine.estado_atual, 2) or esta_em_cpu(engine.estado_atual, 2))

    def test_cpu_livre_nao_pode_deixar_tarefa_em_prontos(self):
        # Cenário: 2 CPUs, uma tarefa chega em t=6.
        # Esperado: no estado do tick 6, ela já deve estar em alguma CPU (não parada em prontos).
        cfg_text = (
            "SRTF;10;2\n"
            "1;FF6B6B;0;20;1;[]\n"
            "4;F7B801;6;3;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)
        estado = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
        engine = SimuladorEngine(config, estado)

        # Avança até chegar no tick 6
        for _ in range(6):
            engine.avancar_tick()

        self.assertEqual(engine.estado_atual.relogio_global, 6)

        cpu_ids = _task_ids_in_cpus(engine.estado_atual)
        prontos_ids = _task_ids_in_prontos(engine.estado_atual)

        self.assertIn(4, cpu_ids)
        self.assertNotIn(4, prontos_ids)

    def test_tarefa_nao_pode_estar_em_cpu_e_em_prontos_ao_mesmo_tempo(self):
        # Regressão: o escalonamento não pode duplicar a mesma tarefa em CPU e fila_prontos.
        engine = self._make_engine(quantum=10, cpus=2)

        # No estado inicial já deve haver escalonamento coerente.
        intersec = _task_ids_in_cpus(engine.estado_atual) & _task_ids_in_prontos(engine.estado_atual)
        self.assertEqual(intersec, set())

        engine.avancar_tick()
        intersec2 = _task_ids_in_cpus(engine.estado_atual) & _task_ids_in_prontos(engine.estado_atual)
        self.assertEqual(intersec2, set())

    def test_nenhuma_tarefa_deve_sumir_do_estado(self):
        # Regressão direta do bug: tarefa escolhida era removida de prontos
        # e não atribuída a nenhuma CPU, ficando 'perdida'.
        cfg = SimuladorConfig('config.txt')
        estado = SimuladorEstado(cfg.listaCPU, cfg.listaTarefasCarregadas, cfg.quantum)
        engine = SimuladorEngine(cfg, estado)

        all_ids = {t.id for t in cfg.listaTarefasCarregadas}

        def present_ids(st):
            ids = set(t.id for t in st.fila_prontos)
            ids |= set(t.id for t in st.tarefas_futuras)
            ids |= set(t.id for t in st.tarefas_finalizadas)
            ids |= set(t.id for t in getattr(st, 'fila_suspensas', []))
            ids |= {cpu.atualTarefa.id for cpu in st.cpus if cpu.atualTarefa is not None}
            return ids

        for _ in range(15):
            missing = all_ids - present_ids(engine.estado_atual)
            self.assertEqual(missing, set())
            if engine.estado_atual.simulacao_finalizada():
                break
            engine.avancar_tick()


if __name__ == "__main__":
    unittest.main()
