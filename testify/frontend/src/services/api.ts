import axios from 'axios';

const API_BASE_URL = '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
  createUser: (data: any) => api.post('/auth/users', data),
  listUsers: () => api.get('/auth/users'),
};

// Classes API
export const classesAPI = {
  create: (data: any) => api.post('/custom/classes', data),
  list: () => api.get('/custom/classes'),
  get: (id: number) => api.get(`/custom/classes/${id}`),
  enrollStudent: (classId: number, studentId: number) =>
    api.post(`/custom/classes/${classId}/enroll`, { student_id: studentId }),
  removeStudent: (classId: number, studentId: number) =>
    api.delete(`/custom/classes/${classId}/students/${studentId}`),
  getExams: (classId: number) => api.get(`/custom/classes/${classId}/exams`),
};

// Exams API
export const examsAPI = {
  create: (data: any) => api.post('/custom/exams', data),
  get: (id: number) => api.get(`/custom/exams/${id}`),
  toggleAvailability: (id: number, status: string) =>
    api.patch(`/custom/exams/${id}/toggle-availability`, {
      availability_status: status,
    }),
  submit: (id: number, answers: any[]) =>
    api.post(`/custom/exams/${id}/submit`, { answers }),
  getSubmissions: (id: number) => api.get(`/custom/exams/${id}/submissions`),
};

export default api;