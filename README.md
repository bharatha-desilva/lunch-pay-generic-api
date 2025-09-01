# Lunch Pay Generic API

A generic FastAPI + MongoDB REST API with authentication and dynamic CRUD operations.

## Features

- **Authentication System**: JWT-based authentication with login, logout, profile, and token validation endpoints
- **Dynamic CRUD Operations**: Generic endpoints that work with any MongoDB collection
- **MongoDB Integration**: Connected to MongoDB Atlas with automatic document serialization
- **CORS Support**: Configured for cross-origin requests
- **Type Conversion**: Automatic query parameter type conversion for filtering

## API Endpoints

### Authentication Endpoints

- **POST** `/auth/register` - Register a new user with name, email, and password
- **POST** `/auth/login` - User login with email/password
- **POST** `/auth/logout` - User logout
- **GET** `/auth/profile` - Get current user profile
- **GET** `/auth/validate` - Validate authentication token

### Dynamic CRUD Endpoints

- **GET** `/{entity}` - Get all documents from a collection
- **GET** `/{entity}/id/{item_id}` - Get a single document by ID
- **POST** `/{entity}` - Save a new document
- **PUT** `/{entity}/{item_id}` - Update an existing document
- **DELETE** `/{entity}/{item_id}` - Delete a document by ID
- **GET** `/{entity}/filter` - Get filtered documents using query parameters

## Installation & Setup

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bharatha-desilva/lunch-pay-generic-api.git
   cd lunch-pay-generic-api
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API:**
   - API Base URL: `http://localhost:8000`
   - Interactive API Documentation: `http://localhost:8000/docs`
   - Alternative API Documentation: `http://localhost:8000/redoc`

### Deployment on Render

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render:**
   - Go to [Render](https://render.com)
   - Connect your GitHub account
   - Select "New Web Service"
   - Choose your repository: `lunch-pay-generic-api`
   - Configure the service:
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python main.py`
     - **Port:** Will be automatically set by Render

3. **Environment Variables (if needed):**
   - The MongoDB URI is currently hardcoded in the application
   - For production, consider setting `MONGODB_URI` as an environment variable

## Database Configuration

The API connects to MongoDB Atlas with the following configuration:
- **Database:** `fastapi_mongo_api`
- **Connection:** MongoDB Atlas cluster

### Users Collection

For authentication, create a `users` collection with documents like:
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "name": "testuser",
  "password": "testpassword",
  "role": "user",
  "created_at": "2024-01-01T00:00:00.000Z",
  "updated_at": "2024-01-01T00:00:00.000Z",
  "last_login": "2024-01-01T00:00:00.000Z",
  "is_active": true,
  "email_verified": false
}
```

**Note:** Currently, passwords are stored in plain text as per project requirements. In production, implement proper password hashing.

## Usage Examples

### Authentication

1. **Register:**
   ```bash
   curl -X POST "http://localhost:8000/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"name": "testuser", "email": "user@example.com", "password": "testpassword"}'
   ```

2. **Login:**
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email": "user@example.com", "password": "testpassword"}'
   ```

3. **Get Profile (requires authentication):**
   ```bash
   curl -X GET "http://localhost:8000/auth/profile" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Dynamic CRUD Operations

1. **Create a new product:**
   ```bash
   curl -X POST "http://localhost:8000/products" \
        -H "Content-Type: application/json" \
        -d '{"name": "Laptop", "price": 999.99, "category": "Electronics"}'
   ```

2. **Get all products:**
   ```bash
   curl -X GET "http://localhost:8000/products"
   ```

3. **Filter products by category:**
   ```bash
   curl -X GET "http://localhost:8000/products/filter?category=Electronics"
   ```

4. **Update a product:**
   ```bash
   curl -X PUT "http://localhost:8000/products/PRODUCT_ID" \
        -H "Content-Type: application/json" \
        -d '{"price": 899.99}'
   ```

5. **Delete a product:**
   ```bash
   curl -X DELETE "http://localhost:8000/products/PRODUCT_ID"
   ```

## Query Parameter Filtering

The `/filter` endpoint automatically converts query parameters:
- `"true"` / `"false"` → boolean
- Numbers → int or float
- Everything else → string
- `_id` is treated as string to avoid ObjectId conversion errors

Example:
```bash
# Filter by multiple criteria
curl "http://localhost:8000/products/filter?price=999&active=true&category=Electronics"
```

## Security Notes

- **JWT Secret:** Change the `SECRET_KEY` in production
- **HTTPS:** Enable HTTPS in production and update cookie settings
- **Password Hashing:** Implement proper password hashing (currently plain text)
- **Environment Variables:** Use environment variables for sensitive configuration
- **Rate Limiting:** Consider implementing rate limiting for production use

## Development

### Project Structure
```
lunch-pay-generic-api/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
└── .cursor/            # Cursor AI configuration
    └── rules/
        ├── auth-guidelines.mdc
        └── api-guidelines.mdc
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the changes
5. Submit a pull request

## License

This project is open source and available under the MIT License.
