'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Calendar, Users, Clock, TrendingUp, ChevronLeft, ChevronRight, 
  BarChart3, Download, Filter, Star, AlertCircle, Award, Activity
} from 'lucide-react';
import cleaningApi, { StaffMonthlyStats } from '@/lib/api/cleaning';

interface StaffMonthlyStatsProps {
  selectedDate?: Date;
}

type SortField = 'working_days' | 'total_tasks' | 'total_hours' | 'efficiency' | 'individual_tasks' | 'group_tasks';
type ViewMode = 'table' | 'cards' | 'chart';

export default function StaffMonthlyStatsComponent({ selectedDate }: StaffMonthlyStatsProps) {
  const today = selectedDate || new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [sortField, setSortField] = useState<SortField>('working_days');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [filterMinDays, setFilterMinDays] = useState<number>(0);
  const [showFilters, setShowFilters] = useState(false);

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

  // 統計データの拡張計算
  const enrichedStats = stats.map(stat => ({
    ...stat,
    efficiency: stat.working_days > 0 ? (stat.total_tasks / stat.working_days) : 0,
    hoursPerTask: stat.total_tasks > 0 ? (stat.total_hours / stat.total_tasks) : 0,
    taskBalance: stat.total_tasks > 0 ? (stat.individual_tasks / stat.total_tasks) : 0,
  }));

  // フィルタリング
  const filteredStats = enrichedStats.filter(stat => stat.working_days >= filterMinDays);

  // ソート機能
  const sortedStats = [...filteredStats].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    if (sortField === 'efficiency') {
      aValue = a.efficiency;
      bValue = b.efficiency;
    }
    
    const multiplier = sortOrder === 'desc' ? -1 : 1;
    return (aValue - bValue) * multiplier;
  });

  // 統計サマリー計算
  const totalWorkingDays = filteredStats.reduce((sum, s) => sum + s.working_days, 0);
  const totalTasks = filteredStats.reduce((sum, s) => sum + s.total_tasks, 0);
  const totalHours = filteredStats.reduce((sum, s) => sum + s.total_hours, 0);
  const averageTasksPerStaff = filteredStats.length > 0 ? (totalTasks / filteredStats.length).toFixed(1) : '0';
  const averageHoursPerStaff = filteredStats.length > 0 ? (totalHours / filteredStats.length).toFixed(1) : '0';
  const averageEfficiency = filteredStats.length > 0 ? 
    (filteredStats.reduce((sum, s) => sum + s.efficiency, 0) / filteredStats.length).toFixed(2) : '0';
  
  // パフォーマンス分析
  const getPerformanceBadge = (stat: typeof enrichedStats[0]) => {
    if (stat.working_days === 0) return null;
    
    if (stat.efficiency >= 1.5) return { label: '高効率', color: 'bg-green-100 text-green-800', icon: Award };
    if (stat.efficiency >= 1.0) return { label: '標準', color: 'bg-blue-100 text-blue-800', icon: Star };
    if (stat.efficiency >= 0.5) return { label: '低効率', color: 'bg-yellow-100 text-yellow-800', icon: AlertCircle };
    return { label: '要改善', color: 'bg-red-100 text-red-800', icon: AlertCircle };
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // CSV出力機能
  const generateCSV = () => {
    const headers = [
      'スタッフ名', '出勤日数', '担当棟数', '個人タスク', 'グループタスク',
      '作業時間', '効率性', '平均時間/棟', 'パフォーマンス'
    ];
    
    const rows = sortedStats.map(stat => {
      const badge = getPerformanceBadge(stat);
      return [
        stat.staff_name,
        stat.working_days,
        stat.total_tasks,
        stat.individual_tasks,
        stat.group_tasks,
        stat.total_hours.toFixed(1),
        stat.efficiency.toFixed(2),
        stat.hoursPerTask.toFixed(1),
        badge?.label || '-'
      ];
    });
    
    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    return csvContent;
  };

  const downloadCSV = (content: string, filename: string) => {
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  };

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
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-gray-900">スタッフ月次統計</h3>
            <span className="text-sm text-gray-500">
              {filteredStats.length}名のスタッフ
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* 表示モード切替 */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('table')}
                className={`p-2 rounded ${viewMode === 'table' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}
                title="テーブル表示"
              >
                <BarChart3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('cards')}
                className={`p-2 rounded ${viewMode === 'cards' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}
                title="カード表示"
              >
                <Users className="h-4 w-4" />
              </button>
            </div>

            {/* フィルターボタン */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-lg border ${showFilters ? 'bg-indigo-50 border-indigo-200 text-indigo-600' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}
              title="フィルター"
            >
              <Filter className="h-4 w-4" />
            </button>

            {/* 月移動 */}
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

        {/* フィルター */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">最小出勤日数:</label>
                <select
                  value={filterMinDays}
                  onChange={(e) => setFilterMinDays(parseInt(e.target.value))}
                  className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value={0}>制限なし</option>
                  <option value={1}>1日以上</option>
                  <option value={5}>5日以上</option>
                  <option value={10}>10日以上</option>
                  <option value={15}>15日以上</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">ソート:</label>
                <select
                  value={sortField}
                  onChange={(e) => setSortField(e.target.value as SortField)}
                  className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="working_days">出勤日数</option>
                  <option value="total_tasks">担当棟数</option>
                  <option value="total_hours">作業時間</option>
                  <option value="efficiency">効率性</option>
                  <option value="individual_tasks">個人タスク</option>
                  <option value="group_tasks">グループタスク</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                  className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"
                >
                  {sortOrder === 'desc' ? '↓' : '↑'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* サマリー統計 */}
      <div className="px-6 py-4 bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600">{filteredStats.length}</div>
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
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{averageHoursPerStaff}</div>
            <div className="text-xs text-gray-500">平均作業時間</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-pink-600">{averageEfficiency}</div>
            <div className="text-xs text-gray-500">平均効率性</div>
          </div>
        </div>
      </div>

      {/* スタッフ別統計 */}
      {viewMode === 'table' ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('working_days')}
                    className="flex items-center space-x-1 hover:text-gray-700"
                  >
                    <span>スタッフ名</span>
                  </button>
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('working_days')}
                    className="flex items-center justify-center space-x-1 hover:text-gray-700"
                  >
                    <span>出勤日数</span>
                    {sortField === 'working_days' && (
                      <span>{sortOrder === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('total_tasks')}
                    className="flex items-center justify-center space-x-1 hover:text-gray-700"
                  >
                    <span>担当棟数</span>
                    {sortField === 'total_tasks' && (
                      <span>{sortOrder === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('efficiency')}
                    className="flex items-center justify-center space-x-1 hover:text-gray-700"
                  >
                    <span>効率性</span>
                    {sortField === 'efficiency' && (
                      <span>{sortOrder === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  個人/グループ
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('total_hours')}
                    className="flex items-center justify-center space-x-1 hover:text-gray-700"
                  >
                    <span>作業時間</span>
                    {sortField === 'total_hours' && (
                      <span>{sortOrder === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  出勤日
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedStats.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">
                    データがありません
                  </td>
                </tr>
              ) : (
                sortedStats.map((stat) => {
                  const badge = getPerformanceBadge(stat);
                  return (
                    <tr key={stat.staff_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <Users className="h-5 w-5 text-gray-400" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">{stat.staff_name}</div>
                            {badge && (
                              <div className="flex items-center mt-1">
                                <badge.icon className="h-3 w-3 mr-1" />
                                <span className={`text-xs px-2 py-0.5 rounded-full ${badge.color}`}>
                                  {badge.label}
                                </span>
                              </div>
                            )}
                          </div>
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
                        <div className="text-sm font-semibold text-gray-900">
                          {stat.efficiency.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-500">棟/日</div>
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
                          <span className="text-sm text-gray-900">{stat.total_hours.toFixed(1)}</span>
                          <span className="text-xs text-gray-500 ml-1">時間</span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          平均 {stat.hoursPerTask.toFixed(1)}h/棟
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-xs text-gray-500">
                          {stat.dates_worked.length > 0 ? (
                            <details className="cursor-pointer">
                              <summary className="hover:text-gray-700">
                                {stat.dates_worked.length}日（詳細を見る）
                              </summary>
                              <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
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
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      ) : (
        /* カード表示 */
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortedStats.length === 0 ? (
              <div className="col-span-full text-center text-gray-500 py-8">
                データがありません
              </div>
            ) : (
              sortedStats.map((stat) => {
                const badge = getPerformanceBadge(stat);
                return (
                  <div key={stat.staff_id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        <Users className="h-5 w-5 text-gray-400" />
                        <h4 className="text-lg font-medium text-gray-900">{stat.staff_name}</h4>
                      </div>
                      {badge && (
                        <div className="flex items-center">
                          <badge.icon className="h-4 w-4 mr-1" />
                          <span className={`text-xs px-2 py-1 rounded-full ${badge.color}`}>
                            {badge.label}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-indigo-600">{stat.working_days}</div>
                        <div className="text-xs text-gray-500">出勤日数</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{stat.total_tasks}</div>
                        <div className="text-xs text-gray-500">担当棟数</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{stat.efficiency.toFixed(2)}</div>
                        <div className="text-xs text-gray-500">効率性 (棟/日)</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">{stat.total_hours.toFixed(1)}</div>
                        <div className="text-xs text-gray-500">作業時間</div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">個人タスク:</span>
                        <span className="font-medium">{stat.individual_tasks}棟</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">グループタスク:</span>
                        <span className="font-medium">{stat.group_tasks}棟</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">平均時間/棟:</span>
                        <span className="font-medium">{stat.hoursPerTask.toFixed(1)}時間</span>
                      </div>
                    </div>

                    {stat.dates_worked.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <details className="cursor-pointer">
                          <summary className="text-sm text-gray-600 hover:text-gray-800">
                            出勤日詳細 ({stat.dates_worked.length}日)
                          </summary>
                          <div className="mt-2 grid grid-cols-3 gap-1 text-xs text-gray-500 max-h-20 overflow-y-auto">
                            {stat.dates_worked.map((date) => (
                              <div key={date} className="text-center">
                                {new Date(date).toLocaleDateString('ja-JP', { 
                                  month: 'numeric', 
                                  day: 'numeric'
                                })}
                              </div>
                            ))}
                          </div>
                        </details>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* 凡例とエクスポート */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-6">
            <span className="flex items-center">
              <Activity className="h-3 w-3 mr-1" />
              効率性 = 担当棟数 ÷ 出勤日数
            </span>
            <span>個人: 個人割当 / グループ: グループ割当</span>
            <span>作業時間はタスクの推定時間から算出</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">高効率</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">標準</span>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">低効率</span>
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">要改善</span>
            </div>
            <button
              onClick={() => {
                const csvContent = generateCSV();
                downloadCSV(csvContent, `staff-stats-${year}-${month.toString().padStart(2, '0')}.csv`);
              }}
              className="flex items-center px-3 py-1 bg-indigo-600 text-white rounded text-xs hover:bg-indigo-700"
            >
              <Download className="h-3 w-3 mr-1" />
              CSV出力
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}