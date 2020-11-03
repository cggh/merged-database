import pandas
import yaml
from collections import OrderedDict
from os.path import join, isdir, isfile

## For data fetching
import psycopg2
import csv
import requests
import ldap
from base64 import b64encode
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

## For data processing
import geojson
import shapely.geometry
import shapely.ops
from shapely.geometry import JOIN_STYLE, Point

import sys # For: csv.field_size_limit(sys.maxsize)
import os # For: os.rename('data.tmp', 'data')

import overpass

with open('settings_nosecrets', 'r') as f:
    settings = yaml.load(f, Loader=yaml.BaseLoader)

with open('settings_local', 'r') as f:
    settings = {**settings, **yaml.load(f, Loader=yaml.BaseLoader)}

csv_value_separator = "\t"
csv_row_separator = "\n"
csv_list_separator = "; "


def run():

    # Determine the paths to the datatable directories.
    datatables_path = join('output')

    #####################################################################
    ### Observatory db server

    # Try to connect to the database,
    # http://initd.org/psycopg/docs/
    conn = psycopg2.connect(
        host = settings["observatoryDbServerHost"],
        port = str(settings["observatoryDbServerPort"]),
        sslmode = settings["observatoryDbServerSSL"],
        database = settings["observatoryDbServerDatabase"],
        user = settings["observatoryDbServerUser"],
        password = settings["observatoryDbServerPass"]
    )
    cur = conn.cursor()

    # Get the authoritative list of studies from the Observatory.
    study_list_query = "SELECT \"" + settings["observatoryDbStudyField"] + "\" FROM \"" + settings["observatoryDbServerDbSchema"] + "\".\"" + settings["observatoryDbStudiesView"] + "\""
    cur.execute(study_list_query)
    obsStudies = [row[0] for row in cur.fetchall()]

    if len(obsStudies) == 0:
        raise ValueError('observatoryDbStudiesView returned zero obsStudies')

    for observatoryDbView_index, observatoryDbView in enumerate(settings["observatoryDbViews"]):
        datatable = settings["panoptesObsTables"][observatoryDbView_index]
        datatable_path = join(datatables_path, datatable)
        data_file_path = join(datatable_path, "data")

        if not isdir(datatable_path):
            os.mkdir(datatable_path)

        # Open the data file for writing.
        data_file = open(data_file_path, 'w')

        # http://initd.org/psycopg/docs/cursor.html#cursor.copy_expert
        ## Mogrify throws a syntax error when I try to interpolate the params.
        # http://initd.org/psycopg/docs/cursor.html#cursor.mogrify
        # https://www.postgresql.org/docs/9.5/static/sql-copy.html
        ## Such queries can be checked first using the psql CLI, e.g.
        # COPY (SELECT * FROM observatory."Samples with types") TO STDOUT (FORMAT csv, HEADER TRUE, DELIMITER E'\t');
        copy_data_query = "COPY (SELECT * FROM \"" + settings["observatoryDbServerDbSchema"] + "\".\"" + observatoryDbView + "\") TO STDOUT (FORMAT csv, HEADER TRUE, DELIMITER E'\t', QUOTE E'\b', ESCAPE E'\b', NULL '')"''
        cur.copy_expert(copy_data_query, data_file)

        # Close the data file.
        data_file.close()

    #Get all countries JSON polygons
    geoJSON_for_country = {}
    query = 'SELECT "'+settings["panoptesObsCountriesTableCountryField"] + '","' + settings["panoptesObsCountriesTableGeoJsonField"] + \
            '" FROM "'+ settings["observatoryDbServerDbSchema"] + '"."' + settings["panoptesObsCountriesTable"] + '"'
    cur.execute(query)
    result = cur.fetchall()
    for (country_id, geoJSON) in result:
        geoJSON_for_country[country_id] = geoJSON


    # Close the db cursor and connection.
    cur.close()
    conn.close()

    #####################################################################
    ### Alfresco server (studies)
    data = requests.get(settings["alfrescoStudiesURL"], auth=(settings["alfrescoUserId"], settings["alfrescoUserPass"])).json()
    alfStudies = data["collaborationNodes"]

    if len(alfStudies) == 0:
        raise ValueError('fetchAlfrescoStudies returned zero collaborationNodes')

    # Collect the studies by name, to facilitate a subsequent parse.
    studiesByName = {}
    for study in alfStudies:
      if study["name"] not in studiesByName:
        studiesByName[study["name"]] = study
      else:
        raise ValueError('Duplicate study name: ', str(study['name']))


    #####################################################################
    ### LDAP server (people)

    ldapPeople = fetchLdapPeople(
        ldapServer=settings["ldapServerURL"]
        , ldapUserDN=settings["ldapUserDN"]
        , ldapUserPass=settings["ldapUserPass"]
        , ldapPeopleBaseDN=settings["ldapPeopleBaseDN"]
        , ldapPeopleFilterString=settings["ldapPeopleFilterString"]
        , ldapPeopleFields=settings["ldapPeopleFields"]
    )


    #####################################################################
    ### Google Sheets (genes)

    gsheets_service = discovery.build(
        settings["gsheetsApiServiceName"],
        settings["gsheetsApiServiceVersion"],
        http=establishGSheetsCredentials(
            settings["gsheetsClientSecretPath"],
            settings["gsheetsCredentialsPath"],
            settings["gsheetsAuthHost"],
            settings["gsheetsAuthPort"]
        ).authorize(httplib2.Http()),
        discoveryServiceUrl=settings["gsheetsApiDiscoveryUrl"]
    )

    for gsheetsId_index, gsheet_id in enumerate(settings["gsheetsIds"]):

        datatable = settings["panoptesGsheetsTables"][gsheetsId_index]
        datatable_path = join(datatables_path, datatable)
        data_file_path = join(datatable_path, "data")

        gsheet_range = settings["gsheetsRanges"][gsheetsId_index]

        if not isdir(datatable_path):
            os.mkdir(datatable_path)

        # Read in the data.
        gsheet_rows = gsheets_service.spreadsheets().values().get(spreadsheetId=gsheet_id, range=gsheet_range).execute().get('values', [])

        # Merge with data fetched from observatoryDb - observatoryDb rows are used and gsheet rows merged in, such that only primary keys from observatoryDb persist
        if datatable in settings["panoptesObsTables"]:
            print("Merging google sheet for " + datatable)
            with open(data_file_path, 'r') as data_file:
                exisiting_rows = list(csv.DictReader(data_file, delimiter=csv_value_separator))

            #Transform the google sheet rows to dicts
            gsheet_columns = gsheet_rows[0]
            gsheet_rows = [{key: (row[i] if i < len(row) else '') for i, key in enumerate(gsheet_columns)} for row in gsheet_rows[1:]]
            #Find the index column
            exisiting_columns = set(exisiting_rows[0].keys())
            matching_columns = set(gsheet_columns).intersection(exisiting_columns)
            all_columns = set(gsheet_columns).union(exisiting_columns)
            if len(matching_columns) != 1:
                raise ValueError('When merging a gsheet there should be one and only one column to match on, we got:', str(matching_columns))
            index_column = list(matching_columns)[0]
            #Index the gsheet data
            indexed_gsheet_rows = {row[index_column]:row for row in gsheet_rows}
            # Write out the data.
            with open(data_file_path, 'w') as data_file:
                writer = csv.DictWriter(data_file, all_columns, delimiter=csv_value_separator, lineterminator=csv_row_separator)
                writer.writeheader()
                for row in exisiting_rows:
                    row.update(indexed_gsheet_rows.get(row[index_column], {}))
                    writer.writerow(row)

        else:
            # Write out the data.
            with open(data_file_path, 'w') as data_file:
                writer = csv.writer(data_file, delimiter=csv_value_separator, lineterminator=csv_row_separator)
                for line in gsheet_rows:
                    writer.writerow(line)


    #####################################################################
    ### Process the Alfresco and LDAP data

    # Determine the paths to the datatable directories.
    alf_studies_datatable_dir_path = join(datatables_path, settings["panoptesAlfStudiesTable"])
    alf_study_publications_datatable_dir_path = join(datatables_path, settings["panoptesAlfStudyPublicationsTable"])
    alf_study_ldap_people_datatable_dir_path = join(datatables_path, settings["panoptesAlfStudyLdapPeopleTable"])


    if not isdir(alf_studies_datatable_dir_path):
        os.mkdir(alf_studies_datatable_dir_path)
    if not isdir(alf_study_publications_datatable_dir_path):
        os.mkdir(alf_study_publications_datatable_dir_path)
    if not isdir(alf_study_ldap_people_datatable_dir_path):
        os.mkdir(alf_study_ldap_people_datatable_dir_path)

    # Determine the paths to the data files.
    alf_studies_data_file_path = join(alf_studies_datatable_dir_path, "data")
    alf_study_publications_data_file_path = join(alf_study_publications_datatable_dir_path, "data")
    alf_study_ldap_people_data_file_path = join(alf_study_ldap_people_datatable_dir_path, "data")

    # Print a warning if any of the data files already exist.
    if isfile(alf_studies_data_file_path):
        print("Warning: Overwriting file: " + alf_studies_data_file_path)
    if isfile(alf_study_publications_data_file_path):
        print("Warning: Overwriting file: " + alf_study_publications_data_file_path)
    if isfile(alf_study_ldap_people_data_file_path):
        print("Warning: Overwriting file: " + alf_study_ldap_people_data_file_path)

    # Open the CSV files for writing.
    alf_studies_data_file = open(alf_studies_data_file_path, 'w')
    alf_study_publications_data_file = open(alf_study_publications_data_file_path, 'w')
    alf_study_ldap_people_data_file = open(alf_study_ldap_people_data_file_path, 'w')

    # Append the heading lines.
    alf_studies_data_file.write(csv_value_separator.join(["study"] + settings["alfrescoStudiesFields"]) + csv_row_separator)
    alf_study_publications_data_file.write(csv_value_separator.join(["study"] + settings["alfrescoStudyPublicationsFields"]) + csv_row_separator)
    alf_study_ldap_people_data_file.write(csv_value_separator.join(["study"] + settings["panoptesAlfStudyLdapPeopleFields"]) + csv_row_separator)

    webStudies = {}
    for study in alfStudies:
        if study['name'] not in obsStudies:
            continue
        if "webStudy" in study:
            webStudies[study['name']] = study['webStudy']['name']
            print("appending", study['webStudy']['name'])
            if study['webStudy']['name'] not in obsStudies:
                obsStudies.append(study['webStudy']['name'])

    studiesNotProcessed = list(obsStudies)
    for study in alfStudies:

        alf_study_name = study['name']
        study_number = getStudyNumber(study['name'], csv_value_separator)

        # Skip this study if the alf_study_name is not in the list of obsStudies.
        if alf_study_name not in obsStudies:
            continue

        if studiesNotProcessed is not None:
          studiesNotProcessed.remove(alf_study_name)

        # Skip anything with a webStudy.
        if "webStudy" in study:
            continue

        # Compose the study row, which will be appended to the CSV file
        # study	study_number    webTitle    description

        study_row = [alf_study_name, study_number]

        if study["webTitleApproved"] == "false":
            print("Warning: webTitle not approved for:" + study['name'])
        study_row.append(study["webTitle"].replace(csv_value_separator, ""))

        if study["descriptionApproved"] == "false":
            print("Warning: description not approved for:" + study['name'])
        study_row.append(study["description"].replace(csv_value_separator, ""))

        alfStudyLdapPeople = getAlfStudyLdapPeople(
            ldapPeople=ldapPeople
            , alfStudy=study
            , panoptesAlfStudyLdapPeopleGroups=settings["panoptesAlfStudyLdapPeopleGroups"]
        )

        # Write the related records: people and publications.
        writeRelatedRecords(study["publications"], alf_study_name, settings["alfrescoStudyPublicationsFields"], alf_study_publications_data_file, csv_list_separator, csv_row_separator, csv_value_separator)
        writeRelatedRecords(alfStudyLdapPeople, alf_study_name, settings["panoptesAlfStudyLdapPeopleFields"], alf_study_ldap_people_data_file, csv_list_separator, csv_row_separator, csv_value_separator)

        # Write the study to the CSV file
        alf_studies_data_file.write((csv_value_separator.join(study_row).replace("\n", " ").replace("\r", " ") + csv_row_separator).encode('ascii', 'xmlcharrefreplace').decode())

    if studiesNotProcessed is not None and len(studiesNotProcessed) > 0:
        raise ValueError('These studies were not found', str(studiesNotProcessed))

    # Close the CSV files.
    alf_studies_data_file.close()
    alf_study_publications_data_file.close()
    alf_study_ldap_people_data_file.close()


    #####################################################################
    ### Determine the paths to the datatable directories and data files.

    # Determine the paths to the datatable directories.
    if settings["panoptesObsRegionsTable"]:
        obs_regions_datatable_dir_path = join(datatables_path, settings["panoptesObsRegionsTable"])
    obs_samples_datatable_dir_path = join(datatables_path, settings["panoptesObsSamplesTable"])
    obs_countries_datatable_dir_path = join(datatables_path, settings["panoptesObsCountriesTable"])
    obs_locations_datatable_dir_path = join(datatables_path, settings["panoptesObsLocationsTable"])

    # Create dirs if the datatable directories are missing.
    if settings["panoptesObsRegionsTable"]:
        if not isdir(obs_regions_datatable_dir_path):
            os.mkdir(obs_regions_datatable_dir_path)
    if not isdir(obs_samples_datatable_dir_path):
        os.mkdir(obs_samples_datatable_dir_path)
    if not isdir(obs_countries_datatable_dir_path):
        os.mkdir(obs_countries_datatable_dir_path)

    # Determine the paths to the data files.
    if settings["panoptesObsRegionsTable"]:
        obs_regions_data_file_path = join(obs_regions_datatable_dir_path, "data")
    obs_samples_data_file_path = join(obs_samples_datatable_dir_path, "data")
    obs_locations_data_file_path = join(obs_locations_datatable_dir_path, "data")
    obs_countries_data_file_path = join(obs_countries_datatable_dir_path, "data")

    # Raise errors if the data files do not exist.
    if settings["panoptesObsRegionsTable"]:
        if not isfile(obs_regions_data_file_path):
            raise ValueError('panoptesObsRegionsTable data file does not exist at path: ', str(obs_regions_data_file_path))
    if not isfile(obs_samples_data_file_path):
        raise ValueError('panoptesObsSamplesTable data file does not exist at path: ', str(obs_samples_data_file_path))
    if not isfile(obs_countries_data_file_path):
        raise ValueError('panoptesObsCountriesTable data file does not exist at path: ', str(obs_countries_data_file_path))


    #####################################################################
    ### Modify the studies table to make studies with a "webStudy" masquerade as that study

    with open(obs_samples_data_file_path, 'r') as data_file:
        samples = list(csv.DictReader(data_file, delimiter=csv_value_separator))
    sample_columns = samples[0].keys()
    study_column = settings["panoptesObsSamplesTableStudyField"]
    with open(obs_samples_data_file_path, 'w') as data_file:
        writer = csv.DictWriter(data_file, sample_columns, delimiter=csv_value_separator, lineterminator=csv_row_separator)
        writer.writeheader()
        for row in samples:
            #Hack around postgres outputing bools as t/f (WTF?)
            if 'qc_pass' in row:
                row['qc_pass'] = 'True' if row['qc_pass'] == 't' else 'False'
            #Rewrite web studies
            if row[study_column] in webStudies:
                print(row[study_column], webStudies.get(row[study_column], row[study_column]))
                row[study_column] = webStudies[row[study_column]]
            writer.writerow(row)

    samples = pandas.read_csv(obs_samples_data_file_path, delimiter=csv_value_separator)

   #PROVINCE AND DISTRICT NOT NEEDED FOR NOW WITH PF6 AS SITES ARE USUALLY LARGE AREAS
   # locations = pandas.read_csv(obs_locations_data_file_path, delimiter=csv_value_separator)
   # locations.set_index('site_id')
   # provinces = []
   # for index, row in locations.iterrows():
   #     print(
   #         'Fetching location data from OSM for ' + row['name'] + ' in ' + row['country_id'])
   #     (province, district) = overpass.admin_levels_for_point(row['lat'], row['lng'])
   #     provinces.append(province)
   # locations['province_id'] = [province['province_id'] for province in provinces]
   # provinces = pandas.DataFrame(provinces).drop_duplicates('province_id')
   # # Denormalise somethings for convenience
   # samples['province_id'] = [locations.loc[s['site_id'], 'province_id'] for index, s in samples.iterrows()]
   # samples['country_id'] = [locations.loc[s['site_id'], 'country_id'] for index, s in samples.iterrows()]

    #os.mkdir(join(datatables_path, 'provinces'))
    #provinces.to_csv(join(datatables_path, 'provinces', 'data'), delimiter=csv_value_separator)
    #locations.to_csv(obs_locations_data_file_path, delimiter=csv_value_separator)

    markers = pandas.read_csv(
        'ftp://ngs.sanger.ac.uk/production/malaria/pfcommunityproject/Pf6/Pf_6_drug_resistance_marker_genotypes.txt',
        delimiter='\t')
    markers = markers.rename(columns={"Sample": "sample_id"})
    markers = markers.set_index('sample_id')

    fws = pandas.read_csv(
        'ftp://ngs.sanger.ac.uk/production/malaria/pfcommunityproject/Pf6/Pf_6_fws.txt',
        delimiter='\t'
    )
    fws = fws.rename(columns={"Sample": "sample_id"})
    fws = fws.set_index('sample_id')

    samples = samples.join(markers)
    samples = samples.join(fws)

    samples.to_csv(obs_samples_data_file_path, index=True, sep=csv_value_separator)

    gene_diff = pandas.read_csv('ftp://ngs.sanger.ac.uk/production/malaria/pfcommunityproject/Pf6/Pf_6_genes_data.txt',
                delimiter='\t')
    if not isdir(join(datatables_path, 'gene_diff')):
        os.mkdir(join(datatables_path, 'gene_diff'))
    gene_diff.to_csv(join(datatables_path, 'gene_diff', 'data'), sep=csv_value_separator)

    #####################################################################
    ### Generate the region GeoJSON

    if settings["panoptesObsRegionsTable"]:
        # Collect all of the distinct countries for each distinct region appearing in the obs_samples data.
        countries_by_region = {}
        sample_points = set()
        obs_samples_data_file_reader = csv.DictReader(open(obs_samples_data_file_path, 'r'), delimiter=csv_value_separator, lineterminator=csv_row_separator)
        i = 0
        countries = {}
        for row in obs_samples_data_file_reader:
            i += 1
            if settings["panoptesObsSamplesTableRegionField"] in row and settings["panoptesObsSamplesTableCountryField"] in row:
                region_id = row[settings["panoptesObsSamplesTableRegionField"]]
                country_id = row[settings["panoptesObsSamplesTableCountryField"]]
                countries.setdefault(country_id, {}).setdefault(region_id, 0)
                countries[country_id][region_id] += 1
                sample_points.add((float(row[settings["panoptesObsSamplesTableLngField"]]), float(row[settings["panoptesObsSamplesTableLatField"]])))
                if region_id in countries_by_region:
                    countries_by_region[region_id].add(country_id)
                else:
                    countries_by_region[region_id] = {country_id}
            else:
                raise ValueError('panoptesObsSamplesTableRegionField and panoptesObsSamplesTableCountryField are not in data at line: ', str(i))

        #If a country is in more than one region then just keep it in the modal region
        for country, region_counts in countries.items():
            bad_regions = sorted(region_counts.keys(),key=lambda r: region_counts[r])[:-1]
            for region in bad_regions:
                countries_by_region[region].remove(country)

        # Combine all of the GeoJSON for every country in each region.
        geojson_by_region = {}
        for region_id in countries_by_region:
            region_shape = None
            for country_id in countries_by_region[region_id].union(settings["panoptesObsRegionsAdditionalCountries"].get(region_id, [])):
                if geoJSON_for_country[country_id] is None or geoJSON_for_country[country_id] == '':
                    print('Ignoring ' + country_id + ' for polygon as no data')
                    continue
                new_region = shapely.geometry.asShape(geoJSON_for_country[country_id]['geometry'])
                if region_shape is None:
                    region_shape = new_region
                else:
                    region_shape = region_shape.union(new_region)
            if region_shape is not None:
                region_shape = region_shape.buffer(0.001, join_style=JOIN_STYLE.mitre).buffer(-0.001, join_style=JOIN_STYLE.mitre).simplify(0.1)
                #Filter the polygons in the shape that don't have samples in (ie islands without samples)
                region_shape = shapely.ops.cascaded_union([poly for poly in region_shape if any(poly.contains(Point(lng, lat)) for (lng, lat) in sample_points)])
            geojson_by_region[region_id] = geojson.Feature(geometry=region_shape, properties={})

        # Add the geojson to the region data file. (We have to write to a temporary file first.)
        with open(obs_regions_data_file_path, 'r') as obs_regions_data_in, open(obs_regions_data_file_path + '.tmp', 'w') as obs_regions_data_out:
            obs_regions_data_file_reader = csv.DictReader(obs_regions_data_in, delimiter=csv_value_separator, lineterminator=csv_row_separator)
            obs_regions_data_file_fieldnames = obs_regions_data_file_reader.fieldnames + [settings["panoptesObsRegionsTableGeoJsonField"]]
            obs_regions_data_file_writer = csv.DictWriter(obs_regions_data_out, fieldnames=obs_regions_data_file_fieldnames, delimiter=csv_value_separator, lineterminator=csv_row_separator, quoting=csv.QUOTE_NONE, escapechar="\\", quotechar="'")
            obs_regions_data_file_writer.writeheader()
            for obs_regions_data_file_line in obs_regions_data_file_reader:
                region_id = obs_regions_data_file_line[settings["panoptesObsRegionsTableRegionField"]]
                obs_regions_data_file_line['geojson'] = geojson_by_region[region_id]
                obs_regions_data_file_writer.writerow(obs_regions_data_file_line)

        # Overwrite the original data file.
        os.rename(obs_regions_data_file_path + '.tmp', obs_regions_data_file_path)

