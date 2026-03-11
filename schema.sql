-- ─────────────────────────────────────────────────────────────────────────────
-- Wine Quality Predictor — Database Schema
-- Run once: mysql -u root -p < schema.sql
-- ─────────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS wine_db;
USE wine_db;


-- ── User accounts ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)        NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255)        NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Prediction history ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    user_id              INT            NOT NULL,
    fixed_acidity        FLOAT          NOT NULL,
    volatile_acidity     FLOAT          NOT NULL,
    citric_acid          FLOAT          NOT NULL,
    residual_sugar       FLOAT          NOT NULL,
    chlorides            FLOAT          NOT NULL,
    free_sulfur_dioxide  FLOAT          NOT NULL,
    total_sulfur_dioxide FLOAT          NOT NULL,
    density              FLOAT          NOT NULL,
    pH                   FLOAT          NOT NULL,
    sulphates            FLOAT          NOT NULL,
    alcohol              FLOAT          NOT NULL,
    predicted_quality    FLOAT          NOT NULL,
    quality_label        VARCHAR(20)    NOT NULL,   -- 'Poor', 'Average', 'Good', 'Excellent'
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Contact messages ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contact_messages (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL,
    message    TEXT         NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
