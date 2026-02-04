import os
import glob
import pandas as pd # type: ignore

def load_data(folder_path: str) -> pd.DataFrame:
    """
    Reads all CSVs in the folder, adds 'location' column from file name,
    cleans common issues, and returns a combined DataFrame.
    """
    files = glob.glob(os.path.join(folder_path, "*.csv"))
    frames = []
    for fp in files:
        city = os.path.splitext(os.path.basename(fp))[0]
        temp = pd.read_csv(fp)
        temp["location"] = city.capitalize()
        if "Unnamed: 0" in temp.columns:
            temp = temp.drop(columns=["Unnamed: 0"])
        frames.append(temp)

    df = pd.concat(frames, ignore_index=True)

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Convert numeric-like columns
    if "company_rating" in df.columns:
        df["company_rating"] = (
            df["company_rating"].astype(str).str.extract(r"(\d+(\.\d+)?)")[0].astype(float)
        )
    if "years_old" in df.columns:
        df["years_old"] = pd.to_numeric(df["years_old"], errors="coerce")
    if "size" in df.columns:
        df["size"] = pd.to_numeric(df["size"], errors="coerce")

    return df
