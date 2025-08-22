'use client';

import { useMemo, memo, useCallback } from 'react';
import { format, startOfWeek, endOfWeek, eachDayOfInterval, addWeeks, subWeeks, isToday, isSameDay, parseISO } from 'date-fns';
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

interface WeekCalendarProps {
  currentDate: Date;
  onDateChange: (date: Date) => void;
  reservations?: Reservation[];
  roomTypes?: any[];
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
}

// 週表示セルのメモ化
const WeekCell = memo(function WeekCell({ 
  day, 
  reservations,
  facilities = []
}: {
  day: Date;
  reservations: ProcessedReservation[];
  facilities: Facility[];
}) {
  const dayReservations = reservations.filter(res => 
    day >= res.checkIn && day < res.checkOut
  );

  // 施設別にグループ化
  const facilitiesData = useMemo(() => {
    return facilities.map(facility => {
      const facilityReservations = dayReservations.filter(res => 
        res.facilityName === facility.name
      );
      
      return {
        facility,
        reservations: facilityReservations
      };
    });
  }, [facilities, dayReservations]);

  return (
    <div className="flex-1 border-r border-gray-200">
      <div className={`p-2 text-center text-sm font-medium border-b ${
        isToday(day) ? 'bg-blue-50 text-blue-600' : 'bg-gray-50 text-gray-600'
      }`}>
        <div>{format(day, 'M/d')}</div>
        <div className="text-xs">{format(day, 'E', { locale: ja })}</div>
      </div>
      
      <div className="divide-y divide-gray-100">
        {facilitiesData.map(({ facility, reservations: facilityReservations }) => (
          <div key={facility.id} className="min-h-[60px] p-1 flex flex-col">
            <div className="text-xs text-gray-500 mb-1 truncate">
              {facility.facility_group ? `[${facility.facility_group}] ` : ''}{facility.name}
            </div>
            {facilityReservations.map((reservation) => (
              <div
                key={reservation.id}
                className="text-xs bg-blue-500 text-white px-1 py-0.5 rounded mb-1 truncate"
                style={{ opacity: reservation.reservation_type === 'キャンセル' ? 0.5 : 1 }}
                title={`${reservation.guestName} (${reservation.ota_name || '直接'})`}
              >
                {reservation.guestName}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
});

function WeekCalendarV3Component({
  currentDate,
  onDateChange,
  reservations = [],
  roomTypes = [],
  facilities = [],
  selectedRoomType,
  showCancelled = false
}: WeekCalendarProps) {
  
  // 週の日付計算
  const weekDates = useMemo(() => {
    const weekStart = startOfWeek(currentDate, { locale: ja });
    const weekEnd = endOfWeek(currentDate, { locale: ja });
    const days = eachDayOfInterval({ start: weekStart, end: weekEnd });
    
    return { weekStart, weekEnd, days };
  }, [currentDate]);

  const { weekStart, weekEnd, days } = weekDates;

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

  // 高速予約処理
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
        ota_name: res.ota_name
      } as ProcessedReservation;
    });
  }, [filteredReservations]);

  // フィルター済み施設
  const filteredFacilities = useMemo(() => {
    if (selectedRoomType) {
      return facilities.filter(f => f.name === selectedRoomType);
    }
    return facilities;
  }, [facilities, selectedRoomType]);

  // ナビゲーション関数をメモ化
  const goToPreviousWeek = useCallback(() => {
    onDateChange(subWeeks(currentDate, 1));
  }, [currentDate, onDateChange]);

  const goToNextWeek = useCallback(() => {
    onDateChange(addWeeks(currentDate, 1));
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
            {format(weekStart, 'yyyy年MM月dd日', { locale: ja })} - {format(weekEnd, 'MM月dd日', { locale: ja })}
          </h2>
          <button
            onClick={goToToday}
            className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
          >
            今週
          </button>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={goToPreviousWeek}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            onClick={goToNextWeek}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* 週表示グリッド */}
      <div className="flex">
        {days.map((day) => (
          <WeekCell
            key={day.toISOString()}
            day={day}
            reservations={processedReservations}
            facilities={filteredFacilities}
          />
        ))}
      </div>
    </div>
  );
}

const WeekCalendarV3 = memo(WeekCalendarV3Component);
export default WeekCalendarV3;