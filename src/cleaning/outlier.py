import pandas as pd

# Membuat salinan DataFrame untuk operasi pembersihan
df_kotor = pd.read_csv('data/raw/E001r.csv')
df_bersih = df_kotor.copy()

# 2. Penanganan Outlier
# Outlier pada sumbu-x
median_x = df_bersih['x'].median()
df_bersih['x'] = df_bersih['x'].apply(lambda x: median_x if x > 15 else x)

# Outlier pada sumbu-y
median_y = df_bersih['y'].median()
df_bersih['y'] = df_bersih['y'].apply(lambda x: median_y if x > 15 else x)

# Outlier pada sumbu-z
median_z = df_bersih['z'].median()
df_bersih['z'] = df_bersih['z'].apply(lambda x: median_z if x > 15 else x)

# Outlier pada Gaji: Menggunakan metode IQR atau Z-score, atau secara sederhana mengganti nilai yang sangat ekstrim
# Kita akan menggunakan metode sederhana dengan mengganti nilai yang sangat besar atau sangat kecil dengan median gaji S1/Sarjana
# median_gaji_s1 = df_bersih[df_bersih['Pendidikan'].isin(['S1', 'Sarjana', 'Bachelor'])]['Gaji'].median()
# Anggap gaji di bawah 3jt atau di atas 200jt sebagai outlier ekstrim
# df_bersih['Gaji'] = df_bersih['Gaji'].apply(lambda x: median_gaji_s1 if x < 3000000 or x > 200000000 else x)

print("\n✅ Penanganan outlier pada sumbu-x, sumbu-y, dan sumbu-z selesai.")
print("Statistik deskriptif sumbu-x setelah penanganan outlier:")
print(df_bersih['x'].describe())
print("\nStatistik deskriptif sumbu-y setelah penanganan outlier:")
print(df_bersih['y'].describe())
print("\nStatistik deskriptif sumbu-z setelah penanganan outlier:")
print(df_bersih['z'].describe())