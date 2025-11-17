import pandas as pd
import os
from glob import glob

def batch_convert_xlsx_to_csv(input_folder: str, output_folder: str):
    os.makedirs(output_folder, exist_ok=True)
    files = glob(os.path.join(input_folder, "*.xlsx"))
    
    for f in files:
        try:
            df = pd.read_excel(f)
            filename = os.path.basename(f).replace(".xlsx", ".csv")
            out_path = os.path.join(output_folder, filename)
            df.to_csv(out_path, index=False)
            print(f"已转换: {f} -> {out_path}")
            print("批量转换完成")
        except Exception as e:
            print(f"转换失败 {f}: {e}")

if __name__ == "__main__":
    input_folder = "/home/phl/PHL/Car-T/datasetcart/processed"
    output_folder = "/home/phl/PHL/Car-T/data_processing/output/dataset_csv"
    batch_convert_xlsx_to_csv(input_folder, output_folder)