'use client';

import { useState, useMemo, useCallback } from 'react';
import { MainLayout } from '@/components/layout/main-layout';
import { Calendar, dateFnsLocalizer, Views, View, SlotInfo } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, addMonths, subMonths } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useQuery } from '@tanstack/react-query';
import { calendarApi } from '@/lib/api';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { ChevronLeft, ChevronRight, Filter, Calendar as CalendarIcon, Building, Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';

// date-fnsのlocalizerを設定
const locales = {
  'ja': ja,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: (date: Date) => startOfWeek(date, { locale: ja }),
  getDay,
  locales,
});

// カレンダーイベントの型定義
interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
  resource: {
    reservation_id: string;
    guest_name: string;
    ota_name: string;
    room_type: string;
    reservation_type: string;
    guest_count: number;
    num_adults: number;
    num_children: number;
    num_infants: number;
    original_start: Date;
    original_end: Date;
    is_checkin: boolean;
    is_checkout: boolean;
  };
}

// カスタムイベントコンポーネント用のラッパー
const CustomEventWrapper = ({ event, continuesPrior, continuesAfter }: any) => {
  return <EventComponent event={event} continuesPrior={continuesPrior} continuesAfter={continuesAfter} />;
};

// カスタムイベントコンポーネント
const EventComponent = ({ event, continuesPrior, continuesAfter }: { 
  event: CalendarEvent; 
  continuesPrior?: boolean;
  continuesAfter?: boolean;
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case '予約':
        return '#3b82f6';
      case 'キャンセル':
        return '#ef4444';
      case '変更':
        return '#eab308';
      default:
        return '#6b7280';
    }
  };

  const baseColor = getStatusColor(event.resource.reservation_type);
  
  // 連泊の表示スタイル決定
  let borderRadius = '4px';
  if (continuesPrior && continuesAfter) {
    // 連泊の中間日
    borderRadius = '0';
  } else if (continuesPrior && !continuesAfter) {
    // チェックアウト日
    borderRadius = '0 4px 4px 0';
  } else if (!continuesPrior && continuesAfter) {
    // チェックイン日
    borderRadius = '4px 0 0 4px';
  }
  // それ以外（単泊）は全角丸

  return (
    <div 
      className="text-white px-1 py-0.5 text-xs overflow-hidden cursor-pointer transition-all hover:opacity-90 h-full flex items-center"
      style={{
        backgroundColor: baseColor,
        borderRadius: borderRadius,
        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
      }}
      title={`${event.resource.guest_name} (${event.resource.ota_name})\n${event.resource.num_adults + event.resource.num_children + event.resource.num_infants}名`}
    >
      <div className="flex-1 min-w-0">
        <div className="font-semibold truncate" style={{ fontSize: '11px' }}>
          {!continuesPrior && <span style={{ color: '#86efac' }}>● </span>}
          {event.resource.guest_name}
          {!continuesAfter && <span style={{ color: '#fca5a5' }}> ●</span>}
        </div>
        {(event.resource.num_adults + event.resource.num_children + event.resource.num_infants) > 0 && (
          <div className="opacity-90" style={{ fontSize: '10px' }}>
            {event.resource.num_adults + event.resource.num_children + event.resource.num_infants}名
          </div>
        )}
      </div>
    </div>
  );
};

