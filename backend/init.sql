-- ============================================================
-- 习惯打卡应用建表脚本（MySQL 8.0）
-- 执行方式：mysql -u root -p < init.sql
-- 字符集 utf8mb4 / 引擎 InnoDB；联合唯一索引是并发防重的物理保证
-- ============================================================
CREATE DATABASE IF NOT EXISTS `habit_checkin`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE `habit_checkin`;

-- 1. 用户表：password 存 bcrypt 哈希（60 字符），禁止明文
CREATE TABLE IF NOT EXISTS `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名（唯一）',
  `password` VARCHAR(100) NOT NULL COMMENT 'bcrypt 哈希',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 打卡项表
-- uk_user_item 联合唯一：同一用户下名称唯一；
-- 其最左前缀 user_id 同时充当查询索引，无需重复建单列索引
CREATE TABLE IF NOT EXISTS `check_item` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '打卡项ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '所属用户ID',
  `item_name` VARCHAR(50) NOT NULL COMMENT '打卡项名称',
  `current_streak` INT NOT NULL DEFAULT 0 COMMENT '当前连续天数（存储口径：截至最后一次打卡）',
  `max_streak` INT NOT NULL DEFAULT 0 COMMENT '历史最高连续天数',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_item` (`user_id`, `item_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打卡项表';

-- 3. 打卡记录表
-- uk_item_date 联合唯一：同一打卡项同一天只能有一条记录（并发兜底）
CREATE TABLE IF NOT EXISTS `check_record` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `item_id` BIGINT UNSIGNED NOT NULL COMMENT '打卡项ID',
  `check_date` DATE NOT NULL COMMENT '打卡日期（北京时间自然日）',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_item_date` (`item_id`, `check_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打卡记录表';

-- 演示账号：demo / 123456
-- 哈希由 bcrypt(cost=12) 生成，已实测 verify=True；禁止在脚本中拼接明文
INSERT INTO `user` (`username`, `password`)
SELECT 'demo', '$2b$12$udQd4txU2oNdBfE8X2pr0.rh290OVj5jY416lBkKMwD8ETftD5Upy'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'demo');
