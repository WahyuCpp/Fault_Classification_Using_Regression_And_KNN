# Motor Faults Classification Using KNN

**An IoT-based motor condition monitoring, fault classification, and predictive maintenance system using K-Nearest Neighbors (KNN) and Linear Regression.**

## Project Overview

This project aims to develop an integrated motor condition monitoring system capable of acquiring sensor measurements, processing operational data, identifying motor fault conditions, and estimating future degradation trends.

The system combines **embedded firmware, signal processing, relational database management, exploratory data analysis (EDA), supervised machine learning, and web-based visualization**.

Two primary machine learning approaches are planned:

- **K-Nearest Neighbors (KNN):** Classifies motor operating conditions based on extracted sensor features.
- **Linear Regression:** Models historical condition indicators to estimate degradation trends and potential threshold-crossing times.

The project is currently **under active development**. Data cleaning has been completed, while MySQL database initialization is in progress. Other subsystems are scheduled for subsequent development.

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Embedded Firmware | C, C++, Arduino (`.ino`) | Sensor acquisition and embedded processing |
| Development Environment | Arduino IDE, PlatformIO | Firmware development and deployment |
| Database | MySQL, SQL | Structured storage of sensor measurements |
| Data Processing | Python, Pandas, NumPy | Data cleaning and feature preparation |
| Data Visualization | Matplotlib, Seaborn | Exploratory data analysis |
| Machine Learning | Scikit-learn | KNN classification and linear regression |
| Frontend | JavaScript, HTML, CSS, npm | Web interface and monitoring dashboard |
| Backend | To be determined | Database access and application API |

## System Architecture

The proposed system follows a modular architecture:

```text
            MOTOR UNDER MONITORING
                      |
                      v
              SENSOR ACQUISITION
                      |
                      v
             EMBEDDED FIRMWARE
             Arduino / PlatformIO
                      |
                      v
              BACKEND / API
                      |
                      v
                MySQL DATABASE
                      |
          +-----------+-----------+
          |                       |
          v                       v
   DATA PROCESSING         HISTORICAL DATA
   Cleaning / EDA             ANALYSIS
          |                       |
          v                       v
   FEATURE EXTRACTION       LINEAR REGRESSION
          |                       |
          v                       v
   KNN CLASSIFICATION       TREND ESTIMATION
          |                       |
          +-----------+-----------+
                      |
                      v
                 WEB DASHBOARD
                   npm / JS
```

This architecture represents the intended implementation and is subject to revision during development.

## Core Modules

### 1. Database Initialization — MySQL

**Status: In Progress**

The database module manages structured historical measurements, timestamps, and processed monitoring results.

Planned functionality includes:

- Database and table initialization.
- Sensor measurement storage.
- Timestamp-based historical data retrieval.
- Data integrity and validation.
- Database integration with the backend and machine learning pipeline.

### 2. Data Cleaning and Exploratory Data Analysis

**Status: Data Cleaning Completed | EDA Pending**

The data processing module prepares acquired measurements for subsequent statistical analysis and machine learning.

Data cleaning activities include:

- Handling missing or invalid measurements.
- Removing duplicated records.
- Checking data types and numerical consistency.
- Preparing cleaned datasets for further analysis.

Planned EDA activities include:

- Statistical descriptions of motor operating data.
- Sensor measurement distributions.
- Correlation analysis.
- Outlier investigation.
- Time-series visualization.
- Feature distribution analysis across motor conditions.

### 3. Motor Fault Classification — KNN

**Status: Planned**

K-Nearest Neighbors is intended to classify motor operating conditions using features derived from sensor measurements.

The classification pipeline will include:

1. Feature selection and extraction.
2. Feature normalization or standardization.
3. Training and testing dataset preparation.
4. KNN model training.
5. Hyperparameter tuning, including the number of neighbors (`k`).
6. Classification performance evaluation.

Evaluation metrics will include accuracy, precision, recall, F1-score, and confusion matrix analysis.

Fault categories will be finalized based on the available labeled dataset and experimental validation.

### 4. Breakdown Prediction — Linear Regression

**Status: Planned**

Linear Regression will be investigated to model changes in motor condition indicators over time.

The proposed implementation includes:

- Historical condition indicator analysis.
- Degradation trend estimation.
- Regression model fitting.
- Future condition indicator estimation.
- Maintenance threshold-crossing estimation.

Model performance will be evaluated using MAE, RMSE, and coefficient of determination (R²), where applicable.

**Note:** Linear Regression alone does not establish a reliable motor breakdown prediction model. Threshold-crossing estimates will be treated as preliminary projections and will require experimental validation before being interpreted as failure or remaining-useful-life predictions.

### 5. Embedded Firmware

**Status: Planned**

Firmware development will use C/C++ with Arduino-compatible microcontrollers.

Supported development environments:

- Arduino IDE
- PlatformIO

