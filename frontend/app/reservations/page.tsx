'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { reservationApi, calendarApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Search, Filter, ChevronUp, ChevronDown, Check } from 'lucide-react';
import { format } from 'date-fns';

export default function ReservationsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // URLパラメータから初期状態を復元
  const [filters, setFilters] = useState({
    ota_name: searchParams.get('ota_name')?.split(',').filter(Boolean) || [],
    room_type: searchParams.get('room_type') || '',
    guest_name: searchParams.get('guest_name') || '',
    check_in_date_from: searchParams.get('check_in_date_from') || '',
    check_in_date_to: searchParams.get('check_in_date_to') || '',
  });

  // ソート設定
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  }>({
    key: searchParams.get('sort_by') || 'check_in_date',
    direction: (searchParams.get('sort_order') as 'asc' | 'desc') || 'desc',
  });

  // OTAドロップダウンの開閉状態
  const [isOtaDropdownOpen, setIsOtaDropdownOpen] = useState(false);
  const otaDropdownRef = useRef<HTMLDivElement>(null);

  // 外側クリックでドロップダウンを閉じる
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (otaDropdownRef.current && !otaDropdownRef.current.contains(event.target as Node)) {
        setIsOtaDropdownOpen(false);
      }
    }

    if (isOtaDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOtaDropdownOpen]);

  // 状態が変更されたときにURLを更新
  const updateURL = (newFilters?: typeof filters, newSortConfig?: typeof sortConfig) => {
    const params = new URLSearchParams();
    
    const filtersToUse = newFilters || filters;
    const sortToUse = newSortConfig || sortConfig;
    
    Object.entries(filtersToUse).forEach(([key, value]) => {
      if (key === 'ota_name' && Array.isArray(value) && value.length > 0) {
        params.set(key, value.join(','));
      } else if (value && typeof value === 'string') {
        params.set(key, value);
      }
    });
    
    // ソート設定をURLに追加
    if (sortToUse.key) {
      params.set('sort_by', sortToUse.key);
      params.set('sort_order', sortToUse.direction);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/reservations?${queryString}` : '/reservations';
    router.replace(url, { scroll: false });
  };

  // フィルターの更新関数
  const handleFilterChange = (key: string, value: string | string[]) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    updateURL(newFilters);
  };

  // OTA選択の切り替え
  const handleOtaToggle = (otaName: string) => {
    const currentOtaNames = filters.ota_name as string[];
    const newOtaNames = currentOtaNames.includes(otaName)
      ? currentOtaNames.filter(name => name !== otaName)
      : [...currentOtaNames, otaName];
    handleFilterChange('ota_name', newOtaNames);
  };

  // ソートの更新関数
  const handleSort = (key: string) => {
    const newDirection = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    const newSortConfig = { key, direction: newDirection };
    setSortConfig(newSortConfig);
    updateURL(undefined, newSortConfig);
  };

  // ソートアイコンを取得する関数
  const getSortIcon = (key: string) => {
    if (sortConfig.key !== key) {
      return <ChevronUp className="h-4 w-4 text-gray-300" />;
    }
    return sortConfig.direction === 'asc' 
      ? <ChevronUp className="h-4 w-4 text-blue-500" />
      : <ChevronDown className="h-4 w-4 text-blue-500" />;
  };

  const { data: reservations, isLoading, error } = useQuery({
    queryKey: ['reservations', filters, sortConfig],
    queryFn: () => {
      const params = {
        ...filters,
        sort_by: sortConfig.key,
        sort_order: sortConfig.direction,
      };
      
      // ota_nameが配列の場合、各要素を個別のパラメータとして送信
      if (Array.isArray(params.ota_name) && params.ota_name.length > 0) {
        // FastAPIのList[str]クエリパラメータは複数の同名パラメータで送信
        return reservationApi.getAll(params);
      } else {
        // 空配列や未定義の場合はota_nameを削除
        const { ota_name, ...paramsWithoutOta } = params;
        return reservationApi.getAll(paramsWithoutOta);
      }
    },
  });
  
  // デバッグログ
  console.log('Current filters:', filters);
  console.log('Query result - reservations:', reservations);
  console.log('Query result - isLoading:', isLoading);
  console.log('Query result - error:', error);

  const { data: roomTypes } = useQuery({
    queryKey: ['room-types'],
    queryFn: () => calendarApi.getRoomTypes(),
  });

  const { data: otaNames } = useQuery({
    queryKey: ['ota-names'],
    queryFn: () => calendarApi.getOtaNames(),
  });

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">予約一覧</h2>
          <button
            onClick={() => window.location.href = '/reservations/new'}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center"
          >
            <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新規予約
          </button>
        </div>

        {/* フィルター */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <div className="relative" ref={otaDropdownRef}>
              <label className="block text-sm font-medium text-gray-700 mb-2">OTA名（複数選択可）</label>
              <div className="relative">
                {/* ドロップダウンボタン */}
                <button
                  type="button"
                  className="w-full h-9 bg-white border border-gray-300 rounded-md px-3 py-2 text-left shadow-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                  onClick={() => setIsOtaDropdownOpen(!isOtaDropdownOpen)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      {(filters.ota_name as string[]).length === 0 ? (
                        <span className="text-gray-500 text-sm">OTAを選択</span>
                      ) : (
                        <div className="flex items-center space-x-1">
                          <span className="text-sm">
                            {(filters.ota_name as string[]).length === 1 
                              ? (filters.ota_name as string[])[0]
                              : `${(filters.ota_name as string[]).length}個のOTA`
                            }
                          </span>
                          {(filters.ota_name as string[]).length > 1 && (
                            <div className="flex -space-x-1">
                              <div className="inline-flex items-center justify-center w-5 h-5 text-xs bg-indigo-100 text-indigo-800 rounded-full">
                                {(filters.ota_name as string[]).length}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="ml-2 flex-shrink-0">
                      {isOtaDropdownOpen ? (
                        <ChevronUp className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      )}
                    </div>
                  </div>
                </button>

                {/* ドロップダウンメニュー */}
                {isOtaDropdownOpen && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                    <div className="p-2">
                      {/* すべて解除ボタン */}
                      {(filters.ota_name as string[]).length > 0 && (
                        <div className="px-2 py-1 border-b border-gray-100 mb-1">
                          <button
                            onClick={() => {
                              handleFilterChange('ota_name', []);
                              setIsOtaDropdownOpen(false);
                            }}
                            className="text-xs text-red-600 hover:text-red-800"
                          >
                            すべて解除
                          </button>
                        </div>
                      )}
                      
                      {/* OTAリスト */}
                      {otaNames && otaNames.length > 0 ? (
                        <div className="space-y-0.5">
                          {otaNames.map((otaName: string) => (
                            <label key={otaName} className="flex items-center space-x-2 px-2 py-1.5 text-sm hover:bg-gray-50 rounded cursor-pointer">
                              <input
                                type="checkbox"
                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                checked={(filters.ota_name as string[]).includes(otaName)}
                                onChange={() => handleOtaToggle(otaName)}
                              />
                              <span className="flex-1 truncate">{otaName}</span>
                              {(filters.ota_name as string[]).includes(otaName) && (
                                <Check className="h-4 w-4 text-indigo-600" />
                              )}
                            </label>
                          ))}
                        </div>
                      ) : (
                        <div className="px-2 py-3 text-sm text-gray-400">OTA名を読み込み中...</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {/* 選択数表示 */}
              {(filters.ota_name as string[]).length > 0 && (
                <div className="mt-1 text-xs text-gray-500">
                  {(filters.ota_name as string[]).length}個選択中
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">部屋タイプ</label>
              <select
                className="block w-full h-9 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                value={filters.room_type}
                onChange={(e) => handleFilterChange('room_type', e.target.value)}
              >
                <option value="">全て</option>
                {roomTypes?.map((roomType: string) => (
                  <option key={roomType} value={roomType}>
                    {roomType}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">宿泊者名</label>
              <input
                type="text"
                className="block w-full h-9 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                placeholder="宿泊者名"
                value={filters.guest_name}
                onChange={(e) => handleFilterChange('guest_name', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">チェックイン（開始）</label>
              <input
                type="date"
                className="block w-full h-9 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                value={filters.check_in_date_from}
                onChange={(e) => handleFilterChange('check_in_date_from', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">チェックイン（終了）</label>
              <input
                type="date"
                className="block w-full h-9 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                value={filters.check_in_date_to}
                onChange={(e) => handleFilterChange('check_in_date_to', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* 予約テーブル */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('reservation_id')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>予約ID</span>
                      {getSortIcon('reservation_id')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('guest_name')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>宿泊者</span>
                      {getSortIcon('guest_name')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('check_in_date')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>チェックイン</span>
                      {getSortIcon('check_in_date')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('check_out_date')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>チェックアウト</span>
                      {getSortIcon('check_out_date')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('num_adults')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>人数</span>
                      {getSortIcon('num_adults')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('ota_name')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>OTA</span>
                      {getSortIcon('ota_name')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('room_type')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>部屋タイプ</span>
                      {getSortIcon('room_type')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('total_amount')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>金額</span>
                      {getSortIcon('total_amount')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('reservation_type')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>ステータス</span>
                      {getSortIcon('reservation_type')}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                      読み込み中...
                    </td>
                  </tr>
                ) : reservations && reservations.length > 0 ? (
                  reservations.map((reservation) => (
                    <tr key={reservation.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => {
                      const currentUrl = window.location.search;
                      window.location.href = `/reservations/${reservation.id}?from=reservations&returnUrl=${encodeURIComponent('/reservations' + currentUrl)}`;
                    }}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        <a href={`/reservations/${reservation.id}?from=reservations&returnUrl=${encodeURIComponent('/reservations' + window.location.search)}`} className="text-indigo-600 hover:text-indigo-900">
                          {reservation.reservation_id}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reservation.guest_name}
                        {reservation.guest_name_kana && (
                          <span className="block text-xs text-gray-500">
                            {reservation.guest_name_kana}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(new Date(reservation.check_in_date), 'yyyy/MM/dd')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(new Date(reservation.check_out_date), 'yyyy/MM/dd')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex flex-col">
                          <div className="text-xs">
                            大人{reservation.num_adults}
                            {reservation.num_children > 0 && ` 子供${reservation.num_children}`}
                            {reservation.num_infants > 0 && ` 幼児${reservation.num_infants}`}
                          </div>
                          <div className="text-xs font-semibold text-gray-700">
                            合計{reservation.num_adults + (reservation.num_children || 0) + (reservation.num_infants || 0)}名
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {reservation.ota_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {reservation.facility && reservation.facility.facility_group ? (
                          <div className="flex flex-col">
                            <span className="text-xs text-gray-400">[{reservation.facility.facility_group}]</span>
                            <span>{reservation.facility.name || reservation.room_type}</span>
                          </div>
                        ) : (
                          reservation.room_type
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {reservation.total_amount 
                          ? `¥${reservation.total_amount.toLocaleString()}`
                          : '-'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          reservation.reservation_type === '予約'
                            ? 'bg-green-100 text-green-800'
                            : reservation.reservation_type === 'キャンセル'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {reservation.reservation_type}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                      予約データがありません
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}