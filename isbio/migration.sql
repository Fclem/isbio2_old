CREATE TABLE `breeze_computetarget` (
  `id`           INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
  `name`         VARCHAR(32)            NOT NULL,
  `label`        VARCHAR(64)            NOT NULL,
  `institute_id` INTEGER                NOT NULL,
  `config`       VARCHAR(100)           NOT NULL,
  `enabled`      BOOL                   NOT NULL
);
ALTER TABLE `breeze_computetarget` ADD CONSTRAINT `institute_id_refs_id_d18a48d0` FOREIGN KEY (`institute_id`) REFERENCES `breeze_institute` (`id`);

CREATE TABLE `breeze_reporttype_targets` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `reporttype_id` integer NOT NULL,
    `computetarget_id` integer NOT NULL,
    UNIQUE (`reporttype_id`, `computetarget_id`)
)
;
ALTER TABLE `breeze_reporttype_targets` ADD CONSTRAINT `computetarget_id_refs_id_2754d9db` FOREIGN KEY (`computetarget_id`) REFERENCES `breeze_computetarget` (`id`);

ALTER TABLE `breeze_reporttype_targets` ADD CONSTRAINT `reporttype_id_refs_id_bb178b4e` FOREIGN KEY (`reporttype_id`) REFERENCES `breeze_reporttype` (`id`);

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
