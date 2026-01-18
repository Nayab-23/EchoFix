interface PipelineStatusProps {
  stats: {
    total: number
    pending: number
    ready: number
    processing: number
    processed: number
    insights: number
  }
}

export default function PipelineStatus({ stats }: PipelineStatusProps) {
  const statusCards = [
    {
      label: 'PENDING',
      count: stats.pending,
      color: 'bg-gray-100 text-gray-800',
      description: 'Below score threshold',
    },
    {
      label: 'READY',
      count: stats.ready,
      color: 'bg-yellow-100 text-yellow-800',
      description: 'Score threshold met',
    },
    {
      label: 'PROCESSING',
      count: stats.processing,
      color: 'bg-blue-100 text-blue-800',
      description: 'Generating plan/issue/PR',
    },
    {
      label: 'PROCESSED',
      count: stats.processed,
      color: 'bg-green-100 text-green-800',
      description: 'Issue/PR created',
    },
    {
      label: 'INSIGHTS',
      count: stats.insights,
      color: 'bg-purple-100 text-purple-800',
      description: 'Generated insights',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      {statusCards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-lg shadow-sm p-6 border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className={`px-2 py-1 rounded text-xs font-semibold ${card.color}`}>
              {card.label}
            </span>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {card.count}
          </div>
          <div className="text-xs text-gray-500">
            {card.description}
          </div>
        </div>
      ))}
    </div>
  )
}
