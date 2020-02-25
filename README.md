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


### Upload to postgres
https://35.185.117.147/phppgadmin/redirect.php  (Lee has login)

Click servers -> PostgreSQL -> login -> observatory_outlandish -> observatory -> samples -> empty

Then "import", choose `samples.csv` and "Empty string/field" as the only checked options

Back to the list of tables and then do the same for `sampletypes` and `sampletypes1/2.csv`, but importing twice as there are two files
(one is too big for the import process)


### Tunnel LDAP and postgres
35.185.117.147 is the postgres server

35.189.232.128 is the analytics staging server we use to tunnel

gcloud.pub is your google ssl key that you add to the analystaging instance (see https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys)

ssh -N -i ~/.ssh/gcloud.pub -L 127.0.0.1:9999:35.185.117.147:5432 ben_jeffery_well@35.189.232.128

Tunnel to LDAP:

`ssh -N -i ~/.ssh/gcloud.pub -L 127.0.0.1:7777:sso1.malariagen.net:636 ben_jeffery_well@35.189.232.128`

LDAP checks the host matches what it expects, so we need to fake it by editing /etc/hosts:

`127.0.0.1       sso1.malariagen.net`


### Create CSV files:
python create_files.py 

### Create postgres DB from the CSVs for export to outlandish
```psql -d pf6 < schema.sql
psql -d pf6 < table-command.sh
```

### Dump out the resulting DB for sending
`pg_dump pf6 --no-owner --no-privileges > pf6_dump`



