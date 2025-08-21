'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Users, Plus, Edit, Trash2, UserPlus, UserMinus, DollarSign } from 'lucide-react';
import staffGroupsApi, { StaffGroup, StaffGroupCreate } from '@/lib/api/staff-groups';
import cleaningApi from '@/lib/api/cleaning';

export default function StaffGroupsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState<StaffGroup | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<StaffGroup | null>(null);
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [selectedStaffIds, setSelectedStaffIds] = useState<number[]>([]);
  const queryClient = useQueryClient();

  // グループ一覧取得
  const { data: groups = [], isLoading } = useQuery({
    queryKey: ['staff-groups'],
    queryFn: () => staffGroupsApi.getGroups({ is_active: true }),
  });

  // スタッフ一覧取得
  const { data: allStaff = [], isLoading: isLoadingStaff, error: staffError } = useQuery({
    queryKey: ['cleaning-staff'],
    queryFn: async () => {
      try {
        const result = await cleaningApi.staff.getAll({ is_active: true });
        console.log('Fetched staff:', result);
        return result;
      } catch (error) {
        console.error('Failed to fetch staff:', error);
        throw error;
      }
    },
  });
  
  // デバッグ用：スタッフデータを確認
  console.log('All staff:', allStaff, 'Loading:', isLoadingStaff, 'Error:', staffError);

  // グループ作成
  const createMutation = useMutation({
    mutationFn: async (group: StaffGroupCreate) => {
      console.log('Creating group:', group);
      try {
        const result = await staffGroupsApi.createGroup(group);
        console.log('Group created:', result);
        return result;
      } catch (error) {
        console.error('Failed to create group:', error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-groups'] });
      setShowCreateModal(false);
      setSelectedStaffIds([]);
      alert('グループを作成しました');
    },
    onError: (error: any) => {
      console.error('Create group error:', error);
      alert(`グループの作成に失敗しました: ${error.message || 'Unknown error'}`);
    },
  });

  // グループ更新
  const updateMutation = useMutation({
    mutationFn: ({ id, group }: { id: number; group: Partial<StaffGroupCreate> }) =>
      staffGroupsApi.updateGroup(id, group),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-groups'] });
      setEditingGroup(null);
    },
  });

  // グループ削除
  const deleteMutation = useMutation({
    mutationFn: (id: number) => staffGroupsApi.deleteGroup(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-groups'] });
    },
  });

  // メンバー追加
  const addMembersMutation = useMutation({
    mutationFn: async ({ groupId, memberIds }: { groupId: number; memberIds: number[] }) => {
      console.log('Adding members:', { groupId, memberIds });
      const result = await staffGroupsApi.addMembers(groupId, memberIds);
      console.log('Add members result:', result);
      return result;
    },
    onSuccess: (data) => {
      console.log('Members added successfully:', data);
      queryClient.invalidateQueries({ queryKey: ['staff-groups'] });
      // selectedGroupを更新して即座に反映
      if (selectedGroup) {
        setSelectedGroup(data);
      }
    },
    onError: (error) => {
      console.error('Failed to add members:', error);
      alert('メンバーの追加に失敗しました');
    },
  });

  // メンバー削除
  const removeMemberMutation = useMutation({
    mutationFn: async ({ groupId, memberIds }: { groupId: number; memberIds: number[] }) => {
      console.log('Removing members:', { groupId, memberIds });
      const result = await staffGroupsApi.removeMembers(groupId, memberIds);
      console.log('Remove members result:', result);
      return result;
    },
    onSuccess: (data) => {
      console.log('Members removed successfully:', data);
      queryClient.invalidateQueries({ queryKey: ['staff-groups'] });
      // selectedGroupを更新して即座に反映
      if (selectedGroup) {
        setSelectedGroup(data);
      }
    },
    onError: (error) => {
      console.error('Failed to remove members:', error);
      alert('メンバーの削除に失敗しました');
    },
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
        <h1 className="text-2xl font-bold text-gray-900">スタッフグループ管理</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center"
        >
          <Plus className="h-5 w-5 mr-2" />
          新規グループ作成
        </button>
      </div>

      {/* グループ一覧 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.map((group) => (
          <div key={group.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{group.name}</h3>
                {group.description && (
                  <p className="text-sm text-gray-500 mt-1">{group.description}</p>
                )}
              </div>
              <Users className="h-6 w-6 text-gray-400" />
            </div>

            {/* メンバー情報 */}
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                メンバー: {group.member_count}名
              </p>
              {group.members && group.members.length > 0 && (
                <div className="mt-2 space-y-1">
                  {group.members
                    .filter(m => !m.left_date)
                    .slice(0, 3)
                    .map((member) => (
                      <div key={member.id} className="text-xs text-gray-500">
                        • {member.staff_name || `スタッフ${member.staff_id}`}
                        {member.is_leader && ' (リーダー)'}
                      </div>
                    ))}
                  {group.member_count > 3 && (
                    <div className="text-xs text-gray-400">他 {group.member_count - 3}名</div>
                  )}
                </div>
              )}
            </div>

            {/* 報酬設定 */}
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <div className="flex items-center text-sm text-gray-600 mb-1">
                <DollarSign className="h-4 w-4 mr-1" />
                報酬設定
              </div>
              <div className="text-xs space-y-1">
                <div>基本: ¥{group.rate_per_property.toLocaleString()}/棟</div>
                <div>オプション付: ¥{group.rate_per_property_with_option.toLocaleString()}/棟</div>
                <div>交通費: ¥{group.transportation_fee.toLocaleString()}</div>
              </div>
            </div>

            {/* 能力 */}
            <div className="mb-4">
              <div className="flex flex-wrap gap-1">
                {group.can_handle_large_properties && (
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                    大型物件対応
                  </span>
                )}
                {group.can_handle_multiple_properties && (
                  <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">
                    複数物件対応
                  </span>
                )}
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                  最大{group.max_properties_per_day}棟/日
                </span>
              </div>
            </div>

            {/* アクション */}
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setSelectedGroup(group);
                  setShowMemberModal(true);
                }}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                title="メンバー管理"
              >
                <UserPlus className="h-4 w-4" />
              </button>
              <button
                onClick={() => setEditingGroup(group)}
                className="p-2 text-gray-600 hover:bg-gray-50 rounded"
                title="編集"
              >
                <Edit className="h-4 w-4" />
              </button>
              <button
                onClick={() => {
                  if (confirm(`「${group.name}」を削除しますか？`)) {
                    deleteMutation.mutate(group.id);
                  }
                }}
                className="p-2 text-red-600 hover:bg-red-50 rounded"
                title="削除"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* グループ作成モーダル */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">新規グループ作成</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                createMutation.mutate({
                  name: formData.get('name') as string,
                  description: formData.get('description') as string,
                  rate_per_property: Number(formData.get('rate_per_property')) || 8000,
                  rate_per_property_with_option: Number(formData.get('rate_per_property_with_option')) || 9000,
                  transportation_fee: Number(formData.get('transportation_fee')) || 0,
                  max_properties_per_day: Number(formData.get('max_properties_per_day')) || 1,
                  can_handle_large_properties: true,
                  can_handle_multiple_properties: true,
                  is_active: true,
                  member_ids: selectedStaffIds,
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  グループ名 *
                </label>
                <input
                  name="name"
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  説明
                </label>
                <textarea
                  name="description"
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              
              {/* スタッフ選択 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  初期メンバー選択
                </label>
                {isLoadingStaff ? (
                  <div className="border border-gray-300 rounded-md p-3">
                    <p className="text-sm text-gray-500">スタッフ情報を読み込み中...</p>
                  </div>
                ) : staffError ? (
                  <div className="border border-gray-300 rounded-md p-3">
                    <p className="text-sm text-red-500">スタッフ情報の読み込みに失敗しました</p>
                  </div>
                ) : allStaff.length === 0 ? (
                  <div className="border border-gray-300 rounded-md p-3">
                    <p className="text-sm text-gray-500">登録されているスタッフがいません</p>
                  </div>
                ) : (
                <div className="border border-gray-300 rounded-md p-3 max-h-48 overflow-y-auto">
                  {allStaff.map((staff) => (
                    <label key={staff.id} className="flex items-center p-2 hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedStaffIds.includes(staff.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedStaffIds([...selectedStaffIds, staff.id]);
                          } else {
                            setSelectedStaffIds(selectedStaffIds.filter(id => id !== staff.id));
                          }
                        }}
                        className="mr-3"
                      />
                      <span className="text-sm">{staff.name}</span>
                      <span className="ml-auto text-xs text-gray-500">
                        ¥{staff.rate_per_property.toLocaleString()}/棟
                      </span>
                    </label>
                  ))}
                </div>
                )}
                {selectedStaffIds.length > 0 && (
                  <p className="mt-2 text-sm text-gray-600">
                    選択中: {selectedStaffIds.length}名
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    基本報酬（円/棟）
                  </label>
                  <input
                    name="rate_per_property"
                    type="number"
                    defaultValue={8000}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    オプション付（円/棟）
                  </label>
                  <input
                    name="rate_per_property_with_option"
                    type="number"
                    defaultValue={9000}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    交通費（円）
                  </label>
                  <input
                    name="transportation_fee"
                    type="number"
                    defaultValue={0}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    最大棟数/日
                  </label>
                  <input
                    name="max_properties_per_day"
                    type="number"
                    defaultValue={1}
                    min={1}
                    max={10}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setSelectedStaffIds([]);
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  キャンセル
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? '作成中...' : '作成'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* グループ編集モーダル */}
      {editingGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">グループ編集</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                updateMutation.mutate({
                  id: editingGroup.id,
                  group: {
                    name: formData.get('name') as string,
                    description: formData.get('description') as string,
                    rate_per_property: Number(formData.get('rate_per_property')),
                    rate_per_property_with_option: Number(formData.get('rate_per_property_with_option')),
                    transportation_fee: Number(formData.get('transportation_fee')),
                    max_properties_per_day: Number(formData.get('max_properties_per_day')),
                  },
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  グループ名 *
                </label>
                <input
                  name="name"
                  type="text"
                  required
                  defaultValue={editingGroup.name}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  説明
                </label>
                <textarea
                  name="description"
                  rows={2}
                  defaultValue={editingGroup.description}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    基本報酬（円/棟）
                  </label>
                  <input
                    name="rate_per_property"
                    type="number"
                    defaultValue={editingGroup.rate_per_property}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    オプション付（円/棟）
                  </label>
                  <input
                    name="rate_per_property_with_option"
                    type="number"
                    defaultValue={editingGroup.rate_per_property_with_option}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    交通費（円）
                  </label>
                  <input
                    name="transportation_fee"
                    type="number"
                    defaultValue={editingGroup.transportation_fee}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    最大棟数/日
                  </label>
                  <input
                    name="max_properties_per_day"
                    type="number"
                    defaultValue={editingGroup.max_properties_per_day}
                    min={1}
                    max={10}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setEditingGroup(null)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  キャンセル
                </button>
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {updateMutation.isPending ? '更新中...' : '更新'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* メンバー管理モーダル */}
      {showMemberModal && selectedGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">
              {selectedGroup.name} - メンバー管理
            </h2>

            {/* 現在のメンバー */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">現在のメンバー</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto border border-gray-200 rounded-md p-3">
                {selectedGroup.members && selectedGroup.members
                  .filter(m => !m.left_date)
                  .map((member) => (
                    <div key={member.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm">
                        {member.staff_name || `スタッフ${member.staff_id}`}
                        {member.is_leader && ' (リーダー)'}
                      </span>
                      <button
                        onClick={() => {
                          if (confirm('メンバーから削除しますか？')) {
                            removeMemberMutation.mutate({
                              groupId: selectedGroup.id,
                              memberIds: [member.staff_id],
                            });
                          }
                        }}
                        className="text-red-600 hover:text-red-800"
                      >
                        <UserMinus className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                {(!selectedGroup.members || selectedGroup.members.filter(m => !m.left_date).length === 0) && (
                  <p className="text-sm text-gray-500">メンバーがいません</p>
                )}
              </div>
            </div>

            {/* スタッフ追加 */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">スタッフを追加</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto border border-gray-200 rounded-md p-3">
                {allStaff
                  .filter(staff => 
                    !selectedGroup.members || 
                    !selectedGroup.members.some(m => m.staff_id === staff.id && !m.left_date)
                  )
                  .map((staff) => (
                    <div key={staff.id} className="flex justify-between items-center p-2 bg-gray-50 rounded hover:bg-gray-100">
                      <div>
                        <span className="text-sm font-medium">{staff.name}</span>
                        <span className="ml-2 text-xs text-gray-500">
                          ¥{staff.rate_per_property.toLocaleString()}/棟
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          addMembersMutation.mutate({
                            groupId: selectedGroup.id,
                            memberIds: [staff.id],
                          });
                        }}
                        disabled={addMembersMutation.isPending}
                        className="text-blue-600 hover:text-blue-800 disabled:opacity-50"
                      >
                        <UserPlus className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                {allStaff.filter(staff => 
                  !selectedGroup.members || 
                  !selectedGroup.members.some(m => m.staff_id === staff.id && !m.left_date)
                ).length === 0 && (
                  <p className="text-sm text-gray-500">追加可能なスタッフがいません</p>
                )}
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setShowMemberModal(false);
                  setSelectedGroup(null);
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                閉じる
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}