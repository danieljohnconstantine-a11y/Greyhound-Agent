import pandas as pd
from src.trainer_parser import parse_trainer_blocks




def test_trainer_extraction_basic():
sample = """
1. 22313 Life's A Journey 2d 31.0kg 1 Trainer: Robin Harnas
City: Adelaide State: SA Win Rate: 18%
Owner: ACME Syndicate Sire: Fast Rocket Dam: Blue Lily Color: Black
"""
df = parse_trainer_blocks(sample, trainer_cache={"Robin Harnas": {"TrainerWinRate": 0.18, "TrainerCity": "Adelaide", "TrainerState": "SA"}})
assert not df.empty
r = df.iloc[0]
assert r["Trainer"] == "Robin Harnas"
assert abs(r["TrainerWinRate"] - 0.18) < 1e-6
assert r["TrainerCity"] == "Adelaide"
assert r["TrainerState"] == "SA"
assert r["Owner"] == "ACME Syndicate"
assert r["Sire"] == "Fast Rocket"
assert r["Dam"] == "Blue Lily"
assert r["Color"] == "Black"
