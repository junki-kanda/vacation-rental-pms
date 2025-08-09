'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { syncApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Upload, CheckCircle, XCircle, AlertCircle, FileText, RefreshCw, Server } from 'lucide-react';

export default function SyncPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [syncId, setSyncId] = useState<number | null>(null);
  const [selectedLocalFile, setSelectedLocalFile] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  // ローカルCSVファイルのリストを取得
  const { data: localFiles, refetch: refetchFiles } = useQuery({
    queryKey: ['local-csv-files'],
    queryFn: syncApi.listCsvFiles,
  });

  // アップロード処理
  const uploadMutation = useMutation({
    mutationFn: (file: File) => syncApi.uploadCsv(file),
    onSuccess: (data) => {
      setSyncId(data.sync_id);
      setSelectedFile(null);
      refetchFiles();
    },
  });

  // ローカルファイル処理
  const processLocalMutation = useMutation({
    mutationFn: (filename: string) => syncApi.processLocalCsv(filename),
    onSuccess: (data) => {
      setSyncId(data.sync_id);
      setSelectedLocalFile(null);
    },
  });

  // 同期ステータス取得
  const { data: syncStatus } = useQuery({
    queryKey: ['sync-status', syncId],
    queryFn: () => syncId ? syncApi.getStatus(syncId) : null,
    enabled: !!syncId,
    refetchInterval: (data) => {
      if (data?.status === 'processing') return 2000;
      return false;
    },
  });

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewData(null);
      setShowPreview(false);
      
      // 自動的にプレビューを取得
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/sync/preview`, {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();
        setPreviewData(data);
      } catch (error) {
        console.error('Preview error:', error);
      }
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  const handleProcessLocal = () => {
    if (selectedLocalFile) {
      processLocalMutation.mutate(selectedLocalFile);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">CSV同期</h2>
          <p className="mt-1 text-sm text-gray-600">
            ねっぱんからダウンロードしたCSVファイルを処理します
          </p>
        </div>

        {/* ローカルファイル選択 */}
        {localFiles?.files && localFiles.files.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center mb-4">
              <Server className="h-5 w-5 text-blue-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">サーバー上のCSVファイル</h3>
              <button
                onClick={() => refetchFiles()}
                className="ml-auto text-sm text-blue-600 hover:text-blue-800"
              >
                <RefreshCw className="h-4 w-4 inline mr-1" />
                更新
              </button>
            </div>
            
            <div className="space-y-2">
              {localFiles.files.map((file: any) => (
                <div
                  key={file.filename}
                  className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                    selectedLocalFile === file.filename
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedLocalFile(file.filename)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-gray-400 mr-2" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.filename}</p>
                        <p className="text-xs text-gray-500">
                          サイズ: {(file.size / 1024).toFixed(2)} KB | 
                          更新: {new Date(file.modified).toLocaleString('ja-JP')}
                        </p>
                      </div>
                    </div>
                    {selectedLocalFile === file.filename && (
                      <button
                        onClick={handleProcessLocal}
                        disabled={processLocalMutation.isPending}
                        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
                      >
                        {processLocalMutation.isPending ? '処理中...' : '処理開始'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* アップロードエリア */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">新しいファイルをアップロード</h3>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
            <div className="text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900">
                    CSVファイルを選択
                  </span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".csv"
                    onChange={handleFileChange}
                  />
                </label>
                <p className="mt-1 text-xs text-gray-500">
                  CSV形式のファイルのみアップロード可能
                </p>
              </div>
            </div>
          </div>

          {selectedFile && (
            <>
              <div className="mt-4 flex items-center justify-between bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-900">{selectedFile.name}</span>
                  <span className="ml-2 text-xs text-gray-500">
                    ({(selectedFile.size / 1024).toFixed(2)} KB)
                  </span>
                </div>
                <div className="flex space-x-2">
                  {previewData && (
                    <button
                      onClick={() => setShowPreview(!showPreview)}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {showPreview ? 'プレビューを隠す' : 'プレビュー表示'}
                    </button>
                  )}
                  <button
                    onClick={handleUpload}
                    disabled={uploadMutation.isPending}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {uploadMutation.isPending ? 'アップロード中...' : 'アップロード'}
                  </button>
                </div>
              </div>
              
              {/* エンコーディング情報 */}
              {previewData && (
                <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-blue-900">文字エンコーディング</h4>
                      <p className="text-sm text-blue-700">
                        検出: <strong>{previewData.detected_encoding || '不明'}</strong>
                        {previewData.encoding_confidence && 
                          ` (信頼度: ${(previewData.encoding_confidence * 100).toFixed(0)}%)`
                        }
                      </p>
                      {previewData.total_rows && (
                        <p className="text-sm text-blue-700">総行数: {previewData.total_rows}行</p>
                      )}
                    </div>
                    {previewData.encoding_confidence < 0.7 && (
                      <AlertCircle className="h-5 w-5 text-yellow-500" />
                    )}
                  </div>
                  {previewData.warnings && previewData.warnings.length > 0 && (
                    <div className="mt-2 text-sm text-yellow-700">
                      {previewData.warnings.map((warning: string, idx: number) => (
                        <p key={idx}>⚠️ {warning}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* プレビューテーブル */}
              {showPreview && previewData && previewData.preview_rows && (
                <div className="mt-4 overflow-x-auto">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">データプレビュー（最初の{previewData.preview_rows.length}行）</h4>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">予約ID</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">宿泊者名</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">チェックイン</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">OTA</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">部屋タイプ</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {previewData.preview_rows.map((row: any, idx: number) => (
                          <tr key={idx}>
                            <td className="px-3 py-2 text-sm text-gray-900">{row.reservation_id}</td>
                            <td className="px-3 py-2 text-sm text-gray-900">{row.guest_name}</td>
                            <td className="px-3 py-2 text-sm text-gray-500">{row.check_in_date}</td>
                            <td className="px-3 py-2 text-sm text-gray-500">{row.ota_name}</td>
                            <td className="px-3 py-2 text-sm text-gray-500">{row.room_type}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* 同期ステータス */}
        {syncStatus && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">同期状態</h3>
            
            <div className="space-y-4">
              <div className="flex items-center">
                {syncStatus.status === 'completed' ? (
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                ) : syncStatus.status === 'failed' ? (
                  <XCircle className="h-5 w-5 text-red-500 mr-2" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-500 mr-2 animate-pulse" />
                )}
                <span className={`font-medium ${
                  syncStatus.status === 'completed' ? 'text-green-600' :
                  syncStatus.status === 'failed' ? 'text-red-600' :
                  'text-yellow-600'
                }`}>
                  {syncStatus.status === 'completed' ? '同期完了' :
                   syncStatus.status === 'failed' ? '同期失敗' :
                   '処理中...'}
                </span>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <div>
                    <dt className="text-xs font-medium text-gray-500">ファイル名</dt>
                    <dd className="mt-1 text-sm text-gray-900">{syncStatus.file_name}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-gray-500">総行数</dt>
                    <dd className="mt-1 text-sm text-gray-900">{syncStatus.total_rows}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-gray-500">処理済み</dt>
                    <dd className="mt-1 text-sm text-gray-900">{syncStatus.processed_rows}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-gray-500">進捗</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {syncStatus.total_rows > 0 
                        ? `${Math.round((syncStatus.processed_rows / syncStatus.total_rows) * 100)}%`
                        : '0%'
                      }
                    </dd>
                  </div>
                  {syncStatus.detected_encoding && (
                    <div className="col-span-2">
                      <dt className="text-xs font-medium text-gray-500">文字エンコーディング</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {syncStatus.detected_encoding}
                        {syncStatus.encoding_confidence && 
                          <span className="text-xs text-gray-500 ml-1">
                            (信頼度: {(syncStatus.encoding_confidence * 100).toFixed(0)}%)
                          </span>
                        }
                      </dd>
                    </div>
                  )}
                </dl>

                {syncStatus.status === 'completed' && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <dl className="grid grid-cols-3 gap-4">
                      <div>
                        <dt className="text-xs font-medium text-gray-500">新規予約</dt>
                        <dd className="mt-1 text-sm font-semibold text-green-600">
                          +{syncStatus.new_reservations}件
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs font-medium text-gray-500">更新</dt>
                        <dd className="mt-1 text-sm font-semibold text-blue-600">
                          {syncStatus.updated_reservations}件
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs font-medium text-gray-500">エラー</dt>
                        <dd className="mt-1 text-sm font-semibold text-red-600">
                          {syncStatus.error_rows}件
                        </dd>
                      </div>
                    </dl>
                  </div>
                )}

                {syncStatus.error_message && (
                  <div className="mt-4 p-3 bg-red-50 rounded-md">
                    <p className="text-sm text-red-800">{syncStatus.error_message}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 使用方法 */}
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-blue-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">CSVファイルの処理方法</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p className="mb-2">
                  <strong>方法1: サーバー上のファイルを処理</strong>
                </p>
                <ol className="list-decimal list-inside space-y-1 ml-2">
                  <li>run-sync.bat でCSVをダウンロード</li>
                  <li>上記リストから該当ファイルを選択</li>
                  <li>「処理開始」をクリック</li>
                </ol>
                <p className="mt-3 mb-2">
                  <strong>方法2: 新しいファイルをアップロード</strong>
                </p>
                <ol className="list-decimal list-inside space-y-1 ml-2">
                  <li>「CSVファイルを選択」をクリック</li>
                  <li>ファイルを選択してアップロード</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}