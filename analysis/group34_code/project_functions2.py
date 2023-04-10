import pandas as pd
import numpy as np


def load_and_process(url_or_path_to_csv_file):

    df_ank = (
        pd.read_csv(url_or_path_to_csv_file)
        .dropna()
        .loc[lambda x: x["Asteroid Magnitude"].between(22.5,27.5)]
        .reset_index(drop=True)
    )
    return df_ank
