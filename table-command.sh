 ls output | xargs -i echo echo "\\\COPY {} \(\\\"\`head -n1 output/{}/data | sed 's/\t/\\\", \\\"/g'\`\\\"\) FROM \'output/{}/data\' DELIMITER E\'\\\t\' CSV HEADER\;" > print-tables.sh
