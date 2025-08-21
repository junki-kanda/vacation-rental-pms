'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ChevronLeft, ChevronRight, Users, AlertTriangle, CheckCircle } from 'lucide-react';
import TaskAssignModal from './TaskAssignModal';

interface CleaningTask {
  id: number;
  facility_id: number;
  facility_name: string;
  scheduled_date: string;
  scheduled_start_time: string | null;
  scheduled_end_time: string | null;
  status: string;
  guest_name: string | null;
  assigned_staff: Array<{ id: number; name: string; status: string }>;
  assigned_group?: { id: number; name: string; member_count: number };
  is_assigned: boolean;
}

interface CalendarData {
  tasks_by_date: { [date: string]: CleaningTask[] };
  facilities: Array<{ id: number; name: string }>;
}

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];

export default function CleaningMonthCalendar() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedTask, setSelectedTask] = useState<CleaningTask | null>(null);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);

  // カレンダーデータ取得
  const { data: calendarData, isLoading, refetch } = useQuery<CalendarData>({
    queryKey: ['cleaning-calendar', format(monthStart, 'yyyy-MM'), format(monthEnd, 'yyyy-MM')],
    queryFn: async () => {
      const response = await fetch(
        `http://localhost:8000/api/cleaning/tasks/calendar?start_date=${format(monthStart, 'yyyy-MM-dd')}&end_date=${format(monthEnd, 'yyyy-MM-dd')}`
      );
      if (!response.ok) throw new Error('Failed to fetch calendar data');
      return response.json();
    },
  });

  // 月の変更
  const changeMonth = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      setCurrentDate(subMonths(currentDate, 1));
    } else {
      setCurrentDate(addMonths(currentDate, 1));
    }
  };

  // タスククリック処理
  const handleTaskClick = (task: CleaningTask) => {
    setSelectedTask(task);
    setIsAssignModalOpen(true);
  };

  // モーダル閉じる処理
  const handleModalClose = () => {
    setSelectedTask(null);
    setIsAssignModalOpen(false);
    refetch();
  };

  // カレンダーの日付生成
  const calendarDays = eachDayOfInterval({ start: monthStart, end: monthEnd });
  const startDayOfWeek = getDay(monthStart);
  const emptyDays = Array(startDayOfWeek).fill(null);

  // タスクステータスによる色分け
  const getTaskColor = (task: CleaningTask) => {
    switch (task.status) {
      case 'completed':
        return 'bg-gray-100 border-gray-400 text-gray-800'; // 完了 - グレー
      case 'assigned':
        return 'bg-green-100 border-green-400 text-green-800'; // 割当済み - 緑
      case 'needs_revision':
        return 'bg-pink-100 border-pink-400 text-pink-800'; // 要修正 - ピンク
      case 'unassigned':
      default:
        return 'bg-orange-100 border-orange-400 text-orange-800'; // 未割当 - オレンジ
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <button
            onClick={() => changeMonth('prev')}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h2 className="text-xl font-bold text-gray-900">
            {format(currentDate, 'yyyy年M月', { locale: ja })}
          </h2>
          <button
            onClick={() => changeMonth('next')}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* カレンダー */}
      {isLoading ? (
        <div className="p-8 text-center text-gray-500">読み込み中...</div>
      ) : (
        <div className="p-4">
          {/* 曜日ヘッダー */}
          <div className="grid grid-cols-7 mb-2">
            {WEEKDAYS.map((day, index) => (
              <div
                key={day}
                className={`text-center text-sm font-medium py-2 ${
                  index === 0 ? 'text-red-600' : index === 6 ? 'text-blue-600' : 'text-gray-700'
                }`}
              >
                {day}
              </div>
            ))}
          </div>

          {/* カレンダー本体 */}
          <div className="grid grid-cols-7 gap-1">
            {/* 空のセル */}
            {emptyDays.map((_, index) => (
              <div key={`empty-${index}`} className="h-24 bg-gray-50" />
            ))}

            {/* 日付セル */}
            {calendarDays.map((day) => {
              const dateStr = format(day, 'yyyy-MM-dd');
              const tasks = calendarData?.tasks_by_date[dateStr] || [];
              const dayOfWeek = getDay(day);
              const isToday = isSameDay(day, new Date());

              return (
                <div
                  key={dateStr}
                  className={`h-24 border ${
                    isToday ? 'border-indigo-500 border-2' : 'border-gray-200'
                  } ${isSameMonth(day, currentDate) ? 'bg-white' : 'bg-gray-50'}`}
                >
                  <div className="p-1">
                    <div
                      className={`text-xs font-medium mb-1 ${
                        dayOfWeek === 0 ? 'text-red-600' : dayOfWeek === 6 ? 'text-blue-600' : 'text-gray-700'
                      }`}
                    >
                      {format(day, 'd')}
                    </div>
                    
                    {/* タスク表示 */}
                    <div className="space-y-0.5 overflow-y-auto max-h-16">
                      {tasks.slice(0, 3).map((task) => (
                        <button
                          key={task.id}
                          onClick={() => handleTaskClick(task)}
                          className={`w-full px-1 py-0.5 text-xs rounded border ${getTaskColor(task)} hover:opacity-80 transition-opacity`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="truncate">{task.facility_name}</span>
                            {task.is_assigned ? (
                              <CheckCircle className="h-3 w-3 flex-shrink-0" />
                            ) : (
                              <AlertTriangle className="h-3 w-3 flex-shrink-0" />
                            )}
                          </div>
                          {(task.assigned_staff.length > 0 || task.assigned_group) && (
                            <div className="text-xs opacity-75 truncate">
                              {task.assigned_group 
                                ? `🏢 ${task.assigned_group.name}` 
                                : task.assigned_staff.map(s => s.name).join(', ')}
                            </div>
                          )}
                        </button>
                      ))}
                      {tasks.length > 3 && (
                        <div className="text-xs text-gray-500 text-center">
                          他 {tasks.length - 3} 件
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 凡例 */}
          <div className="mt-4 flex items-center justify-center space-x-4 text-sm">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-orange-100 border border-orange-400 rounded mr-2" />
              <span>未割当</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-100 border border-green-400 rounded mr-2" />
              <span>割当済</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-gray-100 border border-gray-400 rounded mr-2" />
              <span>完了</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-pink-100 border border-pink-400 rounded mr-2" />
              <span>要修正</span>
            </div>
          </div>
        </div>
      )}

      {/* タスク割当モーダル */}
      {selectedTask && isAssignModalOpen && (
        <TaskAssignModal
          task={{
            id: selectedTask.id,
            facility_id: selectedTask.facility_id,
            facility_name: selectedTask.facility_name,
            checkout_date: selectedTask.scheduled_date,
            scheduled_date: selectedTask.scheduled_date,
            scheduled_start_time: selectedTask.scheduled_start_time,
            scheduled_end_time: selectedTask.scheduled_end_time,
            estimated_duration_minutes: 120,
            guest_name: selectedTask.guest_name,
          } as any}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
}