-- Phase 3 Database Schema Migration
-- Adds support for AI-powered task management, real-time collaboration, and advanced analytics

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- TASK PRIORITIZATION TABLES
-- =====================================================

-- Task prioritization factors table
CREATE TABLE IF NOT EXISTS archon_prioritization_factors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    project_id UUID NOT NULL,
    deadline_weight DECIMAL(3,2) NOT NULL DEFAULT 0.30 CHECK (deadline_weight >= 0 AND deadline_weight <= 1),
    dependency_weight DECIMAL(3,2) NOT NULL DEFAULT 0.25 CHECK (dependency_weight >= 0 AND dependency_weight <= 1),
    user_pattern_weight DECIMAL(3,2) NOT NULL DEFAULT 0.20 CHECK (user_pattern_weight >= 0 AND user_pattern_weight <= 1),
    project_context_weight DECIMAL(3,2) NOT NULL DEFAULT 0.15 CHECK (project_context_weight >= 0 AND project_context_weight <= 1),
    complexity_weight DECIMAL(3,2) NOT NULL DEFAULT 0.10 CHECK (complexity_weight >= 0 AND complexity_weight <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_weights CHECK (
        deadline_weight + dependency_weight + user_pattern_weight + project_context_weight + complexity_weight = 1.0
    )
);

-- User pattern analysis table
CREATE TABLE IF NOT EXISTS archon_user_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    preferred_work_hours JSONB DEFAULT '[]', -- Array of preferred hours (0-23)
    preferred_work_days JSONB DEFAULT '[]', -- Array of preferred days (0-6, Monday-Sunday)
    average_task_duration JSONB DEFAULT '{}', -- task_type -> average minutes
    common_task_types JSONB DEFAULT '[]', -- Array of frequently used task types
    peak_productivity_hours JSONB DEFAULT '[]', -- Hours with highest productivity
    break_frequency INTEGER DEFAULT 90, -- Minutes between breaks
    last_break_time TIMESTAMP WITH TIME ZONE,
    skill_levels JSONB DEFAULT '{}', -- skill -> proficiency (0.0-1.0)
    collaboration_preference TEXT DEFAULT 'moderate' CHECK (collaboration_preference IN ('low', 'moderate', 'high')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- REAL-TIME COLLABORATION TABLES
-- =====================================================

-- Teams table
CREATE TABLE IF NOT EXISTS archon_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    project_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settings JSONB DEFAULT '{
        "default_assignment_strategy": "workload_balance",
        "max_tasks_per_member": 5,
        "auto_assignment_enabled": true
    }'
);

-- Team members table
CREATE TABLE IF NOT EXISTS archon_team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES archon_teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'developer' CHECK (role IN ('owner', 'manager', 'lead', 'developer', 'designer', 'qa', 'analyst', 'stakeholder')),
    skills JSONB DEFAULT '[]', -- Array of skill names
    availability_hours_per_week INTEGER DEFAULT 40 CHECK (availability_hours_per_week >= 0 AND availability_hours_per_week <= 168),
    current_workload INTEGER DEFAULT 0 CHECK (current_workload >= 0),
    capacity_utilization DECIMAL(3,2) DEFAULT 0.0 CHECK (capacity_utilization >= 0 AND capacity_utilization <= 1),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task assignments table
CREATE TABLE IF NOT EXISTS archon_task_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    assignee_id UUID NOT NULL,
    assigned_by UUID NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    estimated_hours INTEGER CHECK (estimated_hours > 0),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    strategy VARCHAR(50) DEFAULT 'manual',
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT
);

-- Collaboration activity log
CREATE TABLE IF NOT EXISTS archon_collaboration_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- TASK DEPENDENCY TABLES
-- =====================================================

-- Task dependencies table
CREATE TABLE IF NOT EXISTS archon_task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    from_task UUID NOT NULL,
    to_task UUID NOT NULL,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'finish_to_start' CHECK (dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')),
    strength VARCHAR(20) DEFAULT 'medium' CHECK (strength IN ('weak', 'medium', 'strong', 'critical')),
    lag_time INTEGER DEFAULT 0, -- Lag time in hours
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(from_task, to_task)
);

-- =====================================================
-- PROGRESS TRACKING TABLES
-- =====================================================

-- Milestones table
CREATE TABLE IF NOT EXISTS archon_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'delayed', 'at_risk', 'cancelled')),
    progress_percentage DECIMAL(5,2) DEFAULT 0.0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    dependencies JSONB DEFAULT '[]', -- Array of milestone IDs this depends on
    deliverables JSONB DEFAULT '[]', -- Array of deliverable descriptions
    owner UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Progress snapshots table (for historical tracking)
