'use client';

import { useMemo, memo, useCallback, useState, useRef, useEffect } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, startOfWeek, endOfWeek, isSameMonth, isToday, isSameDay, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ChevronLeft, ChevronRight } from 'lucide-react';

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

interface VirtualizedCalendarProps {
  currentDate: Date;
  onDateChange: (date: Date) => void;
  reservations?: Reservation[];
  facilities?: Facility[];
  selectedRoomType?: string;
  showCancelled?: boolean;
}

// 仮想化されたカレンダーセル
const VirtualCalendarCell = memo(function VirtualCalendarCell({ 
  day, 
  isCurrentMonth, 
  isToday: isTodayCell,
  reservations,
  style
}: {
  day: Date;
  isCurrentMonth: boolean;
  isToday: boolean;
  reservations: any[];
  style?: React.CSSProperties;
}) {
  // 最大5件までの予約のみ表示
  const visibleReservations = useMemo(() => {
    const dayReservations = reservations.filter(res => 
      day >= res.checkIn && day < res.checkOut
    );
    
    return dayReservations.slice(0, 5);
  }, [reservations, day]);

  const hasMoreReservations = useMemo(() => {
    const dayReservations = reservations.filter(res => 
      day >= res.checkIn && day < res.checkOut
    );
    return dayReservations.length > 5;
  }, [reservations, day]);

  return (
    <div 
      className={`min-h-[120px] border-r border-b border-gray-200 relative ${
        !isCurrentMonth ? 'bg-gray-50' : 'bg-white'
      } ${isTodayCell ? 'bg-blue-50' : ''}`}
      style={style}
    >
      <div className={`text-sm font-medium p-2 ${
        !isCurrentMonth ? 'text-gray-400' : 'text-gray-900'
      } ${isTodayCell ? 'text-blue-600' : ''}`}>
        {format(day, 'd')}
      </div>
      <div className="absolute inset-2 top-8 overflow-hidden">
        {visibleReservations.map((reservation, index) => (
          <div
            key={`${reservation.id}-${index}`}
            className="text-xs bg-blue-500 text-white px-1 py-0.5 rounded mb-1 truncate"
            style={{ opacity: reservation.reservation_type === 'キャンセル' ? 0.5 : 1 }}
            title={`${reservation.guestName} (${reservation.facilityName})`}
          >
            {reservation.guestName}
          </div>
        ))}
        {hasMoreReservations && (
          <div className="text-xs text-gray-500 truncate">
            +{reservations.filter(res => day >= res.checkIn && day < res.checkOut).length - 5}件
          </div>
        )}
      </div>
    </div>
  );
});

function VirtualizedCalendarComponent({ 
  currentDate, 
  onDateChange, 
  reservations = [],
  facilities = [],
  selectedRoomType,
  showCancelled = false
}: VirtualizedCalendarProps) {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 42 });
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  // カレンダーの日付計算
  const calendarDates = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart, { locale: ja });
    const calendarEnd = endOfWeek(monthEnd, { locale: ja });
    
    const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });
    
    return {
      monthStart,
      monthEnd,
      calendarStart,
      calendarEnd,
      days
    };
  }, [currentDate]);

  const { monthStart, days } = calendarDates;
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

  // 予約データの前処理
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
        checkInTime: checkIn.getTime(),
        checkOutTime: checkOut.getTime()
      };
    });
  }, [filteredReservations]);

  // スクロールハンドラー
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;
    
    const container = scrollContainerRef.current;
    const scrollTop = container.scrollTop;
    const cellHeight = 120;
    const rowsPerView = Math.ceil(container.clientHeight / cellHeight);
    const totalRows = Math.ceil(days.length / 7);
    
    const startRow = Math.floor(scrollTop / cellHeight);
    const endRow = Math.min(startRow + rowsPerView + 2, totalRows);
    
    setVisibleRange({
      start: startRow * 7,
      end: Math.min(endRow * 7, days.length)
    });
  }, [days.length]);

  // スクロールイベントの設定
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      handleScroll(); // 初期表示
      
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [handleScroll]);

  // ナビゲーション関数
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

  // 仮想化されたセルを描画
  const renderVirtualizedCells = () => {
    const cells = [];
    const cellHeight = 120;
    
    for (let i = visibleRange.start; i < visibleRange.end; i++) {
      if (i >= days.length) break;
      
      const day = days[i];
      const row = Math.floor(i / 7);
      const col = i % 7;
      
      cells.push(
        <div
          key={day.toISOString()}
          style={{
            position: 'absolute',
            top: row * cellHeight + 40, // ヘッダー分のオフセット
            left: `${(col / 7) * 100}%`,
            width: `${100 / 7}%`,
            height: cellHeight
          }}
        >
          <VirtualCalendarCell
            day={day}
            isCurrentMonth={isSameMonth(day, monthStart)}
            isToday={isToday(day)}
            reservations={processedReservations}
          />
        </div>
      );
    }
    
    return cells;
  };

  const totalHeight = Math.ceil(days.length / 7) * 120 + 40; // ヘッダー分を追加

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

      {/* 仮想化されたカレンダーグリッド */}
      <div className="relative">
        {/* 曜日ヘッダー */}
        <div className="grid grid-cols-7 sticky top-0 z-10 bg-white">
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
        </div>

        {/* 仮想スクロールコンテナ */}
        <div 
          ref={scrollContainerRef}
          className="relative overflow-auto"
          style={{ height: '600px' }}
        >
          <div style={{ height: totalHeight, position: 'relative' }}>
            {renderVirtualizedCells()}
          </div>
        </div>
      </div>
    </div>
  );
}

const VirtualizedCalendar = memo(VirtualizedCalendarComponent);
export default VirtualizedCalendar;