from src.trainer_parser import parse_trainer
import pandas as pd

def test_trainer_extraction():
    sample_text = "Trainer: John Smith City: Brisbane State: QLD Win Rate: 18%"
    df = parse_trainer(sample_text)
    assert "TrainerWinRate" in df.columns
    assert df.loc[0, "Trainer"] == "John Smith"
    assert abs(df.loc[0, "TrainerWinRate"] - 0.18) < 0.001
