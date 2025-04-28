# task_manager_api.py
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
from mysql.connector import Error
from datetime import date

app = FastAPI()

# Database connection configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yourpassword',
    'database': 'task_manager'
}

# Database connection helper
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str

class User(UserCreate):
    user_id: int

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: str = "pending"
    assigned_to: Optional[int] = None

class Task(TaskCreate):
    task_id: int
    created_at: date

# Database initialization (run once)
@app.on_event("startup")
def initialize_database():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create tasks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            due_date DATE,
            status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
            created_at DATE DEFAULT (CURRENT_DATE),
            assigned_to INT,
            FOREIGN KEY (assigned_to) REFERENCES users(user_id)
        )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
    except Error as e:
        print(f"Database initialization error: {e}")

# User CRUD operations
@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, full_name) VALUES (%s, %s, %s)",
            (user.username, user.email, user.full_name)
        )
        connection.commit()
        user_id = cursor.lastrowid
        return {**user.dict(), "user_id": user_id}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating user: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@app.get("/users/", response_model=List[User])
def read_users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SELECT user_id, username, email, full_name FROM users")
    users = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return users

# Task CRUD operations
@app.post("/tasks/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """INSERT INTO tasks 
            (title, description, due_date, status, assigned_to) 
            VALUES (%s, %s, %s, %s, %s)""",
            (task.title, task.description, task.due_date, 
             task.status, task.assigned_to)
        )
        connection.commit()
        task_id = cursor.lastrowid
        
        # Get the created task
        cursor.execute(
            "SELECT * FROM tasks WHERE task_id = %s", (task_id,)
        )
        created_task = cursor.fetchone()
        return created_task
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating task: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@app.get("/tasks/", response_model=List[Task])
def read_tasks(status: Optional[str] = None, assigned_to: Optional[int] = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT * FROM tasks"
    params = []
    
    conditions = []
    if status:
        conditions.append("status = %s")
        params.append(status)
    if assigned_to:
        conditions.append("assigned_to = %s")
        params.append(assigned_to)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return tasks

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskCreate):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """UPDATE tasks SET 
            title = %s, description = %s, due_date = %s, 
            status = %s, assigned_to = %s 
            WHERE task_id = %s""",
            (task.title, task.description, task.due_date, 
             task.status, task.assigned_to, task_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        connection.commit()
        
        # Get the updated task
        cursor.execute(
            "SELECT * FROM tasks WHERE task_id = %s", (task_id,)
        )
        updated_task = cursor.fetchone()
        return updated_task
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating task: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM tasks WHERE task_id = %s", (task_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        connection.commit()
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting task: {e}"
        )
    finally:
        cursor.close()
        connection.close()