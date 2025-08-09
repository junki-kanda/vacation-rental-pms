'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { reservationApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { ArrowLeft, Save, Calendar, User, CreditCard, Home } from 'lucide-react';

export default function NewReservationPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState({
    reservation_id: '',
    reservation_type: '予約',
    reservation_number: '',
    ota_name: '',
    room_type: '',
    check_in_date: '',
    check_out_date: '',
    guest_name: '',
    guest_name_kana: '',
    guest_phone: '',
    guest_email: '',
    num_adults: 1,
    num_children: 0,
    num_infants: 0,
    total_amount: '',
    payment_method: '',
    meal_plan: '食事なし',
    nights: 1,
    rooms: 1,
    notes: '',
    plan_name: '',
    checkin_time: '',
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => reservationApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      router.push(`/reservations/${data.id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // 必須フィールドのチェック
    if (!formData.reservation_id || !formData.guest_name || !formData.check_in_date || !formData.check_out_date) {
      alert('必須項目を入力してください');
      return;
    }
    
    // 金額を数値に変換
    const submitData = {
      ...formData,
      total_amount: formData.total_amount ? parseFloat(formData.total_amount) : null,
    };
    
    createMutation.mutate(submitData);
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/reservations')}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <h1 className="text-2xl font-bold text-gray-900">新規予約登録</h1>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">基本情報</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  予約ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.reservation_id}
                  onChange={(e) => handleInputChange('reservation_id', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  予約区分
                </label>
                <select
                  value={formData.reservation_type}
                  onChange={(e) => handleInputChange('reservation_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="予約">予約</option>
                  <option value="変更">変更</option>
                  <option value="キャンセル">キャンセル</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  予約番号
                </label>
                <input
                  type="text"
                  value={formData.reservation_number}
                  onChange={(e) => handleInputChange('reservation_number', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OTA
                </label>
                <input
                  type="text"
                  value={formData.ota_name}
                  onChange={(e) => handleInputChange('ota_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="例: 一休.com"
                />
              </div>
            </div>
          </div>

          {/* 宿泊情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-gray-400" />
              宿泊情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  チェックイン日 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  required
                  value={formData.check_in_date}
                  onChange={(e) => handleInputChange('check_in_date', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  チェックアウト日 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  required
                  value={formData.check_out_date}
                  onChange={(e) => handleInputChange('check_out_date', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  部屋タイプ
                </label>
                <input
                  type="text"
                  value={formData.room_type}
                  onChange={(e) => handleInputChange('room_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="例: Villa A棟"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  泊数
                </label>
                <input
                  type="number"
                  value={formData.nights}
                  onChange={(e) => handleInputChange('nights', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  室数
                </label>
                <input
                  type="number"
                  value={formData.rooms}
                  onChange={(e) => handleInputChange('rooms', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  食事
                </label>
                <select
                  value={formData.meal_plan}
                  onChange={(e) => handleInputChange('meal_plan', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="食事なし">食事なし</option>
                  <option value="朝食付き">朝食付き</option>
                  <option value="夕食付き">夕食付き</option>
                  <option value="朝夕食付き">朝夕食付き</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  プラン名
                </label>
                <input
                  type="text"
                  value={formData.plan_name}
                  onChange={(e) => handleInputChange('plan_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  チェックイン時刻
                </label>
                <input
                  type="time"
                  value={formData.checkin_time}
                  onChange={(e) => handleInputChange('checkin_time', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
          </div>

          {/* 宿泊者情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <User className="h-5 w-5 mr-2 text-gray-400" />
              宿泊者情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  宿泊者名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.guest_name}
                  onChange={(e) => handleInputChange('guest_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  宿泊者名カナ
                </label>
                <input
                  type="text"
                  value={formData.guest_name_kana}
                  onChange={(e) => handleInputChange('guest_name_kana', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  電話番号
                </label>
                <input
                  type="tel"
                  value={formData.guest_phone}
                  onChange={(e) => handleInputChange('guest_phone', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  メールアドレス
                </label>
                <input
                  type="email"
                  value={formData.guest_email}
                  onChange={(e) => handleInputChange('guest_email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  大人人数
                </label>
                <input
                  type="number"
                  value={formData.num_adults}
                  onChange={(e) => handleInputChange('num_adults', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  子供人数
                </label>
                <input
                  type="number"
                  value={formData.num_children}
                  onChange={(e) => handleInputChange('num_children', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  幼児人数
                </label>
                <input
                  type="number"
                  value={formData.num_infants}
                  onChange={(e) => handleInputChange('num_infants', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  合計人数
                </label>
                <div className="px-3 py-2 bg-gray-100 rounded-md">
                  {formData.num_adults + formData.num_children + formData.num_infants}名
                </div>
              </div>
            </div>
          </div>

          {/* 料金情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <CreditCard className="h-5 w-5 mr-2 text-gray-400" />
              料金情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  合計金額
                </label>
                <input
                  type="number"
                  value={formData.total_amount}
                  onChange={(e) => handleInputChange('total_amount', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  決済方法
                </label>
                <input
                  type="text"
                  value={formData.payment_method}
                  onChange={(e) => handleInputChange('payment_method', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="例: 事前カード決済"
                />
              </div>
            </div>
          </div>

          {/* 備考 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">備考</h2>
            <textarea
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              rows={4}
              placeholder="特記事項があれば入力してください"
            />
          </div>

          {/* 送信ボタン */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => router.push('/reservations')}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center"
            >
              <Save className="h-4 w-4 mr-2" />
              {createMutation.isPending ? '登録中...' : '登録する'}
            </button>
          </div>
        </form>
      </div>
    </MainLayout>
  );
}