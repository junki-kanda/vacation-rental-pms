'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import cleaningApi, { CleaningDashboardStats } from '@/lib/api/cleaning';
import Link from 'next/link';
import { 
  Users, 
  Calendar, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  UserPlus,
  ClipboardList,
  CalendarCheck,
  TrendingUp
} from 'lucide-react';

export default function CleaningDashboardPage() {
  const [targetDate] = useState(new Date());

  // ダッシュボード統計取得
  const { data: stats, isLoading } = useQuery<CleaningDashboardStats>({
    queryKey: ['cleaning-dashboard-stats', format(targetDate, 'yyyy-MM-dd')],
    queryFn: () => cleaningApi.dashboard.getStats(format(targetDate, 'yyyy-MM-dd')),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">清掃管理</h1>
          <p className="text-sm text-gray-500 mt-1">
            {format(targetDate, 'yyyy年MM月dd日（E）', { locale: ja })}の状況
          </p>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Calendar className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">本日のタスク</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.today_tasks || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertCircle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">未割当</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.unassigned_tasks || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Clock className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">作業中</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.in_progress_tasks || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">完了済</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.completed_tasks || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-6 w-6 text-indigo-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">稼働スタッフ</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.active_staff || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* クイックアクション */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          href="/cleaning/staff"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center">
            <UserPlus className="h-8 w-8 text-indigo-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">スタッフ管理</h3>
              <p className="text-sm text-gray-500">スタッフの登録・編集</p>
            </div>
          </div>
        </Link>

        <Link
          href="/cleaning/tasks"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center">
            <ClipboardList className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">タスク一覧</h3>
              <p className="text-sm text-gray-500">清掃タスクの確認・管理</p>
            </div>
          </div>
        </Link>

        <Link
          href="/cleaning/shifts"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center">
            <CalendarCheck className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">シフト管理</h3>
              <p className="text-sm text-gray-500">スタッフの割当・調整</p>
            </div>
          </div>
        </Link>

        <Link
          href="/cleaning/performance"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">実績分析</h3>
              <p className="text-sm text-gray-500">パフォーマンス確認</p>
            </div>
          </div>
        </Link>
      </div>

      {/* 平均完了時間 */}
      {stats?.average_completion_time && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">本日の平均作業時間</h3>
          <p className="text-3xl font-bold text-indigo-600">
            {Math.round(stats.average_completion_time)}分
          </p>
        </div>
      )}
    </div>
  );
}