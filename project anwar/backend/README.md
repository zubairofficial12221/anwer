## NEO-SHOW Backend (Flask + MySQL)

### 1) Create the MySQL database + tables
Start **XAMPP Control Panel** → click **Start** on **MySQL**.

Then either:

**Option A (recommended): run the init script**

From `backend/`:

```bash
python init_db.py
```

**Option B: phpMyAdmin**

Open **phpMyAdmin** (XAMPP) and run the SQL inside `schema.sql`.

Or from command line:
- Import `backend/schema.sql` into MySQL (choose any method you prefer).

### 2) Install Python dependencies
From `backend/`:

```bash
python -m pip install -r requirements.txt
```

### 3) Configure environment
Copy:
- `.env.example` → `.env`

If you use XAMPP defaults, you usually only need to keep:
- `MYSQL_USER=root`
- `MYSQL_PASSWORD=` (empty)

### 4) Run the API
From `backend/`:

```bash
python app.py
```

API base URL:
- `http://127.0.0.1:5000`

Health check:
- `GET /api/health`

### 5) Frontend connection
Your `index.html` and `ticket.html` already call the API at:
- `http://127.0.0.1:5000`

So the flow is:
- `login.html` → `index.html`
- Select seats → **Confirm Purchase** → booking saved in MySQL
- Redirects to `ticket.html?booking_id=123` and shows **seat numbers**

