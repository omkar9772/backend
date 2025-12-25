-- Create device_tokens table for FCM push notifications
CREATE TABLE IF NOT EXISTS device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_token VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('android', 'ios', 'web')),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_device_tokens_device_token ON device_tokens(device_token);
CREATE INDEX IF NOT EXISTS ix_device_tokens_user_id ON device_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_device_tokens_created_at ON device_tokens(created_at);
CREATE INDEX IF NOT EXISTS ix_device_tokens_user_platform ON device_tokens(user_id, platform);

-- Create trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_device_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER device_tokens_updated_at
BEFORE UPDATE ON device_tokens
FOR EACH ROW
EXECUTE FUNCTION update_device_tokens_updated_at();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON device_tokens TO your_backend_user;
