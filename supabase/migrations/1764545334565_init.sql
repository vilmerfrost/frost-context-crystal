-- Drop existing tables (excluding forbidden tables)
DROP TABLE IF EXISTS conversation_vectors, pipeline_metrics, user_settings, pipeline_jobs, conversations CASCADE;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    source TEXT NOT NULL,
    title TEXT,
    raw_data JSONB NOT NULL,
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create pipeline_jobs table
CREATE TABLE IF NOT EXISTS pipeline_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    stage TEXT NOT NULL,
    compressed_summary TEXT,
    verification_score FLOAT,
    grounding_results JSONB,
    final_prompt TEXT,
    compression_ratio FLOAT,
    information_density FLOAT,
    estimated_cost_savings DECIMAL(10,4),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Create conversation_vectors table
CREATE TABLE IF NOT EXISTS conversation_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create user_settings table
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    api_keys JSONB,
    compression_preset TEXT DEFAULT 'balanced',
    preferred_model TEXT DEFAULT 'deepseek',
    auto_copy_prompt BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create pipeline_metrics table
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_job_id UUID NOT NULL REFERENCES pipeline_jobs(id) ON DELETE CASCADE,
    stage_name TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    tokens_used INTEGER,
    cost DECIMAL(10,6),
    success BOOLEAN NOT NULL,
    error_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_source ON conversations(source);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_conversation_id ON pipeline_jobs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status ON pipeline_jobs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_created_at ON pipeline_jobs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversation_vectors_conversation_id ON conversation_vectors(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_vectors_embedding ON conversation_vectors USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_job_id ON pipeline_metrics(pipeline_job_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_stage ON pipeline_metrics(stage_name);

-- Enable Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_metrics ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY users_view_own_conversations ON conversations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY users_view_own_pipeline_jobs ON pipeline_jobs FOR ALL USING (auth.uid() IN (SELECT user_id FROM conversations WHERE id = pipeline_jobs.conversation_id));
CREATE POLICY users_manage_own_settings ON user_settings FOR ALL USING (auth.uid() = user_id);
CREATE POLICY users_view_own_conversation_vectors ON conversation_vectors FOR ALL USING (auth.uid() IN (SELECT user_id FROM conversations WHERE id = conversation_vectors.conversation_id));
CREATE POLICY users_view_own_pipeline_metrics ON pipeline_metrics FOR ALL USING (auth.uid() IN (SELECT user_id FROM conversations WHERE id IN (SELECT conversation_id FROM pipeline_jobs WHERE id = pipeline_metrics.pipeline_job_id)));

-- Insert seed data with valid UUIDs
INSERT INTO conversations (id, user_id, source, title, raw_data, token_count) VALUES 
(gen_random_uuid(), '00000000-0000-0000-0000-000000000000', 'chatgpt', 'AI Development Discussion', '{"messages": [{"role": "user", "content": "How to build AI apps?"}, {"role": "assistant", "content": "Use React and FastAPI"}]}', 150),
(gen_random_uuid(), '00000000-0000-0000-0000-000000000000', 'claude', 'Database Design Patterns', '{"messages": [{"role": "user", "content": "Best practices for PostgreSQL?"}, {"role": "assistant", "content": "Use proper indexing and RLS"}]}', 200),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'perplexity', 'Machine Learning Pipeline', '{"messages": [{"role": "user", "content": "ML pipeline architecture"}, {"role": "assistant", "content": "Data preprocessing, training, evaluation"}]}', 180);

INSERT INTO pipeline_jobs (id, conversation_id, status, stage, compressed_summary, verification_score, compression_ratio, estimated_cost_savings) VALUES 
(gen_random_uuid(), (SELECT id FROM conversations LIMIT 1 OFFSET 0), 'completed', 'compression', 'AI development using modern frameworks', 0.95, 0.65, 0.0450),
(gen_random_uuid(), (SELECT id FROM conversations LIMIT 1 OFFSET 1), 'processing', 'verification', 'Database design best practices', 0.88, 0.72, 0.0380),
(gen_random_uuid(), (SELECT id FROM conversations LIMIT 1 OFFSET 2), 'pending', 'extraction', 'ML pipeline architecture overview', NULL, NULL, NULL);

INSERT INTO conversation_vectors (id, conversation_id, message_index, content, embedding) VALUES 
(gen_random_uuid(), (SELECT id FROM conversations LIMIT 1 OFFSET 0), 0, 'How to build AI apps?', array_fill(0.1, ARRAY[1536])::vector),
(gen_random_uuid(), (SELECT id FROM conversations LIMIT 1 OFFSET 0), 1, 'Use React and FastAPI', array_fill(0.2, ARRAY[1536])::vector),
(gen_random_uuid(), (SELECT id FROM conversations LIMIT 1 OFFSET 1), 0, 'Best practices for PostgreSQL?', array_fill(0.15, ARRAY[1536])::vector);

INSERT INTO user_settings (id, user_id, api_keys, compression_preset) VALUES 
(gen_random_uuid(), '00000000-0000-0000-0000-000000000000', '{"openai": "sk-test123", "anthropic": "claude-test456"}', 'balanced'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', '{"openai": "sk-test789", "anthropic": "claude-test012"}', 'aggressive');

INSERT INTO pipeline_metrics (id, pipeline_job_id, stage_name, duration_ms, tokens_used, success) VALUES 
(gen_random_uuid(), (SELECT id FROM pipeline_jobs LIMIT 1 OFFSET 0), 'compression', 1250, 450, true),
(gen_random_uuid(), (SELECT id FROM pipeline_jobs LIMIT 1 OFFSET 0), 'verification', 890, 320, true),
(gen_random_uuid(), (SELECT id FROM pipeline_jobs LIMIT 1 OFFSET 1), 'extraction', 560, 210, true);