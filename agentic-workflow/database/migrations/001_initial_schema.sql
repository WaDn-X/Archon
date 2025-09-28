-- Initial Database Schema for Zippy-Archon Platform
-- Migration: 001_initial_schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    wallet_address VARCHAR(255) NOT NULL UNIQUE,
    zippycoin_balance DECIMAL(20, 8) DEFAULT 0.0,
    trust_score DECIMAL(3, 2) DEFAULT 0.5,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Requirements table
CREATE TABLE IF NOT EXISTS requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    provider VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    requirements_content TEXT,
    design_content TEXT,
    tasks_content TEXT,
    trust_score DECIMAL(3, 2),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- A/B Tests table
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    versions TEXT[] NOT NULL,
    provider VARCHAR(50) NOT NULL,
    results JSONB NOT NULL,
    winner VARCHAR(50),
    comparison_metrics JSONB,
    num_runs INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Marketplace listings table
CREATE TABLE IF NOT EXISTS marketplace_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content JSONB NOT NULL,
    category VARCHAR(100) NOT NULL,
    tags TEXT[],
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    author_wallet VARCHAR(255) NOT NULL,
    pricing JSONB NOT NULL,
    trust_score DECIMAL(3, 2) DEFAULT 0.5,
    purchase_count INTEGER DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES users(id) ON DELETE CASCADE,
    listing_id UUID REFERENCES marketplace_listings(id) ON DELETE CASCADE,
    amount DECIMAL(20, 8) NOT NULL,
    currency VARCHAR(10) DEFAULT 'ZIPPY',
    status VARCHAR(20) DEFAULT 'pending',
    transaction_hash VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Trust validations table
CREATE TABLE IF NOT EXISTS trust_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    trust_score DECIMAL(3, 2) NOT NULL,
    trust_level VARCHAR(20) NOT NULL,
    metrics JSONB,
    insights TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI usage logs table
CREATE TABLE IF NOT EXISTS ai_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost DECIMAL(10, 6) NOT NULL,
    generation_time DECIMAL(10, 3),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Milestones table
CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    milestone_type VARCHAR(50) NOT NULL,
    reward_amount DECIMAL(20, 8) NOT NULL,
    is_completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_wallet_address ON users(wallet_address);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_requirements_user_id ON requirements(user_id);
