-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 12, 2026 at 01:06 PM
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
  `harga` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `addons`
--

INSERT INTO `addons` (`id_addon`, `nama_addon`, `harga`) VALUES
(1, 'Breakfast', 50000),
(2, 'Extra Bed', 100000),
(3, 'Airport Pickup', 150000),
(4, 'Laundry', 30000);

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
  `status` varchar(20) NOT NULL DEFAULT 'Menunggu'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bookings`
--

INSERT INTO `bookings` (`id_booking`, `id_user`, `id_room`, `tanggal_checkin`, `tanggal_checkout`, `total_harga`, `status`) VALUES
(23, 101, 7, '2026-11-27', '2026-12-01', 3800000, 'batal'),
(25, 104, 7, '2026-11-06', '2026-11-08', 2100000, 'batal'),
(26, 105, 7, '2026-11-11', '2026-11-18', 6980000, 'batal'),
(27, 105, 5, '2026-11-12', '2026-12-26', 15550000, 'batal'),
(28, 101, 7, '2026-11-25', '2026-11-26', 1000000, 'batal'),
(29, 101, 6, '2026-11-11', '2026-11-12', 880000, 'batal'),
(30, 104, 5, '2026-11-14', '2026-11-18', 1550000, 'batal'),
(31, 104, 5, '2026-11-13', '2026-11-18', 1750000, 'batal'),
(32, 104, 5, '2026-11-21', '2026-11-27', 2100000, 'batal'),
(33, 104, 5, '2026-11-20', '2026-11-27', 2450000, 'batal'),
(34, 104, 5, '2026-11-12', '2026-11-21', 3150000, 'batal'),
(35, 104, 5, '2026-11-12', '2026-11-21', 3150000, 'batal'),
(36, 104, 5, '2026-11-13', '2026-11-28', 5400000, 'lunas');

-- --------------------------------------------------------

--
-- Table structure for table `booking_addons`
--

CREATE TABLE `booking_addons` (
  `id_booking` int(11) NOT NULL,
  `id_addon` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `booking_addons`
--

INSERT INTO `booking_addons` (`id_booking`, `id_addon`) VALUES
(25, 1),
(25, 3),
(26, 1),
(26, 2),
(26, 3),
(26, 4),
(27, 3),
(28, 1),
(29, 1),
(29, 2),
(29, 3),
(29, 4),
(30, 3),
(36, 3);

-- --------------------------------------------------------

--
-- Table structure for table `rooms`
--

CREATE TABLE `rooms` (
  `id_room` int(11) NOT NULL,
  `nomor_kamar` varchar(10) NOT NULL,
  `tipe_kamar` varchar(50) NOT NULL,
  `harga_per_malam` int(11) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Tersedia'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `rooms`
--

INSERT INTO `rooms` (`id_room`, `nomor_kamar`, `tipe_kamar`, `harga_per_malam`, `status`) VALUES
(5, '102', 'Standard', 350000, 'Tersedia'),
(6, '201', 'Deluxe', 550000, 'Tersedia'),
(7, '301', 'Suite', 950000, 'Tersedia');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id_user` int(11) NOT NULL,
  `nama` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','customer') DEFAULT 'customer'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id_user`, `nama`, `username`, `password`, `role`) VALUES
(101, 'admin', 'admin123', 'scrypt:32768:8:1$BPVeFcIJTWfIYuXL$ebe061bb81b9813d3a906bc7f0e44c6d3a9252b3ca202495e8a3b5e1dbb35eca74b0af59e393339e3e833162f7bb9c749ed2db9f4426f7cd60b2a8bf52883f5a', 'admin'),
(104, 'npc', 'pembeli', 'scrypt:32768:8:1$2DnM1CkaX0OGneBJ$fa1deae633478cc48b14d3e7f7adb923c6fd2e78c4ca42f0c35f907a5992ee8a1f9bbeee8af5fdb6c57a7dc5b3f1fb636613c5e0d09e918f07f497bab923681d', 'customer'),
(105, 'samlekom', 'samlekom', 'scrypt:32768:8:1$XuujSsDpUPW34IKA$eeba23c71272455bd2b579c7e9d693163baca57ceef2d2258572326f751e5d913e5f6840cc6eb339b4e20584b274606d93205120375dab3085e6df426b215ed2', 'customer');

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
  ADD UNIQUE KEY `username` (`username`);

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
  MODIFY `id_booking` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `rooms`
--
ALTER TABLE `rooms`
  MODIFY `id_room` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id_user` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=106;

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
