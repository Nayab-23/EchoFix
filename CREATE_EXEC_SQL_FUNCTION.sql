-- First, run this SQL in Supabase Dashboard to create the exec_sql function
-- This only needs to be done once, then we can run migrations via Python

CREATE OR REPLACE FUNCTION public.exec_sql(query text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  EXECUTE query;
END;
$$;

-- Grant execute permission to service role
GRANT EXECUTE ON FUNCTION public.exec_sql(text) TO service_role;

COMMENT ON FUNCTION public.exec_sql IS 'Execute arbitrary SQL - use with caution, only via service role';
