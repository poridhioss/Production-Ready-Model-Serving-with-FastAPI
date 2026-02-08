## API Endpoints

### Authentication
POST /api/v1/auth/register - Register new user
POST /api/v1/auth/login - Login and get token

### Users
GET /api/v1/users/me - Get current user info

### Protected
GET /api/v1/protected/test - Test protected route

### Sentiment Analysis
POST /api/v1/sentiment/analyze - Analyze single text
POST /api/v1/sentiment/analyze/batch - Batch analysis (async)
GET /api/v1/sentiment/task/{task_id} - Check task status
GET /api/v1/sentiment/history - Get analysis history

### Health
GET /health - Health check
GET / - API info