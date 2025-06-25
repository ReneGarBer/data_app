cd ../src/

dbt run --full-refresh -s staging.staging_casos_dengue -t stg
dbt debug test -s staging.staging_casos_dengue -t stg > result.log || true

if grep -q "Completed successfully" result.log; then
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
