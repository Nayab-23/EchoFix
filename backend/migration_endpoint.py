"""
Add this to app.py to create a migration endpoint
"""

# Add this endpoint to app.py:

@app.route("/api/admin/run-migration", methods=["POST"])
def run_migration():
    """
    Run the community approval migration.
    This uses a workaround: we'll use the underlying connection pool.
    """
    try:
        # Read migration SQL
        with open('supabase/migrations/00005_add_community_approval.sql', 'r') as f:
            migration_sql = f.read()

        # We need to use a library that can execute raw SQL
        # Install: pip install psycopg2-binary
        import psycopg2
        from urllib.parse import urlparse

        # Parse Supabase connection details
        supabase_url = os.getenv('SUPABASE_URL')
        db_password = os.getenv('SUPABASE_DB_PASSWORD') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        # Extract project ID from URL
        project_id = supabase_url.replace('https://', '').split('.')[0]

        # Connect to Supabase Postgres
        # Format: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
        conn_string = f"postgresql://postgres.{project_id}:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # Execute migration
        cur.execute(migration_sql)
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Migration applied successfully!"
        })

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
