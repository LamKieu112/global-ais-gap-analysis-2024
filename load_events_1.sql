-- Bước 0 (một lần, quyền admin): SET GLOBAL local_infile = 1;
-- Client phải bật local_infile, ví dụ: mysql --local-infile=1 -u USER -p
CREATE DATABASE IF NOT EXISTS ais DEFAULT CHARACTER SET utf8mb4;
USE ais;
DROP TABLE IF EXISTS gap_events;
CREATE TABLE gap_events (
  `start` DATETIME,
  `end` DATETIME,
  `id` VARCHAR(42),
  `type` VARCHAR(13),
  `boundingBox` VARCHAR(96),
  `position_lat` DOUBLE,
  `position_lon` DOUBLE,
  `regions_mpa` VARCHAR(72),
  `regions_eez` VARCHAR(27),
  `regions_rfmo` VARCHAR(80),
  `regions_fao` VARCHAR(60),
  `regions_majorFao` VARCHAR(16),
  `regions_eez12Nm` VARCHAR(19),
  `regions_highSeas` VARCHAR(23),
  `regions_mpaNoTakePartial` VARCHAR(26),
  `regions_mpaNoTake` VARCHAR(26),
  `regions_ebsa` VARCHAR(42),
  `regions_imma` VARCHAR(76),
  `regions_dukePaa` VARCHAR(17),
  `regions_protectedseas` TEXT,
  `regions_hsp` VARCHAR(20),
  `regions_fraGfcmFao` VARCHAR(181),
  `distances_startDistanceFromShoreKm` DOUBLE,
  `distances_endDistanceFromShoreKm` DOUBLE,
  `distances_startDistanceFromPortKm` DOUBLE,
  `distances_endDistanceFromPortKm` DOUBLE,
  `vessel_id` VARCHAR(47),
  `vessel_name` VARCHAR(30),
  `vessel_ssvid` VARCHAR(12),
  `vessel_flag` VARCHAR(13),
  `vessel_type` VARCHAR(27),
  `vessel_nextPort` VARCHAR(20),
  `gap_intentionalDisabling` VARCHAR(14),
  `gap_distanceKm` DOUBLE,
  `gap_durationHours` DOUBLE,
  `gap_impliedSpeedKnots` DOUBLE,
  `gap_positions12HoursBeforeSat` DOUBLE,
  `gap_positionsPerDaySatReception` DOUBLE,
  `gap_offPosition_lat` DOUBLE,
  `gap_offPosition_lon` DOUBLE,
  `gap_onPosition_lat` DOUBLE,
  `gap_onPosition_lon` DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Đổi đường dẫn bên dưới thành đường dẫn thật của file trên máy bạn
LOAD DATA LOCAL INFILE '/duong/dan/events_raw_1.csv'
INTO TABLE gap_events
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@v1, @v2, @v3, @v4, @v5, @v6, @v7, @v8, @v9, @v10, @v11, @v12, @v13, @v14, @v15, @v16, @v17, @v18, @v19, @v20, @v21, @v22, @v23, @v24, @v25, @v26, @v27, @v28, @v29, @v30, @v31, @v32, @v33, @v34, @v35, @v36, @v37, @v38, @v39, @v40, @v41, @v42)
SET
  `start` = STR_TO_DATE(LEFT(NULLIF(@v1,''),19), '%Y-%m-%dT%H:%i:%s'),
  `end` = STR_TO_DATE(LEFT(NULLIF(@v2,''),19), '%Y-%m-%dT%H:%i:%s'),
  `id` = NULLIF(@v3,''),
  `type` = NULLIF(@v4,''),
  `boundingBox` = NULLIF(@v5,''),
  `position_lat` = NULLIF(@v6,''),
  `position_lon` = NULLIF(@v7,''),
  `regions_mpa` = NULLIF(@v8,''),
  `regions_eez` = NULLIF(@v9,''),
  `regions_rfmo` = NULLIF(@v10,''),
  `regions_fao` = NULLIF(@v11,''),
  `regions_majorFao` = NULLIF(@v12,''),
  `regions_eez12Nm` = NULLIF(@v13,''),
  `regions_highSeas` = NULLIF(@v14,''),
  `regions_mpaNoTakePartial` = NULLIF(@v15,''),
  `regions_mpaNoTake` = NULLIF(@v16,''),
  `regions_ebsa` = NULLIF(@v17,''),
  `regions_imma` = NULLIF(@v18,''),
  `regions_dukePaa` = NULLIF(@v19,''),
  `regions_protectedseas` = NULLIF(@v20,''),
  `regions_hsp` = NULLIF(@v21,''),
  `regions_fraGfcmFao` = NULLIF(@v22,''),
  `distances_startDistanceFromShoreKm` = NULLIF(@v23,''),
  `distances_endDistanceFromShoreKm` = NULLIF(@v24,''),
  `distances_startDistanceFromPortKm` = NULLIF(@v25,''),
  `distances_endDistanceFromPortKm` = NULLIF(@v26,''),
  `vessel_id` = NULLIF(@v27,''),
  `vessel_name` = NULLIF(@v28,''),
  `vessel_ssvid` = NULLIF(@v29,''),
  `vessel_flag` = NULLIF(@v30,''),
  `vessel_type` = NULLIF(@v31,''),
  `vessel_nextPort` = NULLIF(@v32,''),
  `gap_intentionalDisabling` = NULLIF(@v33,''),
  `gap_distanceKm` = NULLIF(@v34,''),
  `gap_durationHours` = NULLIF(@v35,''),
  `gap_impliedSpeedKnots` = NULLIF(@v36,''),
  `gap_positions12HoursBeforeSat` = NULLIF(@v37,''),
  `gap_positionsPerDaySatReception` = NULLIF(@v38,''),
  `gap_offPosition_lat` = NULLIF(@v39,''),
  `gap_offPosition_lon` = NULLIF(@v40,''),
  `gap_onPosition_lat` = NULLIF(@v41,''),
  `gap_onPosition_lon` = NULLIF(@v42,'');

-- Kiểm tra: phải ra 46823
SELECT COUNT(*) FROM gap_events;

-- Lọc tập 2.021 dòng
SELECT COUNT(*) FROM gap_events
WHERE `start` >= '2024-01-01' AND `start` < '2024-02-01'
  AND vessel_type <> 'gear'
  AND vessel_ssvid REGEXP '^[0-9]{9}$'
  AND vessel_ssvid NOT LIKE '99%'
  AND gap_impliedSpeedKnots <= 30
  AND gap_durationHours <= 720;
