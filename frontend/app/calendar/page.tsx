'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/main-layout';
import MonthCalendarV3 from '@/components/calendar/MonthCalendarV3';
import WeekCalendarV2 from '@/components/calendar/WeekCalendarV2';
import { useQuery } from '@tanstack/react-query';
import { calendarApi } from '@/lib/api';
import { Calendar as CalendarIcon, Building, Eye, EyeOff, CalendarDays, CalendarRange } from 'lucide-react';
import { format, parse } from 'date-fns';

type ViewType = 'month' | 'week';

export default function CalendarPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URLパラメータから初期状態を復元
  const [currentDate, setCurrentDate] = useState(() => {
    const dateParam = searchParams.get('date');
    return dateParam ? parse(dateParam, 'yyyy-MM-dd', new Date()) : new Date();
  });
  const [selectedRoomType, setSelectedRoomType] = useState<string>(() => 
    searchParams.get('roomType') || ''
  );
  const [showCancelled, setShowCancelled] = useState<boolean>(() => 
    searchParams.get('showCancelled') === 'true'
  );
  const [viewType, setViewType] = useState<ViewType>(() => 
    (searchParams.get('view') as ViewType) || 'month'
  );

  // 状態が変更されたときにURLを更新
  const updateURL = (updates: Partial<{
    date: Date;
    roomType: string;
    showCancelled: boolean;
    view: ViewType;
  }>) => {
    const params = new URLSearchParams();
    
    const date = updates.date || currentDate;
    const roomType = updates.roomType !== undefined ? updates.roomType : selectedRoomType;
    const cancelled = updates.showCancelled !== undefined ? updates.showCancelled : showCancelled;
    const view = updates.view || viewType;
    
    params.set('date', format(date, 'yyyy-MM-dd'));
    if (roomType) params.set('roomType', roomType);
    params.set('showCancelled', cancelled.toString());
    params.set('view', view);
    
    router.replace(`/calendar?${params.toString()}`, { scroll: false });
  };

  const handleDateChange = (date: Date) => {
    setCurrentDate(date);
    updateURL({ date });
  };

  const handleRoomTypeChange = (roomType: string) => {
    setSelectedRoomType(roomType);
    updateURL({ roomType });
  };

  const handleShowCancelledChange = (showCancelled: boolean) => {
    setShowCancelled(showCancelled);
    updateURL({ showCancelled });
  };

  const handleViewTypeChange = (view: ViewType) => {
    setViewType(view);
    updateURL({ view });
  };

  // 部屋タイプ一覧取得
  const { data: roomTypes } = useQuery({
    queryKey: ['room-types'],
    queryFn: () => calendarApi.getRoomTypes(),
  });
  
  // 施設一覧取得
  const { data: facilities } = useQuery({
    queryKey: ['facilities'],
    queryFn: () => calendarApi.getFacilities(),
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
            予約カレンダー
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            施設の予約状況を一覧で確認
          </p>
        </div>

        {/* フィルターコントロール */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* 施設フィルター */}
            <div className="flex items-center space-x-2">
              <Building className="h-4 w-4 text-gray-500" />
              <select
                value={selectedRoomType}
                onChange={(e) => handleRoomTypeChange(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="">全施設</option>
                {facilities?.sort((a, b) => {
                  // 施設グループでソート、次に施設名でソート
                  if (a.facility_group && b.facility_group) {
                    const groupCompare = a.facility_group.localeCompare(b.facility_group);
                    if (groupCompare !== 0) return groupCompare;
                  } else if (a.facility_group) {
                    return -1;
                  } else if (b.facility_group) {
                    return 1;
                  }
                  return a.name.localeCompare(b.name);
                }).map((facility) => (
                  <option key={facility.id} value={facility.name}>
                    {facility.facility_group ? `[${facility.facility_group}] ${facility.name}` : facility.name}
                  </option>
                ))}
              </select>
            </div>

            {/* キャンセル表示切り替え */}
            <button
              onClick={() => handleShowCancelledChange(!showCancelled)}
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
              onClick={() => handleViewTypeChange('month')}
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
              onClick={() => handleViewTypeChange('week')}
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
            onDateChange={handleDateChange}
            reservations={reservations}
            facilities={facilities || []}
            selectedRoomType={selectedRoomType}
            showCancelled={showCancelled}
          />
        ) : (
          <WeekCalendarV2
            currentDate={currentDate}
            onDateChange={handleDateChange}
            reservations={reservations}
            roomTypes={roomTypes || []}
            facilities={facilities || []}
            selectedRoomType={selectedRoomType}
            showCancelled={showCancelled}
          />
        )}

      </div>
    </MainLayout>
  );
}