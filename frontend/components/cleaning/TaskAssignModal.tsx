'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import cleaningApi, { CleaningTask, Staff } from '@/lib/api/cleaning';
import { X, User, Star, Car, Clock } from 'lucide-react';
import { format } from 'date-fns';

interface TaskAssignModalProps {
  task: CleaningTask;
  onClose: () => void;
}

export default function TaskAssignModal({ task, onClose }: TaskAssignModalProps) {
  const queryClient = useQueryClient();
  const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null);
  const [startTime, setStartTime] = useState(task.scheduled_start_time || '10:00');
  const [endTime, setEndTime] = useState(task.scheduled_end_time || '12:00');
  const [isOptionIncluded, setIsOptionIncluded] = useState(false);
  const [notes, setNotes] = useState('');

  // スタッフ一覧取得
  const { data: staffList } = useQuery({
    queryKey: ['cleaning-staff-active'],
    queryFn: () => cleaningApi.staff.getAll({ is_active: true }),
  });

  // シフト作成
  const createShiftMutation = useMutation({
    mutationFn: (data: any) => cleaningApi.shifts.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-shifts'] });
      onClose();
    },
  });

  const handleAssign = async () => {
    if (!selectedStaffId) {
      alert('スタッフを選択してください');
      return;
    }

    await createShiftMutation.mutateAsync({
      staff_id: selectedStaffId,
      task_id: task.id,
      assigned_date: task.scheduled_date,
      scheduled_start_time: startTime,
      scheduled_end_time: endTime,
      is_option_included: isOptionIncluded,
      notes,
      created_by: 'admin', // TODO: ログインユーザー名
    });
  };

  const renderSkillLevel = (level: number) => {
    return (
      <div className="flex items-center">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`h-3 w-3 ${
              i < level ? 'text-yellow-400 fill-current' : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">スタッフ割当</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
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

          {/* スタッフ選択 */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">スタッフ選択</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {staffList?.map((staff: Staff) => (
                <label
                  key={staff.id}
                  className={`flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                    selectedStaffId === staff.id
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-gray-200'
                  }`}
                >
                  <input
                    type="radio"
                    name="staff"
                    value={staff.id}
                    checked={selectedStaffId === staff.id}
                    onChange={() => setSelectedStaffId(staff.id)}
                    className="sr-only"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium">
                          {staff.name.substring(0, 1)}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{staff.name}</div>
                          <div className="text-sm text-gray-500">
                            基本: ¥{staff.rate_per_property.toLocaleString()}/棟
                            {staff.transportation_fee > 0 && ` +交通費¥${staff.transportation_fee}`}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {renderSkillLevel(staff.skill_level)}
                        {staff.has_car && <Car className="h-4 w-4 text-gray-600" />}
                      </div>
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 時間設定 */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">作業時間</h3>
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-gray-400" />
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
              <span className="text-gray-500">〜</span>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          {/* オプション設定 */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={isOptionIncluded}
                onChange={(e) => setIsOptionIncluded(e.target.checked)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="ml-2 text-sm text-gray-900">オプション作業あり</span>
            </label>
            <p className="mt-1 text-xs text-gray-500">
              追加作業がある場合はチェックしてください（オプション料金が適用されます）
            </p>
          </div>

          {/* 備考 */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              備考
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="特記事項があれば入力してください"
            />
          </div>

          {/* ボタン */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              onClick={handleAssign}
              disabled={!selectedStaffId || createShiftMutation.isPending}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              {createShiftMutation.isPending ? '割当中...' : '割当'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}