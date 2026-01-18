'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { GitPullRequest, ExternalLink, MessageSquare, Sparkles } from 'lucide-react'

interface Insight {
  id: string
  title: string
  description: string
  status: string
  entry_count: number
  github_issue_url: string | null
  github_pr_url: string | null
  created_at: string
}

interface InsightsPanelProps {
  insights: Insight[]
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function InsightsPanel({ insights }: InsightsPanelProps) {
  const [creatingPR, setCreatingPR] = useState<string | null>(null)
  const [askingCommunity, setAskingCommunity] = useState<string | null>(null)

  const handleCreatePR = async (insightId: string) => {
    setCreatingPR(insightId)
    try {
      const response = await fetch(`${API_URL}/api/insights/${insightId}/create-pr`, {
        method: 'POST',
      })
      const data = await response.json()

      if (data.success) {
        alert(`PR created successfully! ${data.pr_url}`)
        window.location.reload() // Refresh to show new PR
      } else {
        alert(`Error: ${data.error || 'Failed to create PR'}`)
      }
    } catch (error) {
      console.error('Error creating PR:', error)
      alert('Failed to create PR. Check console for details.')
    } finally {
      setCreatingPR(null)
    }
  }

  const handleAskCommunity = async (insightId: string) => {
    setAskingCommunity(insightId)
    try {
      const response = await fetch(`${API_URL}/api/insights/${insightId}/ask-community`, {
        method: 'POST',
      })
      const data = await response.json()

      if (data.success) {
        if (data.warning) {
          alert(`${data.message}\n\nNote: ${data.warning}`)
        } else {
          alert(`Community approval requested! Reply posted at: ${data.reply_url}`)
        }
        window.location.reload()
      } else {
        alert(`Error: ${data.error || 'Failed to request community approval'}`)
      }
    } catch (error) {
      console.error('Error requesting community approval:', error)
      alert('Failed to request community approval. Check console for details.')
    } finally {
      setAskingCommunity(null)
    }
  }

  if (!insights || insights.length === 0) {
    return (
      <Card className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-8 text-center">
        <div className="flex flex-col items-center space-y-3">
          <Sparkles className="h-12 w-12 text-white/40" />
          <h3 className="text-lg font-semibold text-white">
            No Insights Generated Yet
          </h3>
          <p className="text-white/60 text-sm">
            Process some READY entries to generate AI-powered insights
          </p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-6">
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white flex items-center">
          <Sparkles className="mr-2 h-6 w-6 text-purple-400" />
          AI-Generated Insights ({insights.length})
        </h3>
        <p className="text-white/60 text-sm mt-1">
          Intelligent analysis of Reddit feedback
        </p>
      </div>

      <div className="space-y-4">
        {insights.map((insight) => (
          <Card
            key={insight.id}
            className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 transition-all duration-300"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h4 className="text-base font-semibold text-white">
                    {insight.title}
                  </h4>
                  <Badge
                    className={`text-xs ${
                      insight.status === 'PROCESSED'
                        ? 'bg-green-500/20 text-green-400 border-green-400/30'
                        : 'bg-yellow-500/20 text-yellow-400 border-yellow-400/30'
                    }`}
                  >
                    {insight.status}
                  </Badge>
                </div>

                <p className="text-sm text-white/70 mb-3">
                  {insight.description}
                </p>

                <div className="flex items-center space-x-4 text-xs text-white/50 mb-3">
                  <span className="flex items-center">
                    <MessageSquare className="mr-1 h-3 w-3" />
                    {insight.entry_count} {insight.entry_count === 1 ? 'entry' : 'entries'}
                  </span>
                  <span>
                    🕒 {new Date(insight.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-center space-x-2 flex-wrap">
                  {insight.github_issue_url && (
                    <a
                      href={insight.github_issue_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-1.5 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white/80 hover:text-white text-xs transition-all duration-300"
                    >
                      <ExternalLink className="mr-1 h-3 w-3" />
                      View Issue
                    </a>
                  )}
                  {insight.github_pr_url && (
                    <a
                      href={insight.github_pr_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-400/30 rounded-lg text-purple-300 hover:text-purple-200 text-xs transition-all duration-300"
                    >
                      <GitPullRequest className="mr-1 h-3 w-3" />
                      View PR
                    </a>
                  )}

                  {/* Create PR Button */}
                  {insight.github_issue_url && !insight.github_pr_url && (
                    <Button
                      onClick={() => handleCreatePR(insight.id)}
                      disabled={creatingPR === insight.id}
                      size="sm"
                      className="bg-purple-600/80 hover:bg-purple-600 border border-purple-400/30 text-white transition-all duration-700 ease-out hover:scale-[1.02]"
                    >
                      {creatingPR === insight.id ? 'Creating PR...' : '✅ Approve & Create PR'}
                    </Button>
                  )}

                  {/* Ask Community Button - shown after PR is created */}
                  {insight.github_pr_url && (
                    <Button
                      onClick={() => handleAskCommunity(insight.id)}
                      disabled={askingCommunity === insight.id}
                      size="sm"
                      className="bg-blue-600/80 hover:bg-blue-600 border border-blue-400/30 text-white transition-all duration-700 ease-out hover:scale-[1.02]"
                    >
                      {askingCommunity === insight.id ? 'Posting to Reddit...' : '💬 Ask Community for Approval'}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </Card>
  )
}
