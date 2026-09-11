-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 25, 2024 at 02:15 AM
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
-- Database: `moderator`
--

-- --------------------------------------------------------

--
-- Table structure for table `moderationforms`
--

CREATE TABLE `moderationforms` (
  `id` int(11) NOT NULL,
  `studentattemptid` int(10) NOT NULL,
  `studentname` varchar(255) NOT NULL,
  `studentid` varchar(20) DEFAULT '',
  `coursename` varchar(150) NOT NULL,
  `courseid` int(10) NOT NULL,
  `moderatorname` varchar(255) NOT NULL,
  `coursecompletiondate` timestamp NOT NULL DEFAULT current_timestamp(),
  `moderationdate` timestamp NOT NULL DEFAULT current_timestamp(),
  `question1` tinyint(1) DEFAULT 0,
  `question2` tinyint(1) DEFAULT 0,
  `question3` tinyint(1) DEFAULT 0,
  `question4` tinyint(1) DEFAULT 0,
  `question5` tinyint(1) DEFAULT 0,
  `question6` tinyint(1) DEFAULT 0,
  `question7` tinyint(1) DEFAULT 0,
  `feedback` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `moderationforms`
--
ALTER TABLE `moderationforms`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `studentattemptid` (`studentattemptid`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `moderationforms`
--
ALTER TABLE `moderationforms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
