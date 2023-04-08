import pandas as pd
import re
import numpy as np


def load_and_process(neo_url, orbits_url):
    asteroids = (pd.merge((
        pd.read_csv(orbits_url)
        .dropna()
        .replace("\xa0", " ", regex=True)
        .reset_index(drop=True)
        .assign(**{"Object Name": lambda x: x["Object Name"].str.strip()})
        .assign(**{"Object Name": lambda x: x["Object Name"]
                .apply(lambda y: re.sub(r'.*\((.*)\)', r"\1", y))})
    ), (
        pd.read_csv(neo_url)
        .dropna()
        .replace("\xa0", " ", regex=True)
        .reset_index(drop=True)
        .assign(**{"Object Name": lambda x: x["Object"].str.strip()})
        .assign(**{"Object Name": lambda x: x["Object Name"]
                .apply(lambda y: re.sub(r'.*\((.*)\)', r"\1", y))})
        .drop(columns=["Object"])
    ), on="Object Name", how="right")
                 .dropna(subset=["Object Classification"])
                 .drop_duplicates(subset=["Object Name"])
                 .reset_index(drop=True)
                 .assign(**{"PHA": lambda x: x["Object Classification"].str.contains("Hazard")})
    )
    # try doing this in a pandas chain
    for index, value in enumerate(asteroids["Diameter"]):
        if re.search(r"m.*km", value):
            value = value.split("-")
            max_value = float(value[1].replace(r" +", "").replace("km", "").replace("m", "")) / 1000
        elif "km" in value:
            if "±" in value:
                value = value.split("±")
                max_value = float(value[0]) + float(value[1].replace("km", ""))
            else:
                max_value = float(value.split(" ")[0])
        elif "m" in value:
            value = value.split("-")
            max_value = float(value[1].replace(r" +", "").replace("m", "")) / 1000
        else:
            try:
                max_value = float(value)
            except ValueError:
                max_value = np.nan
        asteroids.at[index, "Diameter"] = max_value

    # drop all asteroids with no diameter or diameter of less than 0.1
    asteroids = asteroids[asteroids["Diameter"] >= 0.1]
    asteroids = asteroids.dropna(subset=["Diameter"])
    # only keep PHAs
    asteroids = asteroids[asteroids["PHA"] == True]
    return asteroids

