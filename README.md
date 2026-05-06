
### 1. Add MongoDB Connection
Edit `.env` and replace with your connection string:
```
MONGO_URI=mongodb://localhost:27017
# or
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Dashboard
```bash
python3 frontend/app.py
```

### 5. Open Dashboard
```
http://localhost:5001
```
