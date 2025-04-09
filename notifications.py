# notifications.py
import boto3

# Boto3 SES client uses environment variables from Render
ses = boto3.client('ses', region_name='us-east-1')  # or your AWS_REGION

def send_email_notification(to_email, doctor_name, date, time_slot, hospital_address):
    ses.send_email(
        Source="your-verified-sender@example.com",  # ✅ Replace with your verified email in AWS SES
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": "Your Appointment Confirmation"},
            "Body": {
                "Text": {
                    "Data": f"""Your appointment with Dr. {doctor_name} is confirmed on {date} at {time_slot}.
Location: {hospital_address}"""
                }
            }
        }
    )
