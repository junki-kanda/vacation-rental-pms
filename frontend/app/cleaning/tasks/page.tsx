'use client';

import { useState } from 'react';
import { Calendar as CalendarIcon, List, Plus } from 'lucide-react';
import CleaningMonthCalendar from '@/components/cleaning/CleaningMonthCalendar';
import CleaningWeekCalendar from '@/components/cleaning/CleaningWeekCalendar';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';

type ViewType = 'month' | 'week';

export default function CleaningTasksPage() {
  const [viewType, setViewType] = useState<ViewType>('month');
  const queryClient = useQueryClient();

  // タスク自動生成
  const autoCreateMutation = useMutation({
    mutationFn: async (date: Date) => {
      const response = await fetch(
        `http://localhost:8000/api/cleaning/tasks/auto-create?checkout_date=${format(date, 'yyyy-MM-dd')}`,
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('Failed to auto-create tasks');
      return response.json();
    },
    onSuccess: (data) => {
      alert(`${data.length}件のタスクを自動生成しました`);
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['cleaning-calendar-week'] });
    },
  });

  const handleAutoCreate = () => {
    const dateStr = prompt('チェックアウト日を入力してください (YYYY-MM-DD形式):');
    if (dateStr) {
      const date = new Date(dateStr);
      if (!isNaN(date.getTime())) {
        autoCreateMutation.mutate(date);
      } else {
        alert('日付の形式が正しくありません');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">清掃タスク管理</h1>
        <div className="flex items-center space-x-3">
          {/* タスク自動生成ボタン */}
          <button
            onClick={handleAutoCreate}
            disabled={autoCreateMutation.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center disabled:opacity-50"
          >
            <Plus className="h-5 w-5 mr-2" />
            {autoCreateMutation.isPending ? '生成中...' : 'タスク自動生成'}
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

      {/* カレンダー表示 */}
      {viewType === 'month' ? (
        <CleaningMonthCalendar />
      ) : (
        <CleaningWeekCalendar />
      )}
    </div>
  );
}