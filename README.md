# placement-portal-application
A Placement Portal web application that allows Admin (Institute), Company, and Student to interact with the system based on their roles.

## Admin Seeding & Initialization

### Purpose

This project uses role-based access control (RBAC) with a predefined Admin user.  
Since the Admin is a system-level actor (not created via the user interface), it is created using a dedicated seeding script.

This ensures:
- A default Admin always exists after database initialization
- Admin creation is deterministic and idempotent
- Credentials and roles are not hard-coded into application runtime logic

---

### Why `seed_admin.py` Exists

The `seed_admin.py` script is responsible for:

- Creating the default Admin user
- Assigning the ADMIN role to that user
- Ensuring the operation runs only once per database lifecycle
- Avoiding duplicate admin creation on repeated runs

This logic is intentionally kept outside `app.py` to:

- Prevent accidental reseeding on every application startup
- Maintain a clear separation between runtime logic and setup logic
- Make database initialization explicit and controlled

---

### How to Run the Admin Seeding Script

The script must be executed as a Python module, not as a plain script.

From the project root directory:

```bash
python -m controller.seed_admin 
```

---

### Why `python -m controller.seed_admin` Is Required

This project follows a **package-based structure**, where `controller/` is a Python module inside the application.

If the script is executed like this:

```bash
python controller/seed_admin.py
```
would cause import errors because Python would not recognize the project root as the import base.

Running the script with `-m`:
```bash
python -m controller.seed_admin
```
ensures that:

- Python treats the project root as the module root

- All internal imports (`controller.db`, `controller.models`, `app`) resolve correctly

- The script runs within the same application and database context as the main app

This avoids:

- Duplicate Flask app instances

- Incorrect database bindings

- Import and context-related runtime errors

---

### When to Run the Seeding Script

You should run `seed_admin.py`:

- Once, after the database tables are created

- Again only if the database (`instance/database.sqlite3`) is deleted or reset

You should NOT run it on every application startup.

---

### What Problem This Solves

This approach solves several common issues:

- Ensures a guaranteed Admin account without manual DB manipulation

- Avoids committing database files to version control

- Prevents admin duplication

- Keeps authentication, authorization, and setup logic cleanly separated

- Maintains compatibility with SQLite and Flask’s app context model

---

### Design Note

Admin users are implemented as:

- Entries in the `user` table

- Assigned the `ADMIN` role via the `user_roles` mapping

This allows:

- Support for multiple admins

- Centralized authentication

- Clean role-based authorization without a separate admin table