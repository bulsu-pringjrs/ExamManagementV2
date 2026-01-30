import React, { useEffect, useState } from 'react';
import { authAPI, classesAPI } from '../../services/api';
import { toast } from 'react-toastify';

const SuperAdminDashboard: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [usersRes, classesRes] = await Promise.all([
        authAPI.listUsers(),
        classesAPI.list(),
      ]);
      setUsers(usersRes.data.users);
      setClasses(classesRes.data.classes);
    } catch (error: any) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  const stats = {
    totalUsers: users.length,
    teachers: users.filter((u) => u.role === 'teacher').length,
    students: users.filter((u) => u.role === 'student').length,
    classes: classes.length,
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-sm text-gray-600 mb-2">Total Users</div>
          <div className="text-3xl font-bold text-orange-500">{stats.totalUsers}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-sm text-gray-600 mb-2">Teachers</div>
          <div className="text-3xl font-bold text-orange-500">{stats.teachers}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-sm text-gray-600 mb-2">Students</div>
          <div className="text-3xl font-bold text-orange-500">{stats.students}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-sm text-gray-600 mb-2">Classes</div>
          <div className="text-3xl font-bold text-orange-500">{stats.classes}</div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Recent Classes</h2>
        <div className="space-y-3">
          {classes.slice(0, 5).map((cls) => (
            <div
              key={cls.id}
              className="flex justify-between items-center p-4 bg-gray-50 rounded"
            >
              <div>
                <div className="font-medium text-gray-800">{cls.class_name}</div>
                <div className="text-sm text-gray-600">{cls.subject}</div>
              </div>
              <div className="text-sm text-gray-600">
                {cls.student_ids.length} students
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SuperAdminDashboard;