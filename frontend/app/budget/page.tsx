'use client';

import { MainLayout } from '@/components/layout/main-layout';
import { TrendingUp, Calendar, DollarSign, BarChart3 } from 'lucide-react';

export default function BudgetPage() {
  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">予実管理</h1>
          <p className="text-sm text-gray-500 mt-1">
            売上実績と予算の比較・分析
          </p>
        </div>

        {/* 開発中メッセージ */}
        <div className="bg-white shadow rounded-lg p-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">予実管理機能</h2>
            <p className="text-gray-600 mb-4">
              この機能は現在開発中です
            </p>
            
            <div className="bg-gray-50 rounded-lg p-6 text-left max-w-2xl mx-auto">
              <h3 className="text-lg font-medium text-gray-900 mb-3">実装予定の機能</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start">
                  <Calendar className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                  <span>月次・年次の売上実績と予算の比較</span>
                </li>
                <li className="flex items-start">
                  <DollarSign className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                  <span>予算設定・編集機能</span>
                </li>
                <li className="flex items-start">
                  <BarChart3 className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                  <span>グラフによる可視化（売上高、稼働率、ADR）</span>
                </li>
                <li className="flex items-start">
                  <TrendingUp className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                  <span>前年同期比較・達成率分析</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}