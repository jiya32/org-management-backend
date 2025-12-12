# **Organization Management Service – Backend Assignment**

This project is a backend service designed for **multi-tenant organization management**, built using **FastAPI** and **MongoDB**.  
Each organization has its own dynamically created collection, while admin and metadata are stored in a **master database**.  
The service supports **organization creation, updating, deletion, and authentication using JWT**.

---

## **Project Structure**

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

---

## **Instructions to Run the Application**

### **Clone the Repository**

```bash
git clone https://github.com/jiya32/org-management-backend.git
cd org-management-backend
```
### **Create a Virtual Environment (Windows)**

```bash
python -m venv venv
venv\Scripts\activate
```
### **Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Create a .env File (not committed)**

```bash
MONGO_URI=your_mongodb_connection_string
MASTER_DB=master_db
JWT_SECRET=supersecretkey
JWT_ALGORITHM=HS256
JWT_EXP_SECONDS=3600
```

### **Start the FastAPI Server in VSCode Terminal**

```bash
uvicorn main:app --reload
```
Server will start at:

**Base URL:** http://127.0.0.1:8000

**API Docs:** http://127.0.0.1:8000/docs

### **Test the API Using Swagger UI**

Open: http://127.0.0.1:8000/docs

Use the Try it out button to test:

POST /org/create

POST /admin/login

PUT /org/update

DELETE /org/delete

After logging in, click Authorize and paste ONLY the JWT access token.

## **High-Level Architecture Diagram**

<img width="605" height="298" alt="image" src="https://github.com/user-attachments/assets/35ea341b-2281-4ebd-a822-03256b6f7e40" />

<img width="1001" height="479" alt="image" src="https://github.com/user-attachments/assets/5973f65c-7e06-4a50-9f90-f167be72e549" />

## **Design Choices**
### 1️. FastAPI for Backend Framework

FastAPI was selected due to its:

* High performance (built on ASGI + Starlette)

* Automatic Swagger UI generation (very useful for assignment review)

* Modern Pythonic syntax and type hints

* Easy dependency injection system (used for JWT auth)

This keeps the codebase clean, modular, and easy to scale.

### 2️. MongoDB as the Database

MongoDB was chosen because:

* It allows flexible schemas, perfect for multi-tenant systems.

* Dynamic creation of collections is straightforward.

* Each organization can have its own isolated collection, which aligns with real-world SaaS architecture.

This provides a clean separation of tenant data and avoids cross-contamination.

### 3️. Multi-Tenant Architecture

Organizations share:

A master database containing metadata (organizations, admins)

But each organization gets its own collection:

org_<sanitized_organization_name>


*Why this design?*

* Simplifies data isolation

* Easy to drop/update/migrate collections

* Enhances security (tenants do not see each other’s data)

* Allows future scalability (shard per organization, etc.)

### 4️. Argon2 for Password Hashing

Initially bcrypt caused backend compatibility issues, so Argon2 was selected because:

* It is considered the strongest password hashing algorithm currently in production cryptography.

* Handles long passwords safely. Fully supported by Passlib.

* This choice resolves the bcrypt edge-case bugs and improves security.

### 5️. JWT for Authentication

JWT tokens are used because they allow:

* Stateless authentication

* Lightweight tokens passed via headers

* No need to store sessions in DB

* FastAPI integrates easily with JWT

The JWT payload includes:

admin_id

org_id

email

expiration time

This enables secure authorization checks for protected routes like update/delete.

### 6️. Soft Delete for Organizations

Instead of permanently deleting organizations, we mark them:

"deleted": true


*Why?*

* Prevents accidental data loss

* Allows restore capability in future

* Maintains audit logs

Still removes dynamic collection immediately (as per assignment requirement)

### 7️. Dynamic Collection Migration (Update Org Name)

When organization name changes:

* A new collection is created

* Old data is copied over

* Metadata updated

* Old collection removed

This demonstrates data migration capability and shows backend engineering skills.

### 8️. Clean, Modular Code Structure

Although the assignment is a single-file prototype, code is designed so it can easily be expanded:

* Helpers grouped together

* Password hashing centralized

* JWT logic isolated

* Pydantic used for strict validation

* Dependency injection used for authentication

This reduces future bugs and simplifies maintenance.

### 9️. Error Handling and Validation

Includes:

* Duplicate organization checks

* Invalid credentials

* Unauthorized operations

* Missing/invalid JWT

* Regex-based organization lookup

* This ensures the backend behaves predictably and securely.

### 10. Why Not Use SQL or ORM?

MongoDB is better suited here because:

* Dynamic collection creation is easier

* No schema migrations needed

The assignment requires per-organization collections, which is simpler in MongoDB

## **Conclusion**

This project demonstrates the complete backend implementation of a multi-tenant organization management system, showcasing real-world backend engineering concepts such as:

* Dynamic collection creation per organization

* Secure authentication and authorization using JWT

* Robust password hashing with Argon2

* Data migration strategies during organization updates

* Soft-delete mechanisms for safer data handling

* Clean API design following FastAPI best practices

The architecture is intentionally designed to be scalable, secure, and easy to extend.
Key components—such as the master database, dynamic tenant collections, and centralized authentication—mirror the structure of production-grade SaaS systems.

This assignment highlights the ability to:

✔️ Work with modern Python frameworks

✔️ Design clean RESTful APIs

✔️ Implement multi-tenant data isolation

✔️ Apply best practices in authentication, security, and validation

✔️ Communicate architecture clearly using diagrams and documentation

With this setup, the service can be extended into a complete SaaS backend by adding user management, role-based access control, billing, analytics, and more.