CREATE TABLE IF NOT EXISTS archon_progress_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_tasks INTEGER NOT NULL DEFAULT 0,
    completed_tasks INTEGER NOT NULL DEFAULT 0,
    in_progress_tasks INTEGER NOT NULL DEFAULT 0,
    blocked_tasks INTEGER NOT NULL DEFAULT 0,
    overdue_tasks INTEGER NOT NULL DEFAULT 0,
    time_spent_hours DECIMAL(8,2) DEFAULT 0.0,
    estimated_remaining_hours DECIMAL(8,2) DEFAULT 0.0,
    velocity_tasks_per_day DECIMAL(5,2) DEFAULT 0.0,
    milestone_progress JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- SMART SUGGESTIONS TABLES
-- =====================================================

-- Suggestion feedback table
CREATE TABLE IF NOT EXISTS archon_suggestion_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    user_id UUID NOT NULL,
    suggestion_type VARCHAR(50) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    usefulness BOOLEAN DEFAULT NULL,
    feedback_text TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Suggestion analytics table
CREATE TABLE IF NOT EXISTS archon_suggestion_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    suggestion_type VARCHAR(50) NOT NULL,
    was_accepted BOOLEAN NOT NULL,
    time_to_action INTEGER, -- Minutes from suggestion to action
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- COMMENTS AND COMMUNICATION TABLES
-- =====================================================

-- Comments table (enhanced for collaboration)
CREATE TABLE IF NOT EXISTS archon_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    user_id UUID NOT NULL,
    username VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    parent_comment_id UUID REFERENCES archon_comments(id) ON DELETE CASCADE,
    mentions JSONB DEFAULT '[]', -- Array of mentioned user IDs
    reactions JSONB DEFAULT '{}', -- user_id -> reaction_type
    is_resolved BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Task prioritization indexes
