/*
 Navicat Premium Data Transfer

 Source Server         : 腾讯云美国服务器MySQL
 Source Server Type    : MySQL
 Source Server Version : 80042
 Source Host           : 43.153.24.226:3306
 Source Schema         : flashsale

 Target Server Type    : MySQL
 Target Server Version : 80042
 File Encoding         : 65001

 Date: 25/05/2025 16:31:33
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for address
-- ----------------------------
DROP TABLE IF EXISTS `address`;
CREATE TABLE `address`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `receiver_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '收货人姓名',
  `phone` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `district` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '区县',
  `detail_address` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '详细地址',
  `is_default` tinyint(1) NULL DEFAULT 0,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `address_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 32 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of address
-- ----------------------------
INSERT INTO `address` VALUES (33, 6, '张伟', '13898765432', '广东省', '广州市', '天河区', '广州市天河路88号天汇大厦1101室', 1, '2025-05-24 15:47:02');
INSERT INTO `address` VALUES (34, 7, 'user', '13898765432', '广东省', '广州市', '天河区', '广州市天河路88号天汇大厦1101室', 1, '2025-05-24 15:56:11');

-- ----------------------------
-- Table structure for category
-- ----------------------------
DROP TABLE IF EXISTS `category`;
CREATE TABLE `category`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of category
-- ----------------------------
INSERT INTO `category` VALUES (1, '电子产品', '电子产品是以电为动力来源、通过电路板进行控制与操作的各类设备。它们在日常生活中扮演着重要角色，包括智能手机、电脑、智能穿戴设备、耳机等。现代电子产品不仅具备强大的功能，还强调设计感和用户体验，是科技与生活的完美融合。');
INSERT INTO `category` VALUES (6, '音响设备', '音响设备用于音频播放、录音、广播等音频相关应用。它们包括耳机、音响、麦克风、功放、音响系统等。音响设备的目标是提供清晰、高质量的声音体验，满足用户在不同场景下的音频需求，如家庭娱乐、工作环境和户外活动等。');
INSERT INTO `category` VALUES (7, '家电', '家电是指家庭日常生活中使用的各种电器产品，如冰箱、洗衣机、空调、微波炉等。这些设备通过提供便捷的生活服务，帮助用户提高生活质量。家电产品一般注重智能化、节能环保以及人性化设计，方便用户日常使用。');
INSERT INTO `category` VALUES (8, '运动用品', '运动用品是指帮助人们进行体育活动的各种设备与服装，如运动鞋、运动服、健身器材、运动配件等。它们不仅增强运动的舒适性与安全性，还有助于提高运动表现和防止运动损伤。现代运动用品越来越注重科技感和设计感，以满足不同人群的运动需求。');

-- ----------------------------
-- Table structure for goods
-- ----------------------------
DROP TABLE IF EXISTS `goods`;
CREATE TABLE `goods`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '商品名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '商品描述',
  `price` float NOT NULL,
  `original_price` float NOT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '商品创建时间',
  `category_id` int NOT NULL,
  `stock` int NOT NULL DEFAULT 0 COMMENT '商品库存',
  `photo_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '商品图片路径',
  `brand` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '品牌',
  `model` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '型号',
  `weight` float NULL DEFAULT NULL COMMENT '重量(kg)',
  `dimensions` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '尺寸(长x宽x高)',
  `material` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '材质',
  `warranty` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '保修信息',
  `sales` int NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `goods_ibfk_1`(`category_id` ASC) USING BTREE,
  CONSTRAINT `goods_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 319 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of goods
-- ----------------------------
INSERT INTO `goods` VALUES (1, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 10100, 10100, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 121);
INSERT INTO `goods` VALUES (2, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 540);
INSERT INTO `goods` VALUES (3, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 339);
INSERT INTO `goods` VALUES (4, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 74);
INSERT INTO `goods` VALUES (5, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 1099.99, 1199.99, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 351);
INSERT INTO `goods` VALUES (6, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 535);
INSERT INTO `goods` VALUES (7, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 621);
INSERT INTO `goods` VALUES (8, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 501);
INSERT INTO `goods` VALUES (12, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 1099.99, 1199.99, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 638);
INSERT INTO `goods` VALUES (13, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 689);
INSERT INTO `goods` VALUES (14, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 528);
INSERT INTO `goods` VALUES (15, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 575);
INSERT INTO `goods` VALUES (16, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 1099.99, 1199.99, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 288);
INSERT INTO `goods` VALUES (17, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 717);
INSERT INTO `goods` VALUES (18, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 721);
INSERT INTO `goods` VALUES (19, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 452);
INSERT INTO `goods` VALUES (27, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 1099.99, 1199.99, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 98);
INSERT INTO `goods` VALUES (28, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 132);
INSERT INTO `goods` VALUES (29, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 366);
INSERT INTO `goods` VALUES (30, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 435);
INSERT INTO `goods` VALUES (31, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 1099.99, 1199.99, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 75);
INSERT INTO `goods` VALUES (32, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 70);
INSERT INTO `goods` VALUES (33, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 124);
INSERT INTO `goods` VALUES (34, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 410);
INSERT INTO `goods` VALUES (35, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 1099.99, 1199.99, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 675);
INSERT INTO `goods` VALUES (36, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 147);
INSERT INTO `goods` VALUES (37, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 710);
INSERT INTO `goods` VALUES (38, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 107);
INSERT INTO `goods` VALUES (39, 'iPhone 16 Pro Max', 'Apple/苹果 iPhone 16 Pro Max（A3297）256GB 原色钛金属 支持移动联通电信5G 双卡双待手机', 1099.99, 1199.99, '2025-05-25 10:00:00', 1, 500, 'uploads/1748142740_cdf626fa-5655-45d5-97cf-64bb40b480d5.png', 'Apple', 'iPhone 16 Pro Max', 0.238, '160.8x78.1x7.65', '铝合金+玻璃', '1年官方保修', 404);
INSERT INTO `goods` VALUES (40, 'Bose QuietComfort 45', 'Bose QuietComfort 45 是一款顶级降噪耳机，提供舒适佩戴体验和优质音质，适合长时间使用，拥有出色的降噪技术，轻松享受音乐和通话。', 329.99, 379.99, '2025-05-25 10:30:00', 6, 300, 'uploads/1748142632_7dfaf29c-498e-4ea0-9ba2-332f566ff9c8.png', 'Bose', 'QuietComfort 45', 0.24, '18.5x18.5x5', '塑料+皮革', '2年官方保修', 697);
INSERT INTO `goods` VALUES (41, 'LG 9公斤滚筒洗衣机', 'LG 9公斤滚筒洗衣机，具有智能感应功能，可以根据衣物的重量和污渍程度自动调节洗涤模式，节能省水，支持Wi-Fi远程控制，满足现代家庭需求。', 799.99, 899.99, '2025-05-25 11:00:00', 7, 200, 'uploads/1748142586_7106f26aea982e9e3f91d4f19364a840.png', 'LG', 'F4V5VYP2T', 65, '60x60x85', '不锈钢+塑料', '3年官方保修', 275);
INSERT INTO `goods` VALUES (42, 'Nike Air Zoom Pegasus 39', 'Nike Air Zoom Pegasus 39 运动鞋，采用先进的Zoom气垫技术，提供卓越的舒适性和支持性，适合跑步和日常运动使用，拥有时尚外观和出色的耐用性。', 129.99, 149.99, '2025-05-25 11:30:00', 8, 600, 'uploads/1748142522_654a9dc11b3bfe48c50034b261cb1ca8.png', 'Nike', 'Air Zoom Pegasus 39', 0.3, '27x10x8', '合成纤维+橡胶', '1年官方保修', 281);

-- ----------------------------
-- Table structure for order
-- ----------------------------
DROP TABLE IF EXISTS `order`;
CREATE TABLE `order`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `activity_id` int NULL DEFAULT NULL,
  `goods_id` int NOT NULL,
  `order_time` datetime NULL DEFAULT NULL,
  `pay_time` datetime NULL DEFAULT NULL COMMENT '支付时间',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'pending',
  `quantity` int NOT NULL DEFAULT 1 COMMENT '购买数量',
  `total_amount` float NOT NULL COMMENT '订单总金额',
  `address_id` int NULL DEFAULT NULL,
  `receiver_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `payment_method` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `transaction_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '交易流水号',
  `phone` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `district` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `detail_address` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `complete_time` datetime NULL DEFAULT NULL,
  `cancel_time` datetime NULL DEFAULT NULL COMMENT '订单取消时间',
  `ship_time` datetime NULL DEFAULT NULL,
  `order_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_order_number`(`order_number` ASC) USING BTREE,
  INDEX `order_ibfk_1`(`user_id` ASC) USING BTREE,
  INDEX `order_ibfk_2`(`activity_id` ASC) USING BTREE,
  INDEX `order_ibfk_3`(`goods_id` ASC) USING BTREE,
  INDEX `order_ibfk_4`(`address_id` ASC) USING BTREE,
  CONSTRAINT `order_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `order_ibfk_2` FOREIGN KEY (`activity_id`) REFERENCES `seckill_activity` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `order_ibfk_3` FOREIGN KEY (`goods_id`) REFERENCES `goods` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `order_ibfk_4` FOREIGN KEY (`address_id`) REFERENCES `address` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 165 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of order
-- ----------------------------

-- ----------------------------
-- Table structure for order_remarks
-- ----------------------------
DROP TABLE IF EXISTS `order_remarks`;
CREATE TABLE `order_remarks`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `admin_id` int NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `order_id`(`order_id` ASC) USING BTREE,
  INDEX `admin_id`(`admin_id` ASC) USING BTREE,
  CONSTRAINT `order_remarks_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `order_remarks_ibfk_2` FOREIGN KEY (`admin_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of order_remarks
-- ----------------------------

-- ----------------------------
-- Table structure for order_status_logs
-- ----------------------------
DROP TABLE IF EXISTS `order_status_logs`;
CREATE TABLE `order_status_logs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `old_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `new_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `admin_id` int NOT NULL,
  `remark` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `order_id`(`order_id` ASC) USING BTREE,
  INDEX `admin_id`(`admin_id` ASC) USING BTREE,
  CONSTRAINT `order_status_logs_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `order_status_logs_ibfk_2` FOREIGN KEY (`admin_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of order_status_logs
-- ----------------------------

-- ----------------------------
-- Table structure for seckill_activity
-- ----------------------------
DROP TABLE IF EXISTS `seckill_activity`;
CREATE TABLE `seckill_activity`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `goods_id` int NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `seckill_price` float NOT NULL,
  `total_stock` int NOT NULL,
  `available_stock` int NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `goods_id`(`goods_id` ASC) USING BTREE,
  CONSTRAINT `seckill_activity_ibfk_1` FOREIGN KEY (`goods_id`) REFERENCES `goods` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 233 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of seckill_activity
-- ----------------------------
INSERT INTO `seckill_activity` VALUES (243, 1, '2025-05-23 12:37:00', '2025-05-28 12:37:00', 9999, 10, 10, 'active');
INSERT INTO `seckill_activity` VALUES (244, 1, '2025-05-30 12:37:00', '2025-06-07 12:37:00', 8888, 10, 10, 'active');
INSERT INTO `seckill_activity` VALUES (245, 1, '2025-05-17 12:38:00', '2025-05-23 12:38:00', 9999, 10, 10, 'active');

-- ----------------------------
-- Table structure for seckill_order
-- ----------------------------
DROP TABLE IF EXISTS `seckill_order`;
CREATE TABLE `seckill_order`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `activity_id` int NOT NULL,
  `create_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  INDEX `activity_id`(`activity_id` ASC) USING BTREE,
  CONSTRAINT `seckill_order_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `seckill_order_ibfk_2` FOREIGN KEY (`activity_id`) REFERENCES `seckill_activity` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of seckill_order
-- ----------------------------

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `role` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'user',
  `email` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE,
  UNIQUE INDEX `phone`(`phone` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (5, '123', 'scrypt:32768:8:1$3mF8RQ9mcjEuVnjn$4be0c3d4a612916f2022e78236ec368fa98b27d07655e7e21f7d1146127face601ff492f4d79afee600186d54a4350fe80ca73052e5a6fc7618cf142c81304cb', 'user', '112@qq.com', '12342678901', '2025-05-24 10:16:06', 1);
INSERT INTO `user` VALUES (6, 'admin', 'pbkdf2:sha256:260000$GupqGaYOGgObLIkk$c77df2778f1bb0d828ad5a89067ffe54b318337729856adb98aa2621a5786a72', 'admin', '2593254994@qq.com', '13415904980', '2025-05-24 15:45:47', 1);
INSERT INTO `user` VALUES (7, 'user', 'pbkdf2:sha256:260000$lZ8dXwZK2iVvHdc7$307f0161dab15589aa21b87d66961d931640d6e1bb68f666034f25ba6201ac6d', 'user', '114@qq.com', '', '2025-05-24 15:54:53', 1);

SET FOREIGN_KEY_CHECKS = 1;
