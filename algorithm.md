## Driver Algorithm:

# Logic:
1. when run first iterate through all emails received in last one year and check if they are already saved in the excel sheet.
      + if missing run algorithm 1 from the time the email was received and come todays date.
2. start running algorithm 1 and check email inbox every 1 minute.
!!it will be running 24/7 and checking emails every 1 minute.

# Algorithm 1:
Model A: pretrained model for specific company emails
Model B: generic model for all other emails
1. run the program to iterate emails
2. check sender company name(*)
    +if the email is from hardcoded companies send it to model A.
    +else run algorithm 2.
3. receive the output from the models in a specific format.
4. write the output to a excel sheet.


# Algorithm 2:
(This algorith should run once a day at a specific time to save computing power)
1. save all emails received in the last 24 hours to a temp folder.
2. run Model B on all emails in the temp folder.

# Model B Algorithm:
1. load the email
2. check if there is an invoice attached.
    + if yes, extract the invoice and run the model on the invoice and the email body.
    + if no, run the model on the email body only.
3. run the model gemma2:2b on the extracted text.
4. get the output in a specific format with specific attributes (**).


# (**):
ATTRIBUTES_TO_EXTRACT = {
    "mail_thread_id": "string",
    "company_name": "string",
    "purchase_date": "YYYY-MM-DD",
    "mail_received_time": "string",
    "purchase_receiver": "string",
    "total_price": "float",
    "sum of other_expanses": "float",
    "items": [
        {
            "item_name": "string",
            "quantity": "integer",
            "price": "float"
        }
    ]
}

