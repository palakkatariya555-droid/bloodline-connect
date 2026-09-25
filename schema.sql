CREATE DATABASE IF NOT EXISTS dbms
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE dbms;

-- ---------------------------------------------------------------
-- ADMIN
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin (
  admin_id   VARCHAR(20)  NOT NULL PRIMARY KEY,
  name       VARCHAR(100) NOT NULL,
  username   VARCHAR(50)  NOT NULL UNIQUE,
  email      VARCHAR(100) NULL,
  password   VARCHAR(255) NOT NULL,
  phone_no   VARCHAR(10)  NOT NULL,
  manages    VARCHAR(50)  NOT NULL,
  handles    VARCHAR(50)  NOT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- DONOR  (admin -manages-> donor : 1:N)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS donor (
  donor_id            VARCHAR(20)  NOT NULL PRIMARY KEY,
  name                VARCHAR(100) NOT NULL,
  email               VARCHAR(100) NULL,
  age                 INT          NOT NULL,
  gender              VARCHAR(10)  NOT NULL,
  blood_group         VARCHAR(5)   NOT NULL,
  phone_no            VARCHAR(10)  NOT NULL,
  city                VARCHAR(50)  NOT NULL,
  last_donation_date  DATE         NULL,
  availability        VARCHAR(15)  NOT NULL,
  password            VARCHAR(255) NULL,
  admin_id            VARCHAR(20)  NOT NULL,
  CONSTRAINT fk_donor_admin
    FOREIGN KEY (admin_id) REFERENCES admin(admin_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- BLOOD_REQUEST  (admin -handles-> blood_request : 1:N)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS blood_request (
  request_id      VARCHAR(20)  NOT NULL PRIMARY KEY,
  patient_name    VARCHAR(100) NOT NULL,
  blood_group     VARCHAR(5)   NOT NULL,
  units_required  INT          NOT NULL,
  hospital_name   VARCHAR(100) NOT NULL,
  city            VARCHAR(50)  NOT NULL,
  contact_no      VARCHAR(10)  NOT NULL,
  request_date    DATE         NOT NULL,
  urgency         VARCHAR(15)  NOT NULL,
  status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
  admin_id        VARCHAR(20)  NOT NULL,
  CONSTRAINT fk_request_admin
    FOREIGN KEY (admin_id) REFERENCES admin(admin_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- DONATION
--   donor -makes-> donation          : 1:N
--   blood_request -fulfills-> donation : 1:N
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS donation (
  donation_id     VARCHAR(20)  NOT NULL PRIMARY KEY,
  blood_group     VARCHAR(5)   NOT NULL,
  donation_date   DATE         NOT NULL,
  units           INT          NOT NULL,
  location        VARCHAR(100) NOT NULL,
  notes           TEXT         NULL,
  donor_id        VARCHAR(20)  NOT NULL,
  request_id      VARCHAR(20)  NOT NULL,
  CONSTRAINT fk_donation_donor
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_donation_request
    FOREIGN KEY (request_id) REFERENCES blood_request(request_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;