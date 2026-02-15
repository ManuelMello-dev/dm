from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Any
import threading
import time
import random
import logging

logger = logging.getLogger("StockAgent")

@dataclass
class StockTick:
    symbol: str
    price: float
    volume: float
    timestamp: float


class StockDataSource:
    """Replace this with real market data (WebSocket, REST, etc.)."""

    def get_latest_tick(self, symbol: str) -> StockTick:
        now = datetime.now(timezone.utc).timestamp()
        price = 100 + random.uniform(-1, 1)
        volume = random.uniform(1000, 10000)
        return StockTick(symbol=symbol, price=price, volume=volume, timestamp=now)


class StockAgent(threading.Thread):
    def __init__(
        self,
        symbol: str,
        data_source: StockDataSource,
        send_observation: Callable[[Dict[str, Any]], None],
        interval_seconds: float = 1.0,
    ):
        super().__init__(daemon=True)
        self.symbol = symbol
        self.data_source = data_source
        self.send_observation = send_observation
        self.interval_seconds = interval_seconds
        self._stop_flag = threading.Event()

    def stop(self) -> None:
        self._stop_flag.set()

    def run(self) -> None:
        logger.info("StockAgent for %s started", self.symbol)
        while not self._stop_flag.is_set():
            try:
                tick = self.data_source.get_latest_tick(self.symbol)
                obs = {
                    "symbol": tick.symbol,
                    "timestamp": tick.timestamp,
                    "price": tick.price,
                    "volume": tick.volume,
                }
                self.send_observation(obs)
            except Exception:
                logger.exception("Error in StockAgent for %s", self.symbol)
            time.sleep(self.interval_seconds)
        logger.info("StockAgent for %s stopped", self.symbol)