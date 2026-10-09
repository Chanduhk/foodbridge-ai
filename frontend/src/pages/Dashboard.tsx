import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Activity, Clock, Heart, Truck } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <span className="text-sm text-gray-500">Welcome back, {user?.full_name}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card flex items-center space-x-4">
          <div className="p-3 bg-eco-light/20 text-eco-primary rounded-lg">
            <Heart className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Total Rescued</p>
            <p className="text-2xl font-bold">1,245 kg</p>
          </div>
        </div>
        
        <div className="card flex items-center space-x-4">
          <div className="p-3 bg-amber-100 text-amber-600 rounded-lg">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Pending Action</p>
            <p className="text-2xl font-bold">3</p>
          </div>
        </div>
        
        <div className="card flex items-center space-x-4">
          <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Matches Found</p>
            <p className="text-2xl font-bold">12</p>
          </div>
        </div>
        
        <div className="card flex items-center space-x-4">
          <div className="p-3 bg-green-100 text-green-600 rounded-lg">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Deliveries</p>
            <p className="text-2xl font-bold">8</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-bold mb-4">Recent Activity</h2>
          <div className="space-y-4">
            <div className="p-4 border border-gray-100 rounded-lg bg-gray-50 flex justify-between items-center">
              <div>
                <p className="font-medium text-sm">Delivery completed</p>
                <p className="text-xs text-gray-500">45kg Produce to Community Kitchen A</p>
              </div>
              <span className="text-xs text-gray-400">2 hours ago</span>
            </div>
            <div className="p-4 border border-gray-100 rounded-lg bg-gray-50 flex justify-between items-center">
              <div>
                <p className="font-medium text-sm">New match found</p>
                <p className="text-xs text-gray-500">AI suggested Community Center B (92%)</p>
              </div>
              <span className="text-xs text-gray-400">5 hours ago</span>
            </div>
          </div>
        </div>
        <div className="card">
          <h2 className="text-lg font-bold mb-4">Quick Actions</h2>
          <div className="flex flex-col space-y-3">
            {user?.role === 'donor' && <button className="btn-primary w-full text-left">Offer Donation</button>}
            {user?.role === 'recipient' && <button className="btn-primary w-full text-left">Update Demand</button>}
            {user?.role === 'volunteer' && <button className="btn-primary w-full text-left">Find Pickups</button>}
            <button className="btn-secondary w-full text-left">View Impact Report</button>
          </div>
        </div>
      </div>
    </div>
  );
};
