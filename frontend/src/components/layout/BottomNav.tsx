import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Home, Heart, Activity, Truck, UserCircle } from 'lucide-react';

export const BottomNav: React.FC = () => {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 pb-safe shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
      <div className="flex justify-around items-center h-16 px-2">
        <NavLink to="/dashboard" className={({ isActive }) => `flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${isActive ? 'text-eco-primary' : 'text-gray-400 hover:text-gray-600'}`}>
          <Home className="w-5 h-5" />
          <span className="text-[10px] font-medium">Home</span>
        </NavLink>

        <NavLink to={user.role === 'recipient' ? "/available" : "/donations"} className={({ isActive }) => `flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${isActive ? 'text-eco-primary' : 'text-gray-400 hover:text-gray-600'}`}>
          <Heart className="w-5 h-5" />
          <span className="text-[10px] font-medium">Food</span>
        </NavLink>

        <NavLink to="/allocations" className={({ isActive }) => `flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${isActive ? 'text-eco-primary' : 'text-gray-400 hover:text-gray-600'}`}>
          <Activity className="w-5 h-5" />
          <span className="text-[10px] font-medium">Matches</span>
        </NavLink>

        <NavLink to="/deliveries" className={({ isActive }) => `flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${isActive ? 'text-eco-primary' : 'text-gray-400 hover:text-gray-600'}`}>
          <Truck className="w-5 h-5" />
          <span className="text-[10px] font-medium">Delivery</span>
        </NavLink>

        <NavLink to="/profile" className={({ isActive }) => `flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${isActive ? 'text-eco-primary' : 'text-gray-400 hover:text-gray-600'}`}>
          <UserCircle className="w-5 h-5" />
          <span className="text-[10px] font-medium">Profile</span>
        </NavLink>
      </div>
    </nav>
  );
};
