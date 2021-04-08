# Tool to create merged database for Outlandish site.

This code is mostly extracted from the panoptes plugin for MalariaGEN Analytics, as that site showed
the same data as the Outlandish site. https://github.com/benjeffery/panoptes-plugin-malobs


### Setup
```
virtualenv -p `which python3` env
source env/bin/activate
pip3 install -r REQUIREMENTS
```
Create a file `settings_local` with credentials in:
```
observatoryDbServerUser: USER (Lee has these)
observatoryDbServerPass: PASS

alfrescoUserId: USER (These are your MalariaGEN SSO)
alfrescoUserPass: PASS

ldapUserDN: cn=website,ou=users,ou=system,dc=malariagen,dc=net
ldapUserPass: PASS (Ian has this)

# The following "client_secret" JSON file can be downloaded from https://console.cloud.google.com/apis/credentials?project=ssdtest-141111
gsheetsClientSecretPath: PATH
# The following credentials JSON file will be stored by the the malobs.py script
gsheetsCredentialsPath: PATH_AS_ABOVE_BUT_WITH_credentials.json

```

### Fetch FTP PF6 files and convert for observatory DB
```jupyter notebook fetch_and_convert.ipynb```

Run all cells to produce 3 csv files.
(Visual Studio Code works quite nicely for this)

### Backup existing DB

``` pg_dump -h localhost -p 9999 -U outlandish observatory_outlandish -n observatory --no-owner --no-privileges > obs_dump```

### Upload to postgres

```load_files.sh```

### Tunnel LDAP and postgres
35.185.117.147 is the postgres server


```
gcloud beta compute ssh --zone "us-east1-c" --project "ssdtest-141111" observatory-db -- -N -L 9999:localhost:5432
```

Connection to LDAP:

Make a temporary hole to allow connection to sso1 on 636 - ask a sysadmin


### Create CSV files:
```
python create_files.py 
```

### Create postgres DB from the CSVs for export to outlandish
```psql -v ON_ERROR_STOP=1 -d pf6 < schema.sql
```
```
./table-command.sh
```
Compare the output of print-tables.sh with load_files.psql to see if any
changes need to be made
```
psql -v ON_ERROR_STOP=1 -d pf6 < load_files.psql
```

Remove extra columns introduced as necessary for the loading process
```
psql -v ON_ERROR_STOP=1 -d pf6 < tidy_up.psql
```
### Dump out the resulting DB for sending

```
pg_dump pf6 --no-owner --no-privileges > pf6_dump
```



