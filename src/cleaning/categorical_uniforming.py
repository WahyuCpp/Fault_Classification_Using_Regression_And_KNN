# Membuat salinan DataFrame untuk operasi pembersihan
# Penyeragaman kategorikal

# df_kotor = pd.read_csv('data/test_Data.csv')
# df_bersih = df_kotor.copy()

# 3. Penyeragaman Nilai Kategorikal
# Menyatukan kategori pendidikan yang serupa: 'Sarjana', 'Bachelor', 'S1' menjadi 'S1'
df_bersih['Pendidikan'] = df_bersih['Pendidikan'].replace(['Sarjana', 'Bachelor'], 'S1')

print("\n✅ Penyeragaman nilai pada kolom Pendidikan selesai.")
print("Distribusi nilai unik pada kolom 'Pendidikan' setelah penyeragaman:")
print(df_bersih['Pendidikan'].value_counts())

# 4. Menghapus Duplikat
# Berdasarkan eksplorasi data awal, tidak ada duplikat, tetapi kode ini tetap disiapkan
df_bersih = df_bersih.drop_duplicates()

print(f"\n✅ Penanganan duplikat selesai. Jumlah baris setelah menghapus duplikat: {len(df_bersih)}")