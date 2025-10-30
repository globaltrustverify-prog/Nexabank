-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 30, 2025 at 02:09 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `nexabank`
--

-- --------------------------------------------------------

--
-- Table structure for table `accounts`
--

CREATE TABLE `accounts` (
  `account_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `account_type` enum('checking','savings') NOT NULL,
  `balance` decimal(15,2) DEFAULT 0.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `accounts`
--

INSERT INTO `accounts` (`account_id`, `user_id`, `account_number`, `account_type`, `balance`, `created_at`) VALUES
(1, 1, 'NBC000001', 'checking', 1679.46, '2025-10-28 22:48:46'),
(2, 1, 'NBS000002', 'savings', 1248.57, '2025-10-28 22:50:00'),
(4, 2, 'NBS000001', 'savings', 50.00, '2025-10-28 23:16:14'),
(6, 4, 'NBC960957306', 'checking', 6100.00, '2025-10-29 15:15:11'),
(7, 4, 'NBS875343940', 'savings', 8150.00, '2025-10-29 15:16:29'),
(8, 5, 'NBC111476274', 'checking', 100.00, '2025-10-29 16:33:13'),
(9, 8, 'NBC704100544', 'checking', 31090.00, '2025-10-30 09:54:50'),
(10, 8, 'NBS781473272', 'savings', 0.00, '2025-10-30 10:23:41');

-- --------------------------------------------------------

--
-- Table structure for table `beneficiaries`
--

CREATE TABLE `beneficiaries` (
  `beneficiary_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `name` varchar(255) NOT NULL,
  `bank_name` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `beneficiaries`
--

INSERT INTO `beneficiaries` (`beneficiary_id`, `user_id`, `account_number`, `name`, `bank_name`, `created_at`) VALUES
(1, 1, 'NBS000001', 'Second User', 'NexaBank', '2025-10-28 23:26:27');

-- --------------------------------------------------------

--
-- Table structure for table `crypto_funding_requests`
--

CREATE TABLE `crypto_funding_requests` (
  `request_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `currency` enum('BTC','ETH','USDT') NOT NULL,
  `crypto_amount` decimal(20,8) NOT NULL,
  `usd_amount` decimal(15,2) NOT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `admin_notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `account_type` varchar(20) DEFAULT 'checking'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `crypto_funding_requests`
--

INSERT INTO `crypto_funding_requests` (`request_id`, `user_id`, `currency`, `crypto_amount`, `usd_amount`, `status`, `admin_notes`, `created_at`, `updated_at`, `account_type`) VALUES
(1, 1, 'BTC', 0.01000000, 450.00, 'approved', 'Approved for testing', '2025-10-29 01:13:45', '2025-10-29 01:15:18', 'checking'),
(2, 1, 'ETH', 0.10000000, 300.00, 'rejected', 'Suspicious activity detected', '2025-10-29 01:16:14', '2025-10-29 01:17:42', 'checking'),
(3, 4, 'BTC', 0.00899281, 1000.00, 'rejected', 'Rejected by administrator', '2025-10-29 17:29:05', '2025-10-30 09:52:36', 'checking'),
(4, 4, 'BTC', 0.00899281, 1000.00, 'rejected', 'Rejected by administrator', '2025-10-29 17:29:07', '2025-10-30 09:52:28', 'checking'),
(5, 4, 'BTC', 0.00444444, 200.00, 'rejected', 'Rejected by administrator', '2025-10-29 17:29:40', '2025-10-30 09:52:18', 'checking'),
(6, 4, 'BTC', 0.00444444, 200.00, 'rejected', 'Rejected by administrator', '2025-10-29 17:29:40', '2025-10-30 09:52:24', 'checking'),
(7, 4, 'ETH', 1.66666667, 5000.00, 'approved', NULL, '2025-10-29 17:32:39', '2025-10-29 17:33:09', 'checking'),
(8, 4, 'ETH', 1.66666667, 5000.00, 'rejected', 'Rejected by administrator', '2025-10-29 17:32:39', '2025-10-30 09:52:16', 'checking'),
(9, 4, 'BTC', 0.04444444, 2000.00, 'approved', 'Approved by admin', '2025-10-29 17:39:31', '2025-10-30 09:51:16', 'checking'),
(10, 4, 'BTC', 0.04444444, 2000.00, 'rejected', 'Rejected by administrator', '2025-10-29 17:39:31', '2025-10-30 09:52:13', 'checking'),
(11, 4, 'BTC', 0.22222222, 10000.00, 'rejected', NULL, '2025-10-29 17:49:35', '2025-10-29 17:53:27', 'checking'),
(12, 4, 'BTC', 0.22222222, 10000.00, 'approved', NULL, '2025-10-29 17:49:35', '2025-10-29 17:53:27', 'checking'),
(13, 4, 'BTC', 0.44444444, 20000.00, 'approved', NULL, '2025-10-29 17:54:36', '2025-10-29 17:54:49', 'checking'),
(14, 4, 'BTC', 0.66666667, 30000.00, 'approved', NULL, '2025-10-29 20:56:38', '2025-10-29 21:08:51', 'savings'),
(15, 4, 'BTC', 0.03333333, 1500.00, 'approved', 'Approved by admin', '2025-10-29 21:20:08', '2025-10-29 21:22:07', 'checking'),
(16, 4, 'ETH', 0.66666667, 2000.00, 'approved', 'Approved by admin', '2025-10-29 21:54:44', '2025-10-29 21:55:39', 'checking'),
(17, 4, 'BTC', 0.06666667, 3000.00, 'approved', 'Approved by admin', '2025-10-29 21:56:43', '2025-10-29 21:57:07', 'savings'),
(18, 4, 'BTC', 0.11111111, 5000.00, 'approved', 'Approved by admin', '2025-10-29 22:34:36', '2025-10-29 22:35:11', 'savings'),
(19, 8, 'BTC', 0.01111111, 500.00, 'rejected', 'Rejected by administrator', '2025-10-30 09:55:18', '2025-10-30 09:55:37', 'checking'),
(20, 8, 'ETH', 0.16666667, 500.00, 'approved', 'Approved by admin', '2025-10-30 09:56:04', '2025-10-30 09:56:15', 'checking'),
(21, 8, 'BTC', 0.01111111, 500.00, 'approved', 'Approved by admin', '2025-10-30 09:57:16', '2025-10-30 09:57:30', 'checking'),
(22, 8, 'USDT', 500.00000000, 500.00, 'approved', 'Approved via admin dashboard', '2025-10-30 10:23:59', '2025-10-30 10:24:12', 'savings');

-- --------------------------------------------------------

--
-- Table structure for table `crypto_transactions`
--

CREATE TABLE `crypto_transactions` (
  `crypto_transaction_id` int(11) NOT NULL,
  `wallet_id` int(11) NOT NULL,
  `type` enum('deposit','withdrawal') NOT NULL,
  `amount` decimal(20,8) NOT NULL,
  `usd_value` decimal(15,2) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `status` enum('pending','confirmed','failed') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `crypto_transactions`
--

INSERT INTO `crypto_transactions` (`crypto_transaction_id`, `wallet_id`, `type`, `amount`, `usd_value`, `address`, `status`, `created_at`) VALUES
(1, 1, 'deposit', 0.01000000, 1128.84, NULL, 'confirmed', '2025-10-28 23:30:04'),
(2, 1, 'withdrawal', 0.00500000, 564.46, NULL, 'confirmed', '2025-10-28 23:30:40'),
(3, 1, 'deposit', 0.00022139, 25.00, NULL, 'confirmed', '2025-10-28 23:31:43'),
(4, 4, 'deposit', 0.03333333, 1500.00, NULL, 'confirmed', '2025-10-29 21:22:07'),
(5, 5, 'deposit', 0.66666667, 2000.00, NULL, 'confirmed', '2025-10-29 21:55:39'),
(6, 4, 'deposit', 0.06666667, 3000.00, NULL, 'confirmed', '2025-10-29 21:57:07'),
(7, 4, 'deposit', 0.11111111, 5000.00, NULL, 'confirmed', '2025-10-29 22:35:11'),
(8, 4, 'deposit', 0.04444444, 2000.00, NULL, 'confirmed', '2025-10-30 09:51:16'),
(9, 14, 'deposit', 0.16666667, 500.00, NULL, 'confirmed', '2025-10-30 09:56:15'),
(10, 13, 'deposit', 0.01111111, 500.00, NULL, 'confirmed', '2025-10-30 09:57:30'),
(11, 15, 'deposit', 500.00000000, 500.00, NULL, 'confirmed', '2025-10-30 10:24:12'),
(12, 13, 'withdrawal', 0.00100000, 45.00, NULL, 'confirmed', '2025-10-30 10:28:45'),
(13, 13, 'withdrawal', 0.00100000, 45.00, NULL, 'confirmed', '2025-10-30 10:28:45');

-- --------------------------------------------------------

--
-- Table structure for table `crypto_wallets`
--

CREATE TABLE `crypto_wallets` (
  `wallet_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `currency` enum('BTC','ETH','USDT') NOT NULL,
  `address` varchar(255) NOT NULL,
  `balance` decimal(20,8) DEFAULT 0.00000000,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `crypto_wallets`
--

INSERT INTO `crypto_wallets` (`wallet_id`, `user_id`, `currency`, `address`, `balance`, `created_at`) VALUES
(1, 1, 'BTC', 'bc1793a18d91bd7eccbbc68690e4caaf39340', 0.00022139, '2025-10-28 22:51:12'),
(2, 1, 'ETH', '0xe3cc804342e5cf086d636feab6875817fd', 0.00000000, '2025-10-28 22:51:13'),
(3, 1, 'USDT', '0xbb4e1ec246700d62631c4ca8009e1c1249', 0.00000000, '2025-10-28 22:51:14'),
(4, 4, 'BTC', 'bc17a16811cb30cdabff649b571f3b194f0c1', 0.25555555, '2025-10-29 14:05:18'),
(5, 4, 'ETH', '0x56acf2f55b65ec6dd022f5ad679a9c9254', 0.66666667, '2025-10-29 14:05:18'),
(6, 4, 'USDT', '0x9c545d805b26968385ef6716ee8295348e', 0.00000000, '2025-10-29 14:05:18'),
(7, 5, 'BTC', 'bc15ab82cf43e9a623b698c6d743eb3afd630', 0.00000000, '2025-10-29 16:33:05'),
(8, 5, 'ETH', '0x4addf46ca1ea6cdf221d9a356215bb74a1', 0.00000000, '2025-10-29 16:33:05'),
(9, 5, 'USDT', '0x4202e4e1f9f6e85cc7d7fc0bddc05bd194', 0.00000000, '2025-10-29 16:33:05'),
(10, 6, 'BTC', 'bc14e82641ed32f8f6afeb71b6ce2cc015ca5', 0.00000000, '2025-10-29 22:46:35'),
(11, 6, 'ETH', '0xb1cd773e3956bdd9bddc34771b6e3fbb3d', 0.00000000, '2025-10-29 22:46:35'),
(12, 6, 'USDT', '0xc68bc3ad999cc0adfc8f3ddae09eac0bd6', 0.00000000, '2025-10-29 22:46:35'),
(13, 8, 'BTC', 'bc14b51c848238efb7843d98a58e3796a3485', 0.00911111, '2025-10-30 09:54:37'),
(14, 8, 'ETH', '0xff5452a00ae9f8c39db696eb03c3881f57', 0.16666667, '2025-10-30 09:54:37'),
(15, 8, 'USDT', '0xecd9700eccd7b9cc4d479bef5aa2da85d5', 500.00000000, '2025-10-30 09:54:37'),
(16, 7, 'BTC', 'bc1518bdbfb933cd9a367cf36357ee0ae0cd9', 0.00000000, '2025-10-30 11:38:18'),
(17, 7, 'ETH', '0x62c0d311a09a02a862a3c2e6f827a6b631', 0.00000000, '2025-10-30 11:38:18'),
(18, 7, 'USDT', '0xa907732610fe332d45331698e9e5397ed1', 0.00000000, '2025-10-30 11:38:18');

-- --------------------------------------------------------

--
-- Table structure for table `kyc_documents`
--

CREATE TABLE `kyc_documents` (
  `document_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `document_type` enum('id_card','passport','driver_license','utility_bill','bank_statement') DEFAULT NULL,
  `document_number` varchar(100) DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  `status` enum('pending','verified','rejected') DEFAULT 'pending',
  `verified_by` int(11) DEFAULT NULL,
  `verified_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `kyc_documents`
--

INSERT INTO `kyc_documents` (`document_id`, `user_id`, `document_type`, `document_number`, `file_path`, `status`, `verified_by`, `verified_at`, `created_at`) VALUES
(1, 1, 'passport', 'AB123456', 'mock_file_path', 'pending', NULL, NULL, '2025-10-28 22:54:39');

-- --------------------------------------------------------

--
-- Table structure for table `stocks`
--

CREATE TABLE `stocks` (
  `stock_id` int(11) NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `current_price` decimal(10,2) DEFAULT NULL,
  `daily_change` decimal(10,2) DEFAULT NULL,
  `daily_change_percent` decimal(5,2) DEFAULT NULL,
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stocks`
--

INSERT INTO `stocks` (`stock_id`, `symbol`, `company_name`, `current_price`, `daily_change`, `daily_change_percent`, `last_updated`) VALUES
(1, 'AAPL', 'Apple Inc.', 182.54, -2.96, -1.60, '2025-10-28 22:52:37'),
(2, 'MSFT', 'Microsoft Corporation', 542.07, 10.55, 1.98, '2025-10-28 22:52:38'),
(3, 'GOOGL', 'Alphabet Inc.', 137.69, -0.51, -0.37, '2025-10-28 22:52:39'),
(4, 'AMZN', 'Amazon.com Inc.', 158.68, 2.93, 1.88, '2025-10-28 22:52:41'),
(5, 'TSLA', 'Tesla Inc.', 242.07, -3.53, -1.44, '2025-10-28 22:52:42'),
(6, 'META', 'Meta Platforms Inc.', 344.85, -5.55, -1.58, '2025-10-28 22:52:44'),
(7, 'NVDA', 'NVIDIA Corporation', 480.36, 5.11, 1.08, '2025-10-28 22:52:45'),
(8, 'NFLX', 'Netflix Inc.', 490.60, 4.70, 0.97, '2025-10-28 22:52:46'),
(9, 'JPM', 'JPMorgan Chase & Co.', 172.84, 2.49, 1.46, '2025-10-28 22:52:47'),
(10, 'V', 'Visa Inc.', 247.27, -3.53, -1.41, '2025-10-28 22:52:49'),
(11, 'MA', 'Mastercard Incorporated', 381.74, -3.71, -0.96, '2025-10-28 22:52:51'),
(12, 'WMT', 'Walmart Inc.', 166.95, 1.75, 1.06, '2025-10-28 22:52:52'),
(13, 'KO', 'The Coca-Cola Company', 58.92, -0.93, -1.56, '2025-10-28 22:52:53'),
(14, 'MCD', 'McDonald\'s Corporation', 283.29, -2.41, -0.84, '2025-10-28 22:52:56'),
(15, 'SPY', 'SPDR S&P 500 ETF Trust', 454.44, -0.86, -0.19, '2025-10-28 22:52:58'),
(16, 'QQQ', 'Invesco QQQ Trust', 380.33, -0.12, -0.03, '2025-10-28 22:52:59'),
(17, 'VOO', 'Vanguard S&P 500 ETF', 417.15, -3.00, -0.71, '2025-10-28 22:53:00'),
(18, 'BABA', 'Alibaba Group Holding Limited', 87.12, 1.52, 1.77, '2025-10-28 22:53:01'),
(19, 'TSM', 'Taiwan Semiconductor Manufacturing Company Limited', 96.69, 1.29, 1.35, '2025-10-28 22:53:02'),
(39, 'GME', 'GameStop Corp.', 30.75, 5.25, 20.59, '2025-10-29 00:14:03');

-- --------------------------------------------------------

--
-- Table structure for table `stock_portfolios`
--

CREATE TABLE `stock_portfolios` (
  `portfolio_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `average_price` decimal(10,2) NOT NULL,
  `total_invested` decimal(15,2) NOT NULL,
  `current_value` decimal(15,2) DEFAULT NULL,
  `unrealized_pnl` decimal(15,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stock_portfolios`
--

INSERT INTO `stock_portfolios` (`portfolio_id`, `user_id`, `symbol`, `quantity`, `average_price`, `total_invested`, `current_value`, `unrealized_pnl`, `created_at`, `updated_at`) VALUES
(1, 1, 'AAPL', 0.50, 183.56, 91.78, 93.29, 1.51, '2025-10-28 23:10:28', '2025-10-28 23:32:40');

-- --------------------------------------------------------

--
-- Table structure for table `stock_transactions`
--

CREATE TABLE `stock_transactions` (
  `transaction_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `type` enum('buy','sell') NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `total_amount` decimal(15,2) NOT NULL,
  `order_type` enum('market','limit') DEFAULT 'market',
  `status` enum('pending','completed','cancelled') DEFAULT 'completed',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stock_transactions`
--

INSERT INTO `stock_transactions` (`transaction_id`, `user_id`, `symbol`, `type`, `quantity`, `price`, `total_amount`, `order_type`, `status`, `created_at`) VALUES
(1, 1, 'AAPL', 'buy', 1.00, 189.04, 183.56, 'market', 'completed', '2025-10-28 23:10:28'),
(2, 1, 'AAPL', 'sell', 0.50, 186.58, 93.29, 'market', 'completed', '2025-10-28 23:32:40');

-- --------------------------------------------------------

--
-- Table structure for table `transactions`
--

CREATE TABLE `transactions` (
  `transaction_id` int(11) NOT NULL,
  `account_id` int(11) NOT NULL,
  `type` enum('deposit','withdraw','transfer') NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `balance_after` decimal(15,2) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `transactions`
--

INSERT INTO `transactions` (`transaction_id`, `account_id`, `type`, `amount`, `balance_after`, `description`, `created_at`) VALUES
(1, 1, 'deposit', 1000.00, 1000.00, 'Cash deposit', '2025-10-28 22:49:16'),
(2, 1, 'withdraw', 200.00, 800.00, 'Transfer to savings: Moving to savings', '2025-10-28 22:50:22'),
(3, 2, 'deposit', 200.00, 200.00, 'Transfer from checking: Moving to savings', '2025-10-28 22:50:22'),
(4, 2, 'withdraw', 183.56, 16.44, 'Stock purchase: 1 shares of AAPL', '2025-10-28 23:10:28'),
(5, 1, 'withdraw', 100.00, 700.00, 'Cash withdrawal', '2025-10-28 23:13:39'),
(6, 1, 'withdraw', 50.00, 650.00, 'Transfer to user2@example.com: Test email transfer', '2025-10-28 23:24:50'),
(7, 4, 'deposit', 50.00, 50.00, 'Transfer from test@example.com: Test email transfer', '2025-10-28 23:24:50'),
(8, 2, 'deposit', 1128.84, 1145.28, 'Crypto funding: 0.01000000 BTC', '2025-10-28 23:30:04'),
(9, 1, 'deposit', 564.46, 1214.46, 'Crypto sale: 0.005 BTC', '2025-10-28 23:30:40'),
(10, 1, 'withdraw', 25.00, 1189.46, 'Crypto purchase: 0.00022139 BTC', '2025-10-28 23:31:43'),
(11, 2, 'deposit', 93.29, 1238.57, 'Stock sale: 0.5 shares of AAPL', '2025-10-28 23:32:40'),
(12, 1, 'withdraw', 10.00, 1179.46, 'Transfer to savings: Quick save: small', '2025-10-28 23:33:23'),
(13, 2, 'deposit', 10.00, 1248.57, 'Transfer from checking: Quick save: small', '2025-10-28 23:33:23'),
(14, 1, 'deposit', 100.00, 1279.46, 'Admin adjustment: Admin bonus', '2025-10-28 23:52:41'),
(15, 1, 'withdraw', 50.00, 1229.46, 'Admin adjustment: Service fee', '2025-10-28 23:53:24'),
(16, 1, 'deposit', 450.00, 1679.46, 'Crypto funding approved: 0.01000000 BTC', '2025-10-29 01:15:18'),
(17, 6, 'withdraw', 100.00, 100.00, 'Transfer to adegoke abiola: free food', '2025-10-29 16:33:59'),
(18, 8, 'deposit', 100.00, 100.00, 'Transfer from aggdgggd hdgdgdhd: free food', '2025-10-29 16:33:59'),
(19, 6, 'deposit', 1500.00, 1600.00, 'Crypto funding approved: 0.03333333 BTC (Approved by admin)', '2025-10-29 21:22:07'),
(20, 6, 'deposit', 2000.00, 3600.00, 'Crypto funding approved: 0.66666667 ETH (Approved by admin)', '2025-10-29 21:55:39'),
(21, 7, 'deposit', 3000.00, 3150.00, 'Crypto funding approved: 0.06666667 BTC (Approved by admin)', '2025-10-29 21:57:07'),
(22, 7, 'deposit', 5000.00, 8150.00, 'Crypto funding approved: 0.11111111 BTC (Approved by admin)', '2025-10-29 22:35:11'),
(23, 6, 'deposit', 2000.00, 5600.00, 'Crypto funding approved: 0.04444444 BTC (Approved by admin)', '2025-10-30 09:51:16'),
(24, 9, 'deposit', 500.00, 500.00, 'Crypto funding approved: 0.16666667 ETH (Approved by admin)', '2025-10-30 09:56:15'),
(25, 9, 'deposit', 500.00, 1000.00, 'Crypto funding approved: 0.01111111 BTC (Approved by admin)', '2025-10-30 09:57:30'),
(26, 9, 'deposit', 500.00, 1500.00, 'Crypto funding approved: 500.00000000 USDT (Approved via admin dashboard)', '2025-10-30 10:24:12'),
(27, 9, 'withdraw', 500.00, 1000.00, 'Transfer to aggdgggd hdgdgdhd: na dash ohh', '2025-10-30 10:27:35'),
(28, 6, 'deposit', 500.00, 6100.00, 'Transfer from kuti: na dash ohh', '2025-10-30 10:27:35'),
(29, 9, 'deposit', 45.00, 1045.00, 'Crypto sale: 0.001 BTC', '2025-10-30 10:28:45'),
(30, 9, 'deposit', 45.00, 1090.00, 'Crypto sale: 0.001 BTC', '2025-10-30 10:28:45'),
(31, 9, 'deposit', 30000.00, 31090.00, 'Admin adjustment: giveaway', '2025-10-30 10:51:31');

-- --------------------------------------------------------

--
-- Table structure for table `transaction_receipts`
--

CREATE TABLE `transaction_receipts` (
  `receipt_id` int(11) NOT NULL,
  `transaction_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  `receipt_type` enum('deposit','withdrawal','transfer','crypto_funding','stock_trade') NOT NULL,
  `receipt_number` varchar(50) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `currency` varchar(10) DEFAULT 'USD',
  `description` text DEFAULT NULL,
  `from_account` varchar(50) DEFAULT NULL,
  `to_account` varchar(50) DEFAULT NULL,
  `transaction_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` enum('completed','pending','failed') DEFAULT 'completed',
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `address` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_admin` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `email`, `password_hash`, `full_name`, `phone`, `date_of_birth`, `address`, `created_at`, `updated_at`, `is_admin`) VALUES
(1, 'test@example.com', '$pbkdf2-sha256$29000$z9n7f0/J.d.bE6J0zvn/Pw$2CbLNzwn/4WEkqrOeVH/xGAlic5vgA0l0TB5RcpvLMk', 'Test User', '', NULL, NULL, '2025-10-28 22:48:05', '2025-10-28 22:48:05', 0),
(2, 'user2@example.com', '$pbkdf2-sha256$29000$/T9HaM3531uLkRJi7P0/Zw$gpGxfCI7HCu4J8LOyuccIOaxzIimBWR5SnYo6VKSfiU', 'Second User', '', NULL, NULL, '2025-10-28 23:14:39', '2025-10-28 23:14:39', 0),
(3, 'admin@nexabank.com', '$pbkdf2-sha256$29000$lrL2XouxNoZQKsXYO.f8Hw$vfwR2n.7aT9H4hlHeQXtaa5FtD7WmhKODb83w185vxE', 'System Administrator', NULL, NULL, NULL, '2025-10-28 23:50:12', '2025-10-28 23:50:12', 1),
(4, 'kutrade3622@gmail.com', '$pbkdf2-sha256$29000$tjbmnDNGKKVUCuEcQ6i19g$dGozfQzF9n6KrVVsw6u/3Wp.bLYNzjgmIRh0O2d9h7w', 'aggdgggd hdgdgdhd', '08037429343', '2002-11-11', 'kskdkkdkdjdheuue', '2025-10-29 13:25:09', '2025-10-29 13:25:09', 0),
(5, 'morisdaniel3622@gmail.com', '$pbkdf2-sha256$29000$qJXSmhPinBNijNF6DwEgBA$dWVKOnrVzfxwiKYHdo0Xtr3m7dWqj8LLqpzW8.vNu9w', 'adegoke abiola', '08037429343', '2000-11-11', 'xxnxnxnxnxnxnx', '2025-10-29 13:48:42', '2025-10-29 13:48:42', 0),
(6, 'admin@example.com', '$pbkdf2-sha256$29000$RQiBcO49JwRAyNl7L8U4Jw$kJk5I4P4zE4UOX/AIWIT6LTHiyYl2l1YYcS25gJecXU', 'Admin User', NULL, NULL, NULL, '2025-10-29 21:16:33', '2025-10-29 21:16:33', 1),
(7, 'admin1@nexabank.com', '$pbkdf2-sha256$29000$z7k3hvAeA2BsjRHifG.tNQ$1nFICczZI.pqtVCneQa29oaMS8gqLxNrtY0culM5Ugo', 'full admin', '08037429343', '2000-11-11', 'cnncncncncncnc', '2025-10-30 08:00:42', '2025-10-30 08:01:05', 1),
(8, 'adegoke36@gmail.com', '$pbkdf2-sha256$29000$USrl/L/XWqtVCqF0TgnBGA$tlohKtLLpzcPuqf1QecpOet.mTxHt3zcKdIu93uQ9ic', 'kuti', '07048093742', '2000-11-11', 'sbsbssbsbsbsbs', '2025-10-30 09:54:02', '2025-10-30 09:54:02', 0),
(9, 'omoniyieze407@gmail.com', '$pbkdf2-sha256$29000$V0pJyfmf8/5f652zFoJwTg$4evjKMwhTNxN0DZ.1BvjZMVlvHdbOd0GD7JV547cpWU', 'akin', '07048093742', '2000-11-11', 'cjjfhfhfjdjdjfhffdjd', '2025-10-30 11:48:08', '2025-10-30 11:48:08', 0),
(10, 'omoniyiezeww407@gmail.com', '$pbkdf2-sha256$29000$VOqd8/7fu/f.fy9lrPXe.w$bhf40Sol/nhC.ZmDpJ/3qDCmwMnwwRGW0XJu3Zebxns', 'akinww', '07048093742', '2000-11-11', 'fjvnv', '2025-10-30 11:50:59', '2025-10-30 11:50:59', 0);

-- --------------------------------------------------------

--
-- Table structure for table `user_addresses`
--

CREATE TABLE `user_addresses` (
  `address_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `address_line1` varchar(255) DEFAULT NULL,
  `address_line2` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `verified` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `user_profiles`
--

CREATE TABLE `user_profiles` (
  `profile_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `date_of_birth` date DEFAULT NULL,
  `phone_verified` tinyint(1) DEFAULT 0,
  `email_verified` tinyint(1) DEFAULT 0,
  `kyc_tier` enum('unverified','basic','id_verified','full_kyc') DEFAULT 'unverified',
  `daily_limit` decimal(15,2) DEFAULT 100.00,
  `monthly_limit` decimal(15,2) DEFAULT 1000.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_profiles`
--

INSERT INTO `user_profiles` (`profile_id`, `user_id`, `date_of_birth`, `phone_verified`, `email_verified`, `kyc_tier`, `daily_limit`, `monthly_limit`, `created_at`, `updated_at`) VALUES
(1, 1, NULL, 1, 1, 'unverified', 100.00, 1000.00, '2025-10-28 22:53:51', '2025-10-28 22:55:59');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `accounts`
--
ALTER TABLE `accounts`
  ADD PRIMARY KEY (`account_id`),
  ADD UNIQUE KEY `account_number` (`account_number`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `beneficiaries`
--
ALTER TABLE `beneficiaries`
  ADD PRIMARY KEY (`beneficiary_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `crypto_funding_requests`
--
ALTER TABLE `crypto_funding_requests`
  ADD PRIMARY KEY (`request_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `crypto_transactions`
--
ALTER TABLE `crypto_transactions`
  ADD PRIMARY KEY (`crypto_transaction_id`),
  ADD KEY `wallet_id` (`wallet_id`);

--
-- Indexes for table `crypto_wallets`
--
ALTER TABLE `crypto_wallets`
  ADD PRIMARY KEY (`wallet_id`),
  ADD UNIQUE KEY `unique_user_currency` (`user_id`,`currency`);

--
-- Indexes for table `kyc_documents`
--
ALTER TABLE `kyc_documents`
  ADD PRIMARY KEY (`document_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `stocks`
--
ALTER TABLE `stocks`
  ADD PRIMARY KEY (`stock_id`),
  ADD UNIQUE KEY `symbol` (`symbol`);

--
-- Indexes for table `stock_portfolios`
--
ALTER TABLE `stock_portfolios`
  ADD PRIMARY KEY (`portfolio_id`),
  ADD UNIQUE KEY `unique_user_stock` (`user_id`,`symbol`),
  ADD KEY `symbol` (`symbol`);

--
-- Indexes for table `stock_transactions`
--
ALTER TABLE `stock_transactions`
  ADD PRIMARY KEY (`transaction_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `symbol` (`symbol`);

--
-- Indexes for table `transactions`
--
ALTER TABLE `transactions`
  ADD PRIMARY KEY (`transaction_id`),
  ADD KEY `account_id` (`account_id`);

--
-- Indexes for table `transaction_receipts`
--
ALTER TABLE `transaction_receipts`
  ADD PRIMARY KEY (`receipt_id`),
  ADD UNIQUE KEY `receipt_number` (`receipt_number`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `user_addresses`
--
ALTER TABLE `user_addresses`
  ADD PRIMARY KEY (`address_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `user_profiles`
--
ALTER TABLE `user_profiles`
  ADD PRIMARY KEY (`profile_id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `accounts`
--
ALTER TABLE `accounts`
  MODIFY `account_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `beneficiaries`
--
ALTER TABLE `beneficiaries`
  MODIFY `beneficiary_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `crypto_funding_requests`
--
ALTER TABLE `crypto_funding_requests`
  MODIFY `request_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT for table `crypto_transactions`
--
ALTER TABLE `crypto_transactions`
  MODIFY `crypto_transaction_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `crypto_wallets`
--
ALTER TABLE `crypto_wallets`
  MODIFY `wallet_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `kyc_documents`
--
ALTER TABLE `kyc_documents`
  MODIFY `document_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `stocks`
--
ALTER TABLE `stocks`
  MODIFY `stock_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=40;

--
-- AUTO_INCREMENT for table `stock_portfolios`
--
ALTER TABLE `stock_portfolios`
  MODIFY `portfolio_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `stock_transactions`
--
ALTER TABLE `stock_transactions`
  MODIFY `transaction_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `transactions`
--
ALTER TABLE `transactions`
  MODIFY `transaction_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `transaction_receipts`
--
ALTER TABLE `transaction_receipts`
  MODIFY `receipt_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `user_addresses`
--
ALTER TABLE `user_addresses`
  MODIFY `address_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user_profiles`
--
ALTER TABLE `user_profiles`
  MODIFY `profile_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `accounts`
--
ALTER TABLE `accounts`
  ADD CONSTRAINT `accounts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `beneficiaries`
--
ALTER TABLE `beneficiaries`
  ADD CONSTRAINT `beneficiaries_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `crypto_funding_requests`
--
ALTER TABLE `crypto_funding_requests`
  ADD CONSTRAINT `crypto_funding_requests_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `crypto_transactions`
--
ALTER TABLE `crypto_transactions`
  ADD CONSTRAINT `crypto_transactions_ibfk_1` FOREIGN KEY (`wallet_id`) REFERENCES `crypto_wallets` (`wallet_id`);

--
-- Constraints for table `crypto_wallets`
--
ALTER TABLE `crypto_wallets`
  ADD CONSTRAINT `crypto_wallets_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `kyc_documents`
--
ALTER TABLE `kyc_documents`
  ADD CONSTRAINT `kyc_documents_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `stock_portfolios`
--
ALTER TABLE `stock_portfolios`
  ADD CONSTRAINT `stock_portfolios_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `stock_portfolios_ibfk_2` FOREIGN KEY (`symbol`) REFERENCES `stocks` (`symbol`);

--
-- Constraints for table `stock_transactions`
--
ALTER TABLE `stock_transactions`
  ADD CONSTRAINT `stock_transactions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `stock_transactions_ibfk_2` FOREIGN KEY (`symbol`) REFERENCES `stocks` (`symbol`);

--
-- Constraints for table `transactions`
--
ALTER TABLE `transactions`
  ADD CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`);

--
-- Constraints for table `transaction_receipts`
--
ALTER TABLE `transaction_receipts`
  ADD CONSTRAINT `transaction_receipts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `user_addresses`
--
ALTER TABLE `user_addresses`
  ADD CONSTRAINT `user_addresses_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `user_profiles`
--
ALTER TABLE `user_profiles`
  ADD CONSTRAINT `user_profiles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
