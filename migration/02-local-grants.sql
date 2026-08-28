SET QUOTED_IDENTIFIER ON;

-- =====================================================
-- Local Supabase Post-Setup Grants
-- =====================================================
-- Grants permissions on tables created by complete_setup.sql
-- Runs after 01-complete-setup.sql
-- =====================================================

-- Grant full access to service_role on all tables
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Grant read access to anon and authenticated
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
