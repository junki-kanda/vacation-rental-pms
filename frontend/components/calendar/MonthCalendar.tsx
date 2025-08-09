'use client';

import { useState, useMemo } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, startOfWeek, endOfWeek, isSameMonth, isToday, isSameDay, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface Reservation {
  id: number;
  guest_name?: string;
  title?: string;
  room_type: string;
  check_in_date?: string;
  check_out_date?: string;
  start?: string;
  end?: string;
  reservation_type: string;
  ota_name?: string;
  guest_count?: number;
}

interface MonthCalendarProps {
  currentDate: Date;
  onDateChange: (date: Date) => void;
  reservations?: Reservation[];
  selectedRoomType?: string;
  showCancelled?: boolean;
}

export default function MonthCalendar({ 
  currentDate, 
  onDateChange, 
  reservations = [],
  selectedRoomType,
  showCancelled = false
}: MonthCalendarProps) {
  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarStart = startOfWeek(monthStart, { locale: ja });
  const calendarEnd = endOfWeek(monthEnd, { locale: ja });

  const days = useMemo(() => {
    return eachDayOfInterval({ start: calendarStart, end: calendarEnd });
  }, [calendarStart, calendarEnd]);

  const weekDays = ['日', '月', '火', '水', '木', '金', '土'];

  // フィルター済みの予約データ
  const filteredReservations = useMemo(() => {
    let filtered = reservations;
    
    // キャンセル表示フィルター
    if (!showCancelled) {
      filtered = filtered.filter(res => res.reservation_type !== 'キャンセル');
    }
    
    // 部屋タイプフィルター
    if (selectedRoomType) {
      filtered = filtered.filter(res => res.room_type === selectedRoomType);
    }
    
    return filtered;
  }, [reservations, showCancelled, selectedRoomType]);

  // 特定の日付のチェックイン/チェックアウトを取得
  const getReservationsForDay = (day: Date) => {
    const checkIns: any[] = [];
    const checkOuts: any[] = [];
    
    filteredReservations.forEach(res => {
      const checkIn = parseISO(res.start || res.check_in_date || '');
      const checkOut = parseISO(res.end || res.check_out_date || '');
      
      if (isSameDay(checkIn, day)) {
        checkIns.push({
          ...res,
          guestName: res.guest_name || res.title?.split(' (')[0] || '不明'
        });
      }
      
      if (isSameDay(checkOut, day)) {
        checkOuts.push({
          ...res,
          guestName: res.guest_name || res.title?.split(' (')[0] || '不明'
        });
      }
    });
    
    return { checkIns, checkOuts };
  };

  // 予約タイプによる色を取得
  const getReservationColor = (type: string) => {
    switch (type) {
      case '予約':
        return 'bg-blue-500 text-white';
      case 'キャンセル':
        return 'bg-red-500 text-white';
      case '変更':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const goToPreviousMonth = () => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() - 1);
    onDateChange(newDate);
  };

  const goToNextMonth = () => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + 1);
    onDateChange(newDate);
  };

  const goToToday = () => {
    onDateChange(new Date());
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-2">
          <button
            onClick={goToPreviousMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            onClick={goToToday}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            今日
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
          <h2 className="text-xl font-bold ml-4">
            {format(currentDate, 'yyyy年MM月', { locale: ja })}
          </h2>
        </div>
      </div>

      {/* カレンダーグリッド */}
      <div className="p-4">
        {/* 曜日ヘッダー */}
        <div className="grid grid-cols-7 gap-0 mb-1">
          {weekDays.map((day, index) => (
            <div
              key={day}
              className={`text-center text-sm font-semibold p-2 ${
                index === 0 ? 'text-red-500' : index === 6 ? 'text-blue-500' : 'text-gray-700'
              }`}
            >
              {day}
            </div>
          ))}
        </div>

        {/* 日付グリッド */}
        <div className="grid grid-cols-7 gap-0 border-l border-t">
          {days.map((day, dayIdx) => {
            const isCurrentMonth = isSameMonth(day, currentDate);
            const isTodayDate = isToday(day);
            const dayOfWeek = day.getDay();

            return (
              <div
                key={day.toISOString()}
                className={`border-r border-b ${
                  !isCurrentMonth ? 'bg-gray-50' : isTodayDate ? 'bg-blue-50' : 'bg-white'
                }`}
                style={{ minHeight: '100px' }}
              >
                {/* 日付ヘッダー */}
                <div className={`text-sm p-1 font-medium ${
                  !isCurrentMonth ? 'text-gray-400' : 
                  dayOfWeek === 0 ? 'text-red-500' : 
                  dayOfWeek === 6 ? 'text-blue-500' : 
                  'text-gray-700'
                }`}>
                  {format(day, 'd')}
                </div>

                {/* 予約表示エリア（左右2分割） */}
                <div className="relative" style={{ height: '80px' }}>
                  <div className="absolute inset-0 flex">
                    {/* 左側：チェックアウト用 */}
                    <div className="w-1/2 border-r-2 border-dashed border-gray-300 bg-gradient-to-r from-red-50 to-transparent p-1">
                      <div className="h-full flex flex-col">
                        {/* ヘッダー */}
                        <div className="text-xs text-red-600 font-bold text-center mb-1" style={{ fontSize: '10px', lineHeight: '12px' }}>
                          OUT
                        </div>
                        {/* チェックアウト予約スペース */}
                        <div className="flex-1 space-y-0.5 overflow-y-auto overflow-x-hidden">
                          {(() => {
                            const { checkOuts } = getReservationsForDay(day);
                            return checkOuts.map((res, idx) => (
                              <div
                                key={`out-${res.id}-${idx}`}
                                className={`${getReservationColor(res.reservation_type)} text-xs px-1 py-0.5 rounded-sm truncate`}
                                title={`${res.guestName}\n${res.room_type}\n${res.ota_name || ''}`}
                                style={{ fontSize: '9px', lineHeight: '11px' }}
                              >
                                {res.guestName}
                              </div>
                            ));
                          })()}
                        </div>
                      </div>
                    </div>

                    {/* 右側：チェックイン用 */}
                    <div className="w-1/2 bg-gradient-to-l from-green-50 to-transparent p-1">
                      <div className="h-full flex flex-col">
                        {/* ヘッダー */}
                        <div className="text-xs text-green-600 font-bold text-center mb-1" style={{ fontSize: '10px', lineHeight: '12px' }}>
                          IN
                        </div>
                        {/* チェックイン予約スペース */}
                        <div className="flex-1 space-y-0.5 overflow-y-auto overflow-x-hidden">
                          {(() => {
                            const { checkIns } = getReservationsForDay(day);
                            return checkIns.map((res, idx) => (
                              <div
                                key={`in-${res.id}-${idx}`}
                                className={`${getReservationColor(res.reservation_type)} text-xs px-1 py-0.5 rounded-sm truncate`}
                                title={`${res.guestName}\n${res.room_type}\n${res.ota_name || ''}`}
                                style={{ fontSize: '9px', lineHeight: '11px' }}
                              >
                                {res.guestName}
                              </div>
                            ));
                          })()}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* 中央の分割線（視覚的強調） */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-400 opacity-30 transform -translate-x-1/2 pointer-events-none"></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 凡例 */}
      <div className="border-t p-4 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center">
              <div className="w-8 h-4 bg-gradient-to-r from-red-50 to-white border border-red-300 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">チェックアウト（左側）</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-4 bg-gradient-to-l from-green-50 to-white border border-green-300 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">チェックイン（右側）</span>
            </div>
            <div className="flex items-center">
              <div className="w-px h-4 bg-gray-400 mx-2"></div>
              <span className="text-gray-500 text-xs">中央の点線が境界</span>
            </div>
          </div>
          <div className="text-xs text-gray-600 italic">
            同じ施設のチェックアウト・チェックインが同日でも重ならずに表示されます
          </div>
        </div>
      </div>
    </div>
  );
}