#!/bin/bash

set -e  # exit on any errorl

cd Binamix

# 4️⃣ Download and unzip the SADIE II Database
echo "Setting up SADIE II database..."
uv run python -m binamix.sadie_db_setup

echo "✅ Binamix setup complete!"
