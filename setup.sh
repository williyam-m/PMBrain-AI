#!/bin/bash
# PMBrain AI — Setup & Start Script
set -e
echo "🧠 PMBrain AI — Setup"
echo "===================="
cd "$(dirname "$0")"

if [ ! -f .env ]; then
    echo "⚠️  .env not found. Please create one with your GEMINI_API_KEY"
    exit 1
fi

echo "📦 Running migrations..."
python3 manage.py makemigrations --noinput 2>/dev/null || true
python3 manage.py migrate --noinput
echo "   ✓ Database migrated"

echo "📁 Collecting static files..."
python3 manage.py collectstatic --noinput --clear 2>/dev/null
echo "   ✓ Static files collected"

mkdir -p media/codebases
echo ""
echo "🚀 Starting PMBrain AI at http://localhost:8000"
echo "   Register a new account to get started!"
echo ""
python3 manage.py runserver 0.0.0.0:8000
