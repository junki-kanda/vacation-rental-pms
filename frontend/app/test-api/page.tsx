'use client'

import { useState, useEffect } from 'react'

export default function TestAPIPage() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')
  const [csvFiles, setCsvFiles] = useState<any[]>([])
  const [selectedFile, setSelectedFile] = useState<string>('')
  const [processResult, setProcessResult] = useState<any>(null)
  const [syncStatus, setSyncStatus] = useState<any>(null)

  useEffect(() => {
    checkAPI()
    fetchCSVFiles()
  }, [])

  const checkAPI = async () => {
    try {
      const res = await fetch('http://localhost:8000/')
      const data = await res.json()
      setApiStatus(`API Connected: ${data.message}`)
    } catch (error) {
      setApiStatus('API Connection Failed')
    }
  }

  const fetchCSVFiles = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/sync/list-csv')
      const data = await res.json()
      setCsvFiles(data.files || [])
      if (data.files && data.files.length > 0) {
        setSelectedFile(data.files[0].filename)
      }
    } catch (error) {
      console.error('Failed to fetch CSV files:', error)
    }
  }

  const processCSV = async () => {
    if (!selectedFile) return

    try {
      const res = await fetch('http://localhost:8000/api/sync/process-local', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: selectedFile })
      })
      const data = await res.json()
      setProcessResult(data)
      
      // Check status after 2 seconds
      if (data.sync_id) {
        setTimeout(() => checkSyncStatus(data.sync_id), 2000)
      }
    } catch (error) {
      console.error('Failed to process CSV:', error)
      setProcessResult({ error: error.message })
    }
  }

  const checkSyncStatus = async (syncId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/sync/status/${syncId}`)
      const data = await res.json()
      setSyncStatus(data)
    } catch (error) {
      console.error('Failed to check sync status:', error)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Connection Test</h1>
      
      <div className="mb-4 p-4 bg-gray-100 rounded">
        <p className="font-semibold">API Status:</p>
        <p>{apiStatus}</p>
      </div>

      <div className="mb-4 p-4 bg-gray-100 rounded">
        <p className="font-semibold mb-2">CSV Files:</p>
        {csvFiles.length > 0 ? (
          <select 
            value={selectedFile} 
            onChange={(e) => setSelectedFile(e.target.value)}
            className="w-full p-2 border rounded mb-2"
          >
            {csvFiles.map((file) => (
              <option key={file.filename} value={file.filename}>
                {file.filename} ({(file.size / 1024).toFixed(2)} KB)
              </option>
            ))}
          </select>
        ) : (
          <p>No CSV files found</p>
        )}
        
        {selectedFile && (
          <button 
            onClick={processCSV}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Process Selected CSV
          </button>
        )}
      </div>

      {processResult && (
        <div className="mb-4 p-4 bg-gray-100 rounded">
          <p className="font-semibold mb-2">Process Result:</p>
          <pre className="text-sm">{JSON.stringify(processResult, null, 2)}</pre>
        </div>
      )}

      {syncStatus && (
        <div className="mb-4 p-4 bg-gray-100 rounded">
          <p className="font-semibold mb-2">Sync Status:</p>
          <pre className="text-sm">{JSON.stringify(syncStatus, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}