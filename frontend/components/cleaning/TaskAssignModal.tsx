'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CleaningTask } from '@/lib/api/cleaning';
import staffGroupsApi, { StaffGroup } from '@/lib/api/staff-groups';
import cleaningApi from '@/lib/api/cleaning';
import { X, Users, DollarSign, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import TaskRevisionModal from './TaskRevisionModal';

interface TaskAssignModalProps {
  task: CleaningTask;
  onClose: () => void;
}

export default function TaskAssignModal({ task, onClose }: TaskAssignModalProps) {
  const queryClient = useQueryClient();
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [startTime, setStartTime] = useState(task.scheduled_start_time || '11:00');
  const [endTime, setEndTime] = useState(task.scheduled_end_time || '16:00');
  const [notes, setNotes] = useState('');
  const [showRevisionModal, setShowRevisionModal] = useState(false);

  // グループ一覧取得
  const { data: groupList, isLoading } = useQuery({
    queryKey: ['staff-groups-active'],
    queryFn: () => staffGroupsApi.getGroups({ is_active: true }),
  });

  // グループ割当
  const assignGroupMutation = useMutation({
    mutationFn: ({ groupId, data }: { groupId: number; data: any }) => 
      staffGroupsApi.assignTasks(groupId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-shifts'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar-week'] });
      alert('グループにタスクを割り当てました');
      onClose();
    },
    onError: (error: any) => {
      console.error('Group assignment error:', error);
      console.error('Task being assigned:', task);
      console.error('Selected group ID:', selectedGroupId);
      alert(`グループ割り当てに失敗しました: ${error.message || 'Unknown error'}`);
    },
  });

  // ステータス更新
  const updateStatusMutation = useMutation({
    mutationFn: (status: string) => cleaningApi.tasks.updateStatus(task.id, status),
    onSuccess: (data, status) => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar-week'] });
      alert(`タスクのステータスを「${status === 'needs_revision' ? '要修正' : status}」に変更しました`);
      onClose();
    },
    onError: (error: any) => {
      console.error('Status update error:', error);
      alert(`ステータス更新に失敗しました: ${error.message || 'Unknown error'}`);
    },
  });

  const handleAssign = async () => {
    if (!selectedGroupId) {
      alert('グループを選択してください');
      return;
    }

    await assignGroupMutation.mutateAsync({
      groupId: selectedGroupId,
      data: {
        task_ids: [task.id],
        assigned_date: task.scheduled_date,
        scheduled_start_time: startTime,
        scheduled_end_time: endTime,
        notes,
      },
    });
  };

  const handleMarkNeedsRevision = () => {
    setShowRevisionModal(true);
  };

  const handleRevisionModalClose = () => {
    setShowRevisionModal(false);
    onClose(); // 親モーダルも閉じる
  };

  const selectedGroup = groupList?.find(g => g.id === selectedGroupId);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* ヘッダー */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">タスク割り当て（グループ）</h2>
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
              <div>チェックアウト: {format(new Date(task.checkout_date), 'yyyy/MM/dd')}</div>
              <div>清掃予定日: {format(new Date(task.scheduled_date), 'yyyy/MM/dd')}</div>
              <div>推定作業時間: {task.estimated_duration_minutes}分</div>
            </div>
          </div>

          {/* グループ選択 */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">グループ選択</h3>
            {isLoading ? (
              <div className="text-center py-4 text-gray-500">読み込み中...</div>
            ) : !groupList || groupList.length === 0 ? (
              <div className="text-center py-4 text-gray-500">利用可能なグループがありません</div>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {groupList.map((group: StaffGroup) => (
                  <label
                    key={group.id}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                      selectedGroupId === group.id
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200'
                    }`}
                  >
                    <input
                      type="radio"
                      name="group"
                      value={group.id}
                      checked={selectedGroupId === group.id}
                      onChange={() => setSelectedGroupId(group.id)}
                      className="sr-only"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="h-10 w-10 rounded-full bg-purple-600 flex items-center justify-center text-white">
                            <Users className="h-5 w-5" />
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">{group.name}</div>
                            <div className="text-sm text-gray-500">
                              メンバー: {group.member_count}名
                            </div>
                            {group.description && (
                              <div className="text-xs text-gray-400 mt-1">{group.description}</div>
                            )}
                          </div>
                        </div>
                        <div>
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">
                              ¥{group.rate_per_property.toLocaleString()}/棟
                            </div>
                            {group.transportation_fee > 0 && (
                              <div className="text-xs text-gray-500">
                                +交通費¥{group.transportation_fee.toLocaleString()}
                              </div>
                            )}
                          </div>
                          <div className="flex justify-end mt-1 gap-1">
                            {group.can_handle_large_properties && (
                              <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                                大型
                              </span>
                            )}
                            {group.can_handle_multiple_properties && (
                              <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-700 rounded">
                                複数
                              </span>
                            )}
                            <span className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                              最大{group.max_properties_per_day}棟/日
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* スケジュール設定 */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">作業時間</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">開始時間</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">終了時間</label>
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* 選択グループの料金表示 */}
          {selectedGroup && (
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <DollarSign className="h-5 w-5 text-blue-600 mr-2" />
                <h4 className="text-sm font-medium text-blue-900">選択グループの料金</h4>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-blue-700">基本料金:</span>
                  <span className="font-medium text-blue-900">¥{selectedGroup.rate_per_property.toLocaleString()}/棟</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">オプション付:</span>
                  <span className="font-medium text-blue-900">¥{selectedGroup.rate_per_property_with_option.toLocaleString()}/棟</span>
                </div>
                {selectedGroup.transportation_fee > 0 && (
                  <div className="flex justify-between">
                    <span className="text-blue-700">交通費:</span>
                    <span className="font-medium text-blue-900">¥{selectedGroup.transportation_fee.toLocaleString()}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-blue-700">メンバー数:</span>
                  <span className="font-medium text-blue-900">{selectedGroup.member_count}名</span>
                </div>
              </div>
            </div>
          )}

          {/* 備考 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">備考</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="作業上の注意点や特別な指示があれば記入してください"
            />
          </div>
        </div>

        {/* フッター - 常に表示 */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-between items-center flex-shrink-0 min-h-[80px]">
          <button
            onClick={handleMarkNeedsRevision}
            disabled={updateStatusMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-pink-600 border border-transparent rounded-md hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <AlertTriangle className="h-4 w-4 mr-1" />
            {updateStatusMutation.isPending ? '更新中...' : '要修正'}
          </button>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              キャンセル
            </button>
            <button
              onClick={handleAssign}
              disabled={!selectedGroupId || assignGroupMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {assignGroupMutation.isPending ? '割り当て中...' : 
               selectedGroupId ? 'グループに割り当て' : 'グループを選択してください'}
            </button>
          </div>
        </div>
      </div>

      {/* 修正要求モーダル */}
      {showRevisionModal && (
        <TaskRevisionModal
          task={task}
          mode="request"
          onClose={handleRevisionModalClose}
        />
      )}
    </div>
  );
}