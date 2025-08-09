'use client';

import { useState } from 'react';
import { MainLayout } from '@/components/layout/main-layout';
import MonthCalendarV3 from '@/components/calendar/MonthCalendarV3';
import WeekCalendarV2 from '@/components/calendar/WeekCalendarV2';
import { useQuery } from '@tanstack/react-query';
import { calendarApi } from '@/lib/api';
import { Calendar as CalendarIcon, Building, Eye, EyeOff, CalendarDays, CalendarRange } from 'lucide-react';

type ViewType = 'month' | 'week';

export default function CalendarV2Page() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedRoomType, setSelectedRoomType] = useState<string>('');
  const [showCancelled, setShowCancelled] = useState<boolean>(false);
  const [viewType, setViewType] = useState<ViewType>('month');

  // 部屋タイプ一覧取得
  const { data: roomTypes } = useQuery({
    queryKey: ['room-types'],
    queryFn: () => calendarApi.getRoomTypes(),
  });

  // 予約データ取得（仮）
  const { data: reservations, isLoading } = useQuery({
    queryKey: ['calendar-reservations', currentDate, selectedRoomType],
    queryFn: () => {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const startDate = new Date(year, month, 1);
      const endDate = new Date(year, month + 1, 0);
      
      return calendarApi.getReservations(
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0],
        selectedRoomType || undefined
      );
    },
  });

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-gray-500">カレンダーを読み込み中...</div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-full mx-auto">
        {/* ヘッダー */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <CalendarIcon className="h-6 w-6 mr-2" />
            予約カレンダー（新UI）
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            各日を左右に分割し、チェックアウトとチェックインを明確に表示
          </p>
        </div>

        {/* フィルターコントロール */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* 部屋タイプフィルター */}
            <div className="flex items-center space-x-2">
              <Building className="h-4 w-4 text-gray-500" />
              <select
                value={selectedRoomType}
                onChange={(e) => setSelectedRoomType(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="">全施設</option>
                {roomTypes?.map((roomType: string) => (
                  <option key={roomType} value={roomType}>
                    {roomType}
                  </option>
                ))}
              </select>
            </div>

            {/* キャンセル表示切り替え */}
            <button
              onClick={() => setShowCancelled(!showCancelled)}
              className={`flex items-center space-x-1 px-3 py-1 rounded-md border transition-colors text-sm ${
                showCancelled 
                  ? 'bg-red-50 border-red-300 text-red-700' 
                  : 'bg-green-50 border-green-300 text-green-700'
              }`}
            >
              {showCancelled ? (
                <>
                  <EyeOff className="h-4 w-4" />
                  <span>キャンセルを表示しない</span>
                </>
              ) : (
                <>
                  <Eye className="h-4 w-4" />
                  <span>キャンセルを表示する</span>
                </>
              )}
            </button>
          </div>

          {/* ビュー切り替え */}
          <div className="flex items-center space-x-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setViewType('month')}
              className={`flex items-center space-x-1 px-3 py-1 rounded text-sm transition-colors ${
                viewType === 'month' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <CalendarDays className="h-4 w-4" />
              <span>月表示</span>
            </button>
            <button
              onClick={() => setViewType('week')}
              className={`flex items-center space-x-1 px-3 py-1 rounded text-sm transition-colors ${
                viewType === 'week' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <CalendarRange className="h-4 w-4" />
              <span>週表示</span>
            </button>
          </div>
        </div>

        {/* カレンダー本体 */}
        {viewType === 'month' ? (
          <MonthCalendarV3
            currentDate={currentDate}
            onDateChange={setCurrentDate}
            reservations={reservations}
            selectedRoomType={selectedRoomType}
            showCancelled={showCancelled}
          />
        ) : (
          <WeekCalendarV2
            currentDate={currentDate}
            onDateChange={setCurrentDate}
            reservations={reservations}
            roomTypes={roomTypes || []}
            selectedRoomType={selectedRoomType}
            showCancelled={showCancelled}
          />
        )}

        {/* 使用方法の説明 */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">新しいカレンダーUIの特徴</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• チェックインからチェックアウトまで一本の連続したバーで表示</li>
            <li>• 同日チェックイン・チェックアウトがある場合は自動的に左右に調整</li>
            <li>• 複数週にまたがる予約も連続性を保って表示</li>
            <li>• 施設ごとに予約の重なりを自動的に複数行で表示</li>
            <li>• 週表示では施設を縦軸に配置し、時間軸を廃止</li>
          </ul>
        </div>
      </div>
    </MainLayout>
  );
}