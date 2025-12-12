# **Organization Management Service – Backend Assignment**

This project is a backend service designed for **multi-tenant organization management**, built using **FastAPI** and **MongoDB**.  
Each organization has its own dynamically created collection, while admin and metadata are stored in a **master database**.  
The service supports **organization creation, updating, deletion, and authentication using JWT**.

---

## **Project Structure**


Project Structure: 
org-management-backend/
│── main.py              # FastAPI application
│── README.md            # Project documentation
│── requirements.txt     # Dependencies
│── .env                 # Environment variables
│── .gitignore           # Ignored files (venv, .env, __pycache__)
└── venv/                # Virtual environment


---

## **Project Features**

### **Organization Lifecycle**

- Create organization  
- Automatically create a dynamic MongoDB collection (`org_<name>`)  
- Store organization metadata in master DB  
- Update organization name + migrate all data to a new collection  
- Delete organization (**soft delete** + collection drop)

---

### **Authentication**

- Admin login using **email + password**  
- Passwords hashed using **Argon2** (safest alternative to bcrypt)  
- JWT tokens with **admin ID + org ID + expiry**  
- Protected endpoints for update/delete organization

---

## **Multi-Tenant Architecture**

### **Master DB contains:**
- `organizations` collection (metadata)  
- `admins` collection  

### **Each organization has:**
- Its own dedicated collection for complete **data isolation**  