CREATE INDEX IF NOT EXISTS idx_prioritization_factors_user_project ON archon_prioritization_factors(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_user_patterns_user ON archon_user_patterns(user_id);

-- Team collaboration indexes
CREATE INDEX IF NOT EXISTS idx_teams_project ON archon_teams(project_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON archon_team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON archon_team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_task_assignments_task ON archon_task_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_assignments_assignee ON archon_task_assignments(assignee_id);

-- Task dependency indexes
CREATE INDEX IF NOT EXISTS idx_task_dependencies_project ON archon_task_dependencies(project_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_from ON archon_task_dependencies(from_task);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_to ON archon_task_dependencies(to_task);

-- Progress tracking indexes
CREATE INDEX IF NOT EXISTS idx_milestones_project ON archon_milestones(project_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON archon_milestones(status);
CREATE INDEX IF NOT EXISTS idx_progress_snapshots_project ON archon_progress_snapshots(project_id);
CREATE INDEX IF NOT EXISTS idx_progress_snapshots_timestamp ON archon_progress_snapshots(timestamp);

-- Smart suggestions indexes
CREATE INDEX IF NOT EXISTS idx_suggestion_feedback_task ON archon_suggestion_feedback(task_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_feedback_user ON archon_suggestion_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_analytics_project ON archon_suggestion_analytics(project_id);

-- Comments indexes
CREATE INDEX IF NOT EXISTS idx_comments_task ON archon_comments(task_id);
CREATE INDEX IF NOT EXISTS idx_comments_user ON archon_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON archon_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_comments_created ON archon_comments(created_at);

-- Collaboration activity indexes
CREATE INDEX IF NOT EXISTS idx_collaboration_activity_project ON archon_collaboration_activity(project_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_activity_user ON archon_collaboration_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_activity_timestamp ON archon_collaboration_activity(timestamp);

-- =====================================================
-- FULL-TEXT SEARCH INDEXES
-- =====================================================

-- Comments full-text search
CREATE INDEX IF NOT EXISTS idx_comments_content_fts ON archon_comments USING gin(to_tsvector('english', content));

-- Task titles and descriptions (assuming these exist in archon_tasks)
-- These would be added if they don't exist in the base schema
-- CREATE INDEX IF NOT EXISTS idx_tasks_title_fts ON archon_tasks USING gin(to_tsvector('english', title));
-- CREATE INDEX IF NOT EXISTS idx_tasks_description_fts ON archon_tasks USING gin(to_tsvector('english', description));

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers to relevant tables
DROP TRIGGER IF EXISTS update_prioritization_factors_updated_at ON archon_prioritization_factors;
CREATE TRIGGER update_prioritization_factors_updated_at
    BEFORE UPDATE ON archon_prioritization_factors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_patterns_updated_at ON archon_user_patterns;
CREATE TRIGGER update_user_patterns_updated_at
    BEFORE UPDATE ON archon_user_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_milestones_updated_at ON archon_milestones;
CREATE TRIGGER update_milestones_updated_at
    BEFORE UPDATE ON archon_milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_comments_updated_at ON archon_comments;
CREATE TRIGGER update_comments_updated_at
    BEFORE UPDATE ON archon_comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- DATA VALIDATION CONSTRAINTS
-- =====================================================

-- Ensure valid JSON structure for arrays
ALTER TABLE archon_team_members
ADD CONSTRAINT valid_skills_json CHECK (jsonb_typeof(skills) = 'array');

ALTER TABLE archon_milestones
ADD CONSTRAINT valid_dependencies_json CHECK (jsonb_typeof(dependencies) = 'array'),
ADD CONSTRAINT valid_deliverables_json CHECK (jsonb_typeof(deliverables) = 'array');

-- =====================================================
-- INITIAL DATA SEEDING
-- =====================================================

-- Insert default prioritization factors for system use
INSERT INTO archon_prioritization_factors (
    user_id, project_id, deadline_weight, dependency_weight,
    user_pattern_weight, project_context_weight, complexity_weight
) VALUES (
    '00000000-0000-0000-0000-000000000000', -- System user
    '00000000-0000-0000-0000-000000000000', -- System project
    0.30, 0.25, 0.20, 0.15, 0.10
) ON CONFLICT DO NOTHING;

-- =====================================================
-- VIEWS FOR ANALYTICS
-- =====================================================

-- Team workload view
CREATE OR REPLACE VIEW team_workload_view AS
SELECT
    tm.team_id,
    tm.user_id,
    tm.username,
    tm.current_workload,
    tm.capacity_utilization,
    tm.availability_hours_per_week,
    COUNT(ta.id) as assigned_tasks,
    AVG(ta.estimated_hours) as avg_estimated_hours
FROM archon_team_members tm
LEFT JOIN archon_task_assignments ta ON tm.user_id = ta.assignee_id
    AND ta.assigned_at >= NOW() - INTERVAL '30 days'
GROUP BY tm.team_id, tm.user_id, tm.username, tm.current_workload,
         tm.capacity_utilization, tm.availability_hours_per_week;

-- Project progress view
CREATE OR REPLACE VIEW project_progress_view AS
SELECT
    ps.project_id,
    ps.timestamp,
    ps.total_tasks,
    ps.completed_tasks,
    ps.in_progress_tasks,
    ps.blocked_tasks,
    ps.overdue_tasks,
    ROUND(ps.completed_tasks::numeric / NULLIF(ps.total_tasks, 0) * 100, 2) as completion_percentage,
    ps.velocity_tasks_per_day,
    ps.time_spent_hours,
    ps.estimated_remaining_hours
FROM archon_progress_snapshots ps
ORDER BY ps.project_id, ps.timestamp DESC;

-- Collaboration activity summary view
CREATE OR REPLACE VIEW collaboration_summary_view AS
SELECT
    project_id,
    DATE_TRUNC('day', timestamp) as date,
    COUNT(*) as total_activities,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(CASE WHEN activity_type = 'task_updated' THEN 1 END) as task_updates,
    COUNT(CASE WHEN activity_type = 'comment_added' THEN 1 END) as comments_added,
    COUNT(CASE WHEN activity_type = 'user_joined' THEN 1 END) as users_joined,
    COUNT(CASE WHEN activity_type = 'user_left' THEN 1 END) as users_left
FROM archon_collaboration_activity
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY project_id, DATE_TRUNC('day', timestamp)
ORDER BY project_id, date DESC;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Phase 3 database schema migration completed successfully';
    RAISE NOTICE 'Created tables: archon_prioritization_factors, archon_user_patterns, archon_teams, archon_team_members, archon_task_assignments, archon_collaboration_activity, archon_task_dependencies, archon_milestones, archon_progress_snapshots, archon_suggestion_feedback, archon_suggestion_analytics, archon_comments';
    RAISE NOTICE 'Created indexes and views for optimal performance';
    RAISE NOTICE 'Added triggers for automatic timestamp updates';
END $$;