###################### Functions


def fetchLdapPeople(ldapServer, ldapUserDN, ldapUserPass, ldapPeopleBaseDN, ldapPeopleFilterString, ldapPeopleFields):

    ldapConnection = ldap.initialize(ldapServer)

    try:
        ldapConnection.bind_s(ldapUserDN, ldapUserPass)
    except ldap.INVALID_CREDENTIALS:
        raise ValueError('Invalid credentials for ldapServer: ', str(ldapServer))
    except ldap.LDAPError as e:
        if hasattr(e, 'message') and type(e.message) == dict and e.message.has_key('desc'):
            print(e.message['desc'])
        else:
            print(str(e))

    searchResults = ldapConnection.search_s(
        ldapPeopleBaseDN
        , ldap.SCOPE_SUBTREE
        , ldapPeopleFilterString
        , [str(x) for x in ldapPeopleFields]
    )

    ldapPeople = {}

    for dn, ldapEntry in searchResults:
      if 'malariagenUID' not in ldapEntry:
          print(("No malariagenUID in DN: ", dn, ", ldapEntry: ", str(ldapEntry)))
          continue

      malariagenUID = str(ldapEntry['malariagenUID'][0],"utf-8")
      ldapPeople[malariagenUID] = {'dn': dn}

      for ldapPeopleField in ldapPeopleFields:
          if ldapPeopleField in ldapEntry:
              ldapPeople[malariagenUID][ldapPeopleField] = str(ldapEntry[ldapPeopleField][0],"utf-8")


    ldapConnection.unbind()

    return ldapPeople


