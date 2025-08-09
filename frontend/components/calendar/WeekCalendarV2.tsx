'use client';

import { useState, useMemo } from 'react';
import { format, startOfWeek, endOfWeek, eachDayOfInterval, addWeeks, subWeeks, isToday, isSameDay, parseISO, differenceInDays } from 'date-fns';
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

interface WeekCalendarProps {
  currentDate: Date;
  onDateChange: (date: Date) => void;
  reservations?: Reservation[];
  roomTypes?: string[];
  facilities?: Facility[];
  selectedRoomType?: string;
  showCancelled?: boolean;
}

interface ProcessedReservation extends Reservation {
  guestName: string;
  checkIn: Date;
  checkOut: Date;
  displayDays: {
    dayIndex: number;
    isCheckIn: boolean;
    isCheckOut: boolean;
    isStaying: boolean;
  }[];
  hasLeftConflict: boolean;
  hasRightConflict: boolean;
  weekStartDay: number;
  weekEndDay: number;
  row: number;
}

export default function WeekCalendarV2({ 
  currentDate, 
  onDateChange, 
  reservations = [],
  roomTypes = [],
  facilities = [],
  selectedRoomType,
  showCancelled = false
}: WeekCalendarProps) {
  const router = useRouter();
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
    
    if (!showCancelled) {
      filtered = filtered.filter(res => res.reservation_type !== 'キャンセル');
    }
    
    if (selectedRoomType) {
      filtered = filtered.filter(res => res.room_type === selectedRoomType);
    }
    
    return filtered;
  }, [reservations, showCancelled, selectedRoomType]);

  // 施設名とデータのマップ
  const facilitiesMap = useMemo(() => {
    const map = new Map<string, Facility>();
    facilities.forEach(facility => {
      map.set(facility.name, facility);
    });
    return map;
  }, [facilities]);

  // 表示する施設のリスト
  const displayFacilities = useMemo(() => {
    // 施設グループでソート、次に施設名でソート
    const sortedFacilities = [...facilities].sort((a, b) => {
      if (a.facility_group && b.facility_group) {
        const groupCompare = a.facility_group.localeCompare(b.facility_group);
        if (groupCompare !== 0) return groupCompare;
      } else if (a.facility_group) {
        return -1;
      } else if (b.facility_group) {
        return 1;
      }
      return a.name.localeCompare(b.name);
    });
    
    if (selectedRoomType) {
      return sortedFacilities.filter(f => f.name === selectedRoomType);
    }
    return sortedFacilities;
  }, [facilities, selectedRoomType]);

  // 各施設の予約を処理
  const processedReservationsByFacility = useMemo(() => {
    const facilityMap = new Map<string, ProcessedReservation[]>();
    
    displayFacilities.forEach(facility => {
      const facilityReservations: ProcessedReservation[] = [];
      
      filteredReservations
        .filter(res => {
          // 施設名で一致を確認（facility.nameがroom_typeまたはfacility.nameと一致）
          return res.room_type === facility.name || 
                 (res.facility && res.facility.name === facility.name);
        })
        .forEach(res => {
          const checkIn = parseISO(res.start || res.check_in_date || '');
          const checkOut = parseISO(res.end || res.check_out_date || '');
          const guestName = res.guest_name || res.title?.split(' (')[0] || '不明';
          
          // この週に関係があるか確認
          if (checkOut < weekStart || checkIn > weekEnd) {
            return;
          }
          
          // 表示範囲を計算
          const displayStart = checkIn < weekStart ? weekStart : checkIn;
          const displayEnd = checkOut > weekEnd ? weekEnd : checkOut;
          
          const processed: ProcessedReservation = {
            ...res,
            guestName,
            checkIn,
            checkOut,
            displayDays: [],
            hasLeftConflict: false,
            hasRightConflict: false,
            weekStartDay: -1,
            weekEndDay: -1,
            row: 0
          };
          
          // 各日の状態を計算
          let firstDay = -1;
          let lastDay = -1;
          
          days.forEach((day, index) => {
            const isCheckInDay = isSameDay(checkIn, day);
            const isCheckOutDay = isSameDay(checkOut, day);
            const isStaying = day >= displayStart && day <= displayEnd;
            
            if (isStaying) {
              if (firstDay === -1) firstDay = index;
              lastDay = index;
              
              processed.displayDays.push({
                dayIndex: index,
                isCheckIn: isCheckInDay,
                isCheckOut: isCheckOutDay,
                isStaying: true
              });
            }
          });
          
          processed.weekStartDay = firstDay;
          processed.weekEndDay = lastDay;
          
          facilityReservations.push(processed);
        });
      
      // 同日チェックイン・アウトの競合を検出
      facilityReservations.forEach(res => {
        facilityReservations.forEach(other => {
          if (res.id !== other.id) {
            if (isSameDay(res.checkIn, other.checkOut)) {
              res.hasLeftConflict = true;
            }
            if (isSameDay(res.checkOut, other.checkIn)) {
              res.hasRightConflict = true;
            }
          }
        });
      });
      
      // 表示行を計算
      facilityReservations.sort((a, b) => a.weekStartDay - b.weekStartDay);
      
      facilityReservations.forEach(res => {
        let row = 0;
        let placed = false;
        
        while (!placed) {
          let canPlace = true;
          
          for (const other of facilityReservations) {
            if (other.id !== res.id && other.row === row) {
              // 期間が重複しないか確認
              if (!(res.weekEndDay < other.weekStartDay || res.weekStartDay > other.weekEndDay)) {
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
      
      facilityMap.set(facility.name, facilityReservations);
    });
    
    return facilityMap;
  }, [filteredReservations, displayFacilities, days, weekStart, weekEnd]);

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
                  {/* OUT/INラベル */}
                  <div className="flex justify-center mt-1">
                    <span className="text-xs text-red-400 font-semibold mr-1">OUT</span>
                    <span className="text-xs text-gray-300">|</span>
                    <span className="text-xs text-green-400 font-semibold ml-1">IN</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 施設別の行 */}
          {displayFacilities.map((facility, facilityIndex) => {
            const facilityReservations = processedReservationsByFacility.get(facility.name) || [];
            const maxRow = Math.max(0, ...facilityReservations.map(r => r.row));
            const rowHeight = Math.max(80, 40 + (maxRow + 1) * 25);
            
            return (
              <div key={`${facility.name}-${facilityIndex}`} className="grid grid-cols-8 border-b hover:bg-gray-50">
                {/* 施設名 */}
                <div className="p-3 text-sm font-medium text-gray-900 border-r bg-white sticky left-0 z-10">
                  {facility.facility_group ? (
                    <div className="flex flex-col">
                      <span className="text-xs text-gray-500">[{facility.facility_group}]</span>
                      <span>{facility.name}</span>
                    </div>
                  ) : (
                    <span>{facility.name}</span>
                  )}
                </div>
                
                {/* 各日のセル */}
                {days.map((day, dayIndex) => (
                  <div
                    key={`${facility.name}-${day.toISOString()}`}
                    className={`relative border-r ${isToday(day) ? 'bg-blue-50/30' : ''}`}
                    style={{ height: `${rowHeight}px` }}
                  >
                    {/* 左右分割の背景 */}
                    <div className="absolute inset-0 flex pointer-events-none">
                      <div className="w-1/2 border-r border-dashed border-gray-200 bg-gradient-to-r from-red-50/20 to-transparent"></div>
                      <div className="w-1/2 bg-gradient-to-l from-green-50/20 to-transparent"></div>
                    </div>
                    
                    {/* 予約バー */}
                    <div className="absolute inset-0" style={{ paddingTop: '40px' }}>
                      {facilityReservations.map(res => {
                        if (res.weekStartDay === -1 || res.weekEndDay === -1) return null;
                        if (dayIndex < res.weekStartDay || dayIndex > res.weekEndDay) return null;
                        
                        const isFirstDay = dayIndex === res.weekStartDay;
                        const isLastDay = dayIndex === res.weekEndDay;
                        const isCheckIn = res.displayDays.some(d => d.dayIndex === dayIndex && d.isCheckIn);
                        const isCheckOut = res.displayDays.some(d => d.dayIndex === dayIndex && d.isCheckOut);
                        
                        // 位置とサイズの計算
                        let left = '0';
                        let width = '100%';
                        let borderRadius = '0';
                        let borderLeft = '';
                        let borderRight = '';
                        
                        // チェックインは必ず右側（IN側）から開始
                        if (isCheckIn && !isCheckOut) {
                          left = '50%';
                          width = '50%'; // チェックインは常に右半分から
                        }
                        
                        // チェックアウトは必ず左側（OUT側）で終了
                        if (isCheckOut && !isCheckIn) {
                          // チェックアウトのみの場合
                          width = '50%';
                        }
                        
                        // 同日チェックイン・チェックアウトの場合
                        if (isCheckIn && isCheckOut) {
                          // 1日だけの予約の場合は全幅使用
                          left = '0';
                          width = '100%';
                        }
                        
                        // borderRadius設定と縁取り（チェックイン左丸め・緑縁、チェックアウト右丸め・赤縁）
                        if (isCheckIn && isCheckOut) {
                          // 同日チェックイン・チェックアウト（両端丸める）
                          borderRadius = '4px';
                          borderLeft = '3px solid #10b981'; // 緑の縁取り
                          borderRight = '3px solid #ef4444'; // 赤の縁取り
                        } else if (isCheckIn) {
                          // チェックイン日（左端のみ丸める）
                          borderRadius = '4px 0 0 4px';
                          borderLeft = '3px solid #10b981'; // 緑の縁取り
                        } else if (isCheckOut) {
                          // チェックアウト日（右端のみ丸める）
                          borderRadius = '0 4px 4px 0';
                          borderRight = '3px solid #ef4444'; // 赤の縁取り
                        } else if (isFirstDay && !isCheckIn) {
                          // 週の開始で継続中（両端直角）
                          borderRadius = '0';
                        } else if (isLastDay && !isCheckOut) {
                          // 週の終了で継続中（両端直角）
                          borderRadius = '0';
                        } else {
                          // 継続中（一本のバー、両端直角）
                          borderRadius = '0';
                        }
                        
                        const topPosition = 5 + res.row * 25;
                        
                        return (
                          <div
                            key={`${res.id}-${dayIndex}`}
                            className="absolute bg-blue-500 text-white text-xs px-1 py-0.5 cursor-pointer hover:opacity-90 transition-opacity"
                            onClick={() => {
                              const currentUrl = window.location.search;
                              router.push(`/reservations/${res.id}?from=calendar&returnUrl=${encodeURIComponent('/calendar' + currentUrl)}`);
                            }}
                            style={{
                              left: left,
                              width: width,
                              top: `${topPosition}px`,
                              borderRadius: borderRadius,
                              borderLeft: borderLeft,
                              borderRight: borderRight,
                              height: '20px',
                              lineHeight: '19px',
                              zIndex: 10,
                              opacity: getReservationOpacity(res.reservation_type),
                            }}
                            title={`${res.guestName}\n${res.ota_name || ''}\n${format(res.checkIn, 'MM/dd')} - ${format(res.checkOut, 'MM/dd')}\n${res.reservation_type}`}
                          >
                            <div className="truncate" style={{ fontSize: '10px' }}>
                              {isFirstDay ? res.guestName : ''}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            );
          })}
          
          {/* データがない場合の表示 */}
          {displayFacilities.length === 0 && (
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
              <div className="w-8 h-4 bg-blue-500 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">予約</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-4 bg-blue-500 opacity-50 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">キャンセル</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-4 bg-blue-500 mr-2 rounded"></div>
              <span className="text-gray-700 font-medium">変更</span>
            </div>
            <div className="flex items-center">
              <div className="w-6 h-4 bg-blue-500 mr-1 rounded-l" style={{ borderLeft: '3px solid #10b981' }}></div>
              <span className="text-gray-600 text-xs">チェックイン</span>
            </div>
            <div className="flex items-center">
              <div className="w-6 h-4 bg-blue-500 mr-1 rounded-r" style={{ borderRight: '3px solid #ef4444' }}></div>
              <span className="text-gray-600 text-xs">チェックアウト</span>
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