#!/bin/bash

# Test script to simulate CircleCI pipeline locally
echo "🧪 Testing CircleCI Pipeline Locally"
echo "====================================="

# Test 1: Build Docker image
echo "1. Building Docker image..."
docker build -t llms-txt-generator .
if [ $? -eq 0 ]; then
    echo "✅ Docker build successful"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Test 2: Test container startup
echo "2. Testing container startup..."
docker run -d --name test-container -p 8000:8000 -e FIRECRAWL_API_KEY=test_key llms-txt-generator
if [ $? -eq 0 ]; then
    echo "✅ Container started successfully"
else
    echo "❌ Container startup failed"
    exit 1
fi

# Test 3: Wait for container to be healthy
echo "3. Waiting for container to be healthy..."
sleep 15
if docker ps | grep test-container | grep -q healthy; then
    echo "✅ Container is healthy"
else
    echo "❌ Container health check failed"
    docker logs test-container
    docker stop test-container
    docker rm test-container
    exit 1
fi

# Test 4: Test API endpoints
echo "4. Testing API endpoints..."
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Root endpoint working"
else
    echo "❌ Root endpoint failed"
    docker stop test-container
    docker rm test-container
    exit 1
fi

if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Docs endpoint working"
else
    echo "❌ Docs endpoint failed"
    docker stop test-container
    docker rm test-container
    exit 1
fi

# Test 5: Test Python imports
echo "5. Testing Python imports..."
if docker run --rm -e FIRECRAWL_API_KEY=test_key llms-txt-generator python -c "import main; print('Application imports successfully')" > /dev/null 2>&1; then
    echo "✅ Python imports working"
else
    echo "❌ Python imports failed"
    docker stop test-container
    docker rm test-container
    exit 1
fi

# Cleanup
echo "6. Cleaning up..."
docker stop test-container
docker rm test-container

echo "🎉 All tests passed! CircleCI pipeline should work correctly."
echo "Next steps:"
echo "1. Push this code to your repository"
echo "2. Connect the repository to CircleCI"
echo "3. Add DOCKER_USERNAME and DOCKER_PASSWORD environment variables"
echo "4. Push to main branch to trigger the pipeline" 