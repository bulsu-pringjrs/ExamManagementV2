import React from 'react';

const Test: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-2xl">
        <h1 className="text-4xl font-bold text-orange-500 mb-4">TESTIFY</h1>
        <h2 className="text-2xl font-semibold text-gray-800 mb-6">
          Smart LAN-Based Examination Management System
        </h2>
        <div className="space-y-4 text-gray-700">
          <p className="text-lg">✅ System successfully deployed!</p>
          <div className="bg-amber-50 p-4 rounded border border-amber-200">
            <p className="font-semibold mb-2">Demo Login Credentials:</p>
            <ul className="space-y-2 text-sm">
              <li><strong>Super Admin:</strong> admin@testify.local / admin123</li>
              <li><strong>Teacher:</strong> teacher1@testify.local / teacher123</li>
              <li><strong>Student:</strong> student1@testify.local / student123</li>
            </ul>
          </div>
          <div className="mt-6">
            <a href="/login" className="inline-block bg-orange-500 text-white px-6 py-3 rounded hover:bg-orange-600 font-medium">
              Go to Login Page
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Test;