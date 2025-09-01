# Generic MongoDB API

A dynamic FastAPI REST API with MongoDB integration that can handle any entity/collection dynamically without predefined models.

## Features

- **Dynamic Entity Support**: Work with any collection/entity name via URL parameters
- **MongoDB Integration**: Full CRUD operations with MongoDB Atlas
- **No Schema Validation**: Accept and store any JSON object as-is
- **Auto Type Conversion**: Smart query parameter conversion for filtering
- **CORS Enabled**: Cross-origin requests supported
- **ObjectId Serialization**: Automatic conversion of MongoDB ObjectId to string

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{entity}` | Fetch all documents from the specified collection |
| GET | `/{entity}/id/{item_id}` | Fetch a single document by ObjectId |
| POST | `/{entity}` | Save a new JSON object |
| PUT | `/{entity}/{item_id}` | Update an existing document |
| GET | `/{entity}/filter` | Fetch documents with dynamic filtering |
| DELETE | `/{entity}/{item_id}` | Delete a document by ObjectId |

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/bharatha-desilva/lunch-pay-generic-api.git
   cd lunch-pay-generic-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - OpenAPI Schema: http://localhost:8000/redoc

### GitHub Deployment

1. **Push to GitHub**
   ```bash
   git init
   git remote add origin https://github.com/bharatha-desilva/lunch-pay-generic-api.git
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git push -u origin main
   ```

### Render Deployment

1. **Connect Repository**
   - Go to [Render](https://render.com)
   - Create a new Web Service
   - Connect your GitHub repository

2. **Configuration**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment**: Python 3

3. **Environment Variables** (if needed)
   - `PORT`: Automatically set by Render
   - MongoDB URI is already configured in the code

## API Usage Examples

### Create a new user
```bash
curl -X POST "https://your-app.onrender.com/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "age": 30}'
```

### Get all users
```bash
curl "https://your-app.onrender.com/users"
```

### Get user by ID
```bash
curl "https://your-app.onrender.com/users/id/64a7b8c9d12345e678901234"
```

### Update user
```bash
curl -X PUT "https://your-app.onrender.com/users/64a7b8c9d12345e678901234" \
  -H "Content-Type: application/json" \
  -d '{"age": 31}'
```

### Filter users
```bash
curl "https://your-app.onrender.com/users/filter?age=30&name=John"
```

### Delete user
```bash
curl -X DELETE "https://your-app.onrender.com/users/64a7b8c9d12345e678901234"
```

## Dynamic Filtering

The `/filter` endpoint supports dynamic query parameters:

- **Boolean conversion**: `"true"` and `"false"` → boolean values
- **Number conversion**: Automatic int/float conversion
- **String handling**: Everything else remains as string
- **Special handling**: `_id` field is kept as string to avoid ObjectId errors

Example:
```
GET /products/filter?price=100&inStock=true&category=electronics
```

## Response Format

All endpoints return data in a consistent format:

```json
{
  "data": { ... },           // Single document or array of documents
  "message": "...",          // Success message (for write operations)
  "count": 10,               // Number of documents (for list/filter operations)
  "filters": { ... }         // Applied filters (for filter operations)
}
```

## MongoDB Configuration

The API connects to MongoDB Atlas with the following configuration:
- **Database**: `fastapi_mongo_api`
- **Connection**: MongoDB Atlas cluster
- **Collections**: Dynamic based on entity parameter

## Error Handling

- **400**: Invalid ObjectId format
- **404**: Document not found
- **500**: Server errors with detailed messages

## Development

### Project Structure
```
lunch-pay-generic-api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.
