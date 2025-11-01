import os
import pandas as pd
from src.box_bias_calculator import load_box_bias_lookup




def test_box_bias_lookup(tmp_path):
arch = tmp_path / "archived"
arch.mkdir(parents=True, exist_ok=True)


# minimal historical CSV
df = pd.DataFrame({
"Track": ["Angle Park", "Angle Park", "Angle Park"],
"Box": [1, 1, 8],
"RaceComment": ["1st strong finish", "3rd fair", "1st led all the way"],
})
f = arch / "hist.csv"
df.to_csv(f, index=False)


lookup = load_box_bias_lookup(str(arch))
assert "ANGLE PARK" in lookup
assert 1 in lookup["ANGLE PARK"]
assert 8 in lookup["ANGLE PARK"]
