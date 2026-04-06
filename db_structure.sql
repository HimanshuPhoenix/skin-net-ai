CREATE TABLE `doctors_master` (
 `doctor_id` int(11) NOT NULL AUTO_INCREMENT,
 `user_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `doctor_name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
 `clinic_name` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `phone_number` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
 `timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
 PRIMARY KEY (`doctor_id`),
 KEY `doctors_master_ibfk_1` (`user_id`),
 CONSTRAINT `doctors_master_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

CREATE TABLE `medical_reports` (
 `report_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
 `user_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `report_date` date DEFAULT NULL,
 `doctor_name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
 `lab_name` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 PRIMARY KEY (`report_id`),
 KEY `user_id` (`user_id`),
 CONSTRAINT `medical_reports_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

CREATE TABLE `medicine_inventory` (
 `inventory_id` int(11) NOT NULL AUTO_INCREMENT,
 `user_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `medicine_name` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `daily_dosage` int(11) DEFAULT NULL,
 `pills_remaining` int(11) DEFAULT NULL,
 `pharmacist_contact_id` int(11) DEFAULT NULL,
 `remarks` text COLLATE utf8_unicode_ci,
 `prescription_id` int(11) DEFAULT NULL,
 PRIMARY KEY (`inventory_id`),
 KEY `user_id` (`user_id`),
 KEY `pharmacist_contact_id` (`pharmacist_contact_id`),
 KEY `fk_prescription` (`prescription_id`),
 CONSTRAINT `fk_prescription` FOREIGN KEY (`prescription_id`) REFERENCES `prescription_history` (`prescription_id`) ON DELETE SET NULL,
 CONSTRAINT `medicine_inventory_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
 CONSTRAINT `medicine_inventory_ibfk_2` FOREIGN KEY (`pharmacist_contact_id`) REFERENCES `priority_contacts` (`contact_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

CREATE TABLE `prescription_history` (
 `prescription_id` int(11) NOT NULL AUTO_INCREMENT,
 `user_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `doctor_id` int(11) DEFAULT NULL,
 `prescription_date` date DEFAULT NULL,
 `image_url` text COLLATE utf8_unicode_ci,
 `remarks` text COLLATE utf8_unicode_ci,
 PRIMARY KEY (`prescription_id`),
 KEY `prescription_history_ibfk_1` (`user_id`),
 KEY `prescription_history_ibfk_2` (`doctor_id`),
 CONSTRAINT `prescription_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
 CONSTRAINT `prescription_history_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors_master` (`doctor_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

CREATE TABLE `priority_contacts` (
 `contact_id` int(11) NOT NULL AUTO_INCREMENT,
 `user_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `contact_name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
 `role` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
 `phone_number` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
 `IsSOS` tinyint(4) NOT NULL DEFAULT '0',
 `telegram_chat_id` VARCHAR(50) COLLATE utf8_unicode_ci DEFAULT NULL;
 PRIMARY KEY (`contact_id`),
 KEY `user_id` (`user_id`),
 CONSTRAINT `priority_contacts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

CREATE TABLE `report_parameters` (
 `id` int(11) NOT NULL AUTO_INCREMENT,
 `report_id` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
 `parameter_name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
 `current_value` decimal(10,2) DEFAULT NULL,
 `normal_range` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
 PRIMARY KEY (`id`),
 KEY `report_id` (`report_id`),
 CONSTRAINT `report_parameters_ibfk_1` FOREIGN KEY (`report_id`) REFERENCES `medical_reports` (`report_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

CREATE TABLE `users` (
 `user_id` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
 `name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
 `email` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
 `mobile_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
 `telegram_chat_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
 `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
 `is_onboarded` tinyint(1) NOT NULL DEFAULT '0',
 `google_connected` tinyint(1) DEFAULT '0',
 PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

-- Stored Procedures:

DELIMITER //

CREATE PROCEDURE sp_log_prescription(
    IN p_user_id VARCHAR(255),
    IN p_doctor_name VARCHAR(100),
    IN p_clinic_name VARCHAR(255),
    IN p_phone_number VARCHAR(20),
    IN p_timings VARCHAR(100),
    IN p_prescription_date DATE,
    IN p_image_url TEXT,
    OUT p_prescription_id INT
)
BEGIN
    DECLARE v_doctor_id INT;

    -- the system to add a doctor's details if they do not already exist in the master table, and then log the prescription history
    -- This procedure securely handles both steps in a single call and returns the new prescription_id to be used by the inventory.

    -- Step 1: Check if the doctor already exists for this user
    SELECT doctor_id INTO v_doctor_id 
    FROM doctors_master 
    WHERE user_id = p_user_id AND doctor_name = p_doctor_name 
    LIMIT 1;

    -- Step 2: Insert doctor if they do not exist
    IF v_doctor_id IS NULL THEN
        INSERT INTO doctors_master (user_id, doctor_name, clinic_name, phone_number, timings)
        VALUES (p_user_id, p_doctor_name, p_clinic_name, p_phone_number, p_timings);
        SET v_doctor_id = LAST_INSERT_ID();
    END IF;

    -- Step 3: Insert the prescription history record
    INSERT INTO prescription_history (user_id, doctor_id, prescription_date, image_url)
    VALUES (p_user_id, v_doctor_id, p_prescription_date, p_image_url);

    -- Step 4: Output the new prescription ID
    SET p_prescription_id = LAST_INSERT_ID();
    
END //

DELIMITER ;

DELIMITER //

CREATE PROCEDURE sp_update_medicine_inventory(
    IN p_user_id VARCHAR(255),
    IN p_medicine_name VARCHAR(255),
    IN p_daily_dosage INT,
    IN p_new_pills INT,
    IN p_prescription_id INT
)
BEGIN
    DECLARE v_old_inventory_id INT;
    DECLARE v_old_pills INT DEFAULT 0;
    DECLARE v_total_pills INT;

    -- sp_update_medicine_inventory (Stock Rollover Logic)
    -- When a new medicine is added, the system must check if the medicine is already in stock, add the old balance to the new entry, and update the previous entry to zero with a remark
    -- This procedure calculates the math and performs the updates.

    -- Step 1: Find any existing active inventory for this exact medicine
    SELECT inventory_id, pills_remaining INTO v_old_inventory_id, v_old_pills
    FROM medicine_inventory
    WHERE user_id = p_user_id 
      AND medicine_name = p_medicine_name 
      AND pills_remaining > 0
    ORDER BY inventory_id DESC 
    LIMIT 1;

    -- Step 2: Calculate the total combined stock
    SET v_total_pills = p_new_pills + v_old_pills;

    -- Step 3: If old stock exists, mark it as zero and add the rollover remark
    IF v_old_inventory_id IS NOT NULL THEN
        UPDATE medicine_inventory
        SET pills_remaining = 0,
            remarks = CONCAT('Balance of ', v_old_pills, ' added to today’s prescription.')
        WHERE inventory_id = v_old_inventory_id;
    END IF;

    -- Step 4: Insert the newly combined active inventory record
    INSERT INTO medicine_inventory (user_id, medicine_name, daily_dosage, pills_remaining, prescription_id)
    VALUES (p_user_id, p_medicine_name, p_daily_dosage, v_total_pills, p_prescription_id);

END //

DELIMITER ;


DELIMITER //

CREATE PROCEDURE sp_save_medical_report(
    IN p_report_id VARCHAR(50),
    IN p_user_id VARCHAR(255),
    IN p_report_date DATE,
    IN p_doctor_name VARCHAR(100),
    IN p_lab_name VARCHAR(255),
    IN p_parameters_json JSON
)
BEGIN
    DECLARE v_i INT DEFAULT 0;
    DECLARE v_count INT;

	-- (Master-Detail JSON Insert)
    -- Instead of having the AI agent make 20 different tool calls to insert 20 different blood test parameters, this procedure allows the agent to pass the master report details and a single JSON array of all parameters. The database will autonomously parse the JSON and insert everything.

    -- Step 1: Insert the master medical report record
    INSERT INTO medical_reports (report_id, user_id, report_date, doctor_name, lab_name)
    VALUES (p_report_id, p_user_id, p_report_date, p_doctor_name, p_lab_name);

    -- Step 2: Extract array length and loop through the JSON to insert each parameter
    SET v_count = JSON_LENGTH(p_parameters_json);

    WHILE v_i < v_count DO
        INSERT INTO report_parameters (report_id, parameter_name, current_value, normal_range)
        VALUES (
            p_report_id,
            JSON_UNQUOTE(JSON_EXTRACT(p_parameters_json, CONCAT('$[', v_i, '].parameter_name'))),
            CAST(JSON_UNQUOTE(JSON_EXTRACT(p_parameters_json, CONCAT('$[', v_i, '].current_value'))) AS DECIMAL(10,2)),
            JSON_UNQUOTE(JSON_EXTRACT(p_parameters_json, CONCAT('$[', v_i, '].normal_range')))
        );
        SET v_i = v_i + 1;
    END WHILE;

END //

DELIMITER ;

DELIMITER //

CREATE PROCEDURE sp_compare_latest_reports(IN p_user_id VARCHAR(255))
BEGIN
    DECLARE v_latest_report_id VARCHAR(50);
    DECLARE v_prev_report_id VARCHAR(50);

    -- (Automated Trend Analysis)
    -- The scope mandates that whenever a user checks their health improvements, the app must compare previous results with current results to celebrate victories or motivate the user
    -- This procedure automatically fetches the user's two most recent reports and calculates the mathematical difference for every parameter.

    -- Step 1: Get the ID of the most recent report
    SELECT report_id INTO v_latest_report_id
    FROM medical_reports
    WHERE user_id = p_user_id ORDER BY report_date DESC LIMIT 1;

    -- Step 2: Get the ID of the second most recent report (the previous one)
    SELECT report_id INTO v_prev_report_id
    FROM medical_reports
    WHERE user_id = p_user_id ORDER BY report_date DESC LIMIT 1 OFFSET 1;

    -- Step 3: Join the parameters of both reports to show the trend
    SELECT 
        curr.parameter_name, 
        prev.current_value AS previous_value, 
        curr.current_value AS latest_value, 
        curr.normal_range,
        (curr.current_value - prev.current_value) AS numerical_difference
    FROM report_parameters curr
    LEFT JOIN report_parameters prev 
      ON curr.parameter_name = prev.parameter_name 
      AND prev.report_id = v_prev_report_id
    WHERE curr.report_id = v_latest_report_id;
    
END //

DELIMITER ;

DELIMITER //

CREATE PROCEDURE sp_get_medicine_inventory(IN p_user_id VARCHAR(255))
BEGIN

    -- (Fetching Active Stock)
    -- To send auto-reminders and allow users to order depleting medicines, the app needs to know the exact remaining stock and the pharmacist's contact details
    -- This procedure safely retrieves only active medicines (where stock > 0) and joins it with your priority contacts table.

    SELECT 
        m.inventory_id,
        m.medicine_name, 
        m.daily_dosage, 
        m.pills_remaining, 
        m.remarks,
        p.contact_name AS pharmacist_name, 
        p.phone_number AS pharmacist_number
    FROM medicine_inventory m
    LEFT JOIN priority_contacts p ON m.pharmacist_contact_id = p.contact_id
    WHERE m.user_id = p_user_id AND m.pills_remaining > 0;
END //

DELIMITER ;

DELIMITER //

-- Create the new dynamic registration procedure
CREATE PROCEDURE sp_register_contact(
    IN p_user_id VARCHAR(255),
    IN p_contact_name VARCHAR(100),
    IN p_role VARCHAR(50),
    IN p_is_sos TINYINT,
    IN p_chat_id VARCHAR(50)
)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM priority_contacts WHERE user_id = p_user_id AND telegram_chat_id = p_chat_id) THEN
        INSERT INTO priority_contacts (user_id, contact_name, role, IsSOS, telegram_chat_id)
        VALUES (p_user_id, p_contact_name, p_role, p_is_sos, p_chat_id);
    END IF;
END //

-- Fetch procedure to return ALL contacts + the IsSOS flag

CREATE PROCEDURE sp_get_priority_contacts(IN p_user_id VARCHAR(255)) 
BEGIN 
    -- Returning IsSOS allows the AI Agent to dynamically decide who gets emergency vs. routine alerts
    SELECT contact_name, role, phone_number, telegram_chat_id, IsSOS 
    FROM priority_contacts 
    WHERE user_id = p_user_id; 
END // 

DELIMITER ;

DELIMITER //

CREATE PROCEDURE sp_complete_onboarding(
    IN p_user_id VARCHAR(255),
    IN p_name VARCHAR(100),
    IN p_mobile_number VARCHAR(20),
    IN p_email VARCHAR(255),
    IN p_is_onboarded TINYINT
)
BEGIN
    UPDATE users
    SET name = p_name,
        mobile_number = p_mobile_number,
        email = p_email,
        is_onboarded = p_is_onboarded
    WHERE user_id = p_user_id;
END //

DELIMITER ;