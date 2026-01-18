'use client'

import React, { useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import dagre from 'dagre'
import 'reactflow/dist/style.css'
import { Card } from './ui/card'
import { Button } from './ui/button'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Task {
  id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed'
  dependencies?: string[]
}

const dagreGraph = new dagre.graphlib.Graph()
dagreGraph.setDefaultEdgeLabel(() => ({}))

const nodeWidth = 200
const nodeHeight = 80

const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  const isHorizontal = direction === 'LR'
  dagreGraph.setGraph({ rankdir: direction })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    node.targetPosition = isHorizontal ? 'left' : 'top'
    node.sourcePosition = isHorizontal ? 'right' : 'bottom'

    // We are shifting the dagre node position (anchor=center center) to the top left
    // so it matches the React Flow node anchor point (top left).
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    }

    return node
  })

  return { nodes, edges }
}

export default function DependencyGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const fetchDependencyGraph = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/dependency-graph`)
      const data = await response.json()

      if (data.tasks && data.tasks.length > 0) {
        setTasks(data.tasks)
        updateGraph(data.tasks)
      }
    } catch (error) {
      console.error('Error fetching dependency graph:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateGraph = (taskList: Task[]) => {
    const newNodes: Node[] = taskList.map((task) => ({
      id: task.id,
      data: {
        label: (
          <div className="px-3 py-2">
            <div className="font-semibold text-sm text-white truncate">{task.title}</div>
            <div className={`text-xs mt-1 ${
              task.status === 'completed' ? 'text-green-300' :
              task.status === 'in_progress' ? 'text-yellow-300' :
              'text-gray-300'
            }`}>
              {task.status === 'completed' ? '✓ Done' :
               task.status === 'in_progress' ? '⚡ In Progress' :
               '○ Pending'}
            </div>
          </div>
        ),
      },
      position: { x: 0, y: 0 },
      style: {
        background: task.status === 'completed' ? '#10b981' :
                   task.status === 'in_progress' ? '#f59e0b' :
                   '#6b7280',
        color: 'white',
        border: '2px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '12px',
        width: nodeWidth,
        backdropFilter: 'blur(10px)',
      },
    }))

    const newEdges: Edge[] = []
    taskList.forEach((task) => {
      if (task.dependencies && task.dependencies.length > 0) {
        task.dependencies.forEach((depId) => {
          newEdges.push({
            id: `${depId}-${task.id}`,
            source: depId,
            target: task.id,
            type: 'smoothstep',
            animated: task.status === 'in_progress',
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: 'rgba(255, 255, 255, 0.5)',
            },
            style: { stroke: 'rgba(255, 255, 255, 0.5)', strokeWidth: 2 },
          })
        })
      }
    })

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      newNodes,
      newEdges,
      'TB'
    )

    setNodes(layoutedNodes)
    setEdges(layoutedEdges)
  }

  const analyzeNewTask = async (taskTitle: string) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/analyze-task-dependencies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_title: taskTitle, existing_tasks: tasks }),
      })
      const data = await response.json()

      if (data.success) {
        await fetchDependencyGraph()
      }
    } catch (error) {
      console.error('Error analyzing task:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDependencyGraph()
    // Poll every 10 seconds for updates
    const interval = setInterval(fetchDependencyGraph, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Card className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-6 h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Dependency Graph</h2>
          <p className="text-white/60 text-sm">AI-powered task dependency analysis</p>
        </div>
        <Button
          onClick={fetchDependencyGraph}
          disabled={loading}
          className="bg-purple-600/80 hover:bg-purple-600 text-white"
        >
          {loading ? 'Refreshing...' : '🔄 Refresh'}
        </Button>
      </div>

      <div className="h-[calc(100%-5rem)] rounded-2xl overflow-hidden border border-white/10">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="rgba(255, 255, 255, 0.1)" gap={16} />
          <Controls className="bg-white/10 backdrop-blur-xl border border-white/20" />
          <MiniMap
            className="bg-white/10 backdrop-blur-xl border border-white/20"
            nodeColor={(node) => {
              const nodeData = tasks.find((t) => t.id === node.id)
              if (!nodeData) return '#6b7280'
              return nodeData.status === 'completed' ? '#10b981' :
                     nodeData.status === 'in_progress' ? '#f59e0b' :
                     '#6b7280'
            }}
          />
        </ReactFlow>
      </div>

      {tasks.length === 0 && !loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white/60">
            <p className="text-lg">No tasks yet</p>
            <p className="text-sm mt-2">Mark insights as in_progress to build the graph</p>
          </div>
        </div>
      )}
    </Card>
  )
}
