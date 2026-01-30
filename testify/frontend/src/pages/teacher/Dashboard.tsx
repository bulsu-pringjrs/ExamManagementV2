import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { classesAPI } from '../../services/api';
import { toast } from 'react-toastify';

const TeacherDashboard: React.FC = () => {
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    class_name: '',
    subject: '',
  });
  const navigate = useNavigate();

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const response = await classesAPI.list();
      setClasses(response.data.classes);
    } catch (error) {
      toast.error('Failed to load classes');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await classesAPI.create(formData);
      toast.success('Class created successfully');
      setShowModal(false);
      setFormData({ class_name: '', subject: '' });
      fetchClasses();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create class');
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">My Classes</h1>
        <button
          onClick={() => setShowModal(true)}
          className="bg-orange-500 text-white px-6 py-2 rounded hover:bg-orange-600"
        >
          Create Class
        </button>
      </div>

      {classes.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow border border-gray-200 text-center">
          <p className="text-gray-600 mb-4">No classes yet</p>
          <button
            onClick={() => setShowModal(true)}
            className="bg-orange-500 text-white px-6 py-2 rounded hover:bg-orange-600"
          >
            Create Your First Class
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classes.map((cls) => (
            <div
              key={cls.id}
              onClick={() => navigate(`/teacher/class/${cls.id}`)}
              className="bg-white p-6 rounded-lg shadow border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <span className="text-orange-600 text-xl font-bold">
                    {cls.class_name.charAt(0)}
                  </span>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                {cls.class_name}
              </h3>
              <p className="text-sm text-gray-600 mb-4">{cls.subject}</p>
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>{cls.student_ids.length} students</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              Create New Class
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Class Name
                </label>
                <input
                  type="text"
                  value={formData.class_name}
                  onChange={(e) =>
                    setFormData({ ...formData, class_name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                  placeholder="e.g., Computer Science 101"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) =>
                    setFormData({ ...formData, subject: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                  placeholder="e.g., Computer Science"
                  required
                />
              </div>
              <div className="flex space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
                >
                  Create Class
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherDashboard;