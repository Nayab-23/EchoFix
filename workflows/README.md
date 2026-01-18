# n8n Workflows for EchoFix

This directory contains n8n workflow definitions for orchestrating the EchoFix pipeline.

## Workflows

### 1. Scheduled Ingestion (`scheduled-ingestion.json`)
Automatically ingests Reddit seed threads on a schedule, refreshes scores, and generates insights locally.

**Trigger**: Cron (every 6 hours)
**Steps**:
1. Ingest Reddit seed threads via `/api/reddit/ingest-seed` (JSON mode, no OAuth)
2. Check if successful
3. Refresh scores via `/api/reddit/refresh-scores` (PENDING → READY)
4. Generate insights via `/api/insights/generate`
5. Fetch insights via `/api/insights`
6. Log results

Optional:
- Use `POST /api/pipeline/auto-process` to run refresh → insights → Gemini → GitHub in one call.

**Configuration**:
- Set `REDDIT_SEED_THREAD_URLS` in backend `.env` (comma-separated URLs)
- Adjust schedule in the "Schedule Every 6 Hours" node
- No Reddit OAuth credentials required!

### 2. Approval Workflow (`approval-workflow.json`)
Handles human approval → Gemini analysis → GitHub issue creation.

**Trigger**: Webhook at `/webhook/approve-insight`
**Steps**:
1. Receive approval webhook
2. Check if action is "approve" or "reject"
3. If approved:
   - Update insight status to approved
   - Analyze with Gemini
   - Create GitHub issue
   - Return success response
4. If rejected:
   - Mark insight as closed

**Webhook Payload Example**:
```json
{
  "insight_id": "uuid-here",
  "action": "approve",
  "user_id": "uuid-here",
  "comment": "Looks good, create issue"
}
```

## Setup Instructions

### 1. Start n8n with Docker Compose

```bash
cd workflows

# Start n8n
docker-compose up -d

# Check logs
docker-compose logs -f n8n
```

n8n will be available at: http://localhost:5678

### 2. Import Workflows

1. Open n8n UI at http://localhost:5678
2. Click "Add Workflow" → "Import from File"
3. Select `scheduled-ingestion.json`
4. Activate the workflow (toggle in top-right)
5. Repeat for `approval-workflow.json`

### 3. Configure Webhook URLs

For the approval workflow:
1. Open the workflow in n8n
2. Click on the "Webhook" node
3. Note the webhook URL (e.g., `http://localhost:5678/webhook/approve-insight`)
4. Use this URL in the frontend approve button

### 4. Test Workflows

#### Test Scheduled Ingestion:
```bash
# Manually trigger in n8n UI, or wait for next scheduled run
# Check backend logs for ingestion activity
```

#### Test Approval Workflow:
```bash
# Send test webhook
curl -X POST http://localhost:5678/webhook/approve-insight \\
  -H "Content-Type: application/json" \\
  -d '{
    "insight_id": "your-insight-id",
    "action": "approve",
    "user_id": "your-user-id"
  }'
```

## Environment Variables

Set these in `docker-compose.yml` or `.env` file:

```bash
# Encryption key for n8n (generate random string)
N8N_ENCRYPTION_KEY=your-random-encryption-key-here

# Timezone
GENERIC_TIMEZONE=America/Los_Angeles

# Backend URL (from n8n container perspective)
ECHOFIX_BACKEND_URL=http://host.docker.internal:8000
```

## Accessing Backend from n8n

When n8n runs in Docker and your backend runs on host:
- Use `http://host.docker.internal:8000` (Mac/Windows)
- Use `http://172.17.0.1:8000` (Linux)

If both run in Docker Compose, use service name:
- Use `http://echofix-backend:8000`

## Custom Workflows

You can create additional workflows:

### Example: Analyze Pending Insights
**Trigger**: Cron (daily)
**Steps**:
1. GET `/api/insights?status=pending&limit=10`
2. For each insight:
   - POST `/api/gemini/analyze/{insight_id}`
3. Notify team of new analyzed insights

### Example: Weekly Summary
**Trigger**: Cron (weekly)
**Steps**:
1. GET `/api/stats`
2. Format statistics
3. Send email/Slack notification

## Debugging

### View n8n Logs:
```bash
docker-compose logs -f n8n
```

### View Execution History:
- Open n8n UI
- Click "Executions" in sidebar
- View past workflow runs with detailed logs

### Common Issues:

**Cannot connect to backend**:
- Check `host.docker.internal` resolves
- Ensure backend is running on port 8000
- Check firewall rules

**Webhook not receiving requests**:
- Verify webhook URL is correct
- Check n8n is running and accessible
- Ensure workflow is active

**Timeout errors**:
- Increase timeout in HTTP Request nodes
- Check backend response times
- Optimize Gemini API calls

## Production Considerations

For production deployment:

1. **Enable Authentication**:
   - Set `N8N_BASIC_AUTH_ACTIVE=true`
   - Set `N8N_BASIC_AUTH_USER` and `N8N_BASIC_AUTH_PASSWORD`

2. **Use HTTPS**:
   - Set `N8N_PROTOCOL=https`
   - Configure reverse proxy (nginx/Caddy)

3. **Persistent Storage**:
   - Ensure `n8n_data` volume is backed up
   - Consider external database for workflow data

4. **Monitoring**:
   - Monitor workflow executions
   - Set up alerts for failures
   - Track execution metrics

## Resources

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Workflow Examples](https://n8n.io/workflows)
- [HTTP Request Node Docs](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- [Webhook Node Docs](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
