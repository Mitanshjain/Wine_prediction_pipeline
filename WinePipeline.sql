-- 1️ Create Database / Database Layer
CREATE OR REPLACE DATABASE wine_db;
USE DATABASE wine_db;x`

-- 2️ Create Schemas (Raw + Processed Layers)
CREATE OR REPLACE SCHEMA raw_data;
CREATE OR REPLACE SCHEMA processed_data;

-- 3️ Create File Format for CSV
CREATE OR REPLACE FILE FORMAT wine_csv_format
TYPE = 'CSV'
FIELD_DELIMITER = ','
SKIP_HEADER = 1
TRIM_SPACE = TRUE;  -- optional but helps remove extra spaces

-- 4️  Create Stage (Connect to S3)
CREATE OR REPLACE STAGE wine_stage
URL='s3://mitanshbucket/'
CREDENTIALS=(
    AWS_KEY_ID='AWS KEY',
    AWS_SECRET_KEY='AWS SECRET KEY'
)
FILE_FORMAT = wine_csv_format;

-- 5️ List files in stage to verify connection
LIST @wine_stage;

-- 6️ Create Raw Table
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

-- 7️ Create Snowpipe for Auto Ingestion
CREATE OR REPLACE PIPE wine_pipe
AUTO_INGEST = TRUE
AS
COPY INTO raw_data.wine_raw
FROM @wine_stage
FILE_FORMAT = wine_csv_format
ON_ERROR = 'CONTINUE';  -- prevents failures if some rows have issues

-- 8️ Verify pipes
SHOW PIPES;

-- 9️ If this is the first time loading, run manual COPY to ingest existing files
COPY INTO raw_data.wine_raw
FROM @wine_stage
FILE_FORMAT = wine_csv_format
ON_ERROR = 'CONTINUE';

-- 10️ Check data in the raw table
SELECT * FROM raw_data.wine_raw LIMIT 10;

-- 11️ Check Snowpipe status
SELECT SYSTEM$PIPE_STATUS('wine_pipe');