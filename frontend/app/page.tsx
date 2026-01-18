'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  MessageSquare,
  TrendingUp,
  GitPullRequest,
  CheckCircle,
  Search,
  Bell,
  Settings,
  Play,
  RefreshCw,
  Clock,
  Zap,
  Github,
  Sparkles,
  Network,
} from 'lucide-react'
import InsightsPanel from '@/components/InsightsPanel'
import RedditEntriesTable from '@/components/RedditEntriesTable'
import ControlPanel from '@/components/ControlPanel'
import DependencyGraph from '@/components/DependencyGraph'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function Home() {
  const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'ready' | 'processing' | 'processed'>('all')
  const [activeView, setActiveView] = useState<'dashboard' | 'dependencies'>('dashboard')

  // Fetch health status
  const { data: healthData } = useSWR(`${API_URL}/health`, fetcher, {
    refreshInterval: 10000,
  })

  // Fetch statistics
  const { data: statsData, mutate: mutateStats } = useSWR(`${API_URL}/api/stats`, fetcher, {
    refreshInterval: 5000,
  })

  // Fetch Reddit entries
  const { data: entriesData, mutate: mutateEntries } = useSWR(
    `${API_URL}/api/reddit/entries`,
    fetcher,
    {
      refreshInterval: 5000,
    }
  )

  // Fetch insights
  const { data: insightsData, mutate: mutateInsights } = useSWR(
    `${API_URL}/api/insights`,
    fetcher,
    {
      refreshInterval: 10000,
    }
  )

  const handleRefresh = () => {
    mutateStats()
    mutateEntries()
    mutateInsights()
  }

  const isHealthy = healthData?.status === 'healthy'
  const entries = entriesData?.entries || []
  const insights = insightsData?.insights || []

  // Filter entries by status
  const filteredEntries = activeTab === 'all'
    ? entries
    : entries.filter((entry: any) => entry.status?.toLowerCase() === activeTab)

  // Calculate stats
  const stats = {
    total: entries.length,
    pending: entries.filter((e: any) => e.status === 'PENDING').length,
    ready: entries.filter((e: any) => e.status === 'READY').length,
    processing: entries.filter((e: any) => e.status === 'PROCESSING').length,
    processed: entries.filter((e: any) => e.status === 'PROCESSED').length,
    insights: insights.length,
  }

  return (
    <div className="h-screen relative overflow-hidden">
      {/* Dark gradient background with animated mesh */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950" />
      <div className="absolute inset-0 bg-gradient-to-tr from-purple-950/40 via-blue-950/20 to-violet-950/40" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />

      <div className="relative z-10 p-6 grid grid-cols-12 gap-6 h-screen">
        {/* Left Sidebar */}
        <Card className="col-span-2 backdrop-blur-2xl bg-white/5 border border-white/10 shadow-2xl shadow-purple-900/20 rounded-3xl p-6 h-fit flex flex-col">
          <div className="space-y-6">
            {/* Logo */}
            <div className="text-center">
              <h1 className="text-2xl font-bold text-white">EchoFix</h1>
              <p className="text-white/60 text-sm">Reddit→Engineering</p>
            </div>

            {/* Main Navigation */}
            <div>
              <h4 className="text-white/80 text-sm font-semibold uppercase tracking-wider mb-3">Views</h4>
              <nav className="space-y-2">
                {[
                  { icon: MessageSquare, label: "Dashboard", view: 'dashboard' as const },
                  { icon: Network, label: "Dependencies", view: 'dependencies' as const },
                ].map((item, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    onClick={() => setActiveView(item.view)}
                    className={`w-full justify-start text-base text-white/80 hover:bg-white/10 hover:text-white transition-all duration-700 ease-out hover:scale-[1.02] h-11 ${
                      activeView === item.view ? "bg-white/20 text-white border border-white/30" : ""
                    }`}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.label}
                  </Button>
                ))}
              </nav>
            </div>

            {/* Pipeline Tools */}
            <div>
              <h4 className="text-white/80 text-sm font-semibold uppercase tracking-wider mb-3">Pipeline</h4>
              <nav className="space-y-2">
                {[
                  { icon: RefreshCw, label: "Refresh Scores" },
                  { icon: Play, label: "Auto Process" },
                  { icon: Github, label: "GitHub Issues" },
                ].map((item, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    className="w-full justify-start text-base text-white/80 hover:bg-white/10 hover:text-white transition-all duration-700 ease-out hover:scale-[1.02] h-11"
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.label}
                  </Button>
                ))}
              </nav>
            </div>

            {/* Settings */}
            <div>
              <h4 className="text-white/80 text-sm font-semibold uppercase tracking-wider mb-3">Settings</h4>
              <nav className="space-y-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-base text-white/80 hover:bg-white/10 hover:text-white transition-all duration-700 ease-out hover:scale-[1.02] h-11"
                >
                  <Settings className="mr-3 h-5 w-5" />
                  Configuration
                </Button>
              </nav>
            </div>
          </div>

          {/* Status Indicator */}
          <div className="flex-shrink-0 space-y-4 pt-4 mt-4 border-t border-white/10">
            <Card className={`backdrop-blur-xl ${isHealthy ? 'bg-gradient-to-br from-green-500/20 to-blue-500/20 border-green-400/30' : 'bg-gradient-to-br from-red-500/20 to-orange-500/20 border-red-400/30'} border rounded-2xl p-4`}>
              <div className="text-center space-y-2">
                <div className="flex justify-center">
                  <Zap className={`h-6 w-6 ${isHealthy ? 'text-green-400' : 'text-red-400'}`} />
                </div>
                <div>
                  <h4 className="text-white font-semibold text-sm">{isHealthy ? 'System Online' : 'System Offline'}</h4>
                  <p className="text-white/70 text-xs">Pipeline Status</p>
                </div>
              </div>
            </Card>
          </div>
        </Card>

        {/* Main Content Area */}
        <div className="col-span-10 space-y-6 h-screen overflow-y-auto">
          {/* Header Card */}
          <Card className="backdrop-blur-2xl bg-white/5 border border-white/10 shadow-xl shadow-purple-900/10 rounded-3xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold text-white">Dashboard 🚀</h2>
                <p className="text-white/60">Reddit Feedback → Engineering Pipeline</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/40 h-4 w-4" />
                  <Input
                    placeholder="Search entries..."
                    className="pl-10 bg-white/5 border border-white/20 rounded-xl text-white placeholder:text-white/40 focus:border-white/40 focus:bg-white/10"
                  />
                </div>
                <Button size="icon" variant="ghost" className="text-white/80 hover:bg-white/10 hover:text-white">
                  <Bell className="h-5 w-5" />
                </Button>
                <Button
                  onClick={handleRefresh}
                  className="bg-white/10 hover:bg-white/20 border border-white/20 hover:border-white/30 text-white transition-all duration-700 ease-out hover:scale-[1.02]"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </div>
          </Card>

          {/* Stats Cards */}
          <div className="grid grid-cols-4 gap-6">
            {[
              { title: "Total Entries", value: stats.total.toString(), change: "All entries", icon: MessageSquare, color: "text-blue-400" },
              { title: "Ready to Process", value: stats.ready.toString(), change: `${stats.pending} pending`, icon: Clock, color: "text-yellow-400" },
              { title: "Insights Generated", value: stats.insights.toString(), change: "AI analyzed", icon: Sparkles, color: "text-purple-400" },
              { title: "Processed", value: stats.processed.toString(), change: "Complete", icon: CheckCircle, color: "text-green-400" },
            ].map((stat, index) => (
              <Card
                key={index}
                className="backdrop-blur-2xl bg-white/5 border border-white/10 shadow-xl shadow-purple-900/10 rounded-3xl p-6 transition-all duration-700 ease-out hover:scale-[1.02] hover:bg-white/10"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white/60 text-sm">{stat.title}</p>
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                    <p className={`text-sm ${stat.color}`}>{stat.change}</p>
                  </div>
                  <stat.icon className={`h-8 w-8 ${stat.color}`} />
                </div>
              </Card>
            ))}
          </div>

          {/* Dashboard View */}
          {activeView === 'dashboard' && (
            <>
              {/* Control Panel */}
              <Card className="backdrop-blur-2xl bg-white/5 border border-white/10 shadow-xl shadow-purple-900/10 rounded-3xl p-6">
                <ControlPanel onRefresh={handleRefresh} />
              </Card>

              {/* Insights Panel */}
              <InsightsPanel insights={insights} />

              {/* Reddit Entries Table */}
          <Card className="backdrop-blur-2xl bg-white/5 border border-white/10 shadow-xl shadow-purple-900/10 rounded-3xl p-6">
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-white mb-4">Reddit Entries 📊</h3>

              {/* Status Tabs */}
              <div className="flex space-x-2">
                {(['all', 'pending', 'ready', 'processing', 'processed'] as const).map((tab) => (
                  <Button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    variant="ghost"
                    size="sm"
                    className={`capitalize ${
                      activeTab === tab
                        ? 'bg-white/20 text-white border border-white/30'
                        : 'text-white/60 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {tab}
                    {tab !== 'all' && (
                      <Badge className="ml-2 bg-white/10 text-white border-white/20">
                        {stats[tab]}
                      </Badge>
                    )}
                  </Button>
                ))}
              </div>
            </div>

            <RedditEntriesTable entries={filteredEntries} onRefresh={handleRefresh} />
          </Card>
            </>
          )}

          {/* Dependency Graph View */}
          {activeView === 'dependencies' && (
            <DependencyGraph />
          )}
        </div>
      </div>

    </div>
  )
}