// 月表示用のカスタムイベントコンポーネント  
const MonthEventComponent = ({ event }: { event: CalendarEvent }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case '予約':
        return '#3b82f6';
      case 'キャンセル':
        return '#ef4444';
      case '変更':
        return '#eab308';
      default:
        return '#6b7280';
    }
  };

  const baseColor = getStatusColor(event.resource.reservation_type);
  const isCheckin = event.resource.is_checkin;
  const isCheckout = event.resource.is_checkout;
  
  // 現在のイベントの日付範囲を取得
  const checkIn = new Date(event.resource.original_start);
  const checkOut = new Date(event.resource.original_end);
  const eventStart = new Date(event.start);
  const eventEnd = new Date(event.end);
  
  checkIn.setHours(0, 0, 0, 0);
  checkOut.setHours(0, 0, 0, 0);
  eventStart.setHours(0, 0, 0, 0);
  eventEnd.setHours(0, 0, 0, 0);
  
  const isFirstDay = checkIn.getTime() === eventStart.getTime();
  const isLastDay = checkOut.getTime() === eventEnd.getTime();
  
  // スタイル決定
  let borderLeft = '4px solid transparent';
  let borderRight = '4px solid transparent';
  let borderRadius = '4px';
  let background = baseColor;
  let displayIcon = '';
  
  if (isCheckin) {
    // 同日チェックアウトがある場合のチェックイン（右半分表示を示す）
    borderLeft = '4px solid #10b981';
    background = `linear-gradient(to right, transparent 0%, transparent 40%, ${baseColor} 60%, ${baseColor} 100%)`;
    displayIcon = '▶ ';
  } else if (isCheckout) {
    // 同日チェックインがある場合のチェックアウト（左半分表示を示す）
    borderRight = '4px solid #ef4444';
    background = `linear-gradient(to right, ${baseColor} 0%, ${baseColor} 40%, transparent 60%, transparent 100%)`;
    displayIcon = '◀ ';
  } else if (isFirstDay && isLastDay) {
    // 単泊
    borderRadius = '4px';
  } else if (isFirstDay) {
    // チェックイン日（通常）
    borderRadius = '4px 0 0 4px';
    borderLeft = '3px solid #10b981';
  } else if (isLastDay) {
    // チェックアウト日（通常）
    borderRadius = '0 4px 4px 0';
    borderRight = '3px solid #ef4444';
  } else {
    // 滞在中
    borderRadius = '0';
  }

  return (
    <div 
      className="text-white px-1 py-0.5 text-xs overflow-hidden cursor-pointer hover:opacity-90 relative"
      style={{
        background: background,
        borderRadius: borderRadius,
        borderLeft: borderLeft,
        borderRight: borderRight,
        minHeight: '20px',
      }}
      title={`${event.resource.guest_name} (${event.resource.ota_name})\n${event.resource.num_adults + event.resource.num_children + event.resource.num_infants}名`}
    >
      <div className="truncate flex items-center" style={{ fontSize: '11px' }}>
        {displayIcon && <span className="mr-1">{displayIcon}</span>}
        <span className={isCheckin || isCheckout ? 'font-bold' : ''}>
          {event.resource.guest_name}
        </span>
        {!isCheckin && !isCheckout && isFirstDay && <span className="ml-1 text-green-200">●</span>}
        {!isCheckin && !isCheckout && isLastDay && <span className="ml-1 text-red-200">●</span>}
      </div>
    </div>
  );
};

