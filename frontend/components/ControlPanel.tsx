'use client'

import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ControlPanelProps {
  onRefresh: () => void
}

export default function ControlPanel({ onRefresh }: ControlPanelProps) {
  const [loading, setLoading] = useState<string | null>(null)
  const [redditUrl, setRedditUrl] = useState('')

  const handleAction = async (endpoint: string, action: string, body?: any) => {
    setLoading(action)
    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: body ? { 'Content-Type': 'application/json' } : {},
        body: body ? JSON.stringify(body) : undefined,
      })
      const data = await response.json()
      console.log(`${action} result:`, data)
      onRefresh()
      alert(`${action} completed! Check console for details.`)
    } catch (error) {
      console.error(`${action} error:`, error)
      alert(`${action} failed. Check console for details.`)
    } finally {
      setLoading(null)
    }
  }

  const handleIngestUrl = async () => {
    if (!redditUrl.trim()) {
      alert('Please enter a Reddit URL')
      return
    }
    await handleAction('/api/reddit/ingest-url', 'Ingest URL', { url: redditUrl })
    setRedditUrl('')
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-8">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Controls</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Ingest Reddit URL */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">
            Ingest Reddit Post
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={redditUrl}
              onChange={(e) => setRedditUrl(e.target.value)}
              placeholder="https://reddit.com/r/..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              onClick={handleIngestUrl}
              disabled={loading === 'Ingest URL'}
              className="px-4 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:bg-gray-400 transition"
            >
              {loading === 'Ingest URL' ? 'Loading...' : 'Ingest'}
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleAction('/api/reddit/ingest-seed', 'Ingest Seed Data')}
            disabled={loading === 'Ingest Seed Data'}
            className="px-4 py-2 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:bg-gray-400 transition"
          >
            {loading === 'Ingest Seed Data' ? '...' : 'Load Demo Data'}
          </button>

          <button
            onClick={() => handleAction('/api/reddit/refresh-scores', 'Refresh Scores')}
            disabled={loading === 'Refresh Scores'}
            className="px-4 py-2 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600 disabled:bg-gray-400 transition"
          >
            {loading === 'Refresh Scores' ? '...' : 'Refresh Scores'}
          </button>

          <button
            onClick={() => handleAction('/api/pipeline/auto-process-ready', 'Auto Process')}
            disabled={loading === 'Auto Process'}
            className="px-4 py-2 bg-purple-500 text-white rounded text-sm hover:bg-purple-600 disabled:bg-gray-400 transition"
          >
            {loading === 'Auto Process' ? '...' : 'Process Ready'}
          </button>

          <button
            onClick={() => handleAction('/api/insights/generate', 'Generate Insights')}
            disabled={loading === 'Generate Insights'}
            className="px-4 py-2 bg-indigo-500 text-white rounded text-sm hover:bg-indigo-600 disabled:bg-gray-400 transition"
          >
            {loading === 'Generate Insights' ? '...' : 'Gen Insights'}
          </button>
        </div>
      </div>

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
        <strong>Pipeline Flow:</strong> Ingest → Wait for upvotes → Refresh Scores (marks READY when MIN_SCORE met) →
        Process Ready (generates plan/issue/PR) → PROCESSED
      </div>

      {/* Clear All Data Button */}
      <div className="mt-4">
        <button
          onClick={async () => {
            if (confirm('⚠️ Delete ALL entries and insights? This cannot be undone!')) {
              await handleAction('/api/admin/clear-all', 'Clear All Data')
            }
          }}
          disabled={loading === 'Clear All Data'}
          className="w-full px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:bg-gray-400 transition"
        >
          {loading === 'Clear All Data' ? 'Clearing...' : '🗑️ Clear All Data'}
        </button>
      </div>
    </div>
  )
}
