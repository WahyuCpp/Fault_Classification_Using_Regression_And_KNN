#File to remove duplicates from raw DataFrame

import pandas as pd

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    # Membuat salinan DataFrame untuk operasi pembersihan
    df = df.copy()

    df = df.drop_duplicates()

    print(f"\n✅ Penanganan duplikat selesai. Jumlah baris setelah menghapus duplikat: {len(df)}")

    print("\n✅ Proses Pembersihan Data Selesai.")
    print("\nInformasi DataFrame setelah Pembersihan:")
    df.info()
    print("\nBeberapa baris pertama dari DataFrame setelah Pembersihan:")
    print(df.head())

    return df