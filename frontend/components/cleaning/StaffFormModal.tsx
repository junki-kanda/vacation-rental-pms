'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import cleaningApi, { Staff } from '@/lib/api/cleaning';
import { cleaningApi as api } from '@/lib/api';
import { X, Check } from 'lucide-react';

interface StaffFormModalProps {
  staff?: Staff | null;
  onClose: () => void;
}

const WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
const WEEKDAY_LABELS: Record<string, string> = {
  monday: '月',
  tuesday: '火',
  wednesday: '水',
  thursday: '木',
  friday: '金',
  saturday: '土',
  sunday: '日',
};

export default function StaffFormModal({ staff, onClose }: StaffFormModalProps) {
  const queryClient = useQueryClient();
  const isEdit = !!staff;

  const [formData, setFormData] = useState({
    name: staff?.name || '',
    name_kana: staff?.name_kana || '',
    phone: staff?.phone || '',
    email: staff?.email || '',
    skill_level: staff?.skill_level || 3,
    can_drive: staff?.can_drive || false,
    has_car: staff?.has_car || false,
    rate_per_property: staff?.rate_per_property || 3000,
    rate_per_property_with_option: staff?.rate_per_property_with_option || 4000,
    transportation_fee: staff?.transportation_fee || 0,
    is_active: staff?.is_active ?? true,
    notes: staff?.notes || '',
    available_schedule: staff?.available_schedule || {},
    available_facilities: staff?.available_facilities || [],
  });

  // 施設一覧を取得
  const { data: facilities = [] } = useQuery({
    queryKey: ['facilities'],
    queryFn: () => api.getFacilities(),
  });

  // スタッフ作成
  const createMutation = useMutation({
    mutationFn: (data: any) => cleaningApi.staff.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-staff'] });
      onClose();
    },
  });

  // スタッフ更新
  const updateMutation = useMutation({
    mutationFn: (data: any) => cleaningApi.staff.update(staff!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-staff'] });
      onClose();
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const submitData = {
      ...formData,
      // available_facilities は既にformDataに含まれているため削除
    };

    if (isEdit) {
      await updateMutation.mutateAsync(submitData);
    } else {
      await createMutation.mutateAsync(submitData);
    }
  };

  const handleFacilityToggle = (facilityId: number) => {
    setFormData((prev) => ({
      ...prev,
      available_facilities: prev.available_facilities.includes(facilityId)
        ? prev.available_facilities.filter(id => id !== facilityId)
        : [...prev.available_facilities, facilityId],
    }));
  };

  const handleScheduleChange = (day: string, field: 'start' | 'end', value: string) => {
    setFormData((prev) => ({
      ...prev,
      available_schedule: {
        ...prev.available_schedule,
        [day]: {
          ...(prev.available_schedule[day] || {}),
          [field]: value,
        },
      },
    }));
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">
            {isEdit ? 'スタッフ編集' : '新規スタッフ登録'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 基本情報 */}
          <div>
            <h3 className="text-md font-medium text-gray-900 mb-4">基本情報</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  氏名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  氏名（カナ）
                </label>
                <input
                  type="text"
                  value={formData.name_kana}
                  onChange={(e) => setFormData({ ...formData, name_kana: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  電話番号
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  メールアドレス
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>
          </div>

          {/* 対応可能施設 */}
          <div>
            <h3 className="text-md font-medium text-gray-900 mb-4">対応可能施設</h3>
            <div className="space-y-2">
              {facilities.length > 0 ? (
                <div className="grid grid-cols-2 gap-3 max-h-48 overflow-y-auto p-2 border rounded-md">
                  {facilities.map((facility) => (
                    <label
                      key={facility.id}
                      className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={formData.available_facilities.includes(facility.id)}
                        onChange={() => handleFacilityToggle(facility.id)}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-700 flex-1">
                        {facility.name}
                        {facility.max_guests && facility.max_guests > 6 && (
                          <span className="ml-1 text-xs text-orange-600 font-medium">
                            (大型)
                          </span>
                        )}
                      </span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">施設データを読み込み中...</p>
              )}
              <div className="flex items-center space-x-4 mt-2">
                <button
                  type="button"
                  onClick={() => {
                    const allFacilityIds = facilities.map(f => f.id);
                    setFormData(prev => ({ ...prev, available_facilities: allFacilityIds }));
                  }}
                  className="text-xs text-indigo-600 hover:text-indigo-500"
                >
                  すべて選択
                </button>
                <button
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, available_facilities: [] }))}
                  className="text-xs text-gray-600 hover:text-gray-500"
                >
                  選択解除
                </button>
                <span className="text-xs text-gray-500">
                  {formData.available_facilities.length}/{facilities.length} 施設選択中
                </span>
              </div>
            </div>
          </div>

          {/* スキル・能力 */}
          <div>
            <h3 className="text-md font-medium text-gray-900 mb-4">スキル・能力</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  スキルレベル（1-5）
                </label>
                <select
                  value={formData.skill_level}
                  onChange={(e) => setFormData({ ...formData, skill_level: Number(e.target.value) })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  {[1, 2, 3, 4, 5].map((level) => (
                    <option key={level} value={level}>
                      {level} - {'★'.repeat(level)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.can_drive}
                    onChange={(e) => setFormData({ ...formData, can_drive: e.target.checked })}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">運転可能</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.has_car}
                    onChange={(e) => setFormData({ ...formData, has_car: e.target.checked })}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">車両保有</span>
                </label>
              </div>
            </div>
          </div>

          {/* 報酬設定 */}
          <div>
            <h3 className="text-md font-medium text-gray-900 mb-4">報酬設定（1棟あたり）</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    基本報酬（円/棟）
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.rate_per_property}
                    onChange={(e) => setFormData({ ...formData, rate_per_property: Number(e.target.value) })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">通常の1棟清掃時の報酬</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    オプション付き報酬（円/棟）
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.rate_per_property_with_option}
                    onChange={(e) => setFormData({ ...formData, rate_per_property_with_option: Number(e.target.value) })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">追加作業がある場合の報酬</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  交通費（円）
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.transportation_fee}
                  onChange={(e) => setFormData({ ...formData, transportation_fee: Number(e.target.value) })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
                <p className="mt-1 text-xs text-gray-500">1回の清掃あたりの交通費</p>
              </div>
              <div className="bg-blue-50 p-3 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>複数人での作業時:</strong> 報酬は人数で等分されます。
                  例: 基本報酬3,000円を2人で作業 → 各1,500円
                </p>
              </div>
            </div>
          </div>

          {/* 稼働可能時間 */}
          <div>
            <h3 className="text-md font-medium text-gray-900 mb-4">稼働可能時間</h3>
            <div className="space-y-2">
              {WEEKDAYS.map((day) => (
                <div key={day} className="flex items-center space-x-2">
                  <span className="w-8 text-sm font-medium text-gray-700">
                    {WEEKDAY_LABELS[day]}
                  </span>
                  <input
                    type="time"
                    value={formData.available_schedule[day]?.start || ''}
                    onChange={(e) => handleScheduleChange(day, 'start', e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <span className="text-gray-500">〜</span>
                  <input
                    type="time"
                    value={formData.available_schedule[day]?.end || ''}
                    onChange={(e) => handleScheduleChange(day, 'end', e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* 備考 */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              備考
            </label>
            <textarea
              rows={3}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          {/* ステータス */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="ml-2 text-sm text-gray-700">稼働中</span>
            </label>
          </div>

          {/* ボタン */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {createMutation.isPending || updateMutation.isPending
                ? '保存中...'
                : isEdit
                ? '更新'
                : '登録'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}