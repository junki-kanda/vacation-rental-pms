'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import cleaningApi, { Staff } from '@/lib/api/cleaning';
import { Plus, Edit2, Trash2, Phone, Mail, Car, Star, Calendar } from 'lucide-react';
import StaffFormModal from '@/components/cleaning/StaffFormModal';
import StaffAvailabilityCalendar from '@/components/cleaning/StaffAvailabilityCalendar';

export default function StaffManagementPage() {
  const queryClient = useQueryClient();
  const [selectedStaff, setSelectedStaff] = useState<Staff | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [availabilityStaff, setAvailabilityStaff] = useState<{ id: number; name: string } | null>(null);

  // スタッフ一覧取得
  const { data: staffList, isLoading } = useQuery({
    queryKey: ['cleaning-staff', filterActive],
    queryFn: () => cleaningApi.staff.getAll({ is_active: filterActive }),
  });

  // スタッフ削除
  const deleteMutation = useMutation({
    mutationFn: (id: number) => cleaningApi.staff.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleaning-staff'] });
    },
  });

  const handleEdit = (staff: Staff) => {
    setSelectedStaff(staff);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('このスタッフを削除してもよろしいですか？')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleFormClose = () => {
    setSelectedStaff(null);
    setIsFormOpen(false);
  };

  const handleAvailabilityClick = (staff: Staff) => {
    setAvailabilityStaff({ id: staff.id, name: staff.name });
  };

  const handleAvailabilityClose = () => {
    setAvailabilityStaff(null);
  };

  const renderSkillLevel = (level: number) => {
    return (
      <div className="flex items-center">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`h-4 w-4 ${
              i < level ? 'text-yellow-400 fill-current' : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">スタッフ管理</h1>
        <button
          onClick={() => setIsFormOpen(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center"
        >
          <Plus className="h-5 w-5 mr-2" />
          新規スタッフ登録
        </button>
      </div>

      {/* フィルター */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">表示:</label>
          <div className="flex space-x-2">
            <button
              onClick={() => setFilterActive(undefined)}
              className={`px-3 py-1 rounded-md text-sm ${
                filterActive === undefined
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              全て
            </button>
            <button
              onClick={() => setFilterActive(true)}
              className={`px-3 py-1 rounded-md text-sm ${
                filterActive === true
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              稼働中
            </button>
            <button
              onClick={() => setFilterActive(false)}
              className={`px-3 py-1 rounded-md text-sm ${
                filterActive === false
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              休止中
            </button>
          </div>
        </div>
      </div>

      {/* スタッフ一覧 */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-center text-gray-500">読み込み中...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    スタッフ名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    連絡先
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    スキル
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    移動手段
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    報酬（1棟あたり）
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステータス
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {staffList?.map((staff) => (
                  <tr key={staff.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {staff.name}
                        </div>
                        {staff.name_kana && (
                          <div className="text-sm text-gray-500">
                            {staff.name_kana}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {staff.phone && (
                          <div className="flex items-center">
                            <Phone className="h-4 w-4 mr-1 text-gray-400" />
                            {staff.phone}
                          </div>
                        )}
                        {staff.email && (
                          <div className="flex items-center">
                            <Mail className="h-4 w-4 mr-1 text-gray-400" />
                            {staff.email}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {renderSkillLevel(staff.skill_level)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-1">
                        {staff.can_drive && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            運転可
                          </span>
                        )}
                        {staff.has_car && (
                          <Car className="h-4 w-4 text-gray-600" />
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div>¥{staff.rate_per_property.toLocaleString()}/棟</div>
                        <div className="text-xs text-gray-500">
                          オプション: ¥{staff.rate_per_property_with_option.toLocaleString()}
                        </div>
                        {staff.transportation_fee > 0 && (
                          <div className="text-xs text-gray-500">
                            交通費: ¥{staff.transportation_fee}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          staff.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {staff.is_active ? '稼働中' : '休止中'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleAvailabilityClick(staff)}
                          className="text-green-600 hover:text-green-900"
                          title="出勤可能日設定"
                        >
                          <Calendar className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(staff)}
                          className="text-indigo-600 hover:text-indigo-900"
                          title="編集"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(staff.id)}
                          className="text-red-600 hover:text-red-900"
                          title="削除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* スタッフフォームモーダル */}
      {isFormOpen && (
        <StaffFormModal
          staff={selectedStaff}
          onClose={handleFormClose}
        />
      )}

      {/* 出勤可能日カレンダーモーダル */}
      {availabilityStaff && (
        <StaffAvailabilityCalendar
          staffId={availabilityStaff.id}
          staffName={availabilityStaff.name}
          onClose={handleAvailabilityClose}
        />
      )}
    </div>
  );
}