#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}[*] RUIJIE Voucher Bypass System${NC}"
echo -e "${YELLOW}[*] Checking Python...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python3 not found!${NC}"
    exit 1
fi

# Install requirements
echo -e "${YELLOW}[*] Installing requirements...${NC}"
pyth
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

# Create symlink if needed
if [ ! -f "zslk.so" ] && [ -f "zs.so" ]; then
    cp zs.so zslk.so
fi

# Run
python3 -c "import zslk; zslk.main()"
EOF

chmod +x run.sh
./run.sh
