Project Summary
TESTIFY is a Smart LAN-Based Examination Management System designed to facilitate classroom-style learning and assessment. The application allows teachers to create classes and exams, students to join classes and take exams, and a Super Admin to manage users and system data. It is built to operate on a local area network (LAN), ensuring modularity and a clean structure for educational institutions.

Project Module Description
The project consists of the following functional modules:

Authentication: User login, registration, and role-based access control.
Class Management: Teachers can create and manage classes, while students can enroll in them.
Exam Management: Teachers can create various types of exams, manage their availability, and review student submissions.
Results Management: Automatic grading for objective questions and manual grading for subjective questions with detailed reporting for both teachers and students.
Directory Tree
app/
├── backend/          # FastAPI backend
│   ├── core/        # Core functionalities (config, database, security)
│   ├── models/      # Database models
│   ├── routers/     # API endpoints (auth, classes, exams)
│   ├── services/    # Business logic
│   ├── main.py      # FastAPI entry point
│   └── requirements.txt
└── frontend/        # React frontend
    ├── src/        # Source code
    ├── public/     # Static assets
    ├── index.html  # Main HTML file
    └── package.json # Dependencies
File Description Inventory
backend/: Contains the FastAPI backend code including routers, models, and services.
frontend/: Contains the React application including components, pages, and services.
requirements.txt: Lists the Python dependencies for the backend.
package.json: Lists the JavaScript dependencies for the frontend.
Technology Stack
Frontend: React, TypeScript, Vite
Backend: FastAPI, PostgreSQL
Database: MongoDB
Authentication: JWT
Usage
Install Dependencies:

For the backend: Navigate to the backend directory and run pip install -r requirements.txt.
For the frontend: Navigate to the frontend directory and run pnpm install.
Build the Application:

For the backend: Run the FastAPI application using uvicorn main:app --reload.
For the frontend: Run pnpm run build to create a production build.
Run the Application:

Start the backend server and ensure the database is running.
Serve the frontend application using a static server or integrate it with the backend.