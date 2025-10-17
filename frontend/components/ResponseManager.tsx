import React, { useState, useRef, useEffect } from 'react'
import { API_BASE } from '../utils/apiBase'
import { copyToClipboard } from '../utils/clipboardUtils'

interface Response {
  id: number
  content: string
  score: number
  grade: string
  feedback: string[]
  quality_breakdown: any
  copied: boolean
  compliance_ack: boolean
  created_at: string
  version?: number
  history?: ResponseVersion[]
}

interface ResponseVersion {
  id: number
  content: string
  version: number
  created_at: string
  edited_by?: string
}

interface ResponseManagerProps {
  responses: Response[]
  token: string
  onResponseUpdate?: (responseId: number, updatedResponse: Response) => void
}

const ResponseManager: React.FC<ResponseManagerProps> = ({ 
  responses, 
  token, 
  onResponseUpdate 
}) => {
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editContent, setEditContent] = useState('')
  const [previewMode, setPreviewMode] = useState<number | null>(null)
  const [showHistory, setShowHistory] = useState<number | null>(null)
  const [copyStatus, setCopyStatus] = useState<{ [key: number]: string }>({})
  const [loadingStates, setLoadingStates] = useState<{ [key: number]: boolean }>({})
  const [expandedResponses, setExpandedResponses] = useState<{ [key: number]: boolean }>({})
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [editContent])

  const startEditing = (response: Response) => {
    setEditingId(response.id)
    setEditContent(response.content)
    setPreviewMode(null)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditContent('')
    setPreviewMode(null)
  }

  const saveEdit = async (responseId: number) => {
    if (!editContent.trim()) return

    setLoadingStates(prev => ({ ...prev, [responseId]: true }))
    
    try {
      const response = await fetch(`${API_BASE}/api/posts/responses/${responseId}/edit`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: editContent.trim() })
      })

      if (response.ok) {
        const updatedResponse = await response.json()
        onResponseUpdate?.(responseId, updatedResponse)
        setEditingId(null)
        setEditContent('')
        setCopyStatus(prev => ({ ...prev, [responseId]: 'Saved!' }))
        setTimeout(() => {
          setCopyStatus(prev => ({ ...prev, [responseId]: '' }))
        }, 2000)
      } else {
        throw new Error('Failed to save edit')
      }
    } catch (error) {
      console.error('Error saving edit:', error)
      setCopyStatus(prev => ({ ...prev, [responseId]: 'Error saving' }))
      setTimeout(() => {
        setCopyStatus(prev => ({ ...prev, [responseId]: '' }))
      }, 3000)
    } finally {
      setLoadingStates(prev => ({ ...prev, [responseId]: false }))
    }
  }

  const copyToClipboardHandler = async (response: Response) => {
    try {
      const result = await copyToClipboard(response.content)
      
      if (result.success) {
        // Mark as copied in backend
        await fetch(`${API_BASE}/api/posts/responses/${response.id}/copied`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        setCopyStatus(prev => ({ 
          ...prev, 
          [response.id]: `Copied! (${result.method})` 
        }))
        setTimeout(() => {
          setCopyStatus(prev => ({ ...prev, [response.id]: '' }))
        }, 2000)
      } else {
        throw new Error(result.error || 'Copy failed')
      }
    } catch (error) {
      console.error('Copy error:', error)
      setCopyStatus(prev => ({ 
        ...prev, 
        [response.id]: 'Copy failed' 
      }))
      setTimeout(() => {
        setCopyStatus(prev => ({ ...prev, [response.id]: '' }))
      }, 3000)
    }
  }

  const acknowledgeCompliance = async (responseId: number) => {
    try {
      await fetch(`${API_BASE}/api/posts/responses/${responseId}/compliance`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      setCopyStatus(prev => ({ ...prev, [responseId]: 'Acknowledged' }))
      setTimeout(() => {
        setCopyStatus(prev => ({ ...prev, [responseId]: '' }))
      }, 2000)
    } catch (error) {
      console.error('Compliance ack error:', error)
    }
  }

  const loadResponseHistory = async (responseId: number) => {
    if (showHistory === responseId) {
      setShowHistory(null)
      return
    }

    try {
      const response = await fetch(`${API_BASE}/api/posts/responses/${responseId}/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const history = await response.json()
        // Update the response with history data
        // This would need to be handled by the parent component
        setShowHistory(responseId)
      }
    } catch (error) {
      console.error('Error loading history:', error)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return 'Unknown date'
    
    try {
      const date = new Date(timestamp)
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'Unknown date'
      }
      
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      return 'Unknown date'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800'
    if (score >= 60) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const getGradeColor = (grade: string) => {
    if (['A', 'A+', 'A-'].includes(grade)) return 'text-green-600'
    if (['B', 'B+', 'B-'].includes(grade)) return 'text-yellow-600'
    return 'text-red-600'
  }

  const toggleResponse = (responseId: number) => {
    setExpandedResponses(prev => ({
      ...prev,
      [responseId]: !prev[responseId]
    }))
  }

  if (!responses || responses.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 italic">No responses generated yet</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {responses.map((response) => {
        const isExpanded = expandedResponses[response.id] || false
        
        return (
          <div key={response.id} className="border rounded-lg bg-white shadow-sm">
            {/* Response Header - Always Visible */}
            <div 
              className="p-4 bg-gray-50 rounded-t-lg cursor-pointer hover:bg-gray-100 transition-colors"
              onClick={() => toggleResponse(response.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <button className="text-gray-500 hover:text-gray-700">
                    {isExpanded ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </button>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(response.score)}`}>
                    Score: {response.score || 0}
                  </span>
                  {response.grade && (
                    <span className={`text-sm font-semibold ${getGradeColor(response.grade)}`}>
                      Grade: {response.grade}
                    </span>
                  )}
                  {response.copied && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                      Previously Copied
                    </span>
                  )}
                  {!isExpanded && (
                    <span className="text-xs text-gray-500 truncate max-w-md">
                      {response.content.substring(0, 80)}...
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-400">
                    {formatTimestamp(response.created_at)}
                  </span>
                </div>
              </div>
            </div>

            {/* Response Content - Collapsible */}
            {isExpanded && (
              <div className="border-t">
                <div className="p-4">
            {editingId === response.id ? (
              <div className="space-y-3">
                <textarea
                  ref={textareaRef}
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Edit your response..."
                  rows={3}
                />
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-500">
                    {editContent.length} characters
                  </div>
                  <div className="space-x-2">
                    <button
                      onClick={cancelEditing}
                      className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => saveEdit(response.id)}
                      disabled={loadingStates[response.id] || !editContent.trim()}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                      {loadingStates[response.id] ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {response.content}
                </div>
                
                {/* Preview Mode */}
                {previewMode === response.id && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                    <div className="text-xs text-gray-600 mb-2">Reddit Preview:</div>
                    <div className="bg-white p-3 rounded border text-sm">
                      <div className="flex items-center space-x-2 mb-2">
                        <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center text-white text-xs">
                          u
                        </div>
                        <span className="text-blue-600 text-xs">your_username</span>
                        <span className="text-gray-500 text-xs">• just now</span>
                      </div>
                      <div className="whitespace-pre-wrap text-sm">
                        {response.content}
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => startEditing(response)}
                      className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => copyToClipboardHandler(response)}
                      className="px-3 py-1 text-sm bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
                    >
                      {copyStatus[response.id] || 'Copy'}
                    </button>
                  </div>
                  <div className="text-xs text-gray-500">
                    {response.content.length} chars
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Quality Feedback */}
          {response.feedback && response.feedback.length > 0 && (
            <div className="px-4 pb-4">
              <details className="text-xs">
                <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
                  Quality Feedback ({response.feedback.length} items)
                </summary>
                <div className="mt-2 space-y-1 pl-4">
                  {response.feedback.map((feedback: string, idx: number) => (
                    <div key={idx} className="flex items-start space-x-2">
                      <span className="text-gray-400 mt-0.5">•</span>
                      <span className="text-gray-600">{feedback}</span>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* Quality Breakdown */}
          {response.quality_breakdown && (
            <div className="px-4 pb-4">
              <details className="text-xs">
                <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
                  Quality Breakdown
                </summary>
                <div className="mt-2 grid grid-cols-2 md:grid-cols-5 gap-2">
                  {Object.entries(response.quality_breakdown).map(([key, value]) => (
                    <div key={key} className="text-center">
                      <div className="text-xs text-gray-500 capitalize">
                        {key.replace('_', ' ')}
                      </div>
                      <div className="text-sm font-medium">
                        {typeof value === 'number' ? `${Math.round(value)}%` : String(value)}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* Response History */}
          {showHistory === response.id && response.history && (
            <div className="px-4 pb-4 border-t bg-gray-50">
              <div className="py-3">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Version History</h4>
                <div className="space-y-2">
                  {response.history.map((version, idx) => (
                    <div key={version.id} className="text-xs bg-white p-2 rounded border">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">Version {version.version}</span>
                        <span className="text-gray-500">{formatTimestamp(version.created_at)}</span>
                      </div>
                      <div className="text-gray-600 truncate">
                        {version.content.substring(0, 100)}
                        {version.content.length > 100 && '...'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default ResponseManager