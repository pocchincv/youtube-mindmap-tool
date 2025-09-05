#!/bin/bash

# YouTube Mind Map Tool - Development Startup Script

echo "🚀 Starting YouTube Mind Map Tool Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required commands exist
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        return 1
    fi
}

echo -e "${BLUE}🔍 Checking dependencies...${NC}"
check_command node || exit 1
check_command npm || exit 1  
check_command python3 || exit 1
check_command pip || exit 1

echo -e "${GREEN}✅ All dependencies found${NC}"

# Start backend
echo -e "${BLUE}🔧 Starting FastAPI backend...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
python app/main.py &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started on http://localhost:8000${NC}"

cd ..

# Start frontend
echo -e "${BLUE}🎨 Starting React frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started on http://localhost:5173${NC}"

cd ..

echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo -e "${BLUE}📱 Frontend: http://localhost:5173${NC}"
echo -e "${BLUE}🔧 Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}📚 API Docs: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}💡 Press Ctrl+C to stop all servers${NC}"

# Wait for interrupt signal
trap 'echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT
wait