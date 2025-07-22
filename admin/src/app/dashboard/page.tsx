'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { analyticsApi } from '@/lib/api';
import { CalendarIcon, UsersIcon, CreditCardIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface DashboardStats {
  total_users: number;
  total_events: number;
  total_bookings: number;
  total_revenue: string;
  recent_events: Array<{
    id: string;
    title: string;
    start_date: string;
    status: string;
  }>;
  user_growth: Array<{
    date: string;
    count: number;
  }>;
}

const stats = [
  {
    name: 'Total Users',
    stat: '0',
    icon: UsersIcon,
    change: '+4.75%',
    changeType: 'increase',
  },
  {
    name: 'Total Events',
    stat: '0',
    icon: CalendarIcon,
    change: '+54.02%',
    changeType: 'increase',
  },
  {
    name: 'Total Bookings',
    stat: '0',
    icon: ChartBarIcon,
    change: '-1.39%',
    changeType: 'decrease',
  },
  {
    name: 'Total Revenue',
    stat: 'UGX 0',
    icon: CreditCardIcon,
    change: '+10.18%',
    changeType: 'increase',
  },
];

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await analyticsApi.getDashboardStats();
        setDashboardData(data);
        setError('');
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Update stats with real data when available
  const updatedStats = dashboardData ? [
    { ...stats[0], stat: dashboardData.total_users.toLocaleString() },
    { ...stats[1], stat: dashboardData.total_events.toLocaleString() },
    { ...stats[2], stat: dashboardData.total_bookings.toLocaleString() },
    { ...stats[3], stat: `UGX ${parseFloat(dashboardData.total_revenue).toLocaleString()}` },
  ] : stats;

  if (loading) {
    return (
      <Layout>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white overflow-hidden shadow rounded-lg p-5">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome to EventFlow Admin - Uganda Event Booking Platform
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 mb-6">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {updatedStats.map((item) => (
          <div key={item.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <item.icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{item.name}</dt>
                    <dd>
                      <div className="text-lg font-medium text-gray-900">{item.stat}</div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-5 py-3">
              <div className="text-sm">
                <span
                  className={`font-medium ${
                    item.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {item.change}
                </span>{' '}
                <span className="text-gray-500">from last month</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Events */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Events</h3>
          
          {dashboardData?.recent_events.length ? (
            <div className="flow-root">
              <ul className="-mb-8">
                {dashboardData.recent_events.map((event, eventIdx) => (
                  <li key={event.id}>
                    <div className="relative pb-8">
                      {eventIdx !== dashboardData.recent_events.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div className="relative">
                          <CalendarIcon
                            className="h-8 w-8 bg-purple-500 text-white rounded-full p-2"
                            aria-hidden="true"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div>
                            <p className="text-sm text-gray-500">
                              <span className="font-medium text-gray-900">{event.title}</span>{' '}
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  event.status === 'published'
                                    ? 'bg-green-100 text-green-800'
                                    : event.status === 'pending'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {event.status}
                              </span>
                            </p>
                            <p className="mt-0.5 text-sm text-gray-500">
                              {new Date(event.start_date).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="text-center py-6">
              <CalendarIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No events</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating your first event.</p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}