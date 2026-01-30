import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { examsAPI } from '../../services/api';
import { toast } from 'react-toastify';

const CreateExam: React.FC = () => {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    duration_minutes: 30,
    total_score: 100,
  });
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState({
    type: 'multiple_choice',
    question: '',
    options: ['', '', '', ''],
    correct_answer: '',
    correct_answers: [''],
    points: 10,
  });

  const questionTypes = [
    { value: 'multiple_choice', label: 'Multiple Choice' },
    { value: 'enumeration', label: 'Enumeration' },
    { value: 'essay', label: 'Essay' },
    { value: 'coding', label: 'Coding' },
  ];

  const addQuestion = () => {
    if (!currentQuestion.question) {
      toast.error('Please enter a question');
      return;
    }

    const newQuestion = {
      id: questions.length + 1,
      ...currentQuestion,
    };

    setQuestions([...questions, newQuestion]);
    setCurrentQuestion({
      type: 'multiple_choice',
      question: '',
      options: ['', '', '', ''],
      correct_answer: '',
      correct_answers: [''],
      points: 10,
    });
    toast.success('Question added');
  };

  const removeQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (questions.length === 0) {
      toast.error('Please add at least one question');
      return;
    }

    try {
      await examsAPI.create({
        class_id: Number(classId),
        ...formData,
        questions,
      });
      toast.success('Exam created successfully');
      navigate(`/teacher/class/${classId}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create exam');
    }
  };

  return (
    <div>
      <button
        onClick={() => navigate(`/teacher/class/${classId}`)}
        className="text-orange-500 hover:text-orange-600 mb-4"
      >
        ← Back to Class
      </button>

      <h1 className="text-3xl font-bold text-gray-800 mb-8">Create New Exam</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Exam Details
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Exam Title
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Duration (minutes)
              </label>
              <input
                type="number"
                value={formData.duration_minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    duration_minutes: Number(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                rows={3}
              />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Add Questions
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Question Type
              </label>
              <select
                value={currentQuestion.type}
                onChange={(e) =>
                  setCurrentQuestion({ ...currentQuestion, type: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
              >
                {questionTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Question
              </label>
              <textarea
                value={currentQuestion.question}
                onChange={(e) =>
                  setCurrentQuestion({
                    ...currentQuestion,
                    question: e.target.value,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                rows={3}
              />
            </div>

            {currentQuestion.type === 'multiple_choice' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Options
                  </label>
                  {currentQuestion.options.map((option, index) => (
                    <input
                      key={index}
                      type="text"
                      value={option}
                      onChange={(e) => {
                        const newOptions = [...currentQuestion.options];
                        newOptions[index] = e.target.value;
                        setCurrentQuestion({
                          ...currentQuestion,
                          options: newOptions,
                        });
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500 mb-2"
                      placeholder={`Option ${index + 1}`}
                    />
                  ))}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Correct Answer
                  </label>
                  <select
                    value={currentQuestion.correct_answer}
                    onChange={(e) =>
                      setCurrentQuestion({
                        ...currentQuestion,
                        correct_answer: e.target.value,
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                  >
                    <option value="">Select correct answer</option>
                    {currentQuestion.options
                      .filter((opt) => opt)
                      .map((option, index) => (
                        <option key={index} value={option}>
                          {option}
                        </option>
                      ))}
                  </select>
                </div>
              </>
            )}

            {currentQuestion.type === 'enumeration' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Correct Answers (one per line)
                </label>
                <textarea
                  value={currentQuestion.correct_answers.join('\n')}
                  onChange={(e) =>
                    setCurrentQuestion({
                      ...currentQuestion,
                      correct_answers: e.target.value.split('\n'),
                    })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                  rows={4}
                  placeholder="Enter each correct answer on a new line"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Points
              </label>
              <input
                type="number"
                value={currentQuestion.points}
                onChange={(e) =>
                  setCurrentQuestion({
                    ...currentQuestion,
                    points: Number(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
              />
            </div>

            <button
              type="button"
              onClick={addQuestion}
              className="w-full bg-orange-500 text-white py-2 rounded hover:bg-orange-600"
            >
              Add Question
            </button>
          </div>
        </div>

        {questions.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Questions ({questions.length})
            </h2>
            <div className="space-y-4">
              {questions.map((q, index) => (
                <div
                  key={index}
                  className="p-4 bg-gray-50 rounded border border-gray-200"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="font-medium text-gray-800">
                        {index + 1}. {q.question}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        Type: {q.type} • Points: {q.points}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeQuestion(index)}
                      className="text-red-500 hover:text-red-600 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex space-x-4">
          <button
            type="button"
            onClick={() => navigate(`/teacher/class/${classId}`)}
            className="flex-1 px-6 py-3 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="flex-1 px-6 py-3 bg-orange-500 text-white rounded hover:bg-orange-600"
          >
            Create Exam
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateExam;