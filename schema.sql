CREATE TABLE "pf_drug_regions" (
  "drug_id" Text,
  "drug_region_id" Text,
  "region_id" Text,
  "resistance" Float,
  "text" Text
);

CREATE TABLE "pf_sites" (
  "ARTresistance" Float,
  "ASMQresistance" Float,
  "AnyHRPdeletion" Float,
  "CQresistance" Float,
  "DHAPPQresistance" Float,
  "HRP23deletion" Float,
  "HRP2deletion" Float,
  "HRP3deletion" Float,
  "MQresistance" Float,
  "PPQresistance" Float,
  "PYRresistance" Float,
  "SDXresistance" Float,
  "SPIPTpresistance" Float,
  "SPresistance" Float,
  "country_id" Text,
  "lat" GeoLatitude,
  "lng" GeoLongitude,
  "name" Text,
  "num_samples" Double,
  "pf_region_id" Text,
  "site_id" Text
);

CREATE TABLE "countries" (
  "ARTresistance" Float,
  "CQresistance" Float,
  "MQresistance" Float,
  "PPQresistance" Float,
  "PYRresistance" Float,
  "SDXresistance" Float,
  "alpha_3_code" Text,
  "country_id" Text,
  "geojson" Text,
  "lat" Double,
  "lng" Double,
  "name" Text,
  "num_samples" Double
);

CREATE TABLE "pf_regions" (
  "ARTresistance" Float,
  "ASMQresistance" Float,
  "CQresistance" Float,
  "DHAPPQresistance" Float,
  "HRP23deletion" Float,
  "HRP2deletion" Float,
  "HRP3deletion" Float,
  "MQresistance" Float,
  "PPQresistance" Float,
  "PYRresistance" Float,
  "SDXresistance" Float,
  "SPIPTpresistance" Float,
  "SPresistance" Float,
  "description" Text,
  "geojson" GeoJSON,
  "lat" Double,
  "lng" Double,
  "name" Text,
  "num_samples" Double,
  "region_id" Text,
  "web_colour" Text
);

CREATE TABLE "study_ldap_people" (
  "ORCID" Text,
  "givenName" Text,
  "jobTitle1" Text,
  "jobTitle2" Text,
  "jobTitle3" Text,
  "mail" Text,
  "malariagenUID" Text,
  "o1" Text,
  "o2" Text,
  "o3" Text,
  "oProfile1" Text,
  "oProfile2" Text,
  "oProfile3" Text,
  "researchGateURL" Text,
  "scholarURL" Text,
  "sn" Text,
  "study" Text,
  "twitterURL" Text,
  "uid" Text
);

CREATE TABLE "pf_drugs" (
  "description" Text,
  "drug_id" Text,
  "is_combination" Boolean,
  "name" Text,
  "short_description" Text
);

CREATE TABLE "studies" (
  "description" Text,
  "study" Text,
  "study_number" Text,
  "webTitle" Text
);

CREATE TABLE "pf_featuretypes" (
  "description" Text,
  "feature" Text,
  "feature_id" Text,
  "type_id" Text
);

CREATE TABLE "pf_features" (
  "category" Text,
  "description" Text,
  "feature_id" Text,
  "name" Text
);

CREATE TABLE "study_publications" (
  "citation" Text,
  "doi" Text,
  "name" Text,
  "pmid" Text,
  "study" Text,
  "title" Text
);

CREATE TABLE "pf_samples" (
  "ARTresistant" Text,
  "ASMQresistant" Text,
  "CQresistant" Text,
  "DHAPPQresistant" Text,
  "HRP23deletion" Text,
  "HRP2deletion" Text,
  "HRP3deletion" Text,
  "MQresistant" Text,
  "PPQresistant" Text,
  "PYRresistant" Text,
  "SDXresistant" Text,
  "SPIPTpresistant" Text,
  "SPresistant" Text,
  "country" Text,
  "country_id" Text,
  "country_lat" Double,
  "country_lng" Double,
  "mean_coverage" Double,
  "pc_genome_callable" Double,
  "qc_pass" Boolean,
  "region" Text,
  "region_id" Text,
  "region_lat" Double,
  "region_lng" Double,
  "run_accessions" Text,
  "sample_id" Text,
  "site" Text,
  "site_id" Text,
  "site_lat" GeoLatitude,
  "site_lng" GeoLongitude,
  "study_id" Text,
  "year" Int16,
  "province_id" Text
);

CREATE TABLE "provinces" (
  "geojson" Text,
  "latitude" GeoLatitude,
  "local_name" Text,
  "longitude" GeoLongitude,
  "name" Text,
  "province_id" Text
);

ALTER TABLE "pf_drug_regions" ADD FOREIGN KEY ("drug_id") REFERENCES "pf_drugs" ("drug_id");

ALTER TABLE "pf_drug_regions" ADD FOREIGN KEY ("region_id") REFERENCES "pf_regions" ("region_id");

ALTER TABLE "pf_sites" ADD FOREIGN KEY ("country_id") REFERENCES "countries" ("country_id");

ALTER TABLE "pf_sites" ADD FOREIGN KEY ("pf_region_id") REFERENCES "pf_regions" ("region_id");

ALTER TABLE "study_ldap_people" ADD FOREIGN KEY ("study") REFERENCES "studies" ("study");

ALTER TABLE "pf_featuretypes" ADD FOREIGN KEY ("feature_id") REFERENCES "pf_features" ("feature_id");

ALTER TABLE "study_publications" ADD FOREIGN KEY ("study") REFERENCES "studies" ("study");

ALTER TABLE "pf_samples" ADD FOREIGN KEY ("country_id") REFERENCES "countries" ("country_id");

ALTER TABLE "pf_samples" ADD FOREIGN KEY ("region_id") REFERENCES "pf_regions" ("region_id");

ALTER TABLE "pf_samples" ADD FOREIGN KEY ("site_id") REFERENCES "pf_sites" ("site_id");

ALTER TABLE "pf_samples" ADD FOREIGN KEY ("study_id") REFERENCES "studies" ("study");

ALTER TABLE "pf_samples" ADD FOREIGN KEY ("province_id") REFERENCES "provinces" ("province_id");
