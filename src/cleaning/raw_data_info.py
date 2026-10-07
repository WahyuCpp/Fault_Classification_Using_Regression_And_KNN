import pandas as pd
import io
import numpy as np

# Baca file CSV ke DataFrame
df_kotor = pd.read_csv('data/raw/E002r.csv')

# Tampilkan informasi dasar tentang DataFrame
print("Informasi DataFrame:")
df_kotor.info()

# Tampilkan beberapa baris pertama
print("\nBeberapa baris pertama dari DataFrame:")
print(df_kotor.head())

# Pemeriksaan Data Kotor
# 1. Periksa nilai yang hilang (Missing Values)
print("Jumlah nilai yang hilang per kolom:")
print(df_kotor.isnull().sum())

# 2. Periksa data duplikat
print("\nJumlah data duplikat:")
print(df_kotor.duplicated().sum())

# 3. Statistik Deskriptif untuk kolom numerik
print("\nStatistik deskriptif untuk kolom numerik:")
print(df_kotor.describe())

# 4. Statistik Deskriptif untuk kolom kategorikal (object)
print("\nStatistik deskriptif untuk kolom kategorikal:")
print(df_kotor.describe(include=['object']))

# 5. Distribusi nilai unik pada kolom kategorikal (opsional, jika ingin melihat lebih detail)
print("\nDistribusi nilai unik pada kolom 'X':")
print(df_kotor['x'].value_counts())
print("\nDistribusi nilai unik pada kolom 'Y':")
print(df_kotor['y'].value_counts())
print("\nDistribusi nilai unik pada kolom 'Z':")
print(df_kotor['z'].value_counts())