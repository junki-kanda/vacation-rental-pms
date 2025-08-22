'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import cleaningApi from '@/lib/api/cleaning';
import { AlertTriangle, CheckCircle, Calendar, MapPin, User } from 'lucide-react';
import TaskRevisionModal from '@/components/cleaning/TaskRevisionModal';

interface Task {
  id: number;
  facility_id: number;
  facility_name?: string;
  guest_name?: string;
  checkout_date: string;
  scheduled_date: string;
  estimated_duration_minutes: number;
  status: string;
  notes?: string;
  priority: number;
  created_at: string;
  updated_at: string;
}

export default function TaskRevisionPage() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [revisionMode, setRevisionMode] = useState<'request' | 'resolve'>('resolve');
  const [selectedFacility, setSelectedFacility] = useState<number | undefined>(undefined);

  // 要修正タスク一覧取得
  const { data: tasks, isLoading, refetch } = useQuery({
    queryKey: ['needs-revision-tasks', selectedFacility],
    queryFn: () => cleaningApi.get('/tasks/needs-revision', {
      params: { facility_id: selectedFacility }
    }),
  });

  // 施設一覧取得（フィルター用）
  const { data: facilities } = useQuery({
    queryKey: ['facilities'],
    queryFn: () => cleaningApi.get('/facilities'),
  });

  const handleTaskSelect = (task: Task, mode: 'request' | 'resolve') => {
    setSelectedTask(task);
    setRevisionMode(mode);
  };

  const handleModalClose = () => {
    setSelectedTask(null);
    refetch(); // データを再取得
  };

  const getPriorityColor = (priority: number) => {
    if (priority >= 4) return 'text-red-600 bg-red-100';
    if (priority >= 3) return 'text-orange-600 bg-orange-100';
    return 'text-green-600 bg-green-100';
  };

  const getPriorityText = (priority: number) => {
    if (priority >= 4) return '高';
    if (priority >= 3) return '中';
    return '低';
  };

  const extractRevisionReason = (notes?: string) => {
    if (!notes) return '';
    const match = notes.match(/【修正要求】(.+?)(?:\n|$)/);
    return match ? match[1] : '';
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <AlertTriangle className="h-6 w-6 mr-3 text-red-500" />
          要修正タスク管理
        </h1>
      </div>

      {/* フィルター */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">施設フィルター:</label>
          <select
            value={selectedFacility || ''}
            onChange={(e) => setSelectedFacility(e.target.value ? parseInt(e.target.value) : undefined)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">全施設</option>
            {facilities?.map((facility: any) => (
              <option key={facility.id} value={facility.id}>
                {facility.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* タスク一覧 */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            要修正タスク一覧 ({tasks?.length || 0}件)
          </h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500">読み込み中...</div>
        ) : tasks?.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
            <p>要修正のタスクはありません</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {tasks?.map((task: Task) => (
              <div key={task.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900">
                        タスクID: {task.id}
                      </h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(task.priority)}`}>
                        優先度: {getPriorityText(task.priority)}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div className="space-y-2">
                        <div className="flex items-center text-sm text-gray-600">
                          <MapPin className="h-4 w-4 mr-2" />
                          {task.facility_name || `施設${task.facility_id}`}
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <User className="h-4 w-4 mr-2" />
                          {task.guest_name || '-'}
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="h-4 w-4 mr-2" />
                          チェックアウト: {new Date(task.checkout_date).toLocaleDateString('ja-JP')}
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="h-4 w-4 mr-2" />
                          清掃予定日: {new Date(task.scheduled_date).toLocaleDateString('ja-JP')}
                        </div>
                      </div>
                    </div>

                    {/* 修正要求理由 */}
                    {extractRevisionReason(task.notes) && (
                      <div className="bg-red-50 border-l-4 border-red-400 p-3 mb-4">
                        <h4 className="text-sm font-medium text-red-800 mb-1">修正要求理由</h4>
                        <p className="text-sm text-red-700">{extractRevisionReason(task.notes)}</p>
                      </div>
                    )}

                    {/* 全体の備考 */}
                    {task.notes && (
                      <div className="bg-gray-50 rounded p-3 mb-4">
                        <h4 className="text-sm font-medium text-gray-800 mb-1">備考</h4>
                        <p className="text-sm text-gray-600 whitespace-pre-wrap">{task.notes}</p>
                      </div>
                    )}

                    <div className="text-xs text-gray-500">
                      作成日: {new Date(task.created_at).toLocaleString('ja-JP')} | 
                      更新日: {new Date(task.updated_at).toLocaleString('ja-JP')}
                    </div>
                  </div>

                  <div className="flex flex-col space-y-2 ml-4">
                    <button
                      onClick={() => handleTaskSelect(task, 'resolve')}
                      className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 flex items-center"
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      修正完了
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 修正モーダル */}
      {selectedTask && (
        <TaskRevisionModal
          task={selectedTask}
          mode={revisionMode}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
}