'use client';

import { useState, useMemo, memo, useCallback } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, startOfWeek, endOfWeek, isSameMonth, isToday, isSameDay, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Facility {
  id: number;
  name: string;
  facility_group?: string;
}

interface Reservation {
  id: number;
  guest_name?: string;
  title?: string;
  room_type: string;
  facility?: Facility;
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
  facilities?: Facility[];
  selectedRoomType?: string;
  showCancelled?: boolean;
}

interface ProcessedReservation {
  id: number;
  guestName: string;
  checkIn: Date;
  checkOut: Date;
  facilityName: string;
  reservation_type: string;
  ota_name?: string;
  checkInTime: number;
  checkOutTime: number;
  segments: ReservationSegment[];
  row: number;
}

interface ReservationSegment {
  weekIndex: number;
  startDay: number;
  endDay: number;
  isFirst: boolean;
  isLast: boolean;
  width: number;
  left: number;
}

// カレンダーセルをメモ化
const CalendarCell = memo(function CalendarCell({ 
  day, 
  isCurrentMonth, 
  isToday: isTodayCell,
  reservations 
}: {
  day: Date;
  isCurrentMonth: boolean;
  isToday: boolean;
  reservations: ProcessedReservation[];
}) {
  const dayReservations = reservations.filter(res => 
    day >= res.checkIn && day < res.checkOut
  );

  return (
    <div className={`min-h-[120px] border-r border-b border-gray-200 relative ${
      !isCurrentMonth ? 'bg-gray-50' : 'bg-white'
    } ${isTodayCell ? 'bg-blue-50' : ''}`}>
      <div className={`text-sm font-medium p-2 ${
        !isCurrentMonth ? 'text-gray-400' : 'text-gray-900'
      } ${isTodayCell ? 'text-blue-600' : ''}`}>
        {format(day, 'd')}
      </div>
      <div className="absolute inset-2 top-8">
        {dayReservations.map((reservation, index) => (
          <div
            key={`${reservation.id}-${index}`}
            className="text-xs bg-blue-500 text-white px-1 py-0.5 rounded mb-1 truncate"
            style={{ opacity: reservation.reservation_type === 'キャンセル' ? 0.5 : 1 }}
            title={`${reservation.guestName} (${reservation.facilityName})`}
          >
            {reservation.guestName}
          </div>
        ))}
      </div>
    </div>
  );
});

function MonthCalendarV4Component({ 
  currentDate, 
  onDateChange, 
  reservations = [],
  facilities = [],
  selectedRoomType,
  showCancelled = false
}: MonthCalendarProps) {
  const router = useRouter();
  
  // カレンダーの日付計算をメモ化
  const calendarDates = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart, { locale: ja });
    const calendarEnd = endOfWeek(monthEnd, { locale: ja });
    
    const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });
    const weeks = [];
    for (let i = 0; i < days.length; i += 7) {
      weeks.push(days.slice(i, i + 7));
    }
    
    return {
      monthStart,
      monthEnd,
      calendarStart,
      calendarEnd,
      days,
      weeks
    };
  }, [currentDate]);

  const { monthStart, days, weeks } = calendarDates;
  const weekDays = ['日', '月', '火', '水', '木', '金', '土'];

  // 高速フィルタリング
  const filteredReservations = useMemo(() => {
    if (!reservations?.length) return [];
    
    return reservations.filter(res => {
      if (!showCancelled && res.reservation_type === 'キャンセル') return false;
      if (selectedRoomType) {
        return res.room_type === selectedRoomType || res.facility?.name === selectedRoomType;
      }
      return true;
    });
  }, [reservations, showCancelled, selectedRoomType]);

  // 高速予約処理（簡略化）
  const processedReservations = useMemo(() => {
    return filteredReservations.map(res => {
      const checkIn = parseISO(res.start || res.check_in_date || '');
      const checkOut = parseISO(res.end || res.check_out_date || '');
      
      return {
        id: res.id,
        guestName: res.guest_name || res.title?.split(' (')[0] || '不明',
        checkIn,
        checkOut,
        facilityName: res.facility?.name || res.room_type,
        reservation_type: res.reservation_type,
        ota_name: res.ota_name,
        checkInTime: checkIn.getTime(),
        checkOutTime: checkOut.getTime(),
        segments: [],
        row: 0
      } as ProcessedReservation;
    });
  }, [filteredReservations]);

  // ナビゲーション関数をメモ化
  const goToPreviousMonth = useCallback(() => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() - 1);
    onDateChange(newDate);
  }, [currentDate, onDateChange]);

  const goToNextMonth = useCallback(() => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + 1);
    onDateChange(newDate);
  }, [currentDate, onDateChange]);

  const goToToday = useCallback(() => {
    onDateChange(new Date());
  }, [onDateChange]);

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {format(monthStart, 'yyyy年MM月', { locale: ja })}
          </h2>
          <button
            onClick={goToToday}
            className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
          >
            今日
          </button>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={goToPreviousMonth}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* カレンダーグリッド */}
      <div className="grid grid-cols-7">
        {/* 曜日ヘッダー */}
        {weekDays.map((day, index) => (
          <div
            key={index}
            className={`p-3 text-center text-sm font-medium border-r border-b border-gray-200 ${
              index === 0 ? 'text-red-600' : index === 6 ? 'text-blue-600' : 'text-gray-600'
            }`}
          >
            {day}
          </div>
        ))}

        {/* カレンダーセル */}
        {days.map((day) => (
          <CalendarCell
            key={day.toISOString()}
            day={day}
            isCurrentMonth={isSameMonth(day, monthStart)}
            isToday={isToday(day)}
            reservations={processedReservations}
          />
        ))}
      </div>
    </div>
  );
}

const MonthCalendarV4 = memo(MonthCalendarV4Component);
export default MonthCalendarV4;