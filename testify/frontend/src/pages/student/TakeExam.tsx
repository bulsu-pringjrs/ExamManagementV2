import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { examsAPI } from '../../services/api';
import { toast } from 'react-toastify';

const TakeExam: React.FC = () => {
  const { examId } = useParams();
  const navigate = useNavigate();
  const [exam, setExam] = useState<any>(null);
  const [answers, setAnswers] = useState<any[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [loading, setLoading] = useState(true);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    fetchExam();
  }, [examId]);

  useEffect(() => {
    if (started && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            handleSubmit();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [started, timeRemaining]);

  const fetchExam = async () => {
    try {
      const response = await examsAPI.get(Number(examId));
      setExam(response.data);
      setTimeRemaining(response.data.duration_minutes * 60);
      setAnswers(
        response.data.questions.map(() => ({
          answer: '',
        }))
      );
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load exam');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (value: any) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = { answer: value };
    setAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    if (!confirm('Submit your exam? You cannot change your answers after submission.')) {
      return;
    }

    try {
      await examsAPI.submit(Number(examId), answers);
      toast.success('Exam submitted successfully');
      navigate(-1);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to submit exam');
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!exam) {
    return <div>Exam not found</div>;
  }

  if (!started) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white p-8 rounded-lg shadow border border-gray-200">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">{exam.title}</h1>
          <p className="text-gray-600 mb-6">{exam.description}</p>
          <div className="space-y-3 mb-8">
            <div className="flex items-center text-gray-700">
              <span className="font-medium mr-2">Duration:</span>
              {exam.duration_minutes} minutes
            </div>
            <div className="flex items-center text-gray-700">
              <span className="font-medium mr-2">Questions:</span>
              {exam.questions.length}
            </div>
            <div className="flex items-center text-gray-700">
              <span className="font-medium mr-2">Total Points:</span>
              {exam.total_score}
            </div>
          </div>
          <div className="bg-amber-50 p-4 rounded border border-amber-200 mb-6">
            <p className="text-sm text-gray-700">
              <strong>Instructions:</strong>
            </p>
            <ul className="list-disc list-inside text-sm text-gray-700 mt-2 space-y-1">
              <li>You have {exam.duration_minutes} minutes to complete this exam</li>
              <li>The exam will auto-submit when time runs out</li>
              <li>You can navigate between questions</li>
              <li>Make sure to answer all questions before submitting</li>
            </ul>
          </div>
          <button
            onClick={() => setStarted(true)}
            className="w-full bg-orange-500 text-white py-3 rounded font-medium hover:bg-orange-600"
          >
            Start Exam
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = exam.questions[currentQuestionIndex];
  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">{exam.title}</h1>
          <div
            className={`text-2xl font-bold ${
              timeRemaining < 300 ? 'text-red-500' : 'text-orange-500'
            }`}
          >
            {minutes}:{seconds.toString().padStart(2, '0')}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-3">
          <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
            <div className="mb-4">
              <span className="text-sm text-gray-600">
                Question {currentQuestionIndex + 1} of {exam.questions.length}
              </span>
              <span className="float-right text-sm text-gray-600">
                {currentQuestion.points} points
              </span>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-6">
              {currentQuestion.question}
            </h2>

            {currentQuestion.type === 'multiple_choice' && (
              <div className="space-y-3">
                {currentQuestion.options.map((option: string, index: number) => (
                  <label
                    key={index}
                    className="flex items-center p-4 border border-gray-300 rounded hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name={`question-${currentQuestionIndex}`}
                      value={option}
                      checked={answers[currentQuestionIndex]?.answer === option}
                      onChange={(e) => handleAnswerChange(e.target.value)}
                      className="mr-3"
                    />
                    <span className="text-gray-800">{option}</span>
                  </label>
                ))}
              </div>
            )}

            {currentQuestion.type === 'enumeration' && (
              <div>
                <label className="block text-sm text-gray-700 mb-2">
                  Enter your answers (one per line)
                </label>
                <textarea
                  value={
                    Array.isArray(answers[currentQuestionIndex]?.answer)
                      ? answers[currentQuestionIndex].answer.join('\n')
                      : ''
                  }
                  onChange={(e) =>
                    handleAnswerChange(e.target.value.split('\n'))
                  }
                  className="w-full px-4 py-3 border border-gray-300 rounded focus:outline-none focus:border-orange-500"
                  rows={5}
                  placeholder="Enter each answer on a new line"
                />
              </div>
            )}

            {(currentQuestion.type === 'essay' ||
              currentQuestion.type === 'coding') && (
              <div>
                <textarea
                  value={answers[currentQuestionIndex]?.answer || ''}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded focus:outline-none focus:border-orange-500 font-mono"
                  rows={12}
                  placeholder={
                    currentQuestion.type === 'coding'
                      ? '// Write your code here'
                      : 'Write your answer here...'
                  }
                />
              </div>
            )}
          </div>

          <div className="flex justify-between">
            <button
              onClick={() =>
                setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))
              }
              disabled={currentQuestionIndex === 0}
              className="px-6 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            {currentQuestionIndex === exam.questions.length - 1 ? (
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                Submit Exam
              </button>
            ) : (
              <button
                onClick={() =>
                  setCurrentQuestionIndex(
                    Math.min(exam.questions.length - 1, currentQuestionIndex + 1)
                  )
                }
                className="px-6 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
              >
                Next
              </button>
            )}
          </div>
        </div>

        <div className="col-span-1">
          <div className="bg-white p-4 rounded-lg shadow border border-gray-200 sticky top-6">
            <h3 className="font-semibold text-gray-800 mb-4">Questions</h3>
            <div className="grid grid-cols-4 gap-2">
              {exam.questions.map((_: any, index: number) => (
                <button
                  key={index}
                  onClick={() => setCurrentQuestionIndex(index)}
                  className={`w-10 h-10 rounded ${
                    index === currentQuestionIndex
                      ? 'bg-orange-500 text-white'
                      : answers[index]?.answer
                      ? 'bg-green-100 text-green-800 border border-green-300'
                      : 'bg-gray-100 text-gray-700 border border-gray-300'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TakeExam;