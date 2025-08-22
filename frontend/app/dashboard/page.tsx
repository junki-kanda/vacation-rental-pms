'use client';

import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/main-layout';
import { dashboardApi, type DashboardStats, type Reservation } from '@/lib/api';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import {
  Calendar, Users, Building, Activity, AlertCircle, RefreshCw
} from 'lucide-react';

export default function DashboardPage() {
  // 基本統計情報（30秒間隔で自動更新）
  const { data: stats, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats(),
    refetchInterval: 30000, // 30秒ごとに自動更新
    refetchIntervalInBackground: true,
    retry: 2,
    retryDelay: 1000,
  });

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
            <div className="text-gray-500">ダッシュボードを読み込み中...</div>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <div className="text-gray-900 font-medium mb-2">データの取得に失敗しました</div>
            <div className="text-gray-500 text-sm mb-4">
              {error instanceof Error ? error.message : 'ネットワークエラーが発生しました'}
            </div>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              再試行
            </button>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-6 flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
            <p className="text-sm text-gray-500 mt-1">
              {format(new Date(), 'yyyy年MM月dd日 HH:mm', { locale: ja })} 時点
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {isRefetching && (
              <div className="flex items-center text-blue-600 text-sm">
                <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                更新中...
              </div>
            )}
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* 本日の統計 */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">本日のチェックイン</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats?.today_checkins || 0}棟</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <Calendar className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">本日のチェックアウト</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats?.today_checkouts || 0}棟</p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <Building className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">本日の宿泊者数</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats?.total_guests_today || 0}名</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <Users className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">本日の稼働率</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats?.occupancy_rate || 0}%</p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-full">
                <Activity className="h-6 w-6 text-yellow-600" />
              </div>
            </div>
          </div>
        </div>

        {/* 最近の予約 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">最近の予約</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    予約ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    宿泊者名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    チェックイン
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    チェックアウト
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    部屋タイプ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステータス
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {stats?.recent_reservations && stats.recent_reservations.length > 0 ? (
                  stats.recent_reservations.map((reservation: Reservation) => (
                    <tr key={reservation.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reservation.reservation_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reservation.guest_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(new Date(reservation.check_in_date), 'MM/dd', { locale: ja })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(new Date(reservation.check_out_date), 'MM/dd', { locale: ja })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {reservation.room_type}
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
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                      最近の予約がありません
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 同期ステータス */}
        {stats?.sync_status && (
          <div className="mt-6 bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">最新の同期状態</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">同期タイプ</p>
                <p className="text-sm font-medium text-gray-900">{stats.sync_status.sync_type}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">処理行数</p>
                <p className="text-sm font-medium text-gray-900">{stats.sync_status.processed_rows} / {stats.sync_status.total_rows}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">新規予約</p>
                <p className="text-sm font-medium text-gray-900">{stats.sync_status.new_reservations}件</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">完了時刻</p>
                <p className="text-sm font-medium text-gray-900">
                  {stats.sync_status.completed_at ? format(new Date(stats.sync_status.completed_at), 'HH:mm:ss', { locale: ja }) : '-'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}