import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Leaf } from 'lucide-react';

export const AvailableFood: React.FC = () => {
  const [donations, setDonations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAvailableFood = async () => {
    try {
      const res = await api.get('/donations/');
      // Filter for approved/eligible donations for the recipient
      setDonations(res.data.filter((d: any) => d.status === 'eligible' || d.status === 'approved'));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAvailableFood();
  }, []);

  if (loading) return <div className="p-4">Loading available food...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Available Food</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {donations.length === 0 ? (
          <div className="col-span-full p-8 text-center text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
            No eligible food currently available.
          </div>
        ) : (
          donations.map(donation => (
            <div key={donation.id} className="card flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start">
                  <h3 className="text-xl font-bold flex items-center">
                    <Leaf className="w-5 h-5 mr-2 text-eco-primary"/> {donation.title}
                  </h3>
                </div>
                <p className="text-sm text-gray-500 mt-2">{donation.description}</p>
                <div className="mt-4 grid grid-cols-2 gap-2 text-sm text-gray-700">
                  <div><strong>Category:</strong> {donation.food_category}</div>
                  <div><strong>Qty:</strong> {donation.quantity_kg} kg</div>
                  <div className="col-span-2"><strong>Expires:</strong> {new Date(donation.expiration_date).toLocaleString()}</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
