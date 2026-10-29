"""Generates benchmark demo datasets conforming to the project specification."""
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from config.main_config import CLEANED_DATA_DIR, BASE_DIR
from config.signal_processing_config import BEARING_CONFIG, ELECTRICAL_CONFIG

def generate_datasets():
    """Populate data/cleaned_data with sample datasets for all 6 fault classes."""
    CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = BASE_DIR / "data" / "raw"

    fs = 1500.0  # 1500 Hz
    duration = 5.0  # seconds
    n_samples = int(fs * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    rpm = 1450.0
    fr = rpm / 60.0  # 24.167 Hz shaft rotational frequency

    # Theoretical bearing frequencies
    Nb = BEARING_CONFIG["number_of_rolling_elements"]
    Bd = BEARING_CONFIG["ball_diameter"]
    Pd = BEARING_CONFIG["pitch_diameter"]
    theta = np.deg2rad(BEARING_CONFIG["contact_angle_deg"])

    bpfo = (Nb / 2.0) * fr * (1.0 - (Bd / Pd) * np.cos(theta))  # ~86.5 Hz
    bpfi = (Nb / 2.0) * fr * (1.0 + (Bd / Pd) * np.cos(theta))  # ~131.0 Hz
    bsf = (Pd / (2.0 * Bd)) * fr * (1.0 - ((Bd / Pd) * np.cos(theta))**2)  # ~56.8 Hz
    ftf = (fr / 2.0) * (1.0 - (Bd / Pd) * np.cos(theta))  # ~9.6 Hz

    base_time = datetime(2026, 7, 12, 13, 15, 0)
    timestamps = [
        (base_time + timedelta(seconds=float(ti))).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        for ti in t
    ]

    # 1. Healthy dataset
    # Has low baseline 1x and noise
    e002_path = raw_dir / "E002r.csv"
    healthy_dir = CLEANED_DATA_DIR / "healthy"
    healthy_dir.mkdir(parents=True, exist_ok=True)

    if e002_path.exists():
        raw_healthy = pd.read_csv(e002_path)
        # Split into healthy_01 and healthy_02
        half = len(raw_healthy) // 2
        df_h1 = raw_healthy.iloc[:half].copy()
        df_h2 = raw_healthy.iloc[half:half + half].copy()
        for df, name in [(df_h1, "healthy_01.csv"), (df_h2, "healthy_02.csv")]:
            if "time" in df.columns and "timestamp" not in df.columns:
                df["timestamp"] = [
                    (base_time + timedelta(seconds=i / fs)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    for i in range(len(df))
                ]
            df["current"] = 0.42 + 0.02 * np.random.randn(len(df))
            df["temperature"] = 43.2 + 0.1 * np.random.randn(len(df))
            df["rpm"] = 1450.0
            cols = ["timestamp", "x", "y", "z", "current", "temperature", "rpm"]
            df[[c for c in cols if c in df.columns]].to_csv(healthy_dir / name, index=False)
    else:
        # Synthesize healthy
        x_h = 0.05 * np.sin(2 * np.pi * fr * t) + 0.02 * np.random.randn(n_samples)
        y_h = 0.04 * np.cos(2 * np.pi * fr * t) + 0.02 * np.random.randn(n_samples)
        z_h = 9.81 + 0.03 * np.sin(2 * np.pi * fr * t) + 0.02 * np.random.randn(n_samples)
        df_h = pd.DataFrame({
            "timestamp": timestamps,
            "x": x_h, "y": y_h, "z": z_h,
            "current": 0.42 + 0.01 * np.random.randn(n_samples),
            "temperature": 43.2 + 0.05 * np.random.randn(n_samples),
            "rpm": 1450.0
        })
        df_h.to_csv(healthy_dir / "healthy_01.csv", index=False)
        df_h.to_csv(healthy_dir / "healthy_02.csv", index=False)

    # 2. Outer Bearing Fault
    e001_path = raw_dir / "E001r.csv"
    outer_dir = CLEANED_DATA_DIR / "outer_bearing_fault"
    outer_dir.mkdir(parents=True, exist_ok=True)

    if e001_path.exists():
        raw_outer = pd.read_csv(e001_path)
        half = len(raw_outer) // 2
        df_o1 = raw_outer.iloc[:half].copy()
        df_o2 = raw_outer.iloc[half:half + half].copy()
        for df, name in [(df_o1, "outer_01.csv"), (df_o2, "outer_02.csv")]:
            if "time" in df.columns and "timestamp" not in df.columns:
                df["timestamp"] = [
                    (base_time + timedelta(seconds=i / fs)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    for i in range(len(df))
                ]
            df["current"] = 0.46 + 0.02 * np.random.randn(len(df))
            df["temperature"] = 48.5 + 0.1 * np.random.randn(len(df))
            df["rpm"] = 1450.0
            cols = ["timestamp", "x", "y", "z", "current", "temperature", "rpm"]
            df[[c for c in cols if c in df.columns]].to_csv(outer_dir / name, index=False)
    else:
        x_o = 0.05 * np.sin(2 * np.pi * fr * t) + 0.25 * np.sin(2 * np.pi * bpfo * t) + 0.05 * np.random.randn(n_samples)
        y_o = 0.04 * np.cos(2 * np.pi * fr * t) + 0.20 * np.cos(2 * np.pi * bpfo * t) + 0.05 * np.random.randn(n_samples)
        z_o = 9.81 + 0.15 * np.sin(2 * np.pi * bpfo * t) + 0.05 * np.random.randn(n_samples)
        df_o = pd.DataFrame({
            "timestamp": timestamps,
            "x": x_o, "y": y_o, "z": z_o,
            "current": 0.46 + 0.02 * np.random.randn(n_samples),
            "temperature": 48.5 + 0.1 * np.random.randn(n_samples),
            "rpm": 1450.0
        })
        df_o.to_csv(outer_dir / "outer_01.csv", index=False)
        df_o.to_csv(outer_dir / "outer_02.csv", index=False)

    # 3. Inner Bearing Fault (impacts at BPFI modulated by shaft rotation fr)
    inner_dir = CLEANED_DATA_DIR / "inner_bearing_fault"
    inner_dir.mkdir(parents=True, exist_ok=True)
    mod = (1 + 0.5 * np.cos(2 * np.pi * fr * t))
    x_i = 0.05 * np.sin(2 * np.pi * fr * t) + 0.3 * mod * np.sin(2 * np.pi * bpfi * t) + 0.05 * np.random.randn(n_samples)
    y_i = 0.04 * np.cos(2 * np.pi * fr * t) + 0.25 * mod * np.cos(2 * np.pi * bpfi * t) + 0.05 * np.random.randn(n_samples)
    z_i = 9.81 + 0.2 * mod * np.sin(2 * np.pi * bpfi * t) + 0.05 * np.random.randn(n_samples)
    df_i = pd.DataFrame({
        "timestamp": timestamps,
        "x": x_i, "y": y_i, "z": z_i,
        "current": 0.48 + 0.02 * np.random.randn(n_samples),
        "temperature": 52.1 + 0.1 * np.random.randn(n_samples),
        "rpm": 1450.0
    })
    df_i.to_csv(inner_dir / "inner_01.csv", index=False)

    # 4. Ball Bearing Fault (impacts at BSF)
    ball_dir = CLEANED_DATA_DIR / "ball_bearing_fault"
    ball_dir.mkdir(parents=True, exist_ok=True)
    x_b = 0.05 * np.sin(2 * np.pi * fr * t) + 0.22 * np.sin(2 * np.pi * bsf * t) + 0.04 * np.random.randn(n_samples)
    y_b = 0.04 * np.cos(2 * np.pi * fr * t) + 0.18 * np.cos(2 * np.pi * bsf * t) + 0.04 * np.random.randn(n_samples)
    z_b = 9.81 + 0.15 * np.sin(2 * np.pi * bsf * t) + 0.04 * np.random.randn(n_samples)
    df_b = pd.DataFrame({
        "timestamp": timestamps,
        "x": x_b, "y": y_b, "z": z_b,
        "current": 0.45 + 0.02 * np.random.randn(n_samples),
        "temperature": 46.8 + 0.1 * np.random.randn(n_samples),
        "rpm": 1450.0
    })
    df_b.to_csv(ball_dir / "ball_01.csv", index=False)

    # 5. Unbalance (Strong 1x rotational harmonic, high radial vibration)
    unb_dir = CLEANED_DATA_DIR / "unbalance"
    unb_dir.mkdir(parents=True, exist_ok=True)
    x_u = 0.45 * np.sin(2 * np.pi * fr * t) + 0.03 * np.random.randn(n_samples)
    y_u = 0.42 * np.cos(2 * np.pi * fr * t) + 0.03 * np.random.randn(n_samples)
    z_u = 9.81 + 0.08 * np.sin(2 * np.pi * fr * t) + 0.03 * np.random.randn(n_samples)
    df_u = pd.DataFrame({
        "timestamp": timestamps,
        "x": x_u, "y": y_u, "z": z_u,
        "current": 0.49 + 0.02 * np.random.randn(n_samples),
        "temperature": 45.0 + 0.1 * np.random.randn(n_samples),
        "rpm": 1450.0
    })
    df_u.to_csv(unb_dir / "unbalance_01.csv", index=False)

    # 6. Misalignment (Prominent 1x and elevated 2x harmonics, strong axial and radial)
    mis_dir = CLEANED_DATA_DIR / "misalignment"
    mis_dir.mkdir(parents=True, exist_ok=True)
    x_m = 0.28 * np.sin(2 * np.pi * fr * t) + 0.35 * np.sin(4 * np.pi * fr * t) + 0.04 * np.random.randn(n_samples)
    y_m = 0.25 * np.cos(2 * np.pi * fr * t) + 0.32 * np.cos(4 * np.pi * fr * t) + 0.04 * np.random.randn(n_samples)
    z_m = 9.81 + 0.30 * np.sin(4 * np.pi * fr * t) + 0.04 * np.random.randn(n_samples)
    df_m = pd.DataFrame({
        "timestamp": timestamps,
        "x": x_m, "y": y_m, "z": z_m,
        "current": 0.52 + 0.02 * np.random.randn(n_samples),
        "temperature": 55.4 + 0.1 * np.random.randn(n_samples),
        "rpm": 1450.0
    })
    df_m.to_csv(mis_dir / "misalignment_01.csv", index=False)

    print("Successfully generated all demonstration datasets in:", CLEANED_DATA_DIR)

if __name__ == "__main__":
    generate_datasets()

