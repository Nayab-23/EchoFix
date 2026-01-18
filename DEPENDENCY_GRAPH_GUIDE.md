# Dependency Graph Feature - Quick Guide

## What It Does

Automatically analyzes task dependencies using AI (Gemini/GPT) and visualizes them in a beautiful interactive graph.

## How It Works

1. **New Tab**: Click "Dependency Graph" in the sidebar
2. **AI Analysis**: When insights are marked as "in_progress", AI analyzes dependencies
3. **Visualization**: See tasks laid out with arrows showing dependencies
4. **Color Coding**:
   - 🟢 Green = Completed
   - 🟡 Yellow = In Progress
   - ⚫ Gray = Pending

## Features

✅ **Auto-layout** using Dagre algorithm
✅ **AI-powered** dependency detection (Gemini → OpenAI fallback)
✅ **Real-time updates** every 10 seconds
✅ **Interactive** - zoom, pan, drag nodes
✅ **Mini-map** for navigation

## API Endpoints

### GET /api/dependency-graph
Returns all tasks with their dependencies:
```json
{
  "tasks": [
    {
      "id": "task_1",
      "title": "Setup authentication",
      "status": "completed",
      "dependencies": []
    },
    {
      "id": "task_2",
      "title": "Add user profiles",
      "status": "in_progress",
      "dependencies": ["task_1"]
    }
  ]
}
```

### POST /api/analyze-task-dependencies
Analyzes a new task:
```json
{
  "task_title": "Add dark mode",
  "existing_tasks": [...]
}
```

Returns:
```json
{
  "success": true,
  "task": {
    "id": "task_3",
    "title": "Add dark mode",
    "status": "pending",
    "dependencies": ["task_2"]
  }
}
```

### POST /api/update-task-status
Updates task status:
```json
{
  "task_id": "task_2",
  "status": "completed"
}
```

## AI Dependency Analysis

The AI considers:
- **Logical ordering** - What must be done first?
- **Implementation dependencies** - Does this need another feature?
- **Code dependencies** - Does this modify files from another task?

**Example**:
- Task: "Add user profiles"
- AI finds dependency on: "Setup authentication"
- Reason: Can't have profiles without auth

## Testing

1. Go to http://localhost:3000
2. Click "Dependency Graph" tab
3. Currently empty - will populate as you create insights
4. Manually test with:
   ```bash
   curl -X POST http://localhost:8000/api/analyze-task-dependencies \
     -H "Content-Type: application/json" \
     -d '{"task_title": "Add dark mode", "existing_tasks": []}'
   ```

## Future Integration

To auto-populate from insights, add this to the PR creation endpoint:

```python
# After creating PR
await fetch(`${API_URL}/api/analyze-task-dependencies`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    task_title: insight.issue_spec.title,
    existing_tasks: dependency_tasks
  })
})
```

## Libraries Used

- **React Flow** - Interactive node-based graph UI
- **Dagre** - Automatic graph layout algorithm
- **Tailwind** - Styling with frosted glass effects

## Customization

Edit colors in [DependencyGraph.tsx](frontend/components/DependencyGraph.tsx):

```typescript
style: {
  background: task.status === 'completed' ? '#10b981' :  // Green
             task.status === 'in_progress' ? '#f59e0b' : // Yellow
             '#6b7280',  // Gray
}
```

## Demo Workflow

1. **Create insight** - "Add dark mode"
2. **System sends to AI** - Analyzes dependencies
3. **AI responds** - Depends on "Setup CSS variables"
4. **Graph updates** - Shows both tasks with arrow
5. **Mark as done** - Node turns green
6. **Next task** - Can now work on dependent tasks

---

**Status**: ✅ Ready to use! Click "Dependency Graph" tab to see it.
