#!/bin/bash
# ATLAS OpenMemory Backup Script
# Purpose: Create dated backups of OpenMemory SQLite database
# Retention: Keep last 7 days of backups

DATE=$(date +%Y%m%d)
SOURCE="C:/Dev/openmemory/data/atlas_memory.sqlite"
BACKUP_DIR="C:/Strat_Trading_Bot/vectorbt-workspace/backups/openmemory"

echo "OpenMemory Backup Script - ATLAS Trading System"
echo "=============================================="
echo "Date: $(date)"
echo ""

# Create backup directory if not exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Check if source database exists
if [ ! -f "$SOURCE" ]; then
    echo "ERROR: Source database not found at: $SOURCE"
    echo "Ensure OpenMemory is installed and has been run at least once."
    exit 1
fi

# Get database size
DB_SIZE=$(du -h "$SOURCE" | cut -f1)
echo "Source database: $SOURCE"
echo "Database size: $DB_SIZE"
echo ""

# Copy database with date stamp
BACKUP_FILE="$BACKUP_DIR/atlas_memory_$DATE.sqlite"
echo "Creating backup: $BACKUP_FILE"
cp "$SOURCE" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup successful!"
    echo ""

    # Keep all backups (no deletion - databases are small)
    # Uncomment below to enable cleanup after 90 days:
    # echo "Cleaning old backups (keeping last 90 days)..."
    # find "$BACKUP_DIR" -name "atlas_memory_*.sqlite" -mtime +90 -delete

    # List current backups
    echo ""
    echo "Current backups:"
    ls -lh "$BACKUP_DIR"/atlas_memory_*.sqlite 2>/dev/null | awk '{print $9, "(" $5 ")"}'

    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/atlas_memory_*.sqlite 2>/dev/null | wc -l)
    echo ""
    echo "Total backups: $BACKUP_COUNT"
else
    echo "ERROR: Backup failed!"
    exit 1
fi

echo ""
echo "=============================================="
echo "Backup completed: atlas_memory_$DATE.sqlite"
