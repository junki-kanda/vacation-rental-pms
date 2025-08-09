'use client';

import { useState, useMemo } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, startOfWeek, endOfWeek, isSameMonth, isToday, isSameDay, parseISO, addDays } from 'date-fns';
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

export default function MonthCalendarV2({ 
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

  const weeks = useMemo(() => {
    const weeksArray = [];
    for (let i = 0; i < days.length; i += 7) {
      weeksArray.push(days.slice(i, i + 7));
    }
    return weeksArray;
  }, [days]);

  const weekDays = ['日', '月', '火', '水', '木', '金', '土'];

  // フィルター済みの予約データ
  const filteredReservations = useMemo(() => {
    let filtered = reservations;
    
    if (!showCancelled) {
      filtered = filtered.filter(res => res.reservation_type !== 'キャンセル');
    }
    
    if (selectedRoomType) {
      filtered = filtered.filter(res => res.room_type === selectedRoomType);
    }
    
    return filtered;
  }, [reservations, showCancelled, selectedRoomType]);

  // 週単位で予約を処理
  const getReservationsForWeek = (week: Date[]) => {
    const weekStart = week[0];
    const weekEnd = week[week.length - 1];
    
    return filteredReservations.filter(res => {
      const checkIn = parseISO(res.start || res.check_in_date || '');
      const checkOut = parseISO(res.end || res.check_out_date || '');
      
      // この週に関連する予約（開始、終了、または通過）
      return checkOut >= weekStart && checkIn <= weekEnd;
    }).map(res => {
      const checkIn = parseISO(res.start || res.check_in_date || '');
      const checkOut = parseISO(res.end || res.check_out_date || '');
      const guestName = res.guest_name || res.title?.split(' (')[0] || '不明';
      
      // この週における表示範囲を計算
      const displayStart = checkIn < weekStart ? weekStart : checkIn;
      const displayEnd = checkOut > weekEnd ? weekEnd : checkOut;
      
      // 開始位置と幅を計算（0-6の曜日インデックス）
      const startDay = week.findIndex(day => isSameDay(day, displayStart));
      const endDay = week.findIndex(day => isSameDay(day, displayEnd));
      const width = endDay - startDay + 1;
      
      // 同日チェックイン・アウトの検出
      const isSameDayInOut = isSameDay(checkIn, checkOut);
      
      // 他の予約との衝突検出（同じ部屋タイプ、同じ日）
      const hasConflictOnCheckIn = filteredReservations.some(other => 
        other.id !== res.id && 
        other.room_type === res.room_type &&
        isSameDay(parseISO(other.end || other.check_out_date || ''), checkIn)
      );
      
      const hasConflictOnCheckOut = filteredReservations.some(other => 
        other.id !== res.id && 
        other.room_type === res.room_type &&
        isSameDay(parseISO(other.start || other.check_in_date || ''), checkOut)
      );
      
      return {
        ...res,
        guestName,
        displayStart,
        displayEnd,
        startDay,
        width,
        isFirstWeek: checkIn >= weekStart && checkIn <= weekEnd,
        isLastWeek: checkOut >= weekStart && checkOut <= weekEnd,
        isSameDayInOut,
        hasConflictOnCheckIn,
        hasConflictOnCheckOut,
        // 表示位置（上下）を決定するための情報
        row: 0 // これは後で計算
      };
    });
  };

  // 予約タイプによる色を取得
  const getReservationColor = (type: string) => {
    switch (type) {
      case '予約':
        return 'bg-blue-500';
      case 'キャンセル':
        return 'bg-red-500';
      case '変更':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
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

        {/* 週ごとの表示 */}
        <div className="border-l border-t">
          {weeks.map((week, weekIndex) => {
            const weekReservations = getReservationsForWeek(week);
            
            // 各予約の表示行を計算（重複を避ける）
            const rows: any[][] = [];
            weekReservations.forEach(res => {
              let placed = false;
              for (let rowIndex = 0; rowIndex < rows.length; rowIndex++) {
                const canPlace = !rows[rowIndex].some(existing => 
                  // 期間が重複するかチェック
                  !(res.startDay > existing.startDay + existing.width - 1 || 
                    res.startDay + res.width - 1 < existing.startDay)
                );
                
                if (canPlace) {
                  rows[rowIndex].push(res);
                  res.row = rowIndex;
                  placed = true;
                  break;
                }
              }
              
              if (!placed) {
                rows.push([res]);
                res.row = rows.length - 1;
              }
            });
            
            const rowHeight = Math.max(80, 30 + rows.length * 25);
            
            return (
              <div key={weekIndex} className="relative" style={{ height: `${rowHeight}px` }}>
                {/* 日付セル */}
                <div className="absolute inset-0 grid grid-cols-7">
                  {week.map((day, dayIndex) => {
                    const isCurrentMonth = isSameMonth(day, currentDate);
                    const isTodayDate = isToday(day);
                    const dayOfWeek = day.getDay();
                    
                    return (
                      <div
                        key={day.toISOString()}
                        className={`border-r border-b relative ${
                          !isCurrentMonth ? 'bg-gray-50' : isTodayDate ? 'bg-blue-50' : 'bg-white'
                        }`}
                      >
                        <div className={`text-sm p-1 font-medium ${
                          !isCurrentMonth ? 'text-gray-400' : 
                          dayOfWeek === 0 ? 'text-red-500' : 
                          dayOfWeek === 6 ? 'text-blue-500' : 
                          'text-gray-700'
                        }`}>
                          {format(day, 'd')}
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                {/* 予約バー */}
                <div className="absolute inset-0 pointer-events-none">
                  {weekReservations.map((res, resIndex) => {
                    const leftPosition = (res.startDay / 7) * 100;
                    const widthPercentage = (res.width / 7) * 100;
                    const topPosition = 25 + res.row * 25;
                    
                    let borderRadius = '4px';
                    let leftPadding = '4px';
                    let rightPadding = '4px';
                    
                    // チェックイン/チェックアウトの衝突がある場合の処理
                    if (res.hasConflictOnCheckIn && res.isFirstWeek) {
                      leftPadding = '50%';
                      borderRadius = '0 4px 4px 0';
                    } else if (res.isFirstWeek) {
                      borderRadius = '4px 0 0 4px';
                    }
                    
                    if (res.hasConflictOnCheckOut && res.isLastWeek) {
                      rightPadding = '50%';
                      borderRadius = borderRadius === '4px 0 0 4px' ? '4px' : '4px 0 0 4px';
                    } else if (res.isLastWeek) {
                      borderRadius = borderRadius === '4px 0 0 4px' ? '4px' : '0 4px 4px 0';
                    }
                    
                    if (!res.isFirstWeek && !res.isLastWeek) {
                      borderRadius = '0';
                    }
                    
                    return (
                      <div
                        key={`${res.id}-${resIndex}`}
                        className={`absolute ${getReservationColor(res.reservation_type)} text-white text-xs px-1 py-0.5 pointer-events-auto cursor-pointer hover:opacity-90 transition-opacity`}
                        style={{
                          left: `calc(${leftPosition}% + ${leftPadding})`,
                          width: `calc(${widthPercentage}% - ${leftPadding} - ${rightPadding})`,
                          top: `${topPosition}px`,
                          borderRadius: borderRadius,
                          height: '20px',
                          lineHeight: '19px',
                          zIndex: 10,
                        }}
                        title={`${res.guestName}\n${res.room_type}\n${res.ota_name || ''}\n${format(parseISO(res.start || res.check_in_date || ''), 'MM/dd')} - ${format(parseISO(res.end || res.check_out_date || ''), 'MM/dd')}`}
                      >
                        <div className="truncate">
                          {res.isFirstWeek && res.hasConflictOnCheckIn && '→ '}
                          {res.guestName}
                          {res.isLastWeek && res.hasConflictOnCheckOut && ' →'}
                        </div>
                      </div>
                    );
                  })}
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
              <div className="w-8 h-4 bg-blue-500 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">予約</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-4 bg-red-500 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">キャンセル</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-4 bg-yellow-500 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">変更</span>
            </div>
          </div>
          <div className="text-xs text-gray-600 italic">
            同日チェックイン・アウトがある場合は自動的に左右に分割表示
          </div>
        </div>
      </div>
    </div>
  );
}