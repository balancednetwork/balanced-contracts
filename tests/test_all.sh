#!/bin/sh
echo "Running tbears tests...."
tbears test tbears_tests

echo "Running python tests"
for dir in $(find . -name tests_py) ; do
  for file in "$dir"/test*
    do
       python3 "$file"
    done
done
