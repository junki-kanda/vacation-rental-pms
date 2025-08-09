'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, Check, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, isSameMonth } from 'date-fns';
import { ja } from 'date-fns/locale';

interface StaffAvailabilityCalendarProps {
  staffId: number;
  staffName: string;
  onClose: () => void;
}

interface AvailabilityData {
  year: number;
  month: number;
  availability_days: { [key: number]: boolean };
}

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];

export default function StaffAvailabilityCalendar({ 
  staffId, 
  staffName, 
  onClose 
}: StaffAvailabilityCalendarProps) {
  const queryClient = useQueryClient();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [availabilityMap, setAvailabilityMap] = useState<{ [key: number]: boolean }>({});
  const [hasChanges, setHasChanges] = useState(false);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1;

  // 出勤可能日データ取得
  const { data: availabilityData, isLoading } = useQuery<AvailabilityData>({
    queryKey: ['staff-availability', staffId, year, month],
    queryFn: async () => {
      const response = await fetch(
        `http://localhost:8000/api/cleaning/staff/${staffId}/availability/${year}/${month}`
      );
      if (!response.ok) throw new Error('Failed to fetch availability');
      return response.json();
    },
  });

  // データが取得できたら状態を更新
  useEffect(() => {
    if (availabilityData) {
      setAvailabilityMap(availabilityData.availability_days || {});
      setHasChanges(false);
    }
  }, [availabilityData]);

  // 出勤可能日更新
  const updateMutation = useMutation({
    mutationFn: async (data: { availability_days: { [key: number]: boolean } }) => {
      const response = await fetch(
        `http://localhost:8000/api/cleaning/staff/${staffId}/availability/${year}/${month}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        }
      );
      if (!response.ok) throw new Error('Failed to update availability');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ 
        queryKey: ['staff-availability', staffId, year, month] 
      });
      setHasChanges(false);
    },
  });

  // 月の変更
  const changeMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (direction === 'prev') {
      newDate.setMonth(newDate.getMonth() - 1);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setCurrentDate(newDate);
  };

  // 日付をトグル
  const toggleDate = (day: number) => {
    setAvailabilityMap((prev) => ({
      ...prev,
      [day]: !prev[day],
    }));
    setHasChanges(true);
  };

  // 全選択/全解除
  const toggleAll = (value: boolean) => {
    const daysInMonth = endOfMonth(currentDate).getDate();
    const newMap: { [key: number]: boolean } = {};
    for (let i = 1; i <= daysInMonth; i++) {
      newMap[i] = value;
    }
    setAvailabilityMap(newMap);
    setHasChanges(true);
  };

  // 保存
  const handleSave = async () => {
    await updateMutation.mutateAsync({ availability_days: availabilityMap });
  };

  // カレンダーの日付生成
  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarDays = eachDayOfInterval({ start: monthStart, end: monthEnd });

  // 月初の曜日に合わせて空のセルを追加
  const startDayOfWeek = getDay(monthStart);
  const emptyDays = Array(startDayOfWeek).fill(null);

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">
              {staffName} - 出勤可能日設定
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* 月選択 */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => changeMonth('prev')}
              className="p-2 hover:bg-gray-100 rounded-md"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <h3 className="text-lg font-medium">
              {format(currentDate, 'yyyy年M月', { locale: ja })}
            </h3>
            <button
              onClick={() => changeMonth('next')}
              className="p-2 hover:bg-gray-100 rounded-md"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          {/* 操作ボタン */}
          <div className="flex space-x-2 mb-4">
            <button
              onClick={() => toggleAll(true)}
              className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
            >
              全て選択
            </button>
            <button
              onClick={() => toggleAll(false)}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
            >
              全て解除
            </button>
          </div>

          {/* カレンダー */}
          {isLoading ? (
            <div className="text-center py-8">読み込み中...</div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              {/* 曜日ヘッダー */}
              <div className="grid grid-cols-7 bg-gray-50">
                {WEEKDAYS.map((day, index) => (
                  <div
                    key={day}
                    className={`text-center py-2 text-sm font-medium ${
                      index === 0 ? 'text-red-600' : index === 6 ? 'text-blue-600' : 'text-gray-700'
                    }`}
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* カレンダー本体 */}
              <div className="grid grid-cols-7">
                {/* 空のセル */}
                {emptyDays.map((_, index) => (
                  <div key={`empty-${index}`} className="h-16 border-r border-b" />
                ))}

                {/* 日付セル */}
                {calendarDays.map((day) => {
                  const dayNumber = day.getDate();
                  const dayOfWeek = getDay(day);
                  const isAvailable = availabilityMap[dayNumber] !== false;

                  return (
                    <button
                      key={dayNumber}
                      onClick={() => toggleDate(dayNumber)}
                      className={`h-16 border-r border-b flex flex-col items-center justify-center hover:bg-gray-50 transition-colors ${
                        isAvailable ? 'bg-green-50' : 'bg-red-50'
                      }`}
                    >
                      <span
                        className={`text-sm mb-1 ${
                          dayOfWeek === 0 ? 'text-red-600' : dayOfWeek === 6 ? 'text-blue-600' : 'text-gray-700'
                        }`}
                      >
                        {dayNumber}
                      </span>
                      {isAvailable ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <X className="h-4 w-4 text-red-600" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 凡例 */}
          <div className="mt-4 flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-50 border rounded mr-2" />
              <span>出勤可能</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-50 border rounded mr-2" />
              <span>出勤不可</span>
            </div>
          </div>

          {/* 保存ボタン */}
          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges || updateMutation.isPending}
              className={`px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white ${
                hasChanges && !updateMutation.isPending
                  ? 'bg-indigo-600 hover:bg-indigo-700'
                  : 'bg-gray-400 cursor-not-allowed'
              }`}
            >
              {updateMutation.isPending ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}