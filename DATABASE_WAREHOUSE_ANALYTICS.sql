-- 1️⃣ Create Warehouse
CREATE OR REPLACE WAREHOUSE wine_wh
WITH WAREHOUSE_SIZE = 'XSMALL'
AUTO_SUSPEND = 60
AUTO_RESUME = TRUE;

USE WAREHOUSE wine_wh;

-- 2️⃣ Create Database
CREATE OR REPLACE DATABASE wine_db;
USE DATABASE wine_db;

-- 3️⃣ Create Schemas
CREATE OR REPLACE SCHEMA raw_data;
CREATE OR REPLACE SCHEMA processed_data;

-- 4️⃣ Create File Format for CSV
CREATE OR REPLACE FILE FORMAT wine_csv_format
TYPE = 'CSV'
FIELD_DELIMITER = ','
SKIP_HEADER = 1
TRIM_SPACE = TRUE;

-- 5️⃣ Create External Stage (Connect Snowflake to S3)
CREATE OR REPLACE STAGE wine_stage
URL='s3://mitanshbucket/'
CREDENTIALS=(
    AWS_KEY_ID='AWS KEY'
    AWS_SECRET_KEY='AWS SECRET KEY'
)
FILE_FORMAT = wine_csv_format;

-- 6️⃣ Verify files in S3
LIST @wine_stage;

-- 7️⃣ Create Raw Table (Landing Layer)
CREATE OR REPLACE TABLE raw_data.wine_raw (
    fixed_acidity FLOAT,
    volatile_acidity FLOAT,
    citric_acid FLOAT,
    residual_sugar FLOAT,
    chlorides FLOAT,
    free_sulfur_dioxide FLOAT,
    total_sulfur_dioxide FLOAT,
    density FLOAT,
    pH FLOAT,
    sulphates FLOAT,
    alcohol FLOAT,
    quality INT,
    id INT
);

-- 8️⃣ Create Snowpipe for Automatic Ingestion
CREATE OR REPLACE PIPE wine_pipe
AUTO_INGEST = TRUE
AS
COPY INTO raw_data.wine_raw
FROM @wine_stage
FILE_FORMAT = wine_csv_format
ON_ERROR = 'CONTINUE';

-- 9️⃣ Verify Snowpipe
SHOW PIPES;

-- 🔟 Initial Load (for existing files)
COPY INTO raw_data.wine_raw
FROM @wine_stage
FILE_FORMAT = wine_csv_format
ON_ERROR = 'CONTINUE';

-- 11️⃣ Verify Raw Data
SELECT * FROM raw_data.wine_raw LIMIT 10;

-- 12️⃣ Create Processed Table (Warehouse Layer)
CREATE OR REPLACE TABLE processed_data.wine_clean AS
SELECT
    fixed_acidity,
    volatile_acidity,
    citric_acid,
    residual_sugar,
    chlorides,
    alcohol,
    quality
FROM raw_data.wine_raw
WHERE quality IS NOT NULL;

-- 13️⃣ Create Analytics Table
CREATE OR REPLACE TABLE processed_data.wine_quality_summary AS
SELECT
    quality,
    AVG(alcohol) AS avg_alcohol,
    AVG(fixed_acidity) AS avg_acidity,
    COUNT(*) AS total_records
FROM processed_data.wine_clean
GROUP BY quality;

-- 14️⃣ Check Analytics Output
SELECT * FROM processed_data.wine_quality_summary;

-- 15️⃣ Check Snowpipe Status
SELECT SYSTEM$PIPE_STATUS('wine_pipe');


-- Archietecture 
-- WineQT.csv
--       ↓
-- AWS S3 Bucket
--       ↓
-- Snowflake Stage
--       ↓
-- Snowpipe
--       ↓
-- RAW TABLE (raw_data.wine_raw)
--       ↓
-- CLEAN TABLE (processed_data.wine_clean)
--       ↓
-- ANALYTICS TABLE (processed_data.wine_quality_summary)

SELECT * 
FROM processed_data.wine_quality_summary
ORDER BY quality;