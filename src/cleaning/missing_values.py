import pandas as pd

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    # Membuat salinan DataFrame untuk operasi pembersihan
    # df_kotor = pd.read_csv('data/raw/E001r.csv')
    df = df.copy()

    # Penanganan Nilai yang Hilang (Missing Values)
    # Mengisi nilai yang hilang pada kolom numerik ('Lama_Kerja', 'Gaji') dengan median
    df['x'] = df['x'].fillna(df['x'].median())
    df['y'] = df['y'].fillna(df['y'].median())
    df['z'] = df['z'].fillna(df['z'].median())

    # Mengisi nilai yang hilang pada kolom kategorikal ('Kota') dengan modus (nilai yang paling sering muncul)
    # df['Kota'] = df['Kota'].fillna(df['Kota'].mode()[0])

    print("✅ Penanganan nilai yang hilang selesai.")
    print("Jumlah nilai yang hilang setelah diisi:")
    print(df.isnull().sum())

    return df