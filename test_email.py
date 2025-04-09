import boto3

def send_test_email():
    ses = boto3.client('ses', region_name='us-east-1')  # Or your region

    response = ses.send_email(
        Source='your-verified-sender@example.com',
        Destination={
            'ToAddresses': ['your-verified-recipient@example.com']
        },
        Message={
            'Subject': {'Data': 'Test Email from SES'},
            'Body': {
                'Text': {
                    'Data': 'This is a test email sent via Amazon SES and Python.'
                }
            }
        }
    )

    print("Email sent! Message ID:", response['MessageId'])

send_test_email()
