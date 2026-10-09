import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { BottomNav } from './BottomNav';
import { useAuth } from '../../contexts/AuthContext';

export const MainLayout: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-eco-background flex flex-col">
      {user && <Navbar />}
      
      {/* pb-20 to accommodate mobile bottom nav without content hiding */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-8 pb-24 md:pb-8">
        <Outlet />
      </main>

      {user && <BottomNav />}
    </div>
  );
};