CREATE INDEX IF NOT EXISTS idx_requirements_provider ON requirements(provider);
CREATE INDEX IF NOT EXISTS idx_requirements_created_at ON requirements(created_at);
CREATE INDEX IF NOT EXISTS idx_ab_tests_user_id ON ab_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created_at ON ab_tests(created_at);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_category ON marketplace_listings(category);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_trust_score ON marketplace_listings(trust_score);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_author_id ON marketplace_listings(author_id);
CREATE INDEX IF NOT EXISTS idx_transactions_buyer_id ON transactions(buyer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_seller_id ON transactions(seller_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_trust_validations_user_id ON trust_validations(user_id);
CREATE INDEX IF NOT EXISTS idx_trust_validations_content_hash ON trust_validations(content_hash);
CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_user_id ON ai_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_provider ON ai_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_created_at ON ai_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_milestones_user_id ON milestones(user_id);
CREATE INDEX IF NOT EXISTS idx_milestones_type ON milestones(milestone_type);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_title_fts ON marketplace_listings USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_description_fts ON marketplace_listings USING gin(to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_requirements_prompt_fts ON requirements USING gin(to_tsvector('english', prompt));

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_requirements_updated_at BEFORE UPDATE ON requirements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ab_tests_updated_at BEFORE UPDATE ON ab_tests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_marketplace_listings_updated_at BEFORE UPDATE ON marketplace_listings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_milestones_updated_at BEFORE UPDATE ON milestones FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to calculate user trust score
CREATE OR REPLACE FUNCTION calculate_user_trust_score(user_uuid UUID)
RETURNS DECIMAL(3, 2) AS $$
DECLARE
    avg_requirement_score DECIMAL(3, 2);
    avg_listing_score DECIMAL(3, 2);
    total_validations INTEGER;
    high_trust_validations INTEGER;
    final_score DECIMAL(3, 2);
BEGIN
    -- Calculate average requirement trust score
    SELECT COALESCE(AVG(trust_score), 0.5)
    INTO avg_requirement_score
    FROM requirements
    WHERE user_id = user_uuid AND trust_score IS NOT NULL;
    
    -- Calculate average marketplace listing trust score
    SELECT COALESCE(AVG(trust_score), 0.5)
    INTO avg_listing_score
    FROM marketplace_listings
    WHERE author_id = user_uuid AND trust_score IS NOT NULL;
    
    -- Count trust validations
    SELECT COUNT(*), COUNT(CASE WHEN trust_level = 'high' THEN 1 END)
    INTO total_validations, high_trust_validations
    FROM trust_validations
    WHERE user_id = user_uuid;
    
    -- Calculate final score (weighted average)
    final_score = (
        COALESCE(avg_requirement_score, 0.5) * 0.4 +
        COALESCE(avg_listing_score, 0.5) * 0.4 +
        CASE 
            WHEN total_validations > 0 THEN (high_trust_validations::DECIMAL / total_validations) * 0.2
            ELSE 0.5 * 0.2
        END
    );
    
    RETURN LEAST(GREATEST(final_score, 0.0), 1.0);
END;
$$ LANGUAGE plpgsql;

-- Create function to update user trust score
CREATE OR REPLACE FUNCTION update_user_trust_score()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users 
    SET trust_score = calculate_user_trust_score(NEW.user_id)
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update user trust scores
CREATE TRIGGER update_user_trust_score_requirements 
    AFTER INSERT OR UPDATE ON requirements 
    FOR EACH ROW EXECUTE FUNCTION update_user_trust_score();

CREATE TRIGGER update_user_trust_score_marketplace 
    AFTER INSERT OR UPDATE ON marketplace_listings 
    FOR EACH ROW EXECUTE FUNCTION update_user_trust_score();

CREATE TRIGGER update_user_trust_score_validations 
    AFTER INSERT ON trust_validations 
    FOR EACH ROW EXECUTE FUNCTION update_user_trust_score();

-- Create function to handle marketplace purchase
CREATE OR REPLACE FUNCTION process_marketplace_purchase()
RETURNS TRIGGER AS $$
BEGIN
    -- Update purchase count
    UPDATE marketplace_listings 
    SET purchase_count = purchase_count + 1
    WHERE id = NEW.listing_id;
    
    -- Transfer ZippyCoin from buyer to seller
    UPDATE users 
    SET zippycoin_balance = zippycoin_balance - NEW.amount
    WHERE id = NEW.buyer_id;
    
    UPDATE users 
    SET zippycoin_balance = zippycoin_balance + NEW.amount
    WHERE id = NEW.seller_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for marketplace purchases
CREATE TRIGGER process_marketplace_purchase_trigger
    AFTER INSERT ON transactions
    FOR EACH ROW
    WHEN (NEW.status = 'completed')
    EXECUTE FUNCTION process_marketplace_purchase();

-- Create views for common queries
CREATE OR REPLACE VIEW marketplace_listings_with_author AS
SELECT 
    ml.*,
    u.username as author_username,
    u.trust_score as author_trust_score
FROM marketplace_listings ml
JOIN users u ON ml.author_id = u.id
WHERE ml.is_active = true;

CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.zippycoin_balance,
    u.trust_score,
    COUNT(DISTINCT r.id) as total_requirements,
    COUNT(DISTINCT ab.id) as total_ab_tests,
    COUNT(DISTINCT ml.id) as total_listings,
    COUNT(DISTINCT t.id) as total_transactions,
    SUM(CASE WHEN t.status = 'completed' THEN t.amount ELSE 0 END) as total_volume
FROM users u
LEFT JOIN requirements r ON u.id = r.user_id
LEFT JOIN ab_tests ab ON u.id = ab.user_id
LEFT JOIN marketplace_listings ml ON u.id = ml.author_id
LEFT JOIN transactions t ON u.id = t.seller_id
GROUP BY u.id, u.username, u.zippycoin_balance, u.trust_score;

-- Insert default data
INSERT INTO users (username, email, wallet_address, zippycoin_balance, trust_score) VALUES
('admin', 'admin@zippy-archon.com', '0x0000000000000000000000000000000000000000', 1000.0, 1.0),
('demo_user', 'demo@zippy-archon.com', '0x1111111111111111111111111111111111111111', 100.0, 0.8)
ON CONFLICT (wallet_address) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
