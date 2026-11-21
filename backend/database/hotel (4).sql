-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 21, 2026 at 12:50 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `hotel`
--

-- --------------------------------------------------------

--
-- Table structure for table `addons`
--

CREATE TABLE `addons` (
  `id_addon` int(11) NOT NULL,
  `nama_addon` varchar(100) NOT NULL,
  `harga` int(11) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Tersedia'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `addons`
--

INSERT INTO `addons` (`id_addon`, `nama_addon`, `harga`, `status`) VALUES
(1, 'Spa & Wellness', 250000, 'Tersedia'),
(2, 'Cultural Experience', 725000, 'Tersedia'),
(3, 'Airport Transfer', 200000, 'Tersedia'),
(4, 'Culinary Journey', 460000, 'Tersedia');

-- --------------------------------------------------------

--
-- Table structure for table `bookings`
--

CREATE TABLE `bookings` (
  `id_booking` int(11) NOT NULL,
  `id_user` int(11) NOT NULL,
  `id_room` int(11) NOT NULL,
  `tanggal_checkin` date NOT NULL,
  `tanggal_checkout` date NOT NULL,
  `total_harga` int(11) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Menunggu',
  `jumlah_tamu` int(11) NOT NULL DEFAULT 1,
  `bank` varchar(20) DEFAULT NULL,
  `va_number` varchar(25) DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bookings`
--

INSERT INTO `bookings` (`id_booking`, `id_user`, `id_room`, `tanggal_checkin`, `tanggal_checkout`, `total_harga`, `status`, `jumlah_tamu`, `bank`, `va_number`, `expires_at`) VALUES
(23, 101, 7, '2026-11-27', '2026-12-01', 3800000, 'batal', 1, NULL, NULL, NULL),
(25, 104, 7, '2026-11-06', '2026-11-08', 2100000, 'batal', 1, NULL, NULL, NULL),
(26, 105, 7, '2026-11-11', '2026-11-18', 6980000, 'batal', 1, NULL, NULL, NULL),
(27, 105, 5, '2026-11-12', '2026-12-26', 15550000, 'batal', 1, NULL, NULL, NULL),
(28, 101, 7, '2026-11-25', '2026-11-26', 1000000, 'batal', 1, NULL, NULL, NULL),
(29, 101, 6, '2026-11-11', '2026-11-12', 880000, 'batal', 1, NULL, NULL, NULL),
(30, 104, 5, '2026-11-14', '2026-11-18', 1550000, 'batal', 1, NULL, NULL, NULL),
(31, 104, 5, '2026-11-13', '2026-11-18', 1750000, 'batal', 1, NULL, NULL, NULL),
(32, 104, 5, '2026-11-21', '2026-11-27', 2100000, 'batal', 1, NULL, NULL, NULL),
(33, 104, 5, '2026-11-20', '2026-11-27', 2450000, 'batal', 1, NULL, NULL, NULL),
(34, 104, 5, '2026-11-12', '2026-11-21', 3150000, 'batal', 1, NULL, NULL, NULL),
(35, 104, 5, '2026-11-12', '2026-11-21', 3150000, 'batal', 1, NULL, NULL, NULL),
(36, 104, 5, '2026-11-13', '2026-11-28', 5400000, 'batal', 1, NULL, NULL, NULL),
(37, 104, 6, '2026-11-26', '2026-12-05', 4950000, 'batal', 1, NULL, NULL, NULL),
(38, 106, 6, '2026-11-21', '2026-11-23', 1350000, 'lunas', 1, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `booking_addons`
--

CREATE TABLE `booking_addons` (
  `id_booking` int(11) NOT NULL,
  `id_addon` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rooms`
--

CREATE TABLE `rooms` (
  `id_room` int(11) NOT NULL,
  `tipe_kamar` varchar(50) NOT NULL,
  `harga_per_malam` int(11) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Tersedia',
  `kapasitas` int(11) NOT NULL DEFAULT 2
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `rooms`
--

INSERT INTO `rooms` (`id_room`, `tipe_kamar`, `harga_per_malam`, `status`, `kapasitas`) VALUES
(5, 'Standard', 350000, 'Tersedia', 2),
(6, 'Deluxe', 550000, 'Tersedia', 2),
(7, 'Suite', 950000, 'Tersedia', 4),
(8, 'Premium', 1600000, 'Tersedia', 2),
(9, 'Exclusive', 2200000, 'Tersedia', 3),
(10, 'Presidential', 3500000, 'Tersedia', 4);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id_user` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','customer') DEFAULT 'customer',
  `email` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id_user`, `username`, `password`, `role`, `email`) VALUES
(101, 'admin123', 'scrypt:32768:8:1$BPVeFcIJTWfIYuXL$ebe061bb81b9813d3a906bc7f0e44c6d3a9252b3ca202495e8a3b5e1dbb35eca74b0af59e393339e3e833162f7bb9c749ed2db9f4426f7cd60b2a8bf52883f5a', 'admin', NULL),
(104, 'pembeli', 'scrypt:32768:8:1$2DnM1CkaX0OGneBJ$fa1deae633478cc48b14d3e7f7adb923c6fd2e78c4ca42f0c35f907a5992ee8a1f9bbeee8af5fdb6c57a7dc5b3f1fb636613c5e0d09e918f07f497bab923681d', 'customer', NULL),
(105, 'samlekom', 'scrypt:32768:8:1$XuujSsDpUPW34IKA$eeba23c71272455bd2b579c7e9d693163baca57ceef2d2258572326f751e5d913e5f6840cc6eb339b4e20584b274606d93205120375dab3085e6df426b215ed2', 'customer', NULL),
(106, 'asd', 'scrypt:32768:8:1$Vi0gnt0MuVb77y1e$360e412da7737ad81926ea1f2657471b611c6668b4f6b3edc83dfa2aef37f49e3a9f221e4c44e2e091dbc324f25c1dd0389ae2ab4acf5d24cfd7addb490ee611', 'customer', 'hahaha@gmail.com');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `addons`
--
ALTER TABLE `addons`
  ADD PRIMARY KEY (`id_addon`);

--
-- Indexes for table `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`id_booking`),
  ADD KEY `id_user` (`id_user`),
  ADD KEY `id_room` (`id_room`);

--
-- Indexes for table `booking_addons`
--
ALTER TABLE `booking_addons`
  ADD PRIMARY KEY (`id_booking`,`id_addon`),
  ADD KEY `id_addon` (`id_addon`);

--
-- Indexes for table `rooms`
--
ALTER TABLE `rooms`
  ADD PRIMARY KEY (`id_room`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id_user`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `addons`
--
ALTER TABLE `addons`
  MODIFY `id_addon` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `bookings`
--
ALTER TABLE `bookings`
  MODIFY `id_booking` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- AUTO_INCREMENT for table `rooms`
--
ALTER TABLE `rooms`
  MODIFY `id_room` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id_user` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=107;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `bookings`
--
ALTER TABLE `bookings`
  ADD CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`),
  ADD CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`id_room`) REFERENCES `rooms` (`id_room`);

--
-- Constraints for table `booking_addons`
--
ALTER TABLE `booking_addons`
  ADD CONSTRAINT `booking_addons_ibfk_1` FOREIGN KEY (`id_booking`) REFERENCES `bookings` (`id_booking`),
  ADD CONSTRAINT `booking_addons_ibfk_2` FOREIGN KEY (`id_addon`) REFERENCES `addons` (`id_addon`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
