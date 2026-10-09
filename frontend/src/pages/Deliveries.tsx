import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Truck, CheckCircle, Package } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const Deliveries: React.FC = () => {
  const [deliveries, setDeliveries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchDeliveries = async () => {
    try {
      // The API endpoint depends on the role (volunteer vs admin)
      // We will try fetching the generic deliveries endpoint
      const res = await api.get('/deliveries/');
      setDeliveries(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeliveries();
  }, []);

  const claimDelivery = async (id: string) => {
    try {
      await api.post(`/deliveries/${id}/claim`);
      fetchDeliveries();
    } catch (err) {
      console.error('Failed to claim delivery', err);
    }
  };

  const updateStatus = async (id: string, status: string) => {
    try {
      await api.patch(`/deliveries/${id}/status`, { status });
      fetchDeliveries();
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  if (loading) return <div className="p-4">Loading deliveries...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Deliveries</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {deliveries.length === 0 ? (
          <div className="col-span-full p-8 text-center text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
            No deliveries found.
          </div>
        ) : (
          deliveries.map(delivery => (
            <div key={delivery.id} className="card flex flex-col justify-between border-l-4 border-l-eco-primary">
              <div>
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold flex items-center"><Truck className="w-5 h-5 mr-2 text-eco-primary"/> Delivery {delivery.id.substring(0, 8)}</h3>
                  <span className="px-2 py-1 text-xs font-semibold bg-gray-100 text-gray-800 rounded-full uppercase">
                    {delivery.status}
                  </span>
                </div>
                <div className="mt-4 text-sm text-gray-700 space-y-2">
                  <p><strong>Pickup Time:</strong> {delivery.pickup_time ? new Date(delivery.pickup_time).toLocaleString() : 'Not scheduled'}</p>
                  <p><strong>Delivery Time:</strong> {delivery.delivery_time ? new Date(delivery.delivery_time).toLocaleString() : 'Not delivered'}</p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                {user?.role === 'volunteer' && delivery.status === 'pending' && (
                  <button onClick={() => claimDelivery(delivery.id)} className="btn-primary w-full text-sm py-2 flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 mr-2" /> Claim Task
                  </button>
                )}
                {user?.role === 'volunteer' && delivery.status === 'assigned' && (
                  <button onClick={() => updateStatus(delivery.id, 'picked_up')} className="btn-primary w-full text-sm py-2 flex items-center justify-center">
                    <Package className="w-4 h-4 mr-2" /> Mark Picked Up
                  </button>
                )}
                {user?.role === 'volunteer' && delivery.status === 'picked_up' && (
                  <button onClick={() => updateStatus(delivery.id, 'in_transit')} className="btn-primary w-full text-sm py-2 flex items-center justify-center">
                    <Truck className="w-4 h-4 mr-2" /> Mark In Transit
                  </button>
                )}
                {user?.role === 'volunteer' && delivery.status === 'in_transit' && (
                  <button onClick={() => updateStatus(delivery.id, 'delivered')} className="btn-primary w-full text-sm py-2 flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 mr-2" /> Mark Delivered
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
