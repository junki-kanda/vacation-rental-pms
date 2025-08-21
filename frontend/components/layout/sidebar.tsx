'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  Calendar, 
  BookOpen, 
  Building, 
  Upload, 
  Settings,
  TrendingUp,
  BarChart3,
  Users,
  ClipboardList,
  UserPlus,
  UsersIcon
} from 'lucide-react';
import { clsx } from 'clsx';
import { useState } from 'react';

const navigation = [
  { name: 'ダッシュボード', href: '/', icon: Home },
  { name: '予約一覧', href: '/reservations', icon: BookOpen },
  { name: 'カレンダー', href: '/calendar', icon: Calendar },
  { 
    name: '清掃管理', 
    href: '/cleaning', 
    icon: Users,
    children: [
      { name: 'ダッシュボード', href: '/cleaning', icon: BarChart3 },
      { name: 'タスク管理', href: '/cleaning/tasks', icon: ClipboardList },
      { name: 'スタッフ管理', href: '/cleaning/staff', icon: UserPlus },
      { name: 'グループ管理', href: '/cleaning/groups', icon: UsersIcon },
    ]
  },
  { name: '予実管理', href: '/budget', icon: TrendingUp },
  { name: '施設管理', href: '/facilities', icon: Building },
  { name: 'CSV同期', href: '/sync', icon: Upload },
  { name: '設定', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [expandedItems, setExpandedItems] = useState<string[]>(['清掃管理']);

  const toggleExpanded = (name: string) => {
    setExpandedItems(prev =>
      prev.includes(name)
        ? prev.filter(item => item !== name)
        : [...prev, name]
    );
  };

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900">
      <div className="flex h-16 items-center px-6">
        <h1 className="text-xl font-bold text-white">ねっぱん管理</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const isExpanded = expandedItems.includes(item.name);
          
          if (item.children) {
            return (
              <div key={item.name}>
                <button
                  onClick={() => toggleExpanded(item.name)}
                  className={clsx(
                    'flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  )}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  <span className="flex-1 text-left">{item.name}</span>
                  <svg
                    className={clsx(
                      'h-4 w-4 transition-transform',
                      isExpanded ? 'rotate-90' : ''
                    )}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                {isExpanded && (
                  <div className="ml-4 mt-1 space-y-1">
                    {item.children.map((child) => {
                      const isChildActive = pathname === child.href;
                      return (
                        <Link
                          key={child.name}
                          href={child.href}
                          className={clsx(
                            'flex items-center rounded-lg px-3 py-2 text-sm transition-colors',
                            isChildActive
                              ? 'bg-gray-700 text-white'
                              : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                          )}
                        >
                          <child.icon className="mr-2 h-4 w-4" />
                          {child.name}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          }
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}