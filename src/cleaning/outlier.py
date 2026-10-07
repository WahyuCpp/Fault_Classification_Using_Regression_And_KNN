# Remove outliers from the DataFrame based on specified thresholds for each axis (x, y, z) and optionally for salary (Gaji).

import pandas as pd

# Membuat salinan DataFrame untuk operasi pembersihan
# df_kotor = pd.read_csv('data/raw/E001r.csv')
# df = df_kotor.copy()

def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df=df.copy()
    # Outlier pada sumbu-x
    median_x = df['x'].median()
    df['x'] = df['x'].apply(lambda x: median_x if x < -0.2 or x > 0.2 else x)

    # Outlier pada sumbu-y
    median_y = df['y'].median()
    df['y'] = df['y'].apply(lambda x: median_y if x < -0.2 or x > 0.2 else x)

    # Outlier pada sumbu-z
    median_z = df['z'].median()
    df['z'] = df['z'].apply(lambda x: median_z if x < -9 or x> 11 else x)

    # Outlier pada Gaji: Menggunakan metode IQR atau Z-score, atau secara sederhana mengganti nilai yang sangat ekstrim
    # Kita akan menggunakan metode sederhana dengan mengganti nilai yang sangat besar atau sangat kecil dengan median gaji S1/Sarjana
    # median_gaji_s1 = df[df['Pendidikan'].isin(['S1', 'Sarjana', 'Bachelor'])]['Gaji'].median()
    # Anggap gaji di bawah 3jt atau di atas 200jt sebagai outlier ekstrim
    # df['Gaji'] = df['Gaji'].apply(lambda x: median_gaji_s1 if x < 3000000 or x > 200000000 else x)

    print("\n✅ Penanganan outlier pada sumbu-x, sumbu-y, dan sumbu-z selesai.")
    print("Statistik deskriptif sumbu-x setelah penanganan outlier:")
    print(df['x'].describe())
    print("\nStatistik deskriptif sumbu-y setelah penanganan outlier:")
    print(df['y'].describe())
    print("\nStatistik deskriptif sumbu-z setelah penanganan outlier:")
    print(df['z'].describe())

    return df