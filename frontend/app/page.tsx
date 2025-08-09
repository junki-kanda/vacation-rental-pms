'use client';

import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { 
  Users, 
  LogIn, 
  LogOut, 
  TrendingUp,
  Calendar,
  Clock
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getStats,
    refetchInterval: 30000, // 30秒ごとに更新
  });

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-gray-500">読み込み中...</div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">ダッシュボード</h2>
          <p className="text-gray-600">
            {format(new Date(), 'yyyy年MM月dd日(E)', { locale: ja })}
          </p>
        </div>

        {/* 統計カード */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <LogIn className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">本日のチェックイン</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats?.today_checkins || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <LogOut className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">本日のチェックアウト</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats?.today_checkouts || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">本日の宿泊者数</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats?.total_guests_today || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">稼働率</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats?.occupancy_rate || 0}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 最近の予約 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">最近の予約</h3>
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
                    OTA
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステータス
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {stats?.recent_reservations?.map((reservation) => (
                  <tr key={reservation.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {reservation.reservation_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {reservation.guest_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(reservation.check_in_date), 'MM/dd')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(reservation.check_out_date), 'MM/dd')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {reservation.ota_name}
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
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 同期ステータス */}
        {stats?.sync_status && (
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">最新の同期状態</h3>
                <p className="text-sm text-gray-500 mt-1">
                  ファイル: {stats.sync_status.file_name}
                </p>
              </div>
              <div className="flex items-center">
                <Clock className="h-5 w-5 text-gray-400 mr-2" />
                <span className="text-sm text-gray-500">
                  {format(new Date(stats.sync_status.started_at), 'MM/dd HH:mm')}
                </span>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">処理状況</span>
                <span className={`font-medium ${
                  stats.sync_status.status === 'completed' ? 'text-green-600' :
                  stats.sync_status.status === 'failed' ? 'text-red-600' :
                  'text-yellow-600'
                }`}>
                  {stats.sync_status.status === 'completed' ? '完了' :
                   stats.sync_status.status === 'failed' ? '失敗' :
                   '処理中'}
                </span>
              </div>
              {stats.sync_status.status === 'completed' && (
                <div className="mt-2 text-sm text-gray-500">
                  新規: {stats.sync_status.new_reservations}件 / 
                  更新: {stats.sync_status.updated_reservations}件 / 
                  エラー: {stats.sync_status.error_rows}件
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}