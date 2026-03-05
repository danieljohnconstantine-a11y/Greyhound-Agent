import pandas as pd
import os

def export_to_excel(dogs, output_path):
    # Flatten list fields
    for dog in dogs:
        dog["recent_positions"] = ", ".join(map(str, dog.get("recent_positions", [])))
        dog["form_trend"] = str(dog.get("form_trend", ""))
        dog["has_win"] = int(dog.get("has_win", 0))
        dog["has_place"] = int(dog.get("has_place", 0))

    # Define strict column order
    columns = [
        "Track", "RaceNumber", "RaceDate", "RaceTime", "Distance",
        "Box", "DogsName", "form_code", "age_sex", "weight", "trainer",
        "wins", "places", "starts", "PrizeMoney", "KmH", "experience_level",
        "FinalScore", "Bet", "strike_rate", "win_percentage", "place_percentage",
        "consistency_rate", "consistent_places", "has_dnf", "has_win", "has_place",
        "recent_races", "recent_positions", "avg_recent_position",
        "best_recent_position", "worst_recent_position", "form_trend",
        "source_file", "Date"
    ]

    # Audit: log unexpected keys not in the expected column list
    all_keys = {k for dog in dogs for k in dog}
    extra_keys = all_keys - set(columns)
    if extra_keys:
        print(f"WARNING: Unexpected keys found across dogs: {extra_keys}")

    # Build DataFrame and reindex to the required column order.
    # fill_value=None matches the original behaviour (missing columns become None,
    # not NaN, so downstream code that checks `is None` continues to work).
    df = pd.DataFrame(dogs).reindex(columns=columns, fill_value=None)

    filename = f"greyhound_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(output_path, filename)
    df.to_excel(filepath, index=False)
    print(f"EXCEL SAVED: {filepath}")
