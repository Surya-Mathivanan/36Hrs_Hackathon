-- Human Population Data Table
-- This is the CORE feature: tracking campus population and their CO2 emissions

CREATE TABLE IF NOT EXISTS human_population (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    student_count INT NOT NULL,
    staff_count INT NOT NULL,
    total_count INT GENERATED ALWAYS AS (student_count + staff_count) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_date (date)
);

-- Add human CO2 emission factor
-- Average human produces ~1 kg CO2 per day (respiration + metabolic processes)
-- This is a conservative estimate for daily presence on campus
INSERT INTO emission_factors (source_type, factor, factor_unit) VALUES
('human_daily', 1.0, 'kg_co2e_per_person_per_day')
ON DUPLICATE KEY UPDATE
    factor = VALUES(factor),
    factor_unit = VALUES(factor_unit);
