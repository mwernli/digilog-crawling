ALTER TABLE municipality_calibration
    ADD COLUMN IF NOT EXISTS inserted_at timestamp NOT NULL DEFAULT NOW();
ALTER TABLE municipality_calibration
    ADD COLUMN IF NOT EXISTS updated_at timestamp NOT NULL DEFAULT NOW();