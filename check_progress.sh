#!/bin/bash
# check_progress.sh - Check GitHub AI talent fetch progress on Hetzner

SERVER="100.112.67.38"
KEY="$HOME/.ssh/id_ed25519"
REMOTE_FILE="/root/github-ai-talent/final_talent_locations.csv"
TOTAL=197402

echo "Connecting to Hetzner..."
ssh -i "$KEY" root@$SERVER << 'EOF'
TOTAL=197402
FILE="/root/github-ai-talent/final_talent_locations.csv"

echo ""
echo "===== GitHub Fetch Progress ====="

# Row count
ROWS=$(wc -l < "$FILE" 2>/dev/null || echo 0)
echo "Rows fetched:     $ROWS / $TOTAL"

# Percentage
PCT=$(awk "BEGIN {printf \"%.1f\", ($ROWS/$TOTAL)*100}")
echo "Progress:         $PCT%"

# Screen status
echo ""
echo "===== Screen Session ====="
screen -ls

# Top locations so far
echo ""
echo "===== Top 10 Locations So Far ====="
awk -F',' 'NR>1 && $5!=""' "$FILE" | cut -d',' -f5 | sort | uniq -c | sort -rn | head -10

echo ""
echo "===== Disk Usage ====="
du -sh "$FILE"
EOF
