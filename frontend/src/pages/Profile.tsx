import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export const Profile: React.FC = () => {
  const { user } = useAuth();

  if (!user) return <div className="p-4">Loading...</div>;

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900">User Profile</h1>
      
      <div className="card space-y-4 border-l-4 border-l-eco-primary">
        <div className="flex items-center space-x-4 pb-4 border-b border-gray-100">
          <div className="w-16 h-16 bg-eco-primary/20 text-eco-primary rounded-full flex items-center justify-center text-2xl font-bold uppercase">
            {user.full_name.charAt(0)}
          </div>
          <div>
            <h2 className="text-2xl font-bold">{user.full_name}</h2>
            <p className="text-gray-500">{user.email}</p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <label className="block text-gray-500 font-medium">Role</label>
            <p className="font-semibold uppercase text-gray-900">{user.role}</p>
          </div>
          <div>
            <label className="block text-gray-500 font-medium">Status</label>
            <p className="font-semibold text-gray-900">{user.is_active ? 'Active' : 'Inactive'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
