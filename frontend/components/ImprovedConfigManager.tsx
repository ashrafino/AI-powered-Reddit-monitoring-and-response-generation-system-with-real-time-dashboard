import React, { useState } from 'react'
import { apiClient, APIClientError } from '../utils/apiBase'

interface Config {
  id: number
  client_id: number
  reddit_subreddits: string
  keywords: string
  is_active: boolean
  reddit_username?: string
}

interface ImprovedConfigManagerProps {
  configs: Config[]
  onUpdate: () => void
}

export default function ImprovedConfigManager({ configs, onUpdate }: ImprovedConfigManagerProps) {
  const [isAdding, setIsAdding] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  
  // Form state
  const [clientId, setClientId] = useState('')
  const [subreddits, setSubreddits] = useState('')
  const [keywords, setKeywords] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [redditUsername, setRedditUsername] = useState('')

  const resetForm = () => {
    setClientId('')
    setSubreddits('')
    setKeywords('')
    setIsActive(true)
    setRedditUsername('')
    setEditingId(null)
    setIsAdding(false)
  }

  const startEdit = (config: Config) => {
    setClientId(config.client_id.toString())
    setSubreddits(config.reddit_subreddits)
    setKeywords(config.keywords)
    setIsActive(config.is_active)
    setRedditUsername(config.reddit_username || '')
    setEditingId(config.id)
    setIsAdding(false)
  }

  const handleSave = async () => {
    try {
      const data = {
        client_id: Number(clientId),
        reddit_subreddits: subreddits,
        keywords: keywords,
        is_active: isActive,
        reddit_username: redditUsername || null,
      }

      if (editingId) {
        await apiClient.put(`/api/configs/${editingId}`, data)
      } else {
        await apiClient.post('/api/configs', data)
      }

      resetForm()
      onUpdate()
      alert('✓ Configuration saved successfully!')
    } catch (error) {
      console.error('Save error:', error)
      if (error instanceof APIClientError) {
        alert(`Failed to save: ${error.message}`)
      } else {
        alert('Error saving configuration')
      }
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this configuration? This cannot be undone.')) return

    try {
      await apiClient.delete(`/api/configs/${id}`)
      onUpdate()
      alert('✓ Configuration deleted')
    } catch (error) {
      console.error('Delete error:', error)
      alert('Error deleting configuration')
    }
  }

  const toggleActive = async (config: Config) => {
    try {
      await apiClient.put(`/api/configs/${config.id}`, {
        ...config,
        is_active: !config.is_active,
      })
      onUpdate()
    } catch (error) {
      console.error('Toggle error:', error)
      alert('Error updating configuration')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Scan Configurations</h2>
          <p className="text-sm text-gray-600 mt-1">
            Configure which subreddits and keywords to monitor. Scans run automatically every 5 minutes.
          </p>
        </div>
        <button
          onClick={() => setIsAdding(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Add Configuration
        </button>
      </div>

      {/* Add/Edit Form */}
      {(isAdding || editingId) && (
        <div className="bg-white border-2 border-blue-200 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold mb-4">
            {editingId ? 'Edit Configuration' : 'New Configuration'}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Client ID *
              </label>
              <input
                type="number"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subreddits * <span className="text-gray-500 font-normal">(comma-separated)</span>
              </label>
              <input
                type="text"
                value={subreddits}
                onChange={(e) => setSubreddits(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="AskReddit, learnprogramming, technology"
              />
              <p className="text-xs text-gray-500 mt-1">
                Example: AskReddit, learnprogramming, technology
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Keywords * <span className="text-gray-500 font-normal">(comma-separated)</span>
              </label>
              <textarea
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="how to, tutorial, help, question, beginner"
              />
              <p className="text-xs text-gray-500 mt-1">
                Posts containing any of these keywords will be matched
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reddit Username <span className="text-gray-500 font-normal">(optional)</span>
              </label>
              <input
                type="text"
                value={redditUsername}
                onChange={(e) => setRedditUsername(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="your_reddit_username"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_active" className="ml-2 text-sm font-medium text-gray-700">
                Active (scan this configuration)
              </label>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleSave}
              disabled={!clientId || !subreddits || !keywords}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {editingId ? 'Update' : 'Create'}
            </button>
            <button
              onClick={resetForm}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Configs List */}
      <div className="space-y-3">
        {configs.length === 0 ? (
          <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
            <p className="text-gray-600">No configurations yet. Add one to start monitoring Reddit!</p>
          </div>
        ) : (
          configs.map((config) => (
            <div
              key={config.id}
              className={`bg-white border rounded-xl p-4 shadow-sm transition-all ${
                config.is_active ? 'border-green-200 bg-green-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-gray-500">
                      Config #{config.id}
                    </span>
                    <span className="text-sm text-gray-500">•</span>
                    <span className="text-sm text-gray-500">
                      Client {config.client_id}
                    </span>
                    <button
                      onClick={() => toggleActive(config)}
                      className={`px-2 py-1 text-xs rounded-full font-medium transition-colors ${
                        config.is_active
                          ? 'bg-green-100 text-green-700 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {config.is_active ? '● Active' : '○ Inactive'}
                    </button>
                  </div>

                  <div className="space-y-2">
                    <div>
                      <span className="text-xs font-medium text-gray-500">Subreddits:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {config.reddit_subreddits.split(',').map((sub, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded"
                          >
                            r/{sub.trim()}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="text-xs font-medium text-gray-500">Keywords:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {config.keywords.split(',').slice(0, 10).map((kw, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded"
                          >
                            {kw.trim()}
                          </span>
                        ))}
                        {config.keywords.split(',').length > 10 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                            +{config.keywords.split(',').length - 10} more
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => startEdit(config)}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(config.id)}
                    className="px-3 py-1 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <h4 className="font-medium text-blue-900 mb-2">ℹ️ How it works</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Scans run automatically every 5 minutes for all active configurations</li>
          <li>• Each scan searches your specified subreddits for posts matching your keywords</li>
          <li>• AI generates 3 response suggestions for each matched post</li>
          <li>• You can have multiple configurations for different topics/clients</li>
          <li>• Toggle "Active" to pause/resume scanning for a configuration</li>
        </ul>
      </div>
    </div>
  )
}