Planned firmware responsibilities include sensor interfacing, signal acquisition, measurement validation, basic signal conditioning, and communication with the data acquisition backend.

Firmware source files may include:

- `.ino` — Arduino sketches.
- `.cpp` — C++ implementation files.
- `.h` — Header files and interface definitions.

Hardware configuration and communication protocols will be documented as development progresses.

### 6. Web-Based Monitoring Interface

**Status: Planned**

A JavaScript-based frontend will be developed using an npm-managed development environment.

Planned dashboard functionality includes:

- Motor monitoring visualization.
- Historical sensor measurements.
- Motor fault classification results.
- Degradation trend visualization.
- Maintenance prediction indicators.
- Communication with the backend API.

The specific frontend framework and build configuration are not yet finalized.

## Proposed Repository Structure

The following structure is a development target rather than a representation of the current repository contents.

```text
Motor-Faults-Classification-Using-KNN/
|
|-- database/
|   |-- init.sql
|   |-- schema.sql
|
|-- data/
|   |-- raw/
|   |-- cleaned/
|   |-- processed/
|
|-- notebooks/
|   |-- data_cleaning.ipynb
|   |-- eda.ipynb
|
|-- ml/
|   |-- knn_classifier.py
|   |-- linear_regression.py
|   |-- preprocessing.py
|   |-- evaluation.py
|
|-- firmware/
|   |-- arduino/
|   |   |-- main.ino
|   |
|   |-- platformio/
|       |-- platformio.ini
|       |-- src/
|       |   |-- main.cpp
|       |-- include/
|           |-- config.h
|
|-- backend/
|   |-- README.md
|
|-- frontend/
|   |-- package.json
|   |-- src/
|   |-- public/
|
|-- docs/
|   |-- architecture/
|   |-- experiments/
|
|-- requirements.txt
|-- .gitignore
|-- LICENSE
|-- README.md
```

## Installation and Development Setup

The following commands describe the intended development workflow. They are not yet verified installation instructions for the complete system.

### Clone the Repository

```bash
git clone https://github.com/<username>/<repository>.git
cd <repository>
```

Replace the placeholders with the actual GitHub repository information.

### Python Environment

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies once `requirements.txt` has been configured:

```bash
pip install -r requirements.txt
```

### MySQL Database

Database initialization scripts will be provided in the `database/` directory.

Once available, the database can be initialized using the project's SQL scripts and appropriate MySQL credentials.

### Frontend

When the frontend package is available:

```bash
cd frontend
npm install
npm run dev
```

The development command may change depending on the selected frontend framework and configured npm scripts.

### Firmware

Firmware can be compiled and uploaded using either Arduino IDE or PlatformIO, subject to the selected microcontroller and hardware configuration.

## Development Roadmap

| No. | Development Task | Status |
|---|---|---|
| 1 | Data Cleaning | Completed |
| 2 | MySQL Database Initialization | In Progress |
| 3 | Exploratory Data Analysis (EDA) | Pending |
| 4 | Feature Engineering and Extraction | Pending |
| 5 | KNN Fault Classification | Pending |
| 6 | Linear Regression for Degradation Prediction | Pending |
| 7 | Embedded Firmware Development | Pending |
| 8 | Frontend Development using npm | Pending |
| 9 | Backend and Database Integration | Pending |
| 10 | System Integration and Validation | Pending |

## Development Status

**Current Phase: Data Preparation and Database Development**

The project is not yet a fully operational motor fault classification system.

Completed work:

- Initial dataset cleaning and preparation.

Ongoing work:

- MySQL database initialization.

Upcoming priorities:

- Exploratory Data Analysis.
- Feature engineering.
- KNN classifier development.
- Regression-based condition trend analysis.
- Embedded firmware and monitoring interface implementation.

## Engineering Considerations

The project will consider several factors affecting monitoring accuracy and predictive performance:

- Sensor measurement quality and calibration.
- Sampling frequency and signal integrity.
- Noise reduction and signal conditioning.
- Dataset labeling and class imbalance.
- Data leakage prevention during model validation.
- Appropriate feature scaling for distance-based KNN classification.
- Generalization across motor operating conditions.
- Reliability of degradation trends and maintenance estimates.

## Project Objectives

The principal objectives are to:

1. Establish a structured acquisition and database pipeline for motor monitoring.
2. Prepare and analyze operational measurements.
3. Develop a supervised KNN-based motor fault classifier.
4. Investigate linear regression for condition degradation forecasting.
5. Integrate embedded data acquisition with a web-based monitoring application.
6. Evaluate the system using reproducible experimental and statistical methods.

## Disclaimer

This repository is intended for engineering research and software development.

The fault classification and predictive maintenance components are under development and should not be considered validated industrial diagnostic or protection systems.

## License

A software license has not yet been specified.

---

**Project Status:** Active Development

**Research Areas:** Electrical Machines · Condition Monitoring · Signal Processing · Supervised Machine Learning · Embedded Systems · Industrial IoT