def getStudyNumber(study_name, csv_value_separator):
  return study_name.split('-')[0].replace(csv_value_separator, "")


def getAlfStudyLdapPeople(ldapPeople, alfStudy, panoptesAlfStudyLdapPeopleGroups):

    study_people = {}
    alfStudyLdapPeople = []

    for group_type in panoptesAlfStudyLdapPeopleGroups:
        group = alfStudy["group" + group_type]
        for study_person in group:
            malariagenUID = study_person['malariagenUID']
            if malariagenUID in ldapPeople:
                person = ldapPeople[malariagenUID]
                if malariagenUID in study_people:
                    for p in alfStudyLdapPeople:
                        if p['malariagenUID'] == malariagenUID:
                            p['class'].append(group_type)
                            if group_type == 'Contact':
                                p['contact'] = '1'
                else:
                    person['class'] = [group_type]
                    if group_type == 'Contact':
                        person['contact'] = '1'
                    else:
                        person['contact'] = '0'
                    study_people[malariagenUID] = person
                    alfStudyLdapPeople.append(person)

    return alfStudyLdapPeople


def writeRelatedRecords(records, foreign_key_value, fields, file, csv_list_separator, csv_row_separator, csv_value_separator):
  for record in records:
      record_values = []
      record_values.append(foreign_key_value)
      for record_field in fields:
          record_field_value = ''
          if record_field in record:
              if isinstance(record[record_field], str):
                  record_field_value = record[record_field]
              elif isinstance(record[record_field], (list, tuple)):
                  record_field_value = csv_list_separator.join(record[record_field])
          record_values.append(record_field_value)
      # Write the record_values to the CSV file.
      file.write((csv_value_separator.join(record_values).replace("\n", " ").replace("\r", " ") + csv_row_separator).encode('ascii', 'xmlcharrefreplace').decode())


