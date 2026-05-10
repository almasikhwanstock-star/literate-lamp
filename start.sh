name=start.sh url=https://github.com/almasikhwanstock-star/literate-lamp/blob/main/start.sh
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear

echo -e "${BLUE}"
echo "════════════════════════════════════════════════════════════"
echo "  Literate Lamp - Starting Application"
echo "════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ ERROR: Virtual environment not found!${NC}"
    echo
    echo "Please run './setup-python.sh' first to setup dependencies."
    echo
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  WARNING: .env file not found!${NC}"
    echo
    echo "1. Copy .env.example to .env"
    echo "2. Edit .env and add your API keys"
    echo
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ ERROR: Node.js not found!${NC}"
    echo "Download: https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}✓ Backend environment ready${NC}"
echo -e "${GREEN}✓ Frontend environment ready${NC}"
echo

# Install frontend dependencies if needed
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⏳ Installing frontend dependencies...${NC}"
    npm install --silent
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        cd ..
        exit 1
    fi
fi
cd ..

echo -e "${GREEN}✓ All systems ready!${NC}"
echo

clear
echo -e "${BLUE}"
echo "════════════════════════════════════════════════════════════"
echo "  ✓ STARTING SERVICES"
echo "════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo
echo -e "📡 Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "🎨 Frontend: ${BLUE}http://localhost:5173${NC}"
echo
echo "Press Ctrl+C to stop all services"
echo

# Start backend in background
echo -e "${YELLOW}⏳ Starting backend...${NC}"
(cd backend && python -m uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend in background
echo -e "${YELLOW}⏳ Starting frontend...${NC}"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo -e "${GREEN}✓ Both services started!${NC}"
echo

# Function to cleanup on exit
cleanup() {
    echo
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for processes
wait
