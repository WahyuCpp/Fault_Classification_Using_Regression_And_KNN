import pandas as pd

# Membuat salinan DataFrame untuk operasi pembersihan
df_kotor = pd.read_csv('data/raw/E001r.csv')
df_bersih = df_kotor.copy()

# 1. Penanganan Nilai yang Hilang (Missing Values)
# Mengisi nilai yang hilang pada kolom numerik ('Lama_Kerja', 'Gaji') dengan median
df_bersih['x'] = df_bersih['x'].fillna(df_bersih['x'].median())
df_bersih['y'] = df_bersih['y'].fillna(df_bersih['y'].median())
df_bersih['z'] = df_bersih['z'].fillna(df_bersih['z'].median())

# Mengisi nilai yang hilang pada kolom kategorikal ('Kota') dengan modus (nilai yang paling sering muncul)
# df_bersih['Kota'] = df_bersih['Kota'].fillna(df_bersih['Kota'].mode()[0])

print("✅ Penanganan nilai yang hilang selesai.")
print("Jumlah nilai yang hilang setelah diisi:")
print(df_bersih.isnull().sum())