def establishGSheetsCredentials(client_secret_path, credentials_path, auth_host_name, auth_host_port):
    store = Storage(credentials_path)
    credentials = None
    if os.path.isfile(credentials_path):
        credentials = store.get()
    if credentials is None or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret_path, 'https://www.googleapis.com/auth/spreadsheets.readonly')
        flow.user_agent = 'malobs'
        # http://oauth2client.readthedocs.io/en/latest/source/oauth2client.tools.html
        # https://docs.python.org/2/library/argparse.html
        # https://stackoverflow.com/questions/24890146/how-to-get-google-analytics-credentials-without-gflags-using-run-flow-instea
        print("Will now try to authenticate by starting a web server (and opening a web browser) using gsheetsAuthHost " + auth_host_name + " and gsheetsAuthPort: " + str(auth_host_port))
        # Note: If this fails, it will try to fall back to using --noauth_local_webserver, which this script is *not* designed to support.
        flags = tools.argparser.parse_args(args=['--noauth_local_webserver', '--logging_level', 'DEBUG', '--auth_host_name', auth_host_name, '--auth_host_port', str(auth_host_port)])
        # http://oauth2client.readthedocs.io/en/latest/_modules/oauth2client/tools.html
        # Note: The ports in this message are hard-coded so misleading: "Failed to start a local webserver listening on either port 8080 or port 8090. Please check your firewall settings and locally running programs that may be blocking or using those ports."
        credentials = tools.run_flow(flow, store, flags)
    return credentials


run()