export default function CalendarPage() {
  const router = useRouter();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedView, setSelectedView] = useState<View>(Views.MONTH);
  const [selectedRoomType, setSelectedRoomType] = useState<string>('');
  const [showCancelled, setShowCancelled] = useState<boolean>(false);

  // 部屋タイプ一覧取得
  const { data: roomTypes } = useQuery({
    queryKey: ['room-types'],
    queryFn: () => calendarApi.getRoomTypes(),
  });

  // カレンダー用の日付範囲を計算
  const dateRange = useMemo(() => {
    const start = startOfWeek(subMonths(currentDate, 1), { locale: ja });
    const end = addMonths(currentDate, 2);
    return { start, end };
  }, [currentDate]);

  // 予約データ取得
  const { data: reservations, isLoading } = useQuery({
    queryKey: ['calendar-reservations', dateRange.start, dateRange.end, selectedRoomType],
    queryFn: () => calendarApi.getReservations(
      format(dateRange.start, 'yyyy-MM-dd'),
      format(dateRange.end, 'yyyy-MM-dd'),
      selectedRoomType || undefined
    ),
  });

  // 予約データをカレンダーイベントに変換（キャンセルフィルター適用）
  const events: CalendarEvent[] = useMemo(() => {
    if (!reservations) return [];
    
    const filteredReservations = showCancelled 
      ? reservations 
      : reservations.filter((res: any) => res.reservation_type !== 'キャンセル');
    
    const processedEvents: CalendarEvent[] = [];
    
    // 部屋タイプと日付でグループ化して同日のチェックイン・チェックアウトを検出
    const conflictMap = new Map<string, Set<string>>(); // roomType-date -> reservation IDs
    
    // まず各予約のチェックイン日とチェックアウト日を記録
    filteredReservations.forEach((res: any) => {
      const checkInDate = new Date(res.start);
      const checkOutDate = new Date(res.end);
      checkInDate.setHours(0, 0, 0, 0);
      checkOutDate.setHours(0, 0, 0, 0);
      
      const checkInKey = `${res.room_type}-in-${checkInDate.toISOString().split('T')[0]}`;
      const checkOutKey = `${res.room_type}-out-${checkOutDate.toISOString().split('T')[0]}`;
      
      if (!conflictMap.has(checkInKey)) conflictMap.set(checkInKey, new Set());
      if (!conflictMap.has(checkOutKey)) conflictMap.set(checkOutKey, new Set());
      
      conflictMap.get(checkInKey)!.add(`${res.id}-in`);
      conflictMap.get(checkOutKey)!.add(`${res.id}-out`);
    });
    
    // 各予約を処理
    filteredReservations.forEach((res: any) => {
      const checkInDate = new Date(res.start);
      const checkOutDate = new Date(res.end);
      checkInDate.setHours(0, 0, 0, 0);
      checkOutDate.setHours(0, 0, 0, 0);
      
      const checkInDateStr = checkInDate.toISOString().split('T')[0];
      const checkOutDateStr = checkOutDate.toISOString().split('T')[0];
      
      // 同じ部屋タイプの同日チェックイン・チェックアウトを確認
      const checkInKey = `${res.room_type}-in-${checkInDateStr}`;
      const checkOutKey = `${res.room_type}-out-${checkInDateStr}`;
      
      const hasCheckInConflict = conflictMap.has(checkOutKey) && 
                                  conflictMap.get(checkOutKey)!.size > 0 &&
                                  !conflictMap.get(checkOutKey)!.has(`${res.id}-out`);
      
      const checkOutConflictKey = `${res.room_type}-in-${checkOutDateStr}`;
      const hasCheckOutConflict = conflictMap.has(checkOutConflictKey) && 
                                   conflictMap.get(checkOutConflictKey)!.size > 0 &&
                                   !conflictMap.get(checkOutConflictKey)!.has(`${res.id}-in`);
      
      // デバッグログ
      if (hasCheckInConflict || hasCheckOutConflict) {
        console.log('Conflict detected:', {
          reservation: res.guest_name,
          room_type: res.room_type,
          checkIn: checkInDateStr,
          checkOut: checkOutDateStr,
          hasCheckInConflict,
          hasCheckOutConflict
        });
      }
      
      // イベントの作成
      const eventStart = new Date(res.start);
      const eventEnd = new Date(res.end);
      
      // 時間調整（同日チェックイン・アウトの場合）
      if (hasCheckInConflict) {
        eventStart.setHours(12, 0, 0, 0); // 午後開始
      }
      if (hasCheckOutConflict) {
        eventEnd.setHours(12, 0, 0, 0); // 正午終了
      }
      
      processedEvents.push({
        id: res.id,
        title: `${res.guest_name} - ${res.room_type}`,
        start: eventStart,
        end: eventEnd,
        resource: {
          reservation_id: res.id,
          guest_name: res.title.split(' (')[0],
          ota_name: res.ota_name,
          room_type: res.room_type,
          reservation_type: res.reservation_type,
          guest_count: res.guest_count,
          num_adults: res.num_adults || 0,
          num_children: res.num_children || 0,
          num_infants: res.num_infants || 0,
          original_start: new Date(res.start),
          original_end: new Date(res.end),
          is_checkin: hasCheckInConflict,
          is_checkout: hasCheckOutConflict,
        },
      });
    });
    
    return processedEvents;
  }, [reservations, showCancelled]);

  // イベントクリック時の処理
  const handleSelectEvent = useCallback((event: CalendarEvent) => {
    router.push(`/reservations/${event.id}`);
  }, [router]);

  // スロット選択時の処理（新規予約作成）
  const handleSelectSlot = useCallback((slotInfo: SlotInfo) => {
    const checkIn = format(slotInfo.start, 'yyyy-MM-dd');
    const checkOut = format(slotInfo.end, 'yyyy-MM-dd');
    router.push(`/reservations/new?check_in=${checkIn}&check_out=${checkOut}`);
  }, [router]);

  // カスタムツールバー
  const CustomToolbar = ({ date, onNavigate, onView, view }: any) => {
    const goToToday = () => onNavigate('TODAY');
    const goToNext = () => onNavigate('NEXT');
    const goToPrev = () => onNavigate('PREV');

    return (
      <div className="flex items-center justify-between mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex items-center space-x-2">
          <button
            onClick={goToPrev}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            onClick={goToToday}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            今日
          </button>
          <button
            onClick={goToNext}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
          <h2 className="text-xl font-bold ml-4">
            {format(date, 'yyyy年MM月', { locale: ja })}
          </h2>
        </div>

        <div className="flex items-center space-x-4">
          {/* 部屋タイプフィルター */}
          <div className="flex items-center space-x-2">
            <Building className="h-4 w-4 text-gray-500" />
            <select
              value={selectedRoomType}
              onChange={(e) => setSelectedRoomType(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md"
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
            className={`flex items-center space-x-1 px-3 py-1 rounded-md border transition-colors ${
              showCancelled 
                ? 'bg-red-50 border-red-300 text-red-700' 
                : 'bg-green-50 border-green-300 text-green-700'
            }`}
          >
            {showCancelled ? (
              <>
                <EyeOff className="h-4 w-4" />
                <span className="text-sm">キャンセルを表示しない</span>
              </>
            ) : (
              <>
                <Eye className="h-4 w-4" />
                <span className="text-sm">キャンセルを表示する</span>
              </>
            )}
          </button>

          {/* ビュー切り替え */}
          <div className="flex space-x-1">
            <button
              onClick={() => onView(Views.MONTH)}
              className={`px-3 py-1 rounded ${view === Views.MONTH ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            >
              月
            </button>
            <button
              onClick={() => onView(Views.WEEK)}
              className={`px-3 py-1 rounded ${view === Views.WEEK ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            >
              週
            </button>
            <button
              onClick={() => onView(Views.DAY)}
              className={`px-3 py-1 rounded ${view === Views.DAY ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            >
              日
            </button>
          </div>
        </div>
      </div>
    );
  };

  // カレンダーのメッセージ（日本語化）
  const messages = {
    allDay: '終日',
    previous: '前',
    next: '次',
    today: '今日',
    month: '月',
    week: '週',
    day: '日',
    agenda: '予定',
    date: '日付',
    time: '時間',
    event: '予約',
    noEventsInRange: '表示する予約はありません',
    showMore: (total: number) => `+${total} 件`,
  };

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
          <div className="flex items-center mt-1">
            <p className="text-sm text-gray-500">
              予約状況を施設（部屋タイプ）別に確認できます
            </p>
            <div className="flex items-center ml-3 space-x-2">
              {selectedRoomType && (
                <span className="inline-flex items-center px-2 py-1 rounded-md bg-blue-100 text-blue-800 text-xs font-medium">
                  <Building className="h-3 w-3 mr-1" />
                  {selectedRoomType}
                </span>
              )}
              {!showCancelled && (
                <span className="inline-flex items-center px-2 py-1 rounded-md bg-green-100 text-green-800 text-xs font-medium">
                  <Eye className="h-3 w-3 mr-1" />
                  有効な予約のみ
                </span>
              )}
              {showCancelled && (
                <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 text-gray-800 text-xs font-medium">
                  <Eye className="h-3 w-3 mr-1" />
                  キャンセル含む
                </span>
              )}
            </div>
          </div>
        </div>

        {/* 統計情報 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-500">今月の予約数</p>
            <p className="text-2xl font-bold text-gray-900">
              {events.filter(e => 
                e.start.getMonth() === currentDate.getMonth() && 
                e.resource.reservation_type === '予約'
              ).length}
              件
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-500">今月のキャンセル</p>
            <p className="text-2xl font-bold text-red-600">
              {reservations?.filter((res: any) => 
                new Date(res.start).getMonth() === currentDate.getMonth() && 
                res.reservation_type === 'キャンセル'
              ).length || 0}
              件
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-500">今月の宿泊者数</p>
            <p className="text-2xl font-bold text-gray-900">
              {events
                .filter(e => e.start.getMonth() === currentDate.getMonth())
                .reduce((sum, e) => sum + e.resource.guest_count, 0)}
              名
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-500">
              {showCancelled ? '表示中の全予約' : '表示中の有効予約'}
            </p>
            <p className="text-2xl font-bold text-blue-600">
              {events.length}
              件
              {!showCancelled && reservations && (
                <span className="text-xs text-gray-500 block">
                  (キャンセル {reservations.filter((r: any) => r.reservation_type === 'キャンセル').length}件を非表示)
                </span>
              )}
            </p>
          </div>
        </div>

        {/* カレンダー */}
        <div className="bg-white rounded-lg shadow p-4" style={{ height: '700px' }}>
          <Calendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            date={currentDate}
            onNavigate={setCurrentDate}
            view={selectedView}
            onView={setSelectedView}
            onSelectEvent={handleSelectEvent}
            onSelectSlot={handleSelectSlot}
            selectable
            messages={messages}
            components={{
              toolbar: CustomToolbar,
              event: selectedView === Views.MONTH ? MonthEventComponent : CustomEventWrapper,
            }}
            formats={{
              monthHeaderFormat: 'yyyy年MM月',
              dayHeaderFormat: 'MM月dd日（eee）',
              dayRangeHeaderFormat: ({ start, end }) =>
                `${format(start, 'MM月dd日', { locale: ja })} - ${format(end, 'MM月dd日', { locale: ja })}`,
            }}
            style={{ height: '100%' }}
          />
        </div>

        {/* 凡例 */}
        <div className="mt-4 bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">凡例</h3>
          <div className="flex space-x-4">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
              <span className="text-sm text-gray-600">予約</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-500 rounded mr-2"></div>
              <span className="text-sm text-gray-600">キャンセル</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-yellow-500 rounded mr-2"></div>
              <span className="text-sm text-gray-600">変更</span>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}