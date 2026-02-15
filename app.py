# app.py
from logging_config import setup_logging
from global_orchestrator import GlobalStockOrchestrator
import time

logger = setup_logging("StockApp")

def main():
    symbols = ["AAPL", "TSLA", "MSFT", "NVDA"]
    orchestrator = GlobalStockOrchestrator(symbols)
    orchestrator.start()
    try:
        while True:
            time.sleep(10)
            logger.info("Metrics: %s", orchestrator.get_metrics())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        orchestrator.stop()

if __name__ == "__main__":
    main()
