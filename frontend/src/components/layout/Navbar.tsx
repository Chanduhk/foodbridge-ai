import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Leaf, LogOut } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <nav className="hidden md:flex sticky top-0 z-50 bg-eco-dark text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 w-full">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2">
              <Leaf className="w-6 h-6 text-eco-light" />
              <span className="font-bold text-xl tracking-tight">FoodBridge AI</span>
            </div>
            
            <div className="flex space-x-1">
              <NavLink to="/dashboard" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-eco-primary text-white' : 'text-gray-200 hover:bg-eco-primary/50 hover:text-white'}`}>
                Dashboard
              </NavLink>
              
              {(user.role === 'donor' || user.role === 'admin') && (
                <NavLink to="/donations" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-eco-primary text-white' : 'text-gray-200 hover:bg-eco-primary/50 hover:text-white'}`}>
                  Donations
                </NavLink>
              )}
              
              {(user.role === 'recipient' || user.role === 'admin') && (
                <NavLink to="/available" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-eco-primary text-white' : 'text-gray-200 hover:bg-eco-primary/50 hover:text-white'}`}>
                  Available Food
                </NavLink>
              )}
              
              <NavLink to="/allocations" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-eco-primary text-white' : 'text-gray-200 hover:bg-eco-primary/50 hover:text-white'}`}>
                Allocations
              </NavLink>

              <NavLink to="/deliveries" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-eco-primary text-white' : 'text-gray-200 hover:bg-eco-primary/50 hover:text-white'}`}>
                Deliveries
              </NavLink>
              
              <NavLink to="/impact" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-eco-primary text-white' : 'text-gray-200 hover:bg-eco-primary/50 hover:text-white'}`}>
                Impact
              </NavLink>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium">{user.full_name}</span>
            <span className="px-2 py-1 text-xs font-semibold bg-eco-light/20 text-eco-light rounded-full uppercase">
              {user.role}
            </span>
            <button onClick={logout} className="p-2 text-gray-200 hover:text-white hover:bg-eco-primary/50 rounded-full transition-colors">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
