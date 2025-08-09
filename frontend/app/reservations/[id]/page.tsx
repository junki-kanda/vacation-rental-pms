'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reservationApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { ArrowLeft, Edit2, Trash2, Save, X, Calendar, User, CreditCard, Home, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export default function ReservationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<any>(null);
  
  // 参照元ページの判定
  const fromPage = searchParams.get('from');
  const returnUrl = searchParams.get('returnUrl');
  const isFromCalendar = fromPage === 'calendar';

  // 予約データ取得
  const { data: reservation, isLoading, error } = useQuery({
    queryKey: ['reservation', params.id],
    queryFn: () => reservationApi.getById(Number(params.id)),
  });

  // 編集用データの初期化
  useEffect(() => {
    if (reservation) {
      setEditData({
        ...reservation,
        check_in_date: reservation.check_in_date?.split('T')[0],
        check_out_date: reservation.check_out_date?.split('T')[0],
        cancel_date: reservation.cancel_date?.split('T')[0],
      });
    }
  }, [reservation]);

  // 更新処理
  const updateMutation = useMutation({
    mutationFn: (data: any) => reservationApi.update(params.id as string, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservation', params.id] });
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      setIsEditing(false);
    },
  });

  // 削除処理
  const deleteMutation = useMutation({
    mutationFn: () => reservationApi.delete(Number(params.id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      // returnUrlがある場合はそちらを優先、なければ従来の判定
      if (returnUrl) {
        router.push(decodeURIComponent(returnUrl));
      } else if (isFromCalendar) {
        router.push('/calendar');
      } else {
        router.push('/reservations');
      }
    },
  });
  
  // 戻るボタンの処理
  const handleBack = () => {
    // returnUrlがある場合はそちらを優先、なければ従来の判定
    if (returnUrl) {
      router.push(decodeURIComponent(returnUrl));
    } else if (isFromCalendar) {
      router.push('/calendar');
    } else {
      router.push('/reservations');
    }
  };

  const handleSave = () => {
    if (editData) {
      updateMutation.mutate(editData);
    }
  };

  const handleDelete = () => {
    if (window.confirm('この予約を削除してもよろしいですか？')) {
      deleteMutation.mutate();
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditData(reservation);
  };

  const handleInputChange = (field: string, value: any) => {
    setEditData((prev: any) => ({
      ...prev,
      [field]: value,
    }));
  };

  if (isLoading) return <MainLayout><div className="p-6">読み込み中...</div></MainLayout>;
  if (error) return <MainLayout><div className="p-6">エラーが発生しました</div></MainLayout>;
  if (!reservation) return <MainLayout><div className="p-6">予約が見つかりません</div></MainLayout>;

  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title={isFromCalendar ? 'カレンダーに戻る' : '予約一覧に戻る'}
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  予約詳細 #{reservation.reservation_id}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  最終更新: {format(new Date(reservation.updated_at), 'yyyy年MM月dd日 HH:mm', { locale: ja })}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {!isEditing ? (
                <>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Edit2 className="h-4 w-4 mr-2" />
                    編集
                  </button>
                  <button
                    onClick={handleDelete}
                    className="inline-flex items-center px-4 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    削除
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleSave}
                    disabled={updateMutation.isPending}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    保存
                  </button>
                  <button
                    onClick={handleCancel}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <X className="h-4 w-4 mr-2" />
                    キャンセル
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* ステータスバッジ */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-500">ステータス</span>
              {isEditing ? (
                <select
                  value={editData?.reservation_type || ''}
                  onChange={(e) => handleInputChange('reservation_type', e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                >
                  <option value="予約">予約</option>
                  <option value="変更">変更</option>
                  <option value="キャンセル">キャンセル</option>
                </select>
              ) : (
                <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                  reservation.reservation_type === '予約'
                    ? 'bg-green-100 text-green-800'
                    : reservation.reservation_type === 'キャンセル'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {reservation.reservation_type}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">予約番号: {reservation.reservation_number}</span>
              <span className="text-sm text-gray-500">OTA: {reservation.ota_name}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 基本情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-gray-400" />
              宿泊情報
            </h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">チェックイン</dt>
                <dd className="text-sm text-gray-900">
                  {isEditing ? (
                    <input
                      type="date"
                      value={editData?.check_in_date || ''}
                      onChange={(e) => handleInputChange('check_in_date', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    format(new Date(reservation.check_in_date), 'yyyy年MM月dd日', { locale: ja })
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">チェックアウト</dt>
                <dd className="text-sm text-gray-900">
                  {isEditing ? (
                    <input
                      type="date"
                      value={editData?.check_out_date || ''}
                      onChange={(e) => handleInputChange('check_out_date', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    format(new Date(reservation.check_out_date), 'yyyy年MM月dd日', { locale: ja })
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">泊数</dt>
                <dd className="text-sm text-gray-900">{reservation.nights || 1}泊</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">部屋タイプ</dt>
                <dd className="text-sm text-gray-900">{reservation.room_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">室数</dt>
                <dd className="text-sm text-gray-900">{reservation.rooms || 1}室</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">プラン</dt>
                <dd className="text-sm text-gray-900">{reservation.plan_name || '-'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">食事</dt>
                <dd className="text-sm text-gray-900">{reservation.meal_plan || '食事なし'}</dd>
              </div>
            </dl>
          </div>

          {/* 宿泊者情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <User className="h-5 w-5 mr-2 text-gray-400" />
              宿泊者情報
            </h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">宿泊者名</dt>
                <dd className="text-sm text-gray-900">
                  {isEditing ? (
                    <input
                      type="text"
                      value={editData?.guest_name || ''}
                      onChange={(e) => handleInputChange('guest_name', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    reservation.guest_name
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">カナ</dt>
                <dd className="text-sm text-gray-900">
                  {isEditing ? (
                    <input
                      type="text"
                      value={editData?.guest_name_kana || ''}
                      onChange={(e) => handleInputChange('guest_name_kana', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    reservation.guest_name_kana || '-'
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">電話番号</dt>
                <dd className="text-sm text-gray-900">
                  {isEditing ? (
                    <input
                      type="tel"
                      value={editData?.guest_phone || ''}
                      onChange={(e) => handleInputChange('guest_phone', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    reservation.guest_phone || '-'
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">メールアドレス</dt>
                <dd className="text-sm text-gray-900 break-all">
                  {isEditing ? (
                    <input
                      type="email"
                      value={editData?.guest_email || ''}
                      onChange={(e) => handleInputChange('guest_email', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded-md w-full"
                    />
                  ) : (
                    reservation.guest_email || '-'
                  )}
                </dd>
              </div>
              <div className="pt-2 border-t">
                <div className="flex justify-between mb-2">
                  <dt className="text-sm font-medium text-gray-500">人数内訳</dt>
                  <dd className="text-sm text-gray-900">
                    {isEditing ? (
                      <div className="flex space-x-2">
                        <input
                          type="number"
                          value={editData?.num_adults || 0}
                          onChange={(e) => handleInputChange('num_adults', parseInt(e.target.value))}
                          className="w-16 px-2 py-1 border border-gray-300 rounded-md"
                          min="1"
                        />
                        <input
                          type="number"
                          value={editData?.num_children || 0}
                          onChange={(e) => handleInputChange('num_children', parseInt(e.target.value))}
                          className="w-16 px-2 py-1 border border-gray-300 rounded-md"
                          min="0"
                        />
                        <input
                          type="number"
                          value={editData?.num_infants || 0}
                          onChange={(e) => handleInputChange('num_infants', parseInt(e.target.value))}
                          className="w-16 px-2 py-1 border border-gray-300 rounded-md"
                          min="0"
                        />
                      </div>
                    ) : (
                      <>
                        大人{reservation.num_adults}
                        {reservation.num_children > 0 && ` 子供${reservation.num_children}`}
                        {reservation.num_infants > 0 && ` 幼児${reservation.num_infants}`}
                      </>
                    )}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">合計人数</dt>
                  <dd className="text-sm font-semibold text-gray-900">
                    {(editData?.num_adults || 0) + (editData?.num_children || 0) + (editData?.num_infants || 0)}名
                  </dd>
                </div>
              </div>
            </dl>
          </div>

          {/* 料金情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <CreditCard className="h-5 w-5 mr-2 text-gray-400" />
              料金情報
            </h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">合計金額</dt>
                <dd className="text-sm text-gray-900">
                  {isEditing ? (
                    <input
                      type="number"
                      value={editData?.total_amount || ''}
                      onChange={(e) => handleInputChange('total_amount', parseFloat(e.target.value))}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    reservation.total_amount ? `¥${reservation.total_amount.toLocaleString()}` : '-'
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">決済方法</dt>
                <dd className="text-sm text-gray-900">{reservation.payment_method || '-'}</dd>
              </div>
              {reservation.booker_name && (
                <>
                  <div className="pt-2 border-t">
                    <div className="flex justify-between">
                      <dt className="text-sm font-medium text-gray-500">予約者名</dt>
                      <dd className="text-sm text-gray-900">{reservation.booker_name}</dd>
                    </div>
                  </div>
                  {reservation.booker_name_kana && (
                    <div className="flex justify-between">
                      <dt className="text-sm font-medium text-gray-500">予約者カナ</dt>
                      <dd className="text-sm text-gray-900">{reservation.booker_name_kana}</dd>
                    </div>
                  )}
                </>
              )}
            </dl>
          </div>

          {/* 予約メタ情報 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <AlertCircle className="h-5 w-5 mr-2 text-gray-400" />
              予約情報
            </h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">予約日</dt>
                <dd className="text-sm text-gray-900">
                  {reservation.reservation_date 
                    ? format(new Date(reservation.reservation_date), 'yyyy年MM月dd日 HH:mm', { locale: ja })
                    : '-'
                  }
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">チェックイン時刻</dt>
                <dd className="text-sm text-gray-900">{reservation.checkin_time || '-'}</dd>
              </div>
              {reservation.cancel_date && (
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">キャンセル日</dt>
                  <dd className="text-sm text-gray-900">
                    {format(new Date(reservation.cancel_date), 'yyyy年MM月dd日', { locale: ja })}
                  </dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">プランコード</dt>
                <dd className="text-sm text-gray-900">{reservation.plan_code || '-'}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* オプション・追加料金 */}
        {(reservation.option_items || reservation.option_amount || reservation.point_amount || isEditing) && (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h2 className="text-lg font-semibold mb-4">オプション・追加料金</h2>
            <dl className="space-y-3">
              {reservation.option_items && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-1">オプション項目</dt>
                  <dd className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                    {reservation.option_items}
                  </dd>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                {reservation.option_amount > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">オプション料金</dt>
                    <dd className="text-sm text-gray-900">¥{reservation.option_amount.toLocaleString()}</dd>
                  </div>
                )}
                {reservation.point_amount > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ポイント利用</dt>
                    <dd className="text-sm text-gray-900">¥{reservation.point_amount.toLocaleString()}</dd>
                  </div>
                )}
                {reservation.point_discount > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ポイント割引</dt>
                    <dd className="text-sm text-red-600">-¥{reservation.point_discount.toLocaleString()}</dd>
                  </div>
                )}
              </div>
            </dl>
          </div>
        )}

        {/* 料金内訳 */}
        {(reservation.adult_rate || reservation.child_rate || reservation.infant_rate) && (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h2 className="text-lg font-semibold mb-4">料金内訳</h2>
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="text-left py-2">区分</th>
                  <th className="text-right py-2">単価</th>
                  <th className="text-right py-2">人数</th>
                  <th className="text-right py-2">小計</th>
                </tr>
              </thead>
              <tbody>
                {reservation.adult_rate > 0 && (
                  <tr className="border-b">
                    <td className="py-2">大人</td>
                    <td className="text-right">¥{reservation.adult_rate?.toLocaleString() || 0}</td>
                    <td className="text-right">{reservation.num_adults}名</td>
                    <td className="text-right font-medium">¥{reservation.adult_amount?.toLocaleString() || 0}</td>
                  </tr>
                )}
                {reservation.child_rate > 0 && (
                  <tr className="border-b">
                    <td className="py-2">子供</td>
                    <td className="text-right">¥{reservation.child_rate?.toLocaleString() || 0}</td>
                    <td className="text-right">{reservation.num_children}名</td>
                    <td className="text-right font-medium">¥{reservation.child_amount?.toLocaleString() || 0}</td>
                  </tr>
                )}
                {reservation.infant_rate > 0 && (
                  <tr className="border-b">
                    <td className="py-2">幼児</td>
                    <td className="text-right">¥{reservation.infant_rate?.toLocaleString() || 0}</td>
                    <td className="text-right">{reservation.num_infants}名</td>
                    <td className="text-right font-medium">¥{reservation.infant_amount?.toLocaleString() || 0}</td>
                  </tr>
                )}
                {reservation.option_amount > 0 && (
                  <tr className="border-b">
                    <td className="py-2" colSpan={3}>オプション・その他</td>
                    <td className="text-right font-medium">¥{reservation.option_amount?.toLocaleString()}</td>
                  </tr>
                )}
                <tr className="font-bold">
                  <td className="py-3" colSpan={3}>合計</td>
                  <td className="text-right text-lg">¥{reservation.total_amount?.toLocaleString() || 0}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* ゲスト情報（住所等） */}
        {(reservation.postal_code || reservation.address || reservation.member_number) && (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h2 className="text-lg font-semibold mb-4">ゲスト詳細情報</h2>
            <dl className="space-y-3">
              {reservation.postal_code && (
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">郵便番号</dt>
                  <dd className="text-sm text-gray-900">〒{reservation.postal_code}</dd>
                </div>
              )}
              {reservation.address && (
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">住所</dt>
                  <dd className="text-sm text-gray-900">{reservation.address}</dd>
                </div>
              )}
              {reservation.member_number && (
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">会員番号</dt>
                  <dd className="text-sm text-gray-900">{reservation.member_number}</dd>
                </div>
              )}
              {reservation.company_info && (
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">法人情報</dt>
                  <dd className="text-sm text-gray-900">{reservation.company_info}</dd>
                </div>
              )}
              {reservation.reservation_route && (
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">予約経路</dt>
                  <dd className="text-sm text-gray-900">{reservation.reservation_route}</dd>
                </div>
              )}
            </dl>
          </div>
        )}

        {/* 備考・メモ */}
        {(reservation.notes || reservation.memo || isEditing) && (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h2 className="text-lg font-semibold mb-4">備考・メモ</h2>
            {reservation.notes && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">備考</h3>
                {isEditing ? (
                  <textarea
                    value={editData?.notes || ''}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    rows={4}
                  />
                ) : (
                  <p className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded">
                    {reservation.notes}
                  </p>
                )}
              </div>
            )}
            {reservation.memo && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">メモ</h3>
                <p className="text-sm text-gray-700 whitespace-pre-wrap bg-yellow-50 p-3 rounded">
                  {reservation.memo}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}