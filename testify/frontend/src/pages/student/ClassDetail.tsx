import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { classesAPI } from '../../services/api';
import { toast } from 'react-toastify';

const StudentClassDetail: React.FC = () => {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [classData, setClassData] = useState<any>(null);
  const [exams, setExams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [classId]);

  const fetchData = async () => {
    try {
      const [classRes, examsRes] = await Promise.all([
        classesAPI.get(Number(classId)),
        classesAPI.getExams(Number(classId)),
      ]);
      setClassData(classRes.data);
      setExams(examsRes.data.exams);
    } catch (error) {
      toast.error('Failed to load class data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!classData) {
    return <div>Class not found</div>;
  }

  return (
    <div>
      <button
        onClick={() => navigate('/student/dashboard')}
        className="text-orange-500 hover:text-orange-600 mb-4"
      >
        ← Back to Classes
      </button>

      <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          {classData.class_name}
        </h1>
        <p className="text-gray-600">{classData.subject}</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Available Exams
        </h2>
        <div className="space-y-4">
          {exams.map((exam) => (
            <div
              key={exam.id}
              className="p-4 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800 mb-1">
                    {exam.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    {exam.description}
                  </p>
                  <div className="flex space-x-4 text-sm text-gray-600">
                    <span>⏱️ {exam.duration_minutes} minutes</span>
                    <span>📝 {exam.question_count} questions</span>
                    <span>💯 {exam.total_score} points</span>
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/student/exam/${exam.id}`)}
                  className="bg-orange-500 text-white px-6 py-2 rounded hover:bg-orange-600"
                >
                  Take Exam
                </button>
              </div>
            </div>
          ))}
          {exams.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              No exams available at this time
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentClassDetail;