'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, AlertTriangle, CheckCircle } from 'lucide-react';
import cleaningApi from '@/lib/api/cleaning';

interface TaskRevisionModalProps {
  task: {
    id: number;
    facility_name?: string;
    facility_id: number;
    guest_name?: string;
    checkout_date: string;
    scheduled_date: string;
    status: string;
    notes?: string;
  };
  mode: 'request' | 'resolve';
  onClose: () => void;
}

export default function TaskRevisionModal({ task, mode, onClose }: TaskRevisionModalProps) {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const requestRevisionMutation = useMutation({
    mutationFn: (data: { taskId: number; reason: string }) =>
      cleaningApi.post(`/tasks/${data.taskId}/revision?revision_reason=${encodeURIComponent(data.reason)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar-week'] });
      alert('タスクを要修正に変更しました');
      onClose();
    },
    onError: (error) => {
      console.error('Failed to request revision:', error);
      alert('修正要求に失敗しました');
    }
  });

  const resolveRevisionMutation = useMutation({
    mutationFn: (data: { taskId: number; notes: string }) =>
      cleaningApi.post(`/tasks/${data.taskId}/resolve-revision?resolution_notes=${encodeURIComponent(data.notes)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar-week'] });
      queryClient.invalidateQueries({ queryKey: ['needs-revision-tasks'] });
      alert('修正対応が完了しました');
      onClose();
    },
    onError: (error) => {
      console.error('Failed to resolve revision:', error);
      alert('修正対応の完了に失敗しました');
    }
  });

  const handleSubmit = () => {
    if (!reason.trim()) {
      alert(mode === 'request' ? '修正理由を入力してください' : '対応内容を入力してください');
      return;
    }

    if (mode === 'request') {
      requestRevisionMutation.mutate({ taskId: task.id, reason: reason.trim() });
    } else {
      resolveRevisionMutation.mutate({ taskId: task.id, notes: reason.trim() });
    }
  };

  const isLoading = requestRevisionMutation.isPending || resolveRevisionMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
        {/* ヘッダー */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            {mode === 'request' ? (
              <>
                <AlertTriangle className="h-5 w-5 mr-2 text-red-500" />
                修正要求
              </>
            ) : (
              <>
                <CheckCircle className="h-5 w-5 mr-2 text-green-500" />
                修正対応完了
              </>
            )}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* タスク情報 */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">タスク情報</h3>
            <div className="space-y-1 text-sm text-gray-600">
              <div>施設: {task.facility_name || `施設${task.facility_id}`}</div>
              <div>ゲスト: {task.guest_name || '-'}</div>
              <div>チェックアウト: {new Date(task.checkout_date).toLocaleDateString('ja-JP')}</div>
              <div>清掃予定日: {new Date(task.scheduled_date).toLocaleDateString('ja-JP')}</div>
              <div>
                ステータス: 
                <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                  task.status === 'needs_revision' 
                    ? 'bg-pink-100 text-pink-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {task.status === 'needs_revision' ? '要修正' : task.status}
                </span>
              </div>
            </div>
          </div>

          {/* 既存の備考 */}
          {task.notes && (
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">既存の備考</h3>
              <div className="text-sm text-gray-600 whitespace-pre-wrap">{task.notes}</div>
            </div>
          )}

          {/* 修正理由/対応内容入力 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {mode === 'request' ? '修正理由' : '修正対応内容'}
              <span className="text-red-500 ml-1">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder={
                mode === 'request' 
                  ? '具体的な修正が必要な内容を記入してください...'
                  : '実施した修正内容や対応結果を記入してください...'
              }
            />
          </div>
        </div>

        {/* フッター */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            キャンセル
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading || !reason.trim()}
            className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
              mode === 'request'
                ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                : 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
            }`}
          >
            {isLoading ? '処理中...' : mode === 'request' ? '修正要求' : '対応完了'}
          </button>
        </div>
      </div>
    </div>
  );
}