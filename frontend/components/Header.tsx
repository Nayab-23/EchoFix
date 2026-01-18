interface HeaderProps {
  isHealthy: boolean
  onRefresh: () => void
}

export default function Header({ isHealthy, onRefresh }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">
              EchoFix
            </h1>
            <span className="text-sm text-gray-500">
              Reddit → Engineering Pipeline
            </span>
          </div>

          <div className="flex items-center space-x-4">
            {/* Health Status */}
            <div className="flex items-center space-x-2">
              <div
                className={`h-2 w-2 rounded-full ${
                  isHealthy ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600">
                {isHealthy ? 'Healthy' : 'Unhealthy'}
              </span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
            >
              Refresh
            </button>

            {/* n8n Link */}
            <a
              href="http://localhost:5678"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1 text-sm bg-purple-500 text-white rounded hover:bg-purple-600 transition"
            >
              Open n8n
            </a>
          </div>
        </div>
      </div>
    </header>
  )
}
