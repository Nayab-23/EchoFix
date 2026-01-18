interface RedditEntry {
  id: string
  reddit_url: string
  title: string
  author: string
  score: number
  status: string
  created_at: string
  last_score_check_at: string | null
  github_issue_url: string | null
  github_pr_url: string | null
  plan_path: string | null
}

interface RedditEntriesTableProps {
  entries: RedditEntry[]
  onRefresh: () => void
}

export default function RedditEntriesTable({ entries, onRefresh }: RedditEntriesTableProps) {
  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'PENDING':
        return 'bg-gray-100 text-gray-800'
      case 'READY':
        return 'bg-yellow-100 text-yellow-800'
      case 'PROCESSING':
        return 'bg-blue-100 text-blue-800'
      case 'PROCESSED':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  if (!entries || entries.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-12 border border-gray-200 text-center">
        <p className="text-gray-500">No Reddit entries found. Try ingesting some data!</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Post
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Score
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Workflow
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {entries.map((entry) => (
              <tr key={entry.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex flex-col">
                    <a
                      href={entry.reddit_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-blue-600 hover:text-blue-800 line-clamp-2"
                    >
                      {entry.title}
                    </a>
                    <span className="text-xs text-gray-500 mt-1">
                      by u/{entry.author}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-semibold text-gray-900">
                    {entry.score}
                  </div>
                  <div className="text-xs text-gray-500">
                    {entry.last_score_check_at
                      ? `Checked ${new Date(entry.last_score_check_at).toLocaleTimeString()}`
                      : 'Not checked'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                      entry.status
                    )}`}
                  >
                    {entry.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-col space-y-1">
                    {entry.plan_path && (
                      <span className="text-xs text-green-600">
                        📄 Plan generated
                      </span>
                    )}
                    {entry.github_issue_url && (
                      <a
                        href={entry.github_issue_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        🔗 Issue
                      </a>
                    )}
                    {entry.github_pr_url && (
                      <a
                        href={entry.github_pr_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-purple-600 hover:text-purple-800"
                      >
                        🔀 PR
                      </a>
                    )}
                    {!entry.plan_path &&
                      !entry.github_issue_url &&
                      !entry.github_pr_url && (
                        <span className="text-xs text-gray-400">
                          No workflow yet
                        </span>
                      )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                  {formatDate(entry.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
