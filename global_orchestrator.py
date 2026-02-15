from __future__ import annotations
from queue import Queue, Empty
from typing import Dict, Any, List
import threading
import time
import logging

from universal_core.core import UniversalCognitiveCore
from universal_core.config import CoreConfig
from .stock_agent import StockAgent, StockDataSource

logger = logging.getLogger("StockOrchestrator")

class GlobalStockOrchestrator:
    def __init__(self, symbols: List[str]):
        self.queue: Queue[Dict[str, Any]] = Queue(maxsize=10000)
        self.core = UniversalCognitiveCore("global_stock_mind", CoreConfig())
        self.symbols = symbols
        self.agents: List[StockAgent] = []
        self._stop_flag = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._worker_loop, daemon=True
        )

    def _send_observation(self, obs: Dict[str, Any]) -> None:
        try:
            self.queue.put(obs, timeout=1.0)
        except Exception:
            logger.warning("Dropping observation due to full queue")

    def _worker_loop(self) -> None:
        logger.info("Global worker loop started")
        while not self._stop_flag.is_set():
            try:
                obs = self.queue.get(timeout=1.0)
            except Empty:
                continue
            try:
                symbol = obs.get("symbol", "UNKNOWN")
                domain = f"stock:{symbol}"
                result = self.core.ingest(obs, domain=domain)
                logger.debug(
                    "Ingested for %s: concept=%s rules=%d",
                    symbol,
                    result.get("concept_id"),
                    result.get("new_rules"),
                )
            except Exception:
                logger.exception("Error ingesting observation")
        logger.info("Global worker loop stopped")

    def start(self) -> None:
        data_source = StockDataSource()
        for sym in self.symbols:
            agent = StockAgent(
                symbol=sym,
                data_source=data_source,
                send_observation=self._send_observation,
                interval_seconds=1.0,
            )
            self.agents.append(agent)
            agent.start()
        self._worker_thread.start()
        logger.info("GlobalStockOrchestrator started with %d agents", len(self.agents))

    def stop(self) -> None:
        self._stop_flag.set()
        for agent in self.agents:
            agent.stop()
        for agent in self.agents:
            agent.join(timeout=2.0)
        self._worker_thread.join(timeout=2.0)
        logger.info("GlobalStockOrchestrator stopped")

    def get_metrics(self) -> Dict[str, Any]:
        return self.core.metrics.to_dict()

    def get_concepts_snapshot(self) -> Dict[str, Any]:
        return {cid: c.to_dict() for cid, c in self.core.concepts.items()}