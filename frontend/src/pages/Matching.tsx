import React from 'react';
import { CheckCircle2, ShieldAlert } from 'lucide-react';

export const Matching: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">AI Matching & Allocations</h1>
      </div>

      <div className="card border-l-4 border-l-eco-primary">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
          <div>
            <p className="text-xs font-semibold text-eco-primary uppercase tracking-wider">AI Match Recommendation</p>
            <h3 className="text-xl font-bold mt-1">Best Match — 92%</h3>
          </div>
          <div className="bg-eco-primary/10 text-eco-primary font-bold px-4 py-2 rounded-lg">
            92%
          </div>
        </div>

        <div className="mb-4">
          <h4 className="font-bold text-lg">Community Kitchen A</h4>
          <p className="text-sm text-gray-500">4.2 km away · Capacity 65 kg · High demand</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <p className="font-semibold mb-2 text-sm">Why this match?</p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center text-gray-700">
              <CheckCircle2 className="w-4 h-4 text-eco-primary mr-2" /> Food category accepted
            </li>
            <li className="flex items-center text-gray-700">
              <CheckCircle2 className="w-4 h-4 text-eco-primary mr-2" /> Sufficient capacity
            </li>
            <li className="flex items-center text-gray-700">
              <CheckCircle2 className="w-4 h-4 text-eco-primary mr-2" /> High current demand
            </li>
            <li className="flex items-center text-gray-700">
              <CheckCircle2 className="w-4 h-4 text-eco-primary mr-2" /> Short pickup distance
            </li>
          </ul>
        </div>
        
        <div className="flex items-center text-amber-600 text-sm mb-6 bg-amber-50 p-3 rounded-md">
          <ShieldAlert className="w-5 h-5 mr-2 flex-shrink-0" />
          <p>This recommendation is for decision support. You may manually adjust the allocation.</p>
        </div>

        <button className="btn-primary flex items-center">
          Propose Allocation <span className="ml-2">→</span>
        </button>
      </div>
    </div>
  );
};
