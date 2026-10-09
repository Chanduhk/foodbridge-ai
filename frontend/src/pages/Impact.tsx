import React, { useState, useEffect } from 'react';
import { Leaf, Truck, Users, Trash2 } from 'lucide-react';
import api from '../lib/api';

export const Impact: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await api.get('/analytics/metrics');
        setMetrics(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, []);

  if (loading) return <div className="p-4">Loading impact metrics...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Community Impact</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card text-center py-8">
          <div className="mx-auto bg-eco-light/20 text-eco-primary p-4 rounded-full w-16 h-16 flex items-center justify-center mb-4">
            <Leaf className="w-8 h-8" />
          </div>
          <p className="text-sm text-gray-500 font-medium">Food Rescued</p>
          <p className="text-3xl font-bold mt-2">{metrics?.total_food_rescued_kg || 0} kg</p>
        </div>
        
        <div className="card text-center py-8">
          <div className="mx-auto bg-blue-100 text-blue-600 p-4 rounded-full w-16 h-16 flex items-center justify-center mb-4">
            <Users className="w-8 h-8" />
          </div>
          <p className="text-sm text-gray-500 font-medium">Est. Meals Served*</p>
          <p className="text-3xl font-bold mt-2">{Math.floor((metrics?.total_food_rescued_kg || 0) / 0.12)}</p>
          <p className="text-[10px] text-gray-400 mt-2">*Project-defined estimate (0.12kg/meal)</p>
        </div>
        
        <div className="card text-center py-8">
          <div className="mx-auto bg-green-100 text-green-600 p-4 rounded-full w-16 h-16 flex items-center justify-center mb-4">
            <Truck className="w-8 h-8" />
          </div>
          <p className="text-sm text-gray-500 font-medium">Deliveries Completed</p>
          <p className="text-3xl font-bold mt-2">{metrics?.deliveries_completed || 0}</p>
        </div>
        
        <div className="card text-center py-8">
          <div className="mx-auto bg-amber-100 text-amber-600 p-4 rounded-full w-16 h-16 flex items-center justify-center mb-4">
            <Trash2 className="w-8 h-8" />
          </div>
          <p className="text-sm text-gray-500 font-medium">Unmet Demand</p>
          <p className="text-3xl font-bold mt-2">{metrics?.unmet_demand_kg || 0} kg</p>
        </div>
      </div>
    </div>
  );
};
