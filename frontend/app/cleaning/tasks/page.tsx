'use client';

import { useState } from 'react';
import { Calendar as CalendarIcon, List, RefreshCw, AlertTriangle, CheckCircle, Eye } from 'lucide-react';
import CleaningMonthCalendar from '@/components/cleaning/CleaningMonthCalendar';
import CleaningWeekCalendar from '@/components/cleaning/CleaningWeekCalendar';
import StaffMonthlyStats from '@/components/cleaning/StaffMonthlyStats';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import cleaningApi from '@/lib/api/cleaning';

type ViewType = 'month' | 'week';

type Alert = {
  type: string;
  message: string;
  timestamp: string;
  details: any;
};

type SyncResult = {
  success: boolean;
  stats: {
    tasks_created: number;
    tasks_cancelled: number;
    tasks_modified: number;
    conflicts_detected: number;
    total_alerts: number;
  };
  alerts: Alert[];
  sync_time: string;
};

export default function CleaningTasksPage() {
  const [viewType, setViewType] = useState<ViewType>('month');
  const [showAlerts, setShowAlerts] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);
  const queryClient = useQueryClient();

  // 同期プレビュー
  const { data: syncPreview, refetch: refetchPreview } = useQuery<SyncResult>({
    queryKey: ['sync-preview'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/cleaning/tasks/sync-preview');
      if (!response.ok) throw new Error('Failed to fetch sync preview');
      return response.json();
    },
    enabled: false, // 手動でトリガー
  });

  // タスク同期実行
  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(
        'http://localhost:8000/api/cleaning/tasks/sync-all',
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('Failed to sync tasks');
      return response.json();
    },
    onSuccess: (data: SyncResult) => {
      setLastSyncResult(data);
      setShowAlerts(true);
      
      // 成功メッセージを表示
      const message = `同期完了: ${data.stats.tasks_created}件作成, ${data.stats.tasks_cancelled}件キャンセル, ${data.stats.tasks_modified}件更新`;
      if (data.stats.conflicts_detected > 0) {
        alert(`⚠️ ${message}\n\n注意: ${data.stats.conflicts_detected}件の競合が検出されました。アラートを確認してください。`);
      } else {
        alert(`✅ ${message}`);
      }
      
      // カレンダーをリフレッシュ
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar-week'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-tasks'] });
    },
  });

  const handleSyncPreview = async () => {
    await refetchPreview();
    if (syncPreview) {
      setLastSyncResult(syncPreview);
      setShowAlerts(true);
    }
  };

  const handleSync = () => {
    if (confirm('清掃タスクを最新の予約データと同期しますか？\n\n新規予約のタスク追加、キャンセル検知、変更検知を行います。')) {
      syncMutation.mutate();
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'task_created':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'task_cancelled':
      case 'conflict_detected':
      case 'staff_reassign_needed':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'task_modified':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getAlertBgColor = (type: string) => {
    switch (type) {
      case 'task_created':
        return 'bg-green-50 border-green-200';
      case 'task_cancelled':
      case 'conflict_detected':
      case 'staff_reassign_needed':
        return 'bg-red-50 border-red-200';
      case 'task_modified':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">清掃タスク管理</h1>
        <div className="flex items-center space-x-3">
          {/* 同期プレビューボタン */}
          <button
            onClick={handleSyncPreview}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center"
          >
            <Eye className="h-5 w-5 mr-2" />
            同期プレビュー
          </button>

          {/* タスク同期ボタン */}
          <button
            onClick={handleSync}
            disabled={syncMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center disabled:opacity-50"
          >
            <RefreshCw className={`h-5 w-5 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            {syncMutation.isPending ? '同期中...' : 'タスク同期'}
          </button>

          {/* ビュー切り替え */}
          <div className="flex rounded-md shadow-sm">
            <button
              onClick={() => setViewType('month')}
              className={`px-4 py-2 text-sm font-medium rounded-l-md border ${
                viewType === 'month'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              <CalendarIcon className="h-4 w-4 inline-block mr-1" />
              月表示
            </button>
            <button
              onClick={() => setViewType('week')}
              className={`px-4 py-2 text-sm font-medium rounded-r-md border-t border-r border-b ${
                viewType === 'week'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              <List className="h-4 w-4 inline-block mr-1" />
              週表示
            </button>
          </div>
        </div>
      </div>

      {/* 同期結果とアラート */}
      {showAlerts && lastSyncResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">同期結果</h2>
            <button
              onClick={() => setShowAlerts(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* 統計情報 */}
          <div className="grid grid-cols-5 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{lastSyncResult.stats.tasks_created}</div>
              <div className="text-sm text-gray-500">新規作成</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{lastSyncResult.stats.tasks_cancelled}</div>
              <div className="text-sm text-gray-500">キャンセル</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{lastSyncResult.stats.tasks_modified}</div>
              <div className="text-sm text-gray-500">変更</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{lastSyncResult.stats.conflicts_detected}</div>
              <div className="text-sm text-gray-500">競合検出</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{lastSyncResult.stats.total_alerts}</div>
              <div className="text-sm text-gray-500">アラート数</div>
            </div>
          </div>

          {/* アラート一覧 */}
          {lastSyncResult.alerts.length > 0 && (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">アラート詳細</h3>
              {lastSyncResult.alerts.map((alert, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-md border ${getAlertBgColor(alert.type)}`}
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0 mr-2">
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{alert.message}</p>
                      {alert.details && Object.keys(alert.details).length > 0 && (
                        <div className="mt-1 text-xs text-gray-600">
                          {alert.details.assigned_staff && alert.details.assigned_staff.length > 0 && (
                            <p>割当スタッフ: {alert.details.assigned_staff.join(', ')}</p>
                          )}
                          {alert.details.changes && alert.details.changes.length > 0 && (
                            <p>変更内容: {alert.details.changes.join(', ')}</p>
                          )}
                          {alert.details.checkout_date && (
                            <p>チェックアウト日: {alert.details.checkout_date}</p>
                          )}
                        </div>
                      )}
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(alert.timestamp).toLocaleString('ja-JP')}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* カレンダー表示 */}
      {viewType === 'month' ? (
        <CleaningMonthCalendar />
      ) : (
        <CleaningWeekCalendar />
      )}

      {/* スタッフ月次統計 */}
      <div className="mt-8">
        <StaffMonthlyStats />
      </div>
    </div>
  );
}