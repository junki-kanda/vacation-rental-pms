'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Users, Clock, TrendingUp, ChevronLeft, ChevronRight } from 'lucide-react';
import cleaningApi, { StaffMonthlyStats } from '@/lib/api/cleaning';

interface StaffMonthlyStatsProps {
  selectedDate?: Date;
}

export default function StaffMonthlyStatsComponent({ selectedDate }: StaffMonthlyStatsProps) {
  const today = selectedDate || new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);

  // 選択された日付が変更されたら、年月を更新
  useEffect(() => {
    if (selectedDate) {
      setYear(selectedDate.getFullYear());
      setMonth(selectedDate.getMonth() + 1);
    }
  }, [selectedDate]);

  const { data: stats = [], isLoading } = useQuery({
    queryKey: ['staff-monthly-stats', year, month],
    queryFn: () => cleaningApi.dashboard.getStaffMonthlyStats(year, month),
  });

  const handlePreviousMonth = () => {
    if (month === 1) {
      setMonth(12);
      setYear(year - 1);
    } else {
      setMonth(month - 1);
    }
  };

  const handleNextMonth = () => {
    if (month === 12) {
      setMonth(1);
      setYear(year + 1);
    } else {
      setMonth(month + 1);
    }
  };

  const monthNames = [
    '1月', '2月', '3月', '4月', '5月', '6月',
    '7月', '8月', '9月', '10月', '11月', '12月'
  ];

  // 統計サマリー計算
  const totalWorkingDays = stats.reduce((sum, s) => sum + s.working_days, 0);
  const totalTasks = stats.reduce((sum, s) => sum + s.total_tasks, 0);
  const totalHours = stats.reduce((sum, s) => sum + s.total_hours, 0);
  const averageTasksPerStaff = stats.length > 0 ? (totalTasks / stats.length).toFixed(1) : '0';

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">スタッフ月次統計</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePreviousMonth}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <ChevronLeft className="h-5 w-5 text-gray-600" />
            </button>
            <span className="text-sm font-medium text-gray-700 min-w-[100px] text-center">
              {year}年 {monthNames[month - 1]}
            </span>
            <button
              onClick={handleNextMonth}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <ChevronRight className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        </div>
      </div>

      {/* サマリー統計 */}
      <div className="px-6 py-4 bg-gray-50 grid grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-indigo-600">{stats.length}</div>
          <div className="text-xs text-gray-500">稼働スタッフ数</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{totalTasks}</div>
          <div className="text-xs text-gray-500">総担当棟数</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{totalHours.toFixed(1)}</div>
          <div className="text-xs text-gray-500">総作業時間</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">{averageTasksPerStaff}</div>
          <div className="text-xs text-gray-500">平均担当棟数</div>
        </div>
      </div>

      {/* スタッフ別統計テーブル */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                スタッフ名
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                出勤日数
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                担当棟数
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                個人/グループ
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                作業時間
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                出勤日
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {stats.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                  データがありません
                </td>
              </tr>
            ) : (
              stats.map((stat) => (
                <tr key={stat.staff_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Users className="h-5 w-5 text-gray-400 mr-2" />
                      <div className="text-sm font-medium text-gray-900">{stat.staff_name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className="text-sm font-semibold text-gray-900">{stat.working_days}</span>
                    <span className="text-xs text-gray-500 ml-1">日</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className="text-sm font-semibold text-gray-900">{stat.total_tasks}</span>
                    <span className="text-xs text-gray-500 ml-1">棟</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center space-x-2 text-xs">
                      {stat.individual_tasks > 0 && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                          個人: {stat.individual_tasks}
                        </span>
                      )}
                      {stat.group_tasks > 0 && (
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                          グループ: {stat.group_tasks}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center">
                      <Clock className="h-4 w-4 text-gray-400 mr-1" />
                      <span className="text-sm text-gray-900">{stat.total_hours}</span>
                      <span className="text-xs text-gray-500 ml-1">時間</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-xs text-gray-500">
                      {stat.dates_worked.length > 0 ? (
                        <details className="cursor-pointer">
                          <summary className="hover:text-gray-700">
                            {stat.dates_worked.length}日（詳細を見る）
                          </summary>
                          <div className="mt-1 space-y-1">
                            {stat.dates_worked.map((date) => (
                              <div key={date} className="pl-2">
                                {new Date(date).toLocaleDateString('ja-JP', { 
                                  month: 'short', 
                                  day: 'numeric',
                                  weekday: 'short'
                                })}
                              </div>
                            ))}
                          </div>
                        </details>
                      ) : (
                        <span>-</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 凡例 */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <TrendingUp className="h-3 w-3 mr-1" />
              出勤日数順で表示
            </span>
            <span>個人: 個人割当 / グループ: グループ割当</span>
          </div>
          <div>
            作業時間はタスクの推定時間から算出
          </div>
        </div>
      </div>
    </div>
  );
}