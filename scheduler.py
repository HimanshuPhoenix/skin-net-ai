# pip install apscheduler
import time
from datetime import datetime, timedelta
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import mysql.connector

def get_db_connection():
    # Return your MySQL connection here
    pass

def send_telegram_message(chat_id, text):
    # Your standard requests.post to Telegram API
    pass

def check_and_send_reminders():
    """Runs every minute to check if it's time to send a medicine reminder."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    current_time = datetime.now().strftime('%H:%M:00')
    current_datetime = datetime.now()
    
    # 1. Find all users who need medicine right now
    cursor.execute("SELECT s.*, u.telegram_chat_id FROM medicine_schedules s JOIN users u ON s.user_id = u.user_id WHERE s.reminder_time = %s", (current_time,))
    due_medicines = cursor.fetchall()
    
    for med in due_medicines:
        # 2. Insert into daily_logs as PENDING
        cursor.execute("INSERT INTO daily_medication_logs (schedule_id, user_id, expected_time, status) VALUES (%s, %s, %s, 'PENDING')", 
                       (med['schedule_id'], med['user_id'], current_datetime))
        
        # 3. Send the Telegram Message directly!
        msg = f"💊 Reminder: Time to take your {med['medicine_name']} ({med['dosage']}). Please reply 'Yes' or 'I took it' once you have!"
        send_telegram_message(med['telegram_chat_id'], msg)
        
    conn.commit()

def check_missed_medications_for_sos():
    """Runs every minute to check if any PENDING logs are older than 1 hour."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    # Find logs older than 1 hour that are still PENDING
    cursor.execute("SELECT l.log_id, l.user_id, s.medicine_name FROM daily_medication_logs l JOIN medicine_schedules s ON l.schedule_id = s.schedule_id WHERE l.status = 'PENDING' AND l.expected_time <= %s", (one_hour_ago,))
    missed_meds = cursor.fetchall()
    
    for med in missed_meds:
        # Fetch SOS contacts
        cursor.execute("SELECT telegram_chat_id FROM priority_contacts WHERE user_id = %s AND IsSOS = 1", (med['user_id'],))
        contacts = cursor.fetchall()
        
        # Send SOS Alert
        for contact in contacts:
            msg = f"🚨 ALERT: The user has not confirmed taking their {med['medicine_name']} for over an hour. Please check on them."
            send_telegram_message(contact['telegram_chat_id'], msg)
            
        # Mark as Escalated so we don't spam the family every minute
        cursor.execute("UPDATE daily_medication_logs SET status = 'ESCALATED' WHERE log_id = %s", (med['log_id'],))
        
    conn.commit()

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_reminders, 'cron', minute='*')
    scheduler.add_job(check_missed_medications_for_sos, 'cron', minute='*')
    scheduler.start()
    
    print("Scheduler running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        scheduler.shutdown()