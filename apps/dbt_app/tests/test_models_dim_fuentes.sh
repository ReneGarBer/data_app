#!bin/bash

cd ../src/

dbt run -s marts.dimensions.dim_fuente -t rfnd > result.log || true

grep -q "Completed successfully" result.log
if [ $? -eq 0 ]; then
    echo "not_failures=true" >> "$GITHUB_OUTPUT"
else
    echo "not_failures=false" >> "$GITHUB_OUTPUT"
fi

RESULT=$(cat result.log)
{
    echo "test_output<<EOF"
    echo "$RESULT"
    echo "EOF"
} >> "$GITHUB_OUTPUT"