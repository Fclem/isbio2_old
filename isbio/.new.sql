__breeze__started__
[94mMYSQL DB		 [0m[[92mOK[0m]
BEGIN;
CREATE TABLE `breeze_post` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `author_id` integer NOT NULL,
    `title` varchar(150) NOT NULL,
    `body` longtext NOT NULL,
    `time` datetime NOT NULL
)
;
ALTER TABLE `breeze_post` ADD CONSTRAINT `author_id_refs_id_11045a41` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_institute` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `institute` varchar(75) NOT NULL
)
;
CREATE TABLE `breeze_project` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(50) NOT NULL UNIQUE,
    `manager` varchar(50) NOT NULL,
    `pi` varchar(50) NOT NULL,
    `author_id` integer NOT NULL,
    `institute_id` integer NOT NULL,
    `collaborative` bool NOT NULL,
    `wbs` varchar(50) NOT NULL,
    `external_id` varchar(50) NOT NULL,
    `description` varchar(1100) NOT NULL
)
;
ALTER TABLE `breeze_project` ADD CONSTRAINT `author_id_refs_id_31e3bfcd` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_project` ADD CONSTRAINT `institute_id_refs_id_f37ac5a5` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
CREATE TABLE `breeze_group_team` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `group_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`group_id`, `user_id`)
)
;
ALTER TABLE `breeze_group_team` ADD CONSTRAINT `user_id_refs_id_9b8510be` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_group` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(50) NOT NULL UNIQUE,
    `author_id` integer NOT NULL
)
;
ALTER TABLE `breeze_group` ADD CONSTRAINT `author_id_refs_id_17519c57` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_group_team` ADD CONSTRAINT `group_id_refs_id_f8d2f0e6` FOREIGN KEY (`group_id`) REFERENCES `breeze_group` (`id`);
CREATE TABLE `breeze_shinyreport` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(55) NOT NULL UNIQUE,
    `description` varchar(350) NOT NULL,
    `author_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `institute_id` integer NOT NULL,
    `custom_header` longtext NOT NULL,
    `custom_loader` longtext NOT NULL,
    `custom_files` longtext NOT NULL,
    `enabled` bool NOT NULL
)
;
ALTER TABLE `breeze_shinyreport` ADD CONSTRAINT `author_id_refs_id_dd40ef9f` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_shinyreport` ADD CONSTRAINT `institute_id_refs_id_26616b47` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
CREATE TABLE `breeze_execconfig` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(32) NOT NULL,
    `label` varchar(64) NOT NULL,
    `institute_id` integer NOT NULL,
    `config` varchar(100) NOT NULL,
    `enabled` bool NOT NULL
)
;
ALTER TABLE `breeze_execconfig` ADD CONSTRAINT `institute_id_refs_id_119307e8` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
CREATE TABLE `breeze_engineconfig` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(32) NOT NULL,
    `label` varchar(64) NOT NULL,
    `institute_id` integer NOT NULL,
    `config` varchar(100) NOT NULL,
    `enabled` bool NOT NULL
)
;
ALTER TABLE `breeze_engineconfig` ADD CONSTRAINT `institute_id_refs_id_e855b9a9` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
CREATE TABLE `breeze_computetarget` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(32) NOT NULL,
    `label` varchar(64) NOT NULL,
    `institute_id` integer NOT NULL,
    `config` varchar(100) NOT NULL,
    `enabled` bool NOT NULL
)
;
ALTER TABLE `breeze_computetarget` ADD CONSTRAINT `institute_id_refs_id_d18a48d0` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
CREATE TABLE `breeze_reporttype_targets` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `reporttype_id` integer NOT NULL,
    `computetarget_id` integer NOT NULL,
    UNIQUE (`reporttype_id`, `computetarget_id`)
)
;
ALTER TABLE `breeze_reporttype_targets` ADD CONSTRAINT `computetarget_id_refs_id_2754d9db` FOREIGN KEY (`computetarget_id`) REFERENCES `breeze_computetarget` (`id`);
CREATE TABLE `breeze_reporttype_access` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `reporttype_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`reporttype_id`, `user_id`)
)
;
ALTER TABLE `breeze_reporttype_access` ADD CONSTRAINT `user_id_refs_id_ede380bf` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_reporttype` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `type` varchar(17) NOT NULL UNIQUE,
    `description` varchar(5500) NOT NULL,
    `search` bool NOT NULL,
    `author_id` integer NOT NULL,
    `institute_id` integer NOT NULL,
    `config` varchar(100),
    `manual` varchar(100),
    `created` date NOT NULL,
    `shiny_report_id` integer
)
;
ALTER TABLE `breeze_reporttype` ADD CONSTRAINT `shiny_report_id_refs_id_c1e99b8b` FOREIGN KEY (`shiny_report_id`) REFERENCES `breeze_shinyreport` (`id`);
ALTER TABLE `breeze_reporttype` ADD CONSTRAINT `author_id_refs_id_78414c19` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_reporttype` ADD CONSTRAINT `institute_id_refs_id_246a641` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
ALTER TABLE `breeze_reporttype_targets` ADD CONSTRAINT `reporttype_id_refs_id_bb178b4e` FOREIGN KEY (`reporttype_id`) REFERENCES `breeze_reporttype` (`id`);
ALTER TABLE `breeze_reporttype_access` ADD CONSTRAINT `reporttype_id_refs_id_ab719b15` FOREIGN KEY (`reporttype_id`) REFERENCES `breeze_reporttype` (`id`);
CREATE TABLE `breeze_script_categories` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `category` varchar(55) NOT NULL UNIQUE,
    `description` varchar(350) NOT NULL
)
;
CREATE TABLE `breeze_user_date` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `install_date` date NOT NULL
)
;
ALTER TABLE `breeze_user_date` ADD CONSTRAINT `user_id_refs_id_83fdc5e8` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_rscripts_report_type` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `rscripts_id` integer NOT NULL,
    `reporttype_id` integer NOT NULL,
    UNIQUE (`rscripts_id`, `reporttype_id`)
)
;
ALTER TABLE `breeze_rscripts_report_type` ADD CONSTRAINT `reporttype_id_refs_id_5bb028d5` FOREIGN KEY (`reporttype_id`) REFERENCES `breeze_reporttype` (`id`);
CREATE TABLE `breeze_rscripts_access` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `rscripts_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`rscripts_id`, `user_id`)
)
;
ALTER TABLE `breeze_rscripts_access` ADD CONSTRAINT `user_id_refs_id_eb89d2db` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_rscripts_install_date` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `rscripts_id` integer NOT NULL,
    `user_date_id` integer NOT NULL,
    UNIQUE (`rscripts_id`, `user_date_id`)
)
;
ALTER TABLE `breeze_rscripts_install_date` ADD CONSTRAINT `user_date_id_refs_id_b2975aa` FOREIGN KEY (`user_date_id`) REFERENCES `breeze_user_date` (`id`);
CREATE TABLE `breeze_rscripts` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(35) NOT NULL UNIQUE,
    `inln` varchar(150) NOT NULL,
    `details` varchar(5500) NOT NULL,
    `category_id` varchar(55) NOT NULL,
    `author_id` integer NOT NULL,
    `creation_date` date NOT NULL,
    `draft` bool NOT NULL,
    `price` numeric(19, 2) NOT NULL,
    `istag` bool NOT NULL,
    `must` bool NOT NULL,
    `order` numeric(3, 1) NOT NULL,
    `docxml` varchar(100) NOT NULL,
    `code` varchar(100) NOT NULL,
    `header` varchar(100) NOT NULL,
    `logo` varchar(100) NOT NULL
)
;
ALTER TABLE `breeze_rscripts` ADD CONSTRAINT `category_id_refs_category_91c63922` FOREIGN KEY (`category_id`) REFERENCES `breeze_script_categories` (`category`);
ALTER TABLE `breeze_rscripts` ADD CONSTRAINT `author_id_refs_id_6020a003` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_rscripts_report_type` ADD CONSTRAINT `rscripts_id_refs_id_f1ef62d9` FOREIGN KEY (`rscripts_id`) REFERENCES `breeze_rscripts` (`id`);
ALTER TABLE `breeze_rscripts_access` ADD CONSTRAINT `rscripts_id_refs_id_ec9e7575` FOREIGN KEY (`rscripts_id`) REFERENCES `breeze_rscripts` (`id`);
ALTER TABLE `breeze_rscripts_install_date` ADD CONSTRAINT `rscripts_id_refs_id_cf07916b` FOREIGN KEY (`rscripts_id`) REFERENCES `breeze_rscripts` (`id`);
CREATE TABLE `breeze_cartinfo` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `script_buyer_id` integer NOT NULL,
    `product_id` integer NOT NULL,
    `type_app` bool NOT NULL,
    `date_created` date NOT NULL,
    `date_updated` date NOT NULL,
    `active` bool NOT NULL
)
;
ALTER TABLE `breeze_cartinfo` ADD CONSTRAINT `script_buyer_id_refs_id_3c84a81f` FOREIGN KEY (`script_buyer_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_cartinfo` ADD CONSTRAINT `product_id_refs_id_97da468f` FOREIGN KEY (`product_id`) REFERENCES `breeze_rscripts` (`id`);
CREATE TABLE `breeze_dataset` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(55) NOT NULL UNIQUE,
    `description` varchar(350) NOT NULL,
    `author_id` integer NOT NULL,
    `rdata` varchar(100) NOT NULL
)
;
ALTER TABLE `breeze_dataset` ADD CONSTRAINT `author_id_refs_id_ca036592` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_inputtemplate` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(55) NOT NULL UNIQUE,
    `description` varchar(350) NOT NULL,
    `author_id` integer NOT NULL,
    `file` varchar(100) NOT NULL
)
;
ALTER TABLE `breeze_inputtemplate` ADD CONSTRAINT `author_id_refs_id_85938d36` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_userprofile` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL UNIQUE,
    `fimm_group` varchar(75) NOT NULL,
    `logo` varchar(100) NOT NULL,
    `institute_info_id` integer NOT NULL,
    `db_agreement` bool NOT NULL,
    `last_active` datetime NOT NULL
)
;
ALTER TABLE `breeze_userprofile` ADD CONSTRAINT `institute_info_id_refs_id_8720b8fa` FOREIGN KEY (`institute_info_id`) REFERENCES `breeze_institute` (`id`);
CREATE TABLE `breeze_jobs` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `breeze_stat` varchar(16) NOT NULL,
    `status` varchar(15) NOT NULL,
    `progress` smallint UNSIGNED NOT NULL,
    `sgeid` varchar(15) NOT NULL,
    `jname` varchar(55) NOT NULL,
    `jdetails` varchar(4900) NOT NULL,
    `juser_id` integer NOT NULL,
    `script_id` integer NOT NULL,
    `staged` datetime NOT NULL,
    `rexecut` varchar(100) NOT NULL,
    `docxml` varchar(100) NOT NULL,
    `mailing` varchar(3) NOT NULL,
    `email` varchar(75) NOT NULL
)
;
ALTER TABLE `breeze_jobs` ADD CONSTRAINT `juser_id_refs_id_dde2df5b` FOREIGN KEY (`juser_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_jobs` ADD CONSTRAINT `script_id_refs_id_e04a4f35` FOREIGN KEY (`script_id`) REFERENCES `breeze_rscripts` (`id`);
CREATE TABLE `breeze_report_shared` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `report_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`report_id`, `user_id`)
)
;
ALTER TABLE `breeze_report_shared` ADD CONSTRAINT `user_id_refs_id_cdcc97fe` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_report` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `breeze_stat` varchar(16) NOT NULL,
    `status` varchar(15) NOT NULL,
    `progress` smallint UNSIGNED NOT NULL,
    `sgeid` varchar(15) NOT NULL,
    `name` varchar(55) NOT NULL,
    `description` varchar(350) NOT NULL,
    `author_id` integer NOT NULL,
    `type_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `institute_id` integer NOT NULL,
    `rexec` varchar(100) NOT NULL,
    `dochtml` varchar(100) NOT NULL,
    `project_id` integer,
    `conf_params` longtext,
    `conf_files` longtext,
    `fm_flag` bool NOT NULL,
    `target_id` integer NOT NULL,
    `shiny_key` varchar(64),
    `rora_id` integer UNSIGNED NOT NULL
)
;
ALTER TABLE `breeze_report` ADD CONSTRAINT `target_id_refs_id_ee2c2728` FOREIGN KEY (`target_id`) REFERENCES `breeze_computetarget` (`id`);
ALTER TABLE `breeze_report` ADD CONSTRAINT `type_id_refs_id_7a90ceef` FOREIGN KEY (`type_id`) REFERENCES `breeze_reporttype` (`id`);
ALTER TABLE `breeze_report` ADD CONSTRAINT `author_id_refs_id_28cb3493` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_report` ADD CONSTRAINT `project_id_refs_id_e871ccad` FOREIGN KEY (`project_id`) REFERENCES `breeze_project` (`id`);
ALTER TABLE `breeze_report` ADD CONSTRAINT `institute_id_refs_id_c39c9995` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
ALTER TABLE `breeze_report_shared` ADD CONSTRAINT `report_id_refs_id_1e60dfd0` FOREIGN KEY (`report_id`) REFERENCES `breeze_report` (`id`);
CREATE TABLE `breeze_shinytag_attached_report` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `shinytag_id` integer NOT NULL,
    `shinyreport_id` integer NOT NULL,
    UNIQUE (`shinytag_id`, `shinyreport_id`)
)
;
ALTER TABLE `breeze_shinytag_attached_report` ADD CONSTRAINT `shinyreport_id_refs_id_8edb5528` FOREIGN KEY (`shinyreport_id`) REFERENCES `breeze_shinyreport` (`id`);
CREATE TABLE `breeze_shinytag` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(55) NOT NULL UNIQUE,
    `description` varchar(350) NOT NULL,
    `author_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `institute_id` integer NOT NULL,
    `order` integer UNSIGNED NOT NULL,
    `menu_entry` longtext NOT NULL,
    `zip_file` varchar(100) NOT NULL,
    `enabled` bool NOT NULL
)
;
ALTER TABLE `breeze_shinytag` ADD CONSTRAINT `institute_id_refs_id_db2eb8bc` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);
ALTER TABLE `breeze_shinytag_attached_report` ADD CONSTRAINT `shinytag_id_refs_id_56dde903` FOREIGN KEY (`shinytag_id`) REFERENCES `breeze_shinytag` (`id`);
CREATE TABLE `breeze_offsiteuser_shiny_access` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `offsiteuser_id` integer NOT NULL,
    `report_id` integer NOT NULL,
    UNIQUE (`offsiteuser_id`, `report_id`)
)
;
ALTER TABLE `breeze_offsiteuser_shiny_access` ADD CONSTRAINT `report_id_refs_id_8d5df4cb` FOREIGN KEY (`report_id`) REFERENCES `breeze_report` (`id`);
CREATE TABLE `breeze_offsiteuser_belongs_to` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `offsiteuser_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`offsiteuser_id`, `user_id`)
)
;
ALTER TABLE `breeze_offsiteuser_belongs_to` ADD CONSTRAINT `user_id_refs_id_7bf47d69` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `breeze_offsiteuser` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `first_name` varchar(32) NOT NULL,
    `last_name` varchar(32) NOT NULL,
    `email` varchar(64) NOT NULL UNIQUE,
    `institute` varchar(32) NOT NULL,
    `role` varchar(32) NOT NULL,
    `user_key` varchar(32) NOT NULL UNIQUE,
    `added_by_id` integer NOT NULL,
    `created` datetime NOT NULL
)
;
ALTER TABLE `breeze_offsiteuser` ADD CONSTRAINT `added_by_id_refs_id_e7974e53` FOREIGN KEY (`added_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `breeze_offsiteuser_shiny_access` ADD CONSTRAINT `offsiteuser_id_refs_id_b72e45dd` FOREIGN KEY (`offsiteuser_id`) REFERENCES `breeze_offsiteuser` (`id`);
ALTER TABLE `breeze_offsiteuser_belongs_to` ADD CONSTRAINT `offsiteuser_id_refs_id_5b6f38c9` FOREIGN KEY (`offsiteuser_id`) REFERENCES `breeze_offsiteuser` (`id`);
CREATE INDEX `breeze_post_cc846901` ON `breeze_post` (`author_id`);
CREATE INDEX `breeze_project_cc846901` ON `breeze_project` (`author_id`);
CREATE INDEX `breeze_project_da5f2290` ON `breeze_project` (`institute_id`);
CREATE INDEX `breeze_group_cc846901` ON `breeze_group` (`author_id`);
CREATE INDEX `breeze_shinyreport_cc846901` ON `breeze_shinyreport` (`author_id`);
CREATE INDEX `breeze_shinyreport_da5f2290` ON `breeze_shinyreport` (`institute_id`);
CREATE INDEX `breeze_execconfig_da5f2290` ON `breeze_execconfig` (`institute_id`);
CREATE INDEX `breeze_engineconfig_da5f2290` ON `breeze_engineconfig` (`institute_id`);
CREATE INDEX `breeze_computetarget_da5f2290` ON `breeze_computetarget` (`institute_id`);
CREATE INDEX `breeze_reporttype_cc846901` ON `breeze_reporttype` (`author_id`);
CREATE INDEX `breeze_reporttype_da5f2290` ON `breeze_reporttype` (`institute_id`);
CREATE INDEX `breeze_reporttype_e3412952` ON `breeze_reporttype` (`shiny_report_id`);
CREATE INDEX `breeze_user_date_fbfc09f1` ON `breeze_user_date` (`user_id`);
CREATE INDEX `breeze_rscripts_42dc49bc` ON `breeze_rscripts` (`category_id`);
CREATE INDEX `breeze_rscripts_cc846901` ON `breeze_rscripts` (`author_id`);
CREATE INDEX `breeze_cartinfo_f299c687` ON `breeze_cartinfo` (`script_buyer_id`);
CREATE INDEX `breeze_cartinfo_bb420c12` ON `breeze_cartinfo` (`product_id`);
CREATE INDEX `breeze_dataset_cc846901` ON `breeze_dataset` (`author_id`);
CREATE INDEX `breeze_inputtemplate_cc846901` ON `breeze_inputtemplate` (`author_id`);
CREATE INDEX `breeze_userprofile_30b79ea6` ON `breeze_userprofile` (`institute_info_id`);
CREATE INDEX `breeze_jobs_7d914542` ON `breeze_jobs` (`juser_id`);
CREATE INDEX `breeze_jobs_c0ece17f` ON `breeze_jobs` (`script_id`);
CREATE INDEX `breeze_report_cc846901` ON `breeze_report` (`author_id`);
CREATE INDEX `breeze_report_777d41c8` ON `breeze_report` (`type_id`);
CREATE INDEX `breeze_report_da5f2290` ON `breeze_report` (`institute_id`);
CREATE INDEX `breeze_report_b6620684` ON `breeze_report` (`project_id`);
CREATE INDEX `breeze_report_9358c897` ON `breeze_report` (`target_id`);
CREATE INDEX `breeze_shinytag_cc846901` ON `breeze_shinytag` (`author_id`);
CREATE INDEX `breeze_shinytag_da5f2290` ON `breeze_shinytag` (`institute_id`);
CREATE INDEX `breeze_offsiteuser_8d09cb1e` ON `breeze_offsiteuser` (`added_by_id`);
COMMIT;