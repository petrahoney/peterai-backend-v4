CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50),
    original_request TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE task_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    action VARCHAR(100),
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    service VARCHAR(50),
    credentials_encrypted TEXT,
    status VARCHAR(50)
);

SELECT 'Tables created!';
