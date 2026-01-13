# 🏨 LetStayInn – FastAPI Hotel Management System

LetStayInn is a **Hotel Management System backend** built with **FastAPI**. It manages **authentication, room bookings, service requests**, and **role-based access control**, and is designed for deployment using **Docker** on **AWS ECS Fargate**.

---

## 🚀 Features

* FastAPI (Python 3.12)
* JWT-based authentication
* Role-Based Access Control (Guest, Manager, Kitchen Staff, Cleaning Staff)
* Room booking & cancellation
* Service requests (Cleaning / Food)
* DynamoDB integration
* Dockerized & ECS Fargate ready
* Health check endpoint

---

## 🧱 Tech Stack

* **Backend:** FastAPI
* **Auth:** JWT
* **Database:** AWS DynamoDB
* **Container:** Docker
* **Cloud:** AWS ECS Fargate, ALB
* **IaC:** CloudFormation

---

## 📁 Project Structure

```text
letstayinn_python/
├── app/
├── tests/
├── Dockerfile
├── requirements.txt
└── deploy/
```

---

## 🐳 Run Locally

```bash
docker build -t letstayinn .
docker run -p 8000:8000 letstayinn
```

API Docs:

```
http://localhost:8000/docs
```

---

## ❤️ Health Check

```
GET /health
```

---

## ☁️ Deployment

* Docker image pushed to **Amazon ECR**
* Deployed on **ECS Fargate** behind **ALB**
* Uses **DynamoDB** for storage

---

## 👨‍💻 Author

**Shyam Pratap**
