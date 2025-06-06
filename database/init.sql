-- 創建一個users的table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    line_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status INTEGER NOT NULL,
    role VARCHAR(255) NOT NULL,
    group_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
