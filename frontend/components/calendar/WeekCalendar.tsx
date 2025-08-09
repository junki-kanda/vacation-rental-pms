'use client';

import { useState, useMemo } from 'react';
import { format, startOfWeek, endOfWeek, eachDayOfInterval, addWeeks, subWeeks, isToday, isSameDay, parseISO } from 'date-fns';
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

interface WeekCalendarProps {
  currentDate: Date;
  onDateChange: (date: Date) => void;
  reservations?: Reservation[];
  roomTypes?: string[];
  selectedRoomType?: string;
  showCancelled?: boolean;
}

export default function WeekCalendar({ 
  currentDate, 
  onDateChange, 
  reservations = [],
  roomTypes = [],
  selectedRoomType,
  showCancelled = false
}: WeekCalendarProps) {
  const weekStart = startOfWeek(currentDate, { locale: ja });
  const weekEnd = endOfWeek(currentDate, { locale: ja });

  const days = useMemo(() => {
    return eachDayOfInterval({ start: weekStart, end: weekEnd });
  }, [weekStart, weekEnd]);

  const goToPreviousWeek = () => {
    onDateChange(subWeeks(currentDate, 1));
  };

  const goToNextWeek = () => {
    onDateChange(addWeeks(currentDate, 1));
  };

  const goToToday = () => {
    onDateChange(new Date());
  };

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

  // 表示する部屋タイプのリスト
  const displayRoomTypes = useMemo(() => {
    if (selectedRoomType) {
      return [selectedRoomType];
    }
    return roomTypes;
  }, [roomTypes, selectedRoomType]);

  // 特定の日付と部屋タイプに該当する予約を取得
  const getReservationsForCell = (day: Date, roomType: string) => {
    return filteredReservations.filter(res => {
      const checkIn = parseISO(res.start || res.check_in_date || '');
      const checkOut = parseISO(res.end || res.check_out_date || '');
      
      // その日がチェックイン日かチェックアウト日か判定
      const isCheckInDay = isSameDay(checkIn, day);
      const isCheckOutDay = isSameDay(checkOut, day);
      const isStayDay = day >= checkIn && day <= checkOut;
      
      return res.room_type === roomType && isStayDay;
    }).map(res => {
      const checkIn = parseISO(res.start || res.check_in_date || '');
      const checkOut = parseISO(res.end || res.check_out_date || '');
      const isCheckInDay = isSameDay(checkIn, day);
      const isCheckOutDay = isSameDay(checkOut, day);
      
      return {
        ...res,
        isCheckIn: isCheckInDay,
        isCheckOut: isCheckOutDay,
        guestName: res.guest_name || res.title?.split(' (')[0] || '不明'
      };
    });
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

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-2">
          <button
            onClick={goToPreviousWeek}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            onClick={goToToday}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            今週
          </button>
          <button
            onClick={goToNextWeek}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
          <h2 className="text-xl font-bold ml-4">
            {format(weekStart, 'yyyy年MM月dd日', { locale: ja })} - {format(weekEnd, 'MM月dd日', { locale: ja })}
          </h2>
        </div>
      </div>

      {/* 週カレンダーグリッド（施設別表示） */}
      <div className="overflow-x-auto">
        <div className="min-w-[900px]">
          {/* 曜日ヘッダー */}
          <div className="grid grid-cols-8 border-b bg-gray-50">
            <div className="p-3 text-sm font-semibold text-gray-700 border-r sticky left-0 bg-gray-50 z-10">
              施設
            </div>
            {days.map((day) => {
              const isTodayDate = isToday(day);
              const dayOfWeek = day.getDay();
              
              return (
                <div
                  key={day.toISOString()}
                  className={`p-2 text-center border-r ${isTodayDate ? 'bg-blue-100' : ''}`}
                >
                  <div className={`text-xs font-medium ${
                    dayOfWeek === 0 ? 'text-red-600' : 
                    dayOfWeek === 6 ? 'text-blue-600' : 
                    'text-gray-700'
                  }`}>
                    {format(day, 'E', { locale: ja })}
                  </div>
                  <div className="text-lg font-bold">
                    {format(day, 'd')}
                  </div>
                </div>
              );
            })}
          </div>

          {/* 施設別の行 */}
          {displayRoomTypes.map((roomType, roomIndex) => (
            <div key={`${roomType}-${roomIndex}`} className="grid grid-cols-8 border-b hover:bg-gray-50">
              {/* 施設名 */}
              <div className="p-3 text-sm font-medium text-gray-900 border-r bg-white sticky left-0 z-10">
                {roomType}
              </div>
              
              {/* 各日のセル（左右分割） */}
              {days.map(day => {
                const reservations = getReservationsForCell(day, roomType);
                const checkouts = reservations.filter(r => r.isCheckOut);
                const checkins = reservations.filter(r => r.isCheckIn);
                const staying = reservations.filter(r => !r.isCheckIn && !r.isCheckOut);
                
                return (
                  <div
                    key={`${roomType}-${day.toISOString()}`}
                    className={`relative border-r ${isToday(day) ? 'bg-blue-50/30' : ''}`}
                    style={{ minHeight: '80px' }}
                  >
                    <div className="absolute inset-0 flex">
                      {/* 左側：チェックアウト */}
                      <div className="w-1/2 border-r border-dashed border-gray-300 bg-gradient-to-r from-red-50/30 to-transparent p-1">
                        <div className="space-y-1">
                          {checkouts.map((res, idx) => (
                            <div
                              key={`out-${res.id}-${idx}`}
                              className={`${getReservationColor(res.reservation_type)} text-xs p-1 rounded-l truncate`}
                              title={`${res.guestName} (${res.ota_name})`}
                              style={{ fontSize: '10px' }}
                            >
                              ← {res.guestName}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* 右側：チェックイン */}
                      <div className="w-1/2 bg-gradient-to-l from-green-50/30 to-transparent p-1">
                        <div className="space-y-1">
                          {checkins.map((res, idx) => (
                            <div
                              key={`in-${res.id}-${idx}`}
                              className={`${getReservationColor(res.reservation_type)} text-xs p-1 rounded-r truncate`}
                              title={`${res.guestName} (${res.ota_name})`}
                              style={{ fontSize: '10px' }}
                            >
                              → {res.guestName}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* 滞在中の予約（全幅表示） */}
                      {staying.length > 0 && (
                        <div className="absolute inset-x-0 top-0 p-1">
                          {staying.map((res, idx) => (
                            <div
                              key={`stay-${res.id}-${idx}`}
                              className={`${getReservationColor(res.reservation_type)} text-xs p-1 rounded truncate opacity-90`}
                              title={`${res.guestName} (${res.ota_name}) - 滞在中`}
                              style={{ fontSize: '10px' }}
                            >
                              {res.guestName}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
          
          {/* データがない場合の表示 */}
          {displayRoomTypes.length === 0 && (
            <div className="p-8 text-center text-gray-500">
              表示する施設がありません
            </div>
          )}
        </div>
      </div>

      {/* 凡例 */}
      <div className="border-t p-4 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center">
              <div className="w-8 h-4 bg-gradient-to-r from-red-50 to-transparent border border-red-300 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">チェックアウト時間帯（左側）</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-4 bg-gradient-to-l from-green-50 to-transparent border border-green-300 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">チェックイン時間帯（右側）</span>
            </div>
          </div>
          <div className="text-xs text-gray-600 italic">
            通常：チェックアウト 10:00 / チェックイン 15:00
          </div>
        </div>
      </div>
    </div>
  );
}