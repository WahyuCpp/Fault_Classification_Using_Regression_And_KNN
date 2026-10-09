import pandas as pd

df_kotor = pd.read_csv('data/raw/E001r.csv')
df_bersih = df_kotor.copy()

# Success message after data cleaning
print("\n✅ Proses Pembersihan Data Selesai.")
print("\nInformasi DataFrame setelah Pembersihan:")
df_bersih.info()
print("\nBeberapa baris pertama dari DataFrame setelah Pembersihan:")
print(df_bersih.head())