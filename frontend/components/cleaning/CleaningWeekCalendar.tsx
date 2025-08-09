'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, startOfWeek, endOfWeek, eachDayOfInterval, addWeeks, subWeeks, isSameDay } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ChevronLeft, ChevronRight, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
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
  is_assigned: boolean;
}

interface CalendarData {
  tasks_by_date: { [date: string]: CleaningTask[] };
  facilities: Array<{ id: number; name: string }>;
}

const WEEKDAYS = [
  { short: '日', full: '日曜日' },
  { short: '月', full: '月曜日' },
  { short: '火', full: '火曜日' },
  { short: '水', full: '水曜日' },
  { short: '木', full: '木曜日' },
  { short: '金', full: '金曜日' },
  { short: '土', full: '土曜日' },
];

export default function CleaningWeekCalendar() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedTask, setSelectedTask] = useState<CleaningTask | null>(null);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);

  const weekStart = startOfWeek(currentDate, { weekStartsOn: 0 });
  const weekEnd = endOfWeek(currentDate, { weekStartsOn: 0 });
  const weekDays = eachDayOfInterval({ start: weekStart, end: weekEnd });

  // カレンダーデータ取得
  const { data: calendarData, isLoading, refetch } = useQuery<CalendarData>({
    queryKey: ['cleaning-calendar-week', format(weekStart, 'yyyy-MM-dd'), format(weekEnd, 'yyyy-MM-dd')],
    queryFn: async () => {
      const response = await fetch(
        `http://localhost:8000/api/cleaning/tasks/calendar?start_date=${format(weekStart, 'yyyy-MM-dd')}&end_date=${format(weekEnd, 'yyyy-MM-dd')}`
      );
      if (!response.ok) throw new Error('Failed to fetch calendar data');
      return response.json();
    },
  });

  // 週の変更
  const changeWeek = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      setCurrentDate(subWeeks(currentDate, 1));
    } else {
      setCurrentDate(addWeeks(currentDate, 1));
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

  // タスクステータスによる色分け
  const getTaskColor = (task: CleaningTask) => {
    if (task.is_assigned) {
      switch (task.status) {
        case 'COMPLETED':
          return 'bg-green-100 border-green-500 text-green-800';
        case 'IN_PROGRESS':
          return 'bg-blue-100 border-blue-500 text-blue-800';
        default:
          return 'bg-gray-100 border-gray-500 text-gray-800';
      }
    }
    return 'bg-orange-100 border-orange-500 text-orange-800';
  };

  // 施設ごとのタスクをグループ化
  const getTasksByFacility = () => {
    if (!calendarData) return {};

    const tasksByFacility: { [facilityId: number]: { [date: string]: CleaningTask[] } } = {};

    // 全施設を初期化
    calendarData.facilities.forEach(facility => {
      tasksByFacility[facility.id] = {};
      weekDays.forEach(day => {
        const dateStr = format(day, 'yyyy-MM-dd');
        tasksByFacility[facility.id][dateStr] = [];
      });
    });

    // タスクを施設ごとに振り分け
    Object.entries(calendarData.tasks_by_date).forEach(([dateStr, tasks]) => {
      tasks.forEach(task => {
        if (!tasksByFacility[task.facility_id]) {
          tasksByFacility[task.facility_id] = {};
        }
        if (!tasksByFacility[task.facility_id][dateStr]) {
          tasksByFacility[task.facility_id][dateStr] = [];
        }
        tasksByFacility[task.facility_id][dateStr].push(task);
      });
    });

    return tasksByFacility;
  };

  const tasksByFacility = getTasksByFacility();

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <button
            onClick={() => changeWeek('prev')}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h2 className="text-xl font-bold text-gray-900">
            {format(weekStart, 'yyyy年M月d日', { locale: ja })} - {format(weekEnd, 'M月d日', { locale: ja })}
          </h2>
          <button
            onClick={() => changeWeek('next')}
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
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="sticky left-0 bg-gray-50 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                  施設
                </th>
                {weekDays.map((day, index) => {
                  const isToday = isSameDay(day, new Date());
                  return (
                    <th
                      key={format(day, 'yyyy-MM-dd')}
                      className={`px-4 py-3 text-center text-xs font-medium uppercase tracking-wider ${
                        isToday ? 'bg-indigo-50' : ''
                      } ${
                        index === 0 ? 'text-red-600' : index === 6 ? 'text-blue-600' : 'text-gray-700'
                      }`}
                    >
                      <div>{WEEKDAYS[index].short}</div>
                      <div className="text-lg font-bold">{format(day, 'd')}</div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {calendarData?.facilities.map((facility) => (
                <tr key={facility.id} className="hover:bg-gray-50">
                  <td className="sticky left-0 bg-white px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-r">
                    {facility.name}
                  </td>
                  {weekDays.map((day) => {
                    const dateStr = format(day, 'yyyy-MM-dd');
                    const tasks = tasksByFacility[facility.id]?.[dateStr] || [];
                    const isToday = isSameDay(day, new Date());

                    return (
                      <td
                        key={dateStr}
                        className={`px-2 py-2 h-24 align-top ${
                          isToday ? 'bg-indigo-50/50' : ''
                        }`}
                      >
                        <div className="space-y-1">
                          {tasks.map((task) => (
                            <button
                              key={task.id}
                              onClick={() => handleTaskClick(task)}
                              className={`w-full px-2 py-1 text-xs rounded-md border-2 ${getTaskColor(task)} hover:shadow-md transition-shadow`}
                            >
                              <div className="flex items-center justify-between mb-1">
                                {task.scheduled_start_time && (
                                  <span className="font-medium">
                                    {task.scheduled_start_time.substring(0, 5)}
                                  </span>
                                )}
                                {task.is_assigned ? (
                                  <CheckCircle className="h-3 w-3" />
                                ) : (
                                  <AlertTriangle className="h-3 w-3" />
                                )}
                              </div>
                              {task.guest_name && (
                                <div className="truncate text-xs opacity-75">
                                  {task.guest_name}
                                </div>
                              )}
                              {task.assigned_staff.length > 0 && (
                                <div className="truncate text-xs font-medium mt-1">
                                  {task.assigned_staff.map(s => s.name).join(', ')}
                                </div>
                              )}
                            </button>
                          ))}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 凡例 */}
      <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-center space-x-4 text-sm">
        <div className="flex items-center">
          <div className="w-4 h-4 bg-orange-100 border-2 border-orange-500 rounded mr-2" />
          <span>未割当</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-gray-100 border-2 border-gray-500 rounded mr-2" />
          <span>割当済</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-blue-100 border-2 border-blue-500 rounded mr-2" />
          <span>作業中</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-green-100 border-2 border-green-500 rounded mr-2" />
          <span>完了</span>
        </div>
      </div>

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