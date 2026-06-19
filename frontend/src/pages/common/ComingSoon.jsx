import React from 'react';
import { Construction } from 'lucide-react';

const ComingSoon = ({ title }) => (
  <div className="flex flex-col items-center justify-center text-center py-20 px-4">
    <Construction className="w-10 h-10 text-gray-300 mb-3" />
    <h1 className="text-lg font-semibold text-gray-800">{title}</h1>
    <p className="text-sm text-gray-500 mt-1">This module is coming soon.</p>
  </div>
);

export default ComingSoon;
