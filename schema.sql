-- Create contacts table
CREATE TABLE IF NOT EXISTS contacts (
    phone_number TEXT PRIMARY KEY,
    name TEXT,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    human_handoff BOOLEAN DEFAULT FALSE
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    phone_number TEXT NOT NULL REFERENCES contacts(phone_number) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'model', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    phone_number TEXT NOT NULL REFERENCES contacts(phone_number) ON DELETE CASCADE,
    customer_name TEXT,
    items TEXT NOT NULL,
    total_amount INTEGER DEFAULT 0,
    delivery_address TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'dispatched', 'delivered', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_phone ON orders(phone_number);
