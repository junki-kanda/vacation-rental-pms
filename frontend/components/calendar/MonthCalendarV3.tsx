'use client';

import { useState, useMemo, memo } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, startOfWeek, endOfWeek, isSameMonth, isToday, isSameDay, parseISO, differenceInDays } from 'date-fns';
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

interface ProcessedReservation extends Reservation {
  guestName: string;
  checkIn: Date;
  checkOut: Date;
  displaySegments: {
    weekIndex: number;
    startDay: number;
    endDay: number;
    isFirst: boolean;
    isLast: boolean;
    hasLeftConflict: boolean;
    hasRightConflict: boolean;
  }[];
  row: number;
}

function MonthCalendarV3Component({ 
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

  const { days, weeks } = calendarDates;

  const weekDays = ['日', '月', '火', '水', '木', '金', '土'];

  // フィルター済みの予約データ（最適化版）
  const filteredReservations = useMemo(() => {
    if (!reservations?.length) return [];
    
    return reservations.filter(res => {
      // キャンセル済み予約のフィルタリング
      if (!showCancelled && res.reservation_type === 'キャンセル') {
        return false;
      }
      
      // 施設フィルタリング
      if (selectedRoomType) {
        return res.room_type === selectedRoomType || 
               (res.facility?.name === selectedRoomType);
      }
      
      return true;
    });
  }, [reservations, showCancelled, selectedRoomType]);

  // 予約データの前処理（日付パース）
  const preprocessedReservations = useMemo(() => {
    return filteredReservations.map(res => {
      const checkIn = parseISO(res.start || res.check_in_date || '');
      const checkOut = parseISO(res.end || res.check_out_date || '');
      const guestName = res.guest_name || res.title?.split(' (')[0] || '不明';
      const facilityName = res.facility?.name || res.room_type;
      
      return {
        ...res,
        guestName,
        checkIn,
        checkOut,
        facilityName,
        checkInTime: checkIn.getTime(),
        checkOutTime: checkOut.getTime()
      };
    });
  }, [filteredReservations]);

  // 予約データの施設別グループ化
  const facilityGroups = useMemo(() => {
    const groups = new Map<string, typeof preprocessedReservations>();
    
    preprocessedReservations.forEach(res => {
      if (!groups.has(res.facilityName)) {
        groups.set(res.facilityName, []);
      }
      groups.get(res.facilityName)!.push(res);
    });
    
    return groups;
  }, [preprocessedReservations]);

  // 予約データを処理（最適化版）
  const processedReservations = useMemo(() => {
    const result: ProcessedReservation[] = [];
    
    facilityGroups.forEach(group => {
      // グループ内の予約をソート
      const sortedGroup = group.sort((a, b) => a.checkInTime - b.checkInTime);
      
      sortedGroup.forEach(res => {
        const processed: ProcessedReservation = {
          ...res,
          displaySegments: [],
          row: 0
        };
      
        // 各週でのセグメントを計算（最適化版）
        const weekStartTime = weeks[0][0].getTime();
        const weekLength = 7 * 24 * 60 * 60 * 1000; // 1週間のミリ秒
        
        weeks.forEach((week, weekIndex) => {
          const weekStart = week[0];
          const weekEnd = week[6];
          const weekStartMs = weekStart.getTime();
          const weekEndMs = weekEnd.getTime();
        const weekEnd = week[week.length - 1];
        
        // この週に予約が関係するか確認
        if (checkOut >= weekStart && checkIn <= weekEnd) {
          const segmentStart = checkIn > weekStart ? checkIn : weekStart;
          const segmentEnd = checkOut < weekEnd ? checkOut : weekEnd;
          
          const startDayIndex = week.findIndex(day => isSameDay(day, segmentStart));
          const endDayIndex = week.findIndex(day => isSameDay(day, segmentEnd));
          
          if (startDayIndex >= 0 && endDayIndex >= 0) {
            processed.displaySegments.push({
              weekIndex,
              startDay: startDayIndex,
              endDay: endDayIndex,
              isFirst: isSameDay(segmentStart, checkIn),
              isLast: isSameDay(segmentEnd, checkOut),
              hasLeftConflict: false,
              hasRightConflict: false
            });
          }
        }
      });
      
      // 施設名を取得（facility.nameまたはroom_type）
      const facilityName = res.facility?.name || res.room_type;
      
      if (!facilityGroups.has(facilityName)) {
        facilityGroups.set(facilityName, []);
      }
      facilityGroups.get(facilityName)!.push(processed);
    });
    
    // 各施設内で同日チェックイン・アウトの競合を検出
    facilityGroups.forEach(group => {
      group.forEach(res => {
        // 同じ施設の他の予約と比較
        group.forEach(other => {
          if (res.id !== other.id) {
            // チェックイン日に他の予約のチェックアウトがあるか
            if (isSameDay(res.checkIn, other.checkOut)) {
              res.displaySegments.forEach(seg => {
                if (seg.isFirst) {
                  seg.hasLeftConflict = true;
                }
              });
            }
            // チェックアウト日に他の予約のチェックインがあるか
            if (isSameDay(res.checkOut, other.checkIn)) {
              res.displaySegments.forEach(seg => {
                if (seg.isLast) {
                  seg.hasRightConflict = true;
                }
              });
            }
          }
        });
      });
      
      // 各予約の表示行を計算（重複を避ける）
      group.sort((a, b) => a.checkIn.getTime() - b.checkIn.getTime());
      
      group.forEach(res => {
        let row = 0;
        let placed = false;
        
        while (!placed) {
          let canPlace = true;
          
          // 同じ行の他の予約と重複しないか確認
          for (const other of group) {
            if (other.id !== res.id && other.row === row) {
              // 期間が重複するか確認
              if (!(res.checkOut < other.checkIn || res.checkIn > other.checkOut)) {
                canPlace = false;
                break;
              }
            }
          }
          
          if (canPlace) {
            res.row = row;
            placed = true;
          } else {
            row++;
          }
        }
      });
    });
    
    return Array.from(facilityGroups.values()).flat();
  }, [filteredReservations, weeks]);

  // 予約タイプによる透明度を取得（すべて青色ベース）
  const getReservationOpacity = (type: string) => {
    switch (type) {
      case '予約':
        return '1'; // 不透明
      case 'キャンセル':
        return '0.5'; // 半透明
      case '変更':
        return '1'; // 不透明
      default:
        return '1';
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
        <div className="border-t">
          {weeks.map((week, weekIndex) => {
            // この週の予約を取得
            const weekReservations = processedReservations.filter(res =>
              res.displaySegments.some(seg => seg.weekIndex === weekIndex)
            );
            
            // 最大行数を計算
            const maxRow = Math.max(0, ...weekReservations.map(r => r.row));
            const reservationAreaHeight = Math.max(50, (maxRow + 1) * 20 + 10);
            
            return (
              <div key={weekIndex}>
                {/* 日付ヘッダー行 */}
                <div className="grid grid-cols-7 border-l border-gray-300">
                  {week.map((day, dayIndex) => {
                    const isCurrentMonth = isSameMonth(day, currentDate);
                    const isTodayDate = isToday(day);
                    const dayOfWeek = day.getDay();
                    
                    return (
                      <div
                        key={day.toISOString()}
                        className={`border-r border-gray-300 h-6 ${
                          !isCurrentMonth ? 'bg-gray-50' : isTodayDate ? 'bg-blue-100' : 'bg-white'
                        }`}
                        style={{ borderBottom: '1px dashed #d1d5db' }}
                      >
                        <div className={`text-sm px-1 font-medium ${
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
                
                {/* OUT/INラベル行 */}
                <div className="grid grid-cols-7 border-l border-gray-300 h-5">
                  {week.map((day) => {
                    const isCurrentMonth = isSameMonth(day, currentDate);
                    const isTodayDate = isToday(day);
                    
                    return (
                      <div
                        key={`label-${day.toISOString()}`}
                        className={`border-r border-gray-300 relative ${
                          !isCurrentMonth ? 'bg-gray-50' : isTodayDate ? 'bg-blue-50/30' : 'bg-white'
                        }`}
                        style={{ borderBottom: '1px dotted #e5e7eb' }}
                      >
                        <div className="absolute inset-0 flex pointer-events-none">
                          <div className="w-1/2 border-r-2 border-dashed border-gray-200 bg-gradient-to-r from-red-50/20 to-transparent">
                            <div className="text-center text-xs text-red-400 font-semibold" style={{ fontSize: '8px', lineHeight: '20px' }}>
                              OUT
                            </div>
                          </div>
                          <div className="w-1/2 bg-gradient-to-l from-green-50/20 to-transparent">
                            <div className="text-center text-xs text-green-400 font-semibold" style={{ fontSize: '8px', lineHeight: '20px' }}>
                              IN
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                {/* 予約表示エリア */}
                <div className="relative" style={{ height: `${reservationAreaHeight}px` }}>
                  {/* 背景セル */}
                  <div className="absolute inset-0 grid grid-cols-7 border-l border-gray-300">
                    {week.map((day) => {
                      const isCurrentMonth = isSameMonth(day, currentDate);
                      const isTodayDate = isToday(day);
                      
                      return (
                        <div
                          key={`bg-${day.toISOString()}`}
                          className={`border-r border-b border-gray-300 relative ${
                            !isCurrentMonth ? 'bg-gray-50' : isTodayDate ? 'bg-blue-50/50' : 'bg-white'
                          }`}
                        >
                          {/* 左右分割の視覚的ガイドライン */}
                          <div className="absolute inset-0 flex pointer-events-none">
                            <div className="w-1/2 border-r border-dashed border-gray-200"></div>
                            <div className="w-1/2"></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* 予約バー */}
                  <div className="absolute inset-0 pointer-events-none" style={{ paddingTop: '5px' }}>
                  {weekReservations.map(res => {
                    const segment = res.displaySegments.find(seg => seg.weekIndex === weekIndex);
                    if (!segment) return null;
                    
                    // 位置とサイズの計算
                    const cellWidth = 100 / 7;
                    let leftPosition = segment.startDay * cellWidth;
                    let width = (segment.endDay - segment.startDay + 1) * cellWidth;
                    
                    // チェックインは必ず右側（IN側）から開始
                    if (segment.isFirst) {
                      // チェックイン日は右半分から開始
                      leftPosition += cellWidth * 0.5;
                      width -= cellWidth * 0.5;
                    }
                    
                    // チェックアウトは必ず左側（OUT側）で終了
                    if (segment.isLast) {
                      // チェックアウト日は左半分で終了
                      width -= cellWidth * 0.5;
                    }
                    
                    const topPosition = 3 + res.row * 20;
                    
                    // 境界のスタイル（チェックイン左丸め、チェックアウト右丸め）
                    let borderRadius = '0';
                    let borderLeft = '';
                    let borderRight = '';
                    
                    if (segment.isFirst && segment.isLast) {
                      // 単日（同日チェックイン・チェックアウト）の場合は両端丸める
                      borderRadius = '4px';
                      borderLeft = '3px solid #10b981'; // 緑の縁取り
                      borderRight = '3px solid #ef4444'; // 赤の縁取り
                    } else if (segment.isFirst) {
                      // チェックイン週（左端のみ丸める）
                      borderRadius = '4px 0 0 4px';
                      borderLeft = '3px solid #10b981'; // 緑の縁取り
                    } else if (segment.isLast) {
                      // チェックアウト週（右端のみ丸める）
                      borderRadius = '0 4px 4px 0';
                      borderRight = '3px solid #ef4444'; // 赤の縁取り
                    } else {
                      // 中間週（角丸なし、一本のバー）
                      borderRadius = '0';
                    }
                    
                    return (
                      <div
                        key={`${res.id}-${weekIndex}`}
                        className="absolute bg-blue-500 text-white text-xs px-1 py-0.5 pointer-events-auto cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => {
                          const currentUrl = window.location.search;
                          router.push(`/reservations/${res.id}?from=calendar&returnUrl=${encodeURIComponent('/calendar' + currentUrl)}`);
                        }}
                        style={{
                          left: `${leftPosition}%`,
                          width: `${width}%`,
                          top: `${topPosition}px`,
                          borderRadius: borderRadius,
                          borderLeft: borderLeft,
                          borderRight: borderRight,
                          height: '16px',
                          lineHeight: '15px',
                          zIndex: 10 + res.row,
                          opacity: getReservationOpacity(res.reservation_type),
                        }}
                        title={`${res.guestName}\n${res.facility?.facility_group ? `[${res.facility.facility_group}] ` : ''}${res.facility?.name || res.room_type}\n${res.ota_name || ''}\n${format(res.checkIn, 'MM/dd')} - ${format(res.checkOut, 'MM/dd')}\n${res.reservation_type}`}
                      >
                        <div className="truncate">
                          {res.guestName}
                        </div>
                      </div>
                    );
                  })}
                  </div>
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
            <div className="flex items-center">
              <div className="w-px h-4 bg-gray-400 mx-2"></div>
              <span className="text-gray-500 text-xs">左側OUT / 右側IN</span>
            </div>
          </div>
          <div className="text-xs text-gray-600 italic">
            同日チェックイン・アウトは自動的に左右に分割表示
          </div>
        </div>
      </div>
    </div>
  );
}