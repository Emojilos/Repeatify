#!/bin/bash
# Re-scrape all 19 EGE 2025 tasks from SDAMGIA and upload to Supabase
# The parser extracts actual "Тип N" from each problem page,
# so theme IDs don't need to match EGE 2025 numbering.
set -e

cd "$(dirname "$0")/../.."
source .env
export SUPABASE_URL SUPABASE_SERVICE_KEY

for task in $(seq 1 19); do
    echo ""
    echo "========================================="
    echo "  Scraping themes for task $task / 19"
    echo "========================================="
    python3 tools/parsers/sdamgia_parser.py \
        --task-number "$task" \
        --max-problems 50 \
        --upload \
        --upload-images \
        --output "tools/parsers/sdamgia_task_${task}.json"
    echo "  Task $task done!"
done

echo ""
echo "All themes scraped and uploaded!"
echo "Note: Problems are classified by their actual 'Тип N' from SDAMGIA,"
echo "which may differ from the theme-based task number."
