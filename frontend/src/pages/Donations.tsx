import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { PlusCircle } from 'lucide-react';

export const Donations: React.FC = () => {
  const [donations, setDonations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    food_category: 'produce',
    quantity_kg: 0,
    expiration_date: new Date(Date.now() + 86400000).toISOString(),
    pickup_location: ''
  });

  const fetchDonations = async () => {
    try {
      const res = await api.get('/donations/my-donations');
      setDonations(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDonations();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/donations/', formData);
      setShowForm(false);
      fetchDonations();
    } catch (err) {
      console.error('Failed to create donation', err);
    }
  };

  if (loading) return <div className="p-4">Loading donations...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">My Donations</h1>
        <button 
          onClick={() => setShowForm(!showForm)} 
          className="btn-primary flex items-center"
        >
          <PlusCircle className="w-5 h-5 mr-2" /> New Donation
        </button>
      </div>

      {showForm && (
        <div className="card border-l-4 border-l-eco-primary">
          <h2 className="text-xl font-bold mb-4">Create Donation</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Title</label>
              <input type="text" required className="w-full mt-1 p-2 border rounded-md" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea className="w-full mt-1 p-2 border rounded-md" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Category</label>
                <select className="w-full mt-1 p-2 border rounded-md" value={formData.food_category} onChange={e => setFormData({...formData, food_category: e.target.value})}>
                  <option value="produce">Produce</option>
                  <option value="dairy">Dairy</option>
                  <option value="bakery">Bakery</option>
                  <option value="prepared">Prepared</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Quantity (kg)</label>
                <input type="number" required min="1" className="w-full mt-1 p-2 border rounded-md" value={formData.quantity_kg} onChange={e => setFormData({...formData, quantity_kg: parseFloat(e.target.value)})} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Expiration Date</label>
              <input type="datetime-local" required className="w-full mt-1 p-2 border rounded-md" value={formData.expiration_date.slice(0, 16)} onChange={e => setFormData({...formData, expiration_date: new Date(e.target.value).toISOString()})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Pickup Location</label>
              <input type="text" required className="w-full mt-1 p-2 border rounded-md" value={formData.pickup_location} onChange={e => setFormData({...formData, pickup_location: e.target.value})} />
            </div>
            <button type="submit" className="btn-primary w-full">Submit Donation</button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {donations.length === 0 ? (
          <div className="col-span-full p-8 text-center text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
            No donations yet. Click "New Donation" to get started!
          </div>
        ) : (
          donations.map(donation => (
            <div key={donation.id} className="card flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start">
                  <h3 className="text-xl font-bold">{donation.title}</h3>
                  <span className="px-2 py-1 text-xs font-semibold bg-gray-100 text-gray-800 rounded-full uppercase">
                    {donation.status}
                  </span>
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
