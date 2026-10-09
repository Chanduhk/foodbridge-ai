import React, { useState } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { Leaf, Eye, EyeOff, Heart, Store, Truck } from 'lucide-react';

export const Register: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'donor'
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect to dashboard
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    
    try {
      // API expects: email, password, full_name, role
      await api.post('/auth/register', {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        role: formData.role
      });
      
      // Successfully created, backend doesn't return JWT on register.
      // Redirect to login page
      navigate('/login', { state: { message: 'Registration successful! Please sign in.' } });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-64px)] pb-16 md:pb-0">
      {/* Left Column: Info/Branding (Hidden on mobile) */}
      <div className="hidden md:flex flex-col justify-center w-1/2 bg-eco-primary text-white p-12 lg:p-20">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center space-x-3 mb-8">
            <div className="bg-white p-2 rounded-full text-eco-primary">
              <Leaf className="w-8 h-8" />
            </div>
            <span className="text-3xl font-bold tracking-tight">FoodBridge AI</span>
          </div>
          
          <h1 className="text-4xl lg:text-5xl font-bold mb-6 leading-tight">
            Connect surplus food with communities that need it.
          </h1>
          
          <p className="text-eco-light text-lg mb-10">
            Join our platform to help eliminate food waste and fight hunger. Our intelligent agent matches excess food from donors directly to the recipients who need it most.
          </p>
          
          <div className="space-y-6">
            <div className="flex items-start">
              <Store className="w-6 h-6 mr-4 text-amber-300 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-xl">For Donors</h3>
                <p className="text-eco-light mt-1">Easily log surplus food and let AI find the perfect match.</p>
              </div>
            </div>
            <div className="flex items-start">
              <Heart className="w-6 h-6 mr-4 text-amber-300 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-xl">For Recipients</h3>
                <p className="text-eco-light mt-1">Receive verified food donations tailored to your community's needs.</p>
              </div>
            </div>
            <div className="flex items-start">
              <Truck className="w-6 h-6 mr-4 text-amber-300 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-xl">For Volunteers</h3>
                <p className="text-eco-light mt-1">Make an impact by delivering food the last mile.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Form */}
      <div className="flex flex-col items-center justify-center w-full md:w-1/2 p-6 md:p-12 bg-gray-50">
        <div className="w-full max-w-md card p-8 bg-white shadow-sm border border-gray-100 rounded-xl">
          <div className="flex flex-col items-center mb-8 md:hidden">
            <div className="bg-eco-light/20 p-3 rounded-full mb-4">
              <Leaf className="w-10 h-10 text-eco-primary" />
            </div>
          </div>
          
          <h2 className="text-2xl font-bold text-center text-gray-900 md:text-left">Join FoodBridge AI</h2>
          <p className="text-sm text-gray-500 mt-1 text-center md:text-left mb-6">Create an account to get started</p>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6 text-sm" role="alert">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="full_name">Full Name</label>
              <input 
                id="full_name"
                name="full_name"
                type="text" 
                className="input-field" 
                value={formData.full_name}
                onChange={handleChange}
                placeholder="e.g. Jane Doe"
                required 
                minLength={2}
                autoComplete="name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="email">Email Address</label>
              <input 
                id="email"
                name="email"
                type="email" 
                className="input-field" 
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required 
                autoComplete="email"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="role">I want to join as a:</label>
              <select
                id="role"
                name="role"
                className="input-field bg-white"
                value={formData.role}
                onChange={handleChange}
                required
              >
                <option value="donor">Donor (Share surplus food)</option>
                <option value="recipient">Recipient (Access eligible food)</option>
                <option value="volunteer">Volunteer (Help deliver food)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="password">Password</label>
              <div className="relative">
                <input 
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"} 
                  className="input-field pr-10" 
                  value={formData.password}
                  onChange={handleChange}
                  required 
                  minLength={8}
                  autoComplete="new-password"
                />
                <button 
                  type="button" 
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">Min. 8 characters, 1 uppercase, 1 lowercase, 1 number.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="confirmPassword">Confirm Password</label>
              <div className="relative">
                <input 
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"} 
                  className="input-field pr-10" 
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required 
                  minLength={8}
                  autoComplete="new-password"
                />
                <button 
                  type="button" 
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            
            <button 
              type="submit" 
              disabled={loading}
              className="w-full btn-primary mt-6 py-2.5"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-eco-primary hover:text-eco-hover">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
