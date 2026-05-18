-- =============================================================================
-- 企业资产漏洞台账库初始化脚本
-- 场景：开放环境企业资产漏洞合规与威胁研判
-- 使用前请根据 .env 中的 MYSQL_DATABASE 创建数据库并执行本脚本
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. 企业资产表
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `asset_vulnerabilities`;
DROP TABLE IF EXISTS `company_assets`;

CREATE TABLE `company_assets` (
    `asset_id`          VARCHAR(32)  NOT NULL COMMENT '资产唯一标识',
    `server_name`       VARCHAR(128) NOT NULL COMMENT '服务器/主机名称',
    `ip_address`        VARCHAR(45)  NOT NULL COMMENT '内网或公网 IP',
    `department`        VARCHAR(64)  NOT NULL COMMENT '所属业务部门',
    `is_internet_exposed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否互联网暴露面 0否 1是',
    PRIMARY KEY (`asset_id`),
    KEY `idx_ip` (`ip_address`),
    KEY `idx_exposed` (`is_internet_exposed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业资产台账';

-- -----------------------------------------------------------------------------
-- 2. 资产漏洞表
-- -----------------------------------------------------------------------------
CREATE TABLE `asset_vulnerabilities` (
    `vuln_id`       VARCHAR(32)  NOT NULL COMMENT '漏洞记录 ID',
    `asset_id`      VARCHAR(32)  NOT NULL COMMENT '关联资产 ID',
    `cve_id`        VARCHAR(32)  NOT NULL COMMENT 'CVE 编号',
    `vuln_name`     VARCHAR(256) NOT NULL COMMENT '漏洞名称',
    `severity`      ENUM('低危','中危','高危','严重') NOT NULL COMMENT '危害等级',
    `repair_status` ENUM('未修复','修复中','已修复') NOT NULL DEFAULT '未修复' COMMENT '修复状态',
    PRIMARY KEY (`vuln_id`),
    KEY `idx_asset` (`asset_id`),
    KEY `idx_cve` (`cve_id`),
    KEY `idx_status_severity` (`repair_status`, `severity`),
    CONSTRAINT `fk_vuln_asset` FOREIGN KEY (`asset_id`) REFERENCES `company_assets` (`asset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资产漏洞台账';

-- -----------------------------------------------------------------------------
-- 3. 仿真种子数据：未修复高危/严重漏洞（Agent 研判触发源）
-- -----------------------------------------------------------------------------
INSERT INTO `company_assets` (`asset_id`, `server_name`, `ip_address`, `department`, `is_internet_exposed`) VALUES
('AST-2026-001', 'prod-gateway-apache-01', '203.0.113.88',  '信息技术部-对外业务', 1),
('AST-2026-002', 'erp-mysql-cluster-02',   '10.20.30.15',   '财务部-核心业务',     0),
('AST-2026-003', 'oa-jenkins-build-03',    '10.20.40.22',   '研发部-DevOps',       0),
('AST-2026-004', 'mail-exchange-edge-04',  '198.51.100.12', '行政部-邮件网关',     1),
('AST-2026-005', 'bi-redis-cache-05',      '10.20.50.33',   '数据中心-分析平台',   0);

INSERT INTO `asset_vulnerabilities` (`vuln_id`, `asset_id`, `cve_id`, `vuln_name`, `severity`, `repair_status`) VALUES
('VULN-2026-1001', 'AST-2026-001', 'CVE-2026-23345', 'Apache HTTP Server 远程代码执行漏洞（在野利用活跃）', '严重', '未修复'),
('VULN-2026-1002', 'AST-2026-001', 'CVE-2026-18402', 'OpenSSL 心脏出血变种侧信道信息泄露',               '高危', '未修复'),
('VULN-2026-1003', 'AST-2026-004', 'CVE-2026-11298', 'Microsoft Exchange SSRF 至任意文件读取',           '严重', '修复中'),
('VULN-2026-1004', 'AST-2026-002', 'CVE-2026-30112', 'MySQL 认证绕过导致越权访问业务库',                 '高危', '未修复'),
('VULN-2026-1005', 'AST-2026-003', 'CVE-2026-08776', 'Jenkins Script Console 未授权 RCE',                '严重', '未修复');

SET FOREIGN_KEY_CHECKS = 1;

-- 验证查询示例（供 DBA / Agent 联调）:
-- SELECT a.server_name, a.ip_address, a.is_internet_exposed, v.cve_id, v.vuln_name, v.severity, v.repair_status
-- FROM company_assets a
-- JOIN asset_vulnerabilities v ON a.asset_id = v.asset_id
-- WHERE v.repair_status = '未修复' AND v.severity IN ('高危','严重');
