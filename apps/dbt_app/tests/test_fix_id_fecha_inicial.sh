#!bin/bash

cd ../src/
dbt deps
dbt run -f -s marts.facts.fac_casos_dengue -t rfnd 
dbt test -s marts.facts.fac_casos_dengue -t rfnd > result.log || true

if grep -q "Completed successfully" result.log; then
    echo "not_failures='true'" >> "$GITHUB_OUTPUT"
else
    echo "not_failures='false'" >> "$GITHUB_OUTPUT"
fi

RESULT=$(cat result.log)
{
    echo "test_output<<EOF"
    echo "$RESULT"
    echo "EOF"
} >> "$GITHUB_OUTPUT"