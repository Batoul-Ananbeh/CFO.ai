from pathlib import Path

from src.engines.financial_engine import FinancialEngine


BASE_DIR = Path(__file__).resolve().parents[1]
DATASET = BASE_DIR / "Data" / "online_retail_II.csv"


def test_load_dataset():
    engine = FinancialEngine(DATASET)

    df = engine.load()

    assert df is not None
    assert len(df) > 0


def test_clean_dataset():
    engine = FinancialEngine(DATASET)

    engine.load()
    df = engine.clean()

    assert "Revenue" in df.columns
    assert len(df) > 0