
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

Or run setup script:
- **Windows**: `setup.bat`
- **Mac/Linux**: `bash setup.sh`

### 3. Start Backend (Terminal 1)
```bash
python app.py
```

### 4. Start Frontend Server (Terminal 2)
```bash
python -m http.server 8000
```

### 5. Open Dashboard
```
http://localhost:8000
```

trouble shooting
- Try API directly: `http://localhost:5000/api/info`
