import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { classesAPI, authAPI } from '../../services/api';
import { toast } from 'react-toastify';

const ClassDetail: React.FC = () => {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [classData, setClassData] = useState<any>(null);
  const [exams, setExams] = useState<any[]>([]);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState('');

  useEffect(() => {
    fetchData();
  }, [classId]);

  const fetchData = async () => {
    try {
      const [classRes, examsRes, usersRes] = await Promise.all([
        classesAPI.get(Number(classId)),
        classesAPI.getExams(Number(classId)),
        authAPI.listUsers(),
      ]);
      setClassData(classRes.data);
      setExams(examsRes.data.exams);
      setAllUsers(usersRes.data.users);
    } catch (error) {
      toast.error('Failed to load class data');
    } finally {
      setLoading(false);
    }
  };

  const handleEnrollStudent = async () => {
    if (!selectedStudent) return;
    try {
      await classesAPI.enrollStudent(Number(classId), Number(selectedStudent));
      toast.success('Student enrolled successfully');
      setShowEnrollModal(false);
      setSelectedStudent('');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to enroll student');
    }
  };

  const handleRemoveStudent = async (studentId: number) => {
    if (!confirm('Remove this student from the class?')) return;
    try {
      await classesAPI.removeStudent(Number(classId), studentId);
      toast.success('Student removed successfully');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to remove student');
    }
  };

  const toggleExamAvailability = async (examId: number, currentStatus: string) => {
    const newStatus = currentStatus === 'enabled' ? 'disabled' : 'enabled';
    try {
      const { examsAPI } = await import('../../services/api');
      await examsAPI.toggleAvailability(examId, newStatus);
      toast.success(`Exam ${newStatus}`);
      fetchData();
    } catch (error: any) {
      toast.error('Failed to toggle exam availability');
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!classData) {
    return <div>Class not found</div>;
  }

  const enrolledStudents = allUsers.filter((user) =>
    classData.student_ids.includes(user.id)
  );
  const availableStudents = allUsers.filter(
    (user) =>
      user.role === 'student' && !classData.student_ids.includes(Number(user.id))
  );

  return (
    <div>
      <button
        onClick={() => navigate('/teacher/dashboard')}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">
              Enrolled Students ({enrolledStudents.length})
            </h2>
            <button
              onClick={() => setShowEnrollModal(true)}
              className="bg-orange-500 text-white px-4 py-2 rounded text-sm hover:bg-orange-600"
            >
              Add Student
            </button>
          </div>
          <div className="space-y-2">
            {enrolledStudents.map((student) => (
              <div
                key={student.id}
                className="flex justify-between items-center p-3 bg-gray-50 rounded"
              >
                <div>
                  <div className="font-medium text-gray-800">
                    {student.full_name}
                  </div>
                  <div className="text-sm text-gray-600">{student.email}</div>
                </div>
                <button
                  onClick={() => handleRemoveStudent(Number(student.id))}
                  className="text-red-500 hover:text-red-600 text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
            {enrolledStudents.length === 0 && (
              <p className="text-gray-500 text-center py-4">No students enrolled</p>
            )}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">
              Exams ({exams.length})
            </h2>
            <button
              onClick={() => navigate(`/teacher/class/${classId}/create-exam`)}
              className="bg-orange-500 text-white px-4 py-2 rounded text-sm hover:bg-orange-600"
            >
              Create Exam
            </button>
          </div>
          <div className="space-y-2">
            {exams.map((exam) => (
              <div
                key={exam.id}
                className="p-4 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">{exam.title}</div>
                    <div className="text-sm text-gray-600">
                      {exam.duration_minutes} min • {exam.question_count} questions
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exam.availability_status === 'enabled'}
                      onChange={() =>
                        toggleExamAvailability(exam.id, exam.availability_status)
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-500"></div>
                  </label>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => navigate(`/teacher/exam/${exam.id}/submissions`)}
                    className="text-sm text-orange-500 hover:text-orange-600"
                  >
                    View Submissions
                  </button>
                </div>
              </div>
            ))}
            {exams.length === 0 && (
              <p className="text-gray-500 text-center py-4">No exams created</p>
            )}
          </div>
        </div>
      </div>

      {showEnrollModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              Enroll Student
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Student
                </label>
                <select
                  value={selectedStudent}
                  onChange={(e) => setSelectedStudent(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                >
                  <option value="">Choose a student...</option>
                  {availableStudents.map((student) => (
                    <option key={student.id} value={student.id}>
                      {student.full_name} ({student.email})
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowEnrollModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEnrollStudent}
                  disabled={!selectedStudent}
                  className="flex-1 px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:bg-gray-400"
                >
                  Enroll
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClassDetail;