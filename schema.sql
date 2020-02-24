CREATE TABLE "pf_drug_regions" (
  "drug_id" Text,
  "drug_region_id" Text PRIMARY KEY,
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
  "lat" Float,
  "lng" Float,
  "name" Text,
  "num_samples" Int,
  "pf_region_id" Text,
  "site_id" Text PRIMARY KEY
);

CREATE TABLE "countries" (
  "ARTresistance" Float,
  "CQresistance" Float,
  "MQresistance" Float,
  "PPQresistance" Float,
  "PYRresistance" Float,
  "SDXresistance" Float,
  "alpha_3_code" Text,
  "country_id" Text PRIMARY KEY,
  "geojson" Text,
  "lat" Float,
  "lng" Float,
  "name" Text,
  "num_samples" Int
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
  "geojson" Text,
  "lat" Float,
  "lng" Float,
  "name" Text,
  "num_samples" Int,
  "region_id" Text PRIMARY KEY,
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
  "uid" Text,
  PRIMARY KEY("uid", "study")
);

CREATE TABLE "pf_drugs" (
  "description" Text,
  "drug_id" Text PRIMARY KEY,
  "is_combination" Boolean,
  "name" Text,
  "short_description" Text
);

CREATE TABLE "studies" (
  "description" Text,
  "study" Text PRIMARY KEY,
  "study_number" Text,
  "webTitle" Text
);

CREATE TABLE "pf_featuretypes" (
  "description" Text,
  "feature" Text,
  "feature_id" Text,
  "type_id" Text,
  PRIMARY KEY(feature_id, type_id)
);

CREATE TABLE "pf_features" (
  "category" Text,
  "description" Text,
  "feature_id" Text PRIMARY KEY,
  "name" Text
);

CREATE TABLE "study_publications" (
  "citation" Text,
  "doi" Text,
  "name" Text,
  "pmid" Text,
  "study" Text,
  "title" Text,
  PRIMARY KEY("doi", "study")
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
  "country_lat" Float,
  "country_lng" Float,
  "mean_coverage" Float,
  "pc_genome_callable" Float,
  "qc_pass" Boolean,
  "region" Text,
  "region_id" Text,
  "region_lat" Float,
  "region_lng" Float,
  "run_accessions" Text,
  "sample_id" Text PRIMARY KEY,
  "site" Text,
  "site_id" Text,
  "site_lat" Float,
  "site_lng" Float,
  "study_id" Text,
  "year" Int,
  "crt_76[K]" Text,
  "crt_72-76[CVMNK]" Text,
  "dhfr_51[N]" Text,
  "dhfr_59[C]" Text,
  "dhfr_108[S]" Text,
  "dhfr_164[I]" Text,
  "dhps_437[G]" Text,
  "dhps_540[K]" Text,
  "dhps_581[A]" Text,
  "dhps_613[A]" Text,
  "k13_class" Text,
  "k13_alleles" Text,
  "cn_mdr1" Text,
  "cn_pm2" Text,
  "cn_gch1" Text,
  "breakpoint_mdr1" Text,
  "breakpoint_pm2" Text,
  "breakpoint_gch1" Text,
  "Fws" Float
);

CREATE TABLE "gene_diff" (
  "gene_id" Text PRIMARY KEY,
  "gene_name" Text, 
  "chrom" Text,
  "start" Int,
  "end" Int,
  "global_differentiation_score" Float,
  "local_differentiation_score" Float,
  "distance_to_higher_local_diff_score" Float
);

CREATE TABLE "pf_drug_gene" (
  "gene_id" Text,
  "drug_id" Text,
  PRIMARY KEY ("gene_id", "drug_id")
);

CREATE TABLE "pf_resgenes" (
  "gene_id" Text PRIMARY KEY, 
  "name" Text,
  "long_name" Text,
  "short_description" Text,
  "description" Text,
  "marker_name" Text
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
ALTER TABLE "pf_drug_gene" ADD FOREIGN KEY ("drug_id") REFERENCES "pf_drugs" ("drug_id");
ALTER TABLE "pf_drug_gene" ADD FOREIGN KEY ("gene_id") REFERENCES "pf_resgenes" ("gene_id");
ALTER TABLE "pf_resgenes" ADD FOREIGN KEY ("gene_id") REFERENCES "gene_diff" ("gene_id");


\COPY countries ("country_id", "lat", "lng", "name", "alpha_3_code", "geojson", "num_samples", "CQresistance", "PYRresistance", "SDXresistance", "MQresistance", "ARTresistance", "PPQresistance") FROM 'output/countries/data' DELIMITER E'\t' CSV HEADER;
\COPY gene_diff ("gene_id", "gene_name", "chrom", "start", "end", "global_differentiation_score", "local_differentiation_score", "distance_to_higher_local_diff_score") FROM 'output/gene_diff/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_drugs ("drug_id", "is_combination", "name", "short_description", "description") FROM 'output/pf_drugs/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_features ("feature_id", "name", "category", "description") FROM 'output/pf_features/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_featuretypes ("feature_id", "type_id", "description", "feature") FROM 'output/pf_featuretypes/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_regions ("region_id", "lat", "lng", "name", "description", "num_samples", "web_colour", "CQresistance", "PYRresistance", "SDXresistance", "MQresistance", "ARTresistance", "PPQresistance", "SPIPTpresistance", "ASMQresistance", "DHAPPQresistance", "HRP2deletion", "HRP3deletion", "HRP23deletion", "SPresistance", "geojson") FROM 'output/pf_regions/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_resgenes ("gene_id", "name", "long_name", "short_description", "description", "marker_name") FROM 'output/pf_resgenes/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_sites ("site_id", "lat", "lng", "name", "num_samples", "pf_region_id", "country_id", "CQresistance", "PYRresistance", "SDXresistance", "MQresistance", "ARTresistance", "PPQresistance", "SPIPTpresistance", "ASMQresistance", "DHAPPQresistance", "HRP2deletion", "HRP3deletion", "HRP23deletion", "SPresistance", "AnyHRPdeletion") FROM 'output/pf_sites/data' DELIMITER E'\t' CSV HEADER;
\COPY studies ("study", "study_number", "webTitle", "description") FROM 'output/studies/data' DELIMITER E'\t' CSV HEADER;
\COPY study_ldap_people ("study", "jobTitle1", "jobTitle2", "jobTitle3", "uid", "researchGateURL", "scholarURL", "twitterURL", "malariagenUID", "oProfile1", "oProfile2", "oProfile3", "ORCID", "sn", "mail", "givenName", "o1", "o2", "o3") FROM 'output/study_ldap_people/data' DELIMITER E'\t' CSV HEADER;
\COPY study_publications ("study", "doi", "name", "title", "citation", "pmid") FROM 'output/study_publications/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_drug_gene ("gene_id", "drug_id") FROM 'output/pf_drug_gene/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_drug_regions ("region_id", "drug_region_id", "text", "resistance", "drug_id") FROM 'output/pf_drug_regions/data' DELIMITER E'\t' CSV HEADER;
\COPY pf_samples ("sample_id", "PYRresistant", "MQresistant", "country_lat", "country_lng", "region_lng", "HRP23deletion", "ARTresistant", "site_id", "site_lng", "year", "country", "CQresistant", "pc_genome_callable", "ASMQresistant", "HRP2deletion", "qc_pass", "site_lat", "region_lat", "DHAPPQresistant", "SPresistant", "SPIPTpresistant", "mean_coverage", "HRP3deletion", "site", "PPQresistant", "region_id", "SDXresistant", "run_accessions", "region", "study_id", "country_id", "crt_76[K]", "crt_72-76[CVMNK]", "dhfr_51[N]", "dhfr_59[C]", "dhfr_108[S]", "dhfr_164[I]", "dhps_437[G]", "dhps_540[K]", "dhps_581[A]", "dhps_613[A]", "k13_class", "k13_alleles", "cn_mdr1", "cn_pm2", "cn_gch1", "breakpoint_mdr1", "breakpoint_pm2", "breakpoint_gch1", "Fws") FROM 'output/pf_samples/data' DELIMITER E'\t' CSV HEADER;

