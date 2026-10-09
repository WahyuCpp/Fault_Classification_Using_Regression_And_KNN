# File to run the entire cleaning data pipeline

import pandas as pd

from missing_values import handle_missing_values
from duplicates_remover import remove_duplicates
# from .categorical_uniforming import uniform_categories
from outlier import remove_outliers

input_file = 'data/raw/E002r.csv'
output_file = 'data/clean/E002_cleaned.csv'

def clean_data(input_file, output_file):
    # Load CSV 
    df = pd.read_csv(input_file)

    # Pass the same DataFrame through each cleaning stage
    df = handle_missing_values(df)
    df = remove_duplicates(df)
    # df = uniform_categories(df)
    df = remove_outliers(df)

    # Save .csv once
    df.to_csv(output_file, index=False)

    return df

clean_data(input_file, output_